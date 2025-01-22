#!/bin/bash

# Author: masood.faisal@gmail.com
# This script provision a minimal, non-production ready, EKS cluster with two nodes and karpenter configuration. The script install karpenter and Kuberay operator on the cluster.


# Check if the script has passed CLUSTER_NAME and REGION as arguments
# if [[ $# -ne 2 ]]; then
#   echo "Usage: $0 <param1> <param2>"
#   exit 1
# fi



REGION=us-east-1
CLUSTER_NAME=llm-eks-cluster


# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo "jq is not installed. Please install jq and try again."
  exit 1
fi

# Check if yq is installed
if ! command -v yq &> /dev/null; then
  echo "yq is not installed. Please install yq and try again."
  exit 1
fi

if ! command -v eksctl &> /dev/null; then
  echo "eksctl is not installed. Please install eksctl and eksctl again."
  exit 1
fi


# Check if cluster exists and delete if it does
if aws eks describe-cluster --name "${CLUSTER_NAME}" --region "${REGION}" >/dev/null 2>&1; then
    echo "Found existing cluster ${CLUSTER_NAME} in region ${REGION}, proceeding with deletion..."
    eksctl delete cluster --name "${CLUSTER_NAME}" --region "${REGION}" --wait
    echo "Cluster deletion completed"
else
    echo "No existing cluster named ${CLUSTER_NAME} in region ${REGION}, skipping deletion"
fi

# Check if cluster exists and delete if it does
if aws eks describe-cluster --name "${CLUSTER_NAME}" --region "${REGION}" >/dev/null 2>&1; then
    echo "Found existing cluster ${CLUSTER_NAME} in region ${REGION}, proceeding with deletion..."
    
    # Delete the CloudFormation stack directly
    STACK_NAME="eksctl-${CLUSTER_NAME}-cluster"
    echo "Deleting CloudFormation stack: ${STACK_NAME}"
    aws cloudformation delete-stack --stack-name "${STACK_NAME}"
    echo "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}"
    echo "Stack deletion completed"
else
    echo "No existing cluster named ${CLUSTER_NAME} in region ${REGION}, skipping deletion"
fi



ALLOWED_VPC=$(aws service-quotas get-service-quota --service-code vpc --quota-code L-F678F1CE | jq '.Quota.Value | floor')
CONSUMED_VPC=$(aws ec2 describe-vpcs --query "Vpcs" --output json | jq '. | length')
if [[ $CONSUMED_VPC -ge $ALLOWED_VPC ]]; then
  echo "You have reached the limit of VPCs in your account. This script will need to create a new VPC! Exiting ..."
  exit 1
else
  echo "You have $CONSUMED_VPC VPCs in your account. You can create $((ALLOWED_VPC - CONSUMED_VPC)) more VPCs."
fi

# get user ARN and store it in a variable
# IAM_PRINCIPAL_ARN=$(aws sts get-caller-identity --query "Arn" --output text)
IAM_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
IAM_PRINCIPAL_ARN=arn:aws:sts::${IAM_ACCOUNT_ID}:assumed-role/Admin/{{SessionName}}
IAM_PRINCIPAL_ROLE_ARN=arn:aws:iam::${IAM_ACCOUNT_ID}:role/Admin

# validate and fail if there is no user ARN
if [[ -z $IAM_PRINCIPAL_ARN ]]; then
  echo "Failed to get the user ARN. Make sure that you are logged in to the AWS CLI with the correct user."
  exit 1
fi


# create cluster using eksctl

eksctl create cluster --name=$CLUSTER_NAME --version 1.31 --nodes=2 --region=$REGION --managed --auto-kubeconfig 

# add addons
# Check and install VPC-CNI
if ! aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name vpc-cni >/dev/null 2>&1; then
    echo "Installing vpc-cni addon..."
    aws eks create-addon --cluster-name $CLUSTER_NAME --addon-name vpc-cni
else
    echo "vpc-cni addon already exists"
fi
aws eks describe-addon --addon-name vpc-cni --cluster-name $CLUSTER_NAME

# Check and install CoreDNS
if ! aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name coredns >/dev/null 2>&1; then
    echo "Installing coredns addon..."
    aws eks create-addon --cluster-name $CLUSTER_NAME --addon-name coredns
else
    echo "coredns addon already exists"
fi
aws eks describe-addon --addon-name coredns --cluster-name $CLUSTER_NAME

# Check and install Pod Identity Agent
if ! aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name eks-pod-identity-agent >/dev/null 2>&1; then
    echo "Installing eks-pod-identity-agent addon..."
    aws eks create-addon --cluster-name $CLUSTER_NAME --addon-name eks-pod-identity-agent
else
    echo "eks-pod-identity-agent addon already exists"
fi
aws eks describe-addon --addon-name eks-pod-identity-agent --cluster-name $CLUSTER_NAME



# list access policies
aws eks list-access-policies 

aws eks update-cluster-config --name $CLUSTER_NAME --access-config authenticationMode=API


# Add an access entry to allow current AWS user to be ClusterAdmin access policy
#aws eks create-access-entry --cluster-name $CLUSTER_NAME --principal-arn $IAM_PRINCIPAL_ROLE_ARN
#aws eks associate-access-policy --cluster-name $CLUSTER_NAME --principal-arn $IAM_PRINCIPAL_ARN --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy --access-scope type=cluster


aws eks update-kubeconfig --name $CLUSTER_NAME  --region $REGION
kubectl -n kube-system get pods

#install cert manager
echo "Adding Cert Manager ..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.3/cert-manager.yaml

echo "Base EKS Setup completed"




# deploy Karpenter on EKS
echo "Adding Karpenter ..."

export KARPENTER_NAMESPACE="kube-system"
export KARPENTER_VERSION="1.0.3"
export K8S_VERSION="1.31"
export AWS_PARTITION="aws" # if you are not using standard partitions, you may need to configure to aws-cn / aws-us-gov
export AWS_DEFAULT_REGION=${REGION}
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export TEMPOUT="$(mktemp)"


KARPENTER_ROLE_NAME="FMKarpenterRole"
KARPENTER_POLICY_NAME="FMKARPENTERPolicy"

export KARPENTER_ROLE_NAME

# Create the IAM role
aws iam create-role --role-name $KARPENTER_ROLE_NAME --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "pods.eks.amazonaws.com"
    },
    "Action": ["sts:AssumeRole","sts:TagSession"]
  }]
}'

# Create the policy
# https://karpenter.sh/docs/getting-started/migrating-from-cas/
# this is useful too
aws iam create-policy --policy-name $KARPENTER_POLICY_NAME --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ec2:DescribeImages",
        "ec2:RunInstances",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeInstanceTypeOfferings",
        "ec2:DeleteLaunchTemplate",
        "ec2:CreateTags",
        "ec2:CreateLaunchTemplate",
        "ec2:CreateFleet",
        "ec2:DescribeSpotPriceHistory",
        "pricing:GetProducts",
        "ec2:TerminateInstances",
        "ec2:CreateTags",
        "iam:PassRole",
        "eks:DescribeCluster",
        "iam:CreateInstanceProfile",
        "iam:TagInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:DeleteInstanceProfile",  
        "iam:GetInstanceProfile",
        "sqs:*"      

      ],
      "Resource": [
        "*"
      ]
    }
  ]
}'

# Attach the policy to the role
KARPENTER_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='$KARPENTER_POLICY_NAME'].Arn" --output text)
aws iam attach-role-policy --role-name $KARPENTER_ROLE_NAME --policy-arn $KARPENTER_POLICY_ARN

# Get the ARN of the role
KARPENTER_ROLE_ARN=$(aws iam get-role --role-name $KARPENTER_ROLE_NAME --query "Role.Arn" --output text)
aws eks create-pod-identity-association --cluster-name $CLUSTER_NAME --namespace karpenter --service-account karpenter --role-arn $KARPENTER_ROLE_ARN
aws eks list-pod-identity-associations --cluster-name $CLUSTER_NAME

CLUSTER_ENDPOINT="$(aws eks describe-cluster --name ${CLUSTER_NAME} --query "cluster.endpoint" --output text)"
echo $CLUSTER_ENDPOINT
echo $KARPENTER_ROLE_ARN

# Create an SQS queue
QUEUE_NAME=${CLUSTER_NAME}
aws sqs create-queue --queue-name $QUEUE_NAME --region $REGION

helm registry logout public.ecr.aws

helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter --version 1.0.0 --namespace karpenter --create-namespace \
  --set "serviceAccount.annotations.eks\.amazonaws\.com/role-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:role/${KARPENTER_ROLE_NAME}" \
  --set "settings.clusterName=${CLUSTER_NAME}" \
  --set "settings.interruptionQueue=${CLUSTER_NAME}" \
  --set controller.resources.requests.cpu=1 \
  --set controller.resources.requests.memory=1Gi \
  --set controller.resources.limits.cpu=1 \
  --set controller.resources.limits.memory=1Gi \
  --wait





## KubeRay
# https://github.com/ray-project/kuberay/blob/master/helm-chart/ray-cluster/README.md
echo "Adding Kubray Operator ..."
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update

helm install kuberay-operator kuberay/kuberay-operator --namespace kuberay-system  --create-namespace --version 1.2.2

# Register Node Pool
# get role of managed worker nodes to be associated to karpenter nodes
NODE_ROLE_PATTERN=eksctl-${CLUSTER_NAME}-nodegroup-ng-
NODE_ROLE_NAME=$(aws iam list-roles --query "Roles[?starts_with(RoleName, '${NODE_ROLE_PATTERN}')].RoleName" --output text | head -n 1)


export CLUSTER_NAME
export NODE_ROLE_NAME

update_cluster_name_in_yaml() {
  local filename=$1
  echo "Changing $filename to update the cluster tag for your cluster $CLUSTER_NAME"
  yq eval 'select(.kind == "EC2NodeClass").spec.subnetSelectorTerms[].tags."eksctl.cluster.k8s.io/v1alpha1/cluster-name" = env(CLUSTER_NAME)' -i "$filename"
  yq eval 'select(.kind == "EC2NodeClass").spec.securityGroupSelectorTerms[].tags."eksctl.cluster.k8s.io/v1alpha1/cluster-name"  = env(CLUSTER_NAME)' -i "$filename"
  yq eval 'select(.kind == "EC2NodeClass").spec.role = env(NODE_ROLE_NAME)' -i "$filename"

}

update_cluster_name_in_yaml "../karpenter-pools/karpenter-cpu.yaml"
update_cluster_name_in_yaml "../karpenter-pools/karpenter-cpu-inference.yaml"
update_cluster_name_in_yaml "../karpenter-pools/karpenter-cpu-inference-arm.yaml"

echo "Creating Krpenter NodePools..."
kubectl create -f ../karpenter-pools/karpenter-cpu.yaml
kubectl create -f ../karpenter-pools/karpenter-cpu-inference.yaml
kubectl create -f ../karpenter-pools/karpenter-cpu-inference-arm.yaml


kubectl config set-context --current --namespace=kuberay-system  # set the namespace to kuberay-system

echo "Ready to deploy your Ray Service...."
#######################################

echo "Adding Grafana and Prometheus"
# PROM and GRAFANA
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts

helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace --wait

helm install grafana grafana/grafana --namespace monitoring --create-namespace --wait

kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

kubectl create -f prometheus-monitoring.yaml 



#!/bin/bash

# Script to validate existing EKS cluster and install KubeRay and NVIDIA GPU operators

set -e

# Color codes for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to display messages with timestamp
log() {
  echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
  exit 1
}

success() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
  log "Checking prerequisites..."
  
  # Check AWS CLI
  if ! command -v aws &> /dev/null; then
    error "AWS CLI is not installed. Please install it first."
  fi
  
  # Check kubectl
  if ! command -v kubectl &> /dev/null; then
    error "kubectl is not installed. Please install it first."
  fi
  
  # Check helm
  if ! command -v helm &> /dev/null; then
    error "Helm is not installed. Please install it first."
  fi
  
  # Check AWS credentials
  if ! aws sts get-caller-identity &> /dev/null; then
    error "AWS credentials not configured or invalid. Please configure AWS CLI."
  fi
  
  success "All prerequisites satisfied."
}

# Validate existing EKS cluster
validate_eks_cluster() {
  log "Validating existing EKS cluster..."
  
  # Check if kubectl is configured to access a cluster
  if ! kubectl cluster-info &> /dev/null; then
    error "Cannot access Kubernetes cluster. Please check your kubeconfig."
  fi
  
  # Get cluster info
  CLUSTER_INFO=$(kubectl cluster-info)
  log "Connected to Kubernetes cluster:"
  echo "$CLUSTER_INFO"
  
  # Check nodes
  log "Checking cluster nodes..."
  NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
  if [ "$NODE_COUNT" -lt 1 ]; then
    error "No nodes found in the cluster. Please check your EKS cluster."
  fi
  
  log "Found $NODE_COUNT nodes in the cluster:"
  kubectl get nodes
  
  # Check for GPU nodes (optional)
  if kubectl get nodes -o=custom-columns=NAME:.metadata.name,GPU:.status.capacity.nvidia\\.com\\/gpu --no-headers | grep -v "<none>" &> /dev/null; then
    log "GPU nodes detected in the cluster."
  else
    warn "No GPU nodes detected. NVIDIA GPU operator will still be installed but may not be utilized."
  fi
  
  success "EKS cluster validation completed successfully!"
}

# Install KubeRay operator
install_kuberay_operator() {
  log "Installing KubeRay operator..."
  
  # Create namespace for KubeRay
  kubectl create namespace kuberay --dry-run=client -o yaml | kubectl apply -f -
  
  # Add KubeRay Helm repository
  helm repo add kuberay https://ray-project.github.io/kuberay-helm/
  helm repo update
  
  # Check if KubeRay operator is already installed
  if helm list -n kuberay | grep kuberay-operator &> /dev/null; then
    warn "KubeRay operator is already installed. Upgrading..."
    helm upgrade kuberay-operator kuberay/kuberay-operator -n kuberay
  else
    # Install KubeRay operator
    helm install kuberay-operator kuberay/kuberay-operator -n kuberay
  fi
  
  # Wait for the operator to be ready
  log "Waiting for KubeRay operator to be ready..."
  kubectl wait --for=condition=available --timeout=300s deployment/kuberay-operator -n kuberay
  
  success "KubeRay operator installed successfully!"
}

# Install NVIDIA GPU operator
install_nvidia_gpu_operator() {
  log "Installing NVIDIA GPU operator..."
  
  # Create namespace for GPU operator
  kubectl create namespace gpu-operator --dry-run=client -o yaml | kubectl apply -f -
  
  # Add NVIDIA Helm repository
  helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
  helm repo update
  
  # Check if NVIDIA GPU operator is already installed
  if helm list -n gpu-operator | grep gpu-operator &> /dev/null; then
    warn "NVIDIA GPU operator is already installed. Upgrading..."
    helm upgrade -n gpu-operator $(helm list -n gpu-operator | grep gpu-operator | awk '{print $1}') nvidia/gpu-operator
  else
    # Install NVIDIA GPU operator
    helm install --wait --generate-name \
      -n gpu-operator \
      nvidia/gpu-operator
  fi
  
  # Wait for the operator to be ready
  log "Waiting for NVIDIA GPU operator to be ready..."
  kubectl wait --for=condition=available --timeout=600s -n gpu-operator deployment/gpu-operator-node-feature-discovery-master 2>/dev/null || true
  kubectl wait --for=condition=available --timeout=600s -n gpu-operator deployment/gpu-operator 2>/dev/null || true
  
  success "NVIDIA GPU operator installed successfully!"
}

# Verify installations
verify_installations() {
  log "Verifying KubeRay operator installation..."
  kubectl get all -n kuberay
  
  log "Verifying NVIDIA GPU operator installation..."
  kubectl get all -n gpu-operator
  
  log "Checking for RayCluster CRD..."
  if kubectl get crd rayclusters.ray.io &> /dev/null; then
    success "RayCluster CRD is installed."
  else
    warn "RayCluster CRD not found. KubeRay operator might not be functioning correctly."
  fi
  
  log "Checking for NVIDIA GPU operator components..."
  if kubectl get pods -n gpu-operator | grep -q "nvidia-device-plugin"; then
    success "NVIDIA device plugin found."
  else
    warn "NVIDIA device plugin not found. GPU operator might still be initializing."
  fi
}

# Main execution
main() {
  log "Starting validation and installation process..."
  
  check_prerequisites
  validate_eks_cluster
  install_kuberay_operator
  install_nvidia_gpu_operator
  verify_installations
  
  success "All components installed successfully!"
  log "Your EKS cluster now has KubeRay and NVIDIA GPU operators installed."
}

# Execute main function
main

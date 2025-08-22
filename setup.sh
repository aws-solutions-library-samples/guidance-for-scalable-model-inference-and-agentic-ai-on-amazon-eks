#!/bin/bash

# Script to deploy model observability services

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

# Function to check if Langfuse is already deployed
check_existing_deployment() {
  if kubectl get pods -l app.kubernetes.io/instance=langfuse --no-headers 2>/dev/null | grep -q "Running"; then
    warn "Langfuse appears to be already running. Checking deployment status..."
    kubectl get pods -l app.kubernetes.io/instance=langfuse
    return 0
  fi
  return 1
}

log "Checking for existing Langfuse deployment..."
if check_existing_deployment; then
  log "Langfuse is already deployed and running. Skipping deployment steps..."
else
  log "Installing Langfuse secrets..."
  if kubectl apply -f langfuse-secret.yaml --dry-run=client > /dev/null 2>&1; then
    kubectl apply -f langfuse-secret.yaml
    success "Langfuse secrets applied successfully!"
  else
    error "Failed to validate langfuse-secret.yaml"
  fi

  log "Adding Langfuse Helm repository..."
  helm repo add langfuse https://langfuse.github.io/langfuse-k8s
  helm repo update
  success "Langfuse Helm repository added and updated!"

  log "Installing Langfuse using Helm..."
  if [ -f "langfuse-value.yaml" ]; then
    helm install langfuse langfuse/langfuse -f langfuse-value.yaml \
      --set nodeSelector."kubernetes\.io/arch"=arm64 \
      --set global.storageClass=auto-ebs-sc
    success "Langfuse Helm installation initiated with arm64 node selector and auto-ebs-sc storage class!"
  else
    error "langfuse-value.yaml not found"
  fi

  log "Creating Redis port configuration patch..."
  cat <<EOF > langfuse-redis-port-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langfuse-web
  namespace: default
spec:
  template:
    spec:
      containers:
      - name: langfuse-web
        env:
        - name: REDIS_PORT
          value: "6379"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langfuse-worker
  namespace: default
spec:
  template:
    spec:
      containers:
      - name: langfuse-worker
        env:
        - name: REDIS_PORT
          value: "6379"
EOF
  success "Redis port configuration patch created!"

  log "Applying Redis port configuration patch..."
  kubectl apply -f langfuse-redis-port-patch.yaml
  success "Redis port configuration patch applied!"

  log "Waiting for Langfuse pods to be running (timeout: 10 minutes)..."
  # Wait for a short time to allow pods to start
  sleep 30
  
  # Check if all pods are in Running state (regardless of readiness)
  TIMEOUT=600
  START_TIME=$(date +%s)
  while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED_TIME=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED_TIME -gt $TIMEOUT ]; then
      error "Langfuse deployment failed - pods did not enter Running state within 10 minutes"
      break
    fi
    
    # Count total pods and running pods
    TOTAL_PODS=$(kubectl get pods --selector=app.kubernetes.io/instance=langfuse --no-headers | wc -l)
    RUNNING_PODS=$(kubectl get pods --selector=app.kubernetes.io/instance=langfuse --no-headers | grep -c "Running" || true)
    
    if [ "$TOTAL_PODS" -eq "$RUNNING_PODS" ] && [ "$TOTAL_PODS" -gt 0 ]; then
      success "Langfuse deployment completed successfully! All $TOTAL_PODS pods are running."
      kubectl get pods --selector=app.kubernetes.io/instance=langfuse
      break
    else
      log "Waiting for pods to be running ($RUNNING_PODS/$TOTAL_PODS are running)... Elapsed time: ${ELAPSED_TIME}s"
      sleep 10
    fi
  done
fi

log "Installing Langfuse web ingress..."
if [ -f "langfuse-web-ingress.yaml" ]; then
  if kubectl apply -f langfuse-web-ingress.yaml; then
    success "Langfuse web ingress installed successfully!"
  else
    warn "Failed to install Langfuse web ingress, but continuing..."
  fi
else
  warn "langfuse-web-ingress.yaml not found, skipping ingress installation"
fi

log "Verifying Langfuse installation..."
kubectl get pods -l app.kubernetes.io/instance=langfuse
kubectl get service -l app.kubernetes.io/instance=langfuse
kubectl get ingress langfuse-web-ingress 2>/dev/null || warn "Langfuse ingress not found"

success "Model observability setup completed!"
log "Refer to README.md to access Langfuse and define Public/Private Keys"

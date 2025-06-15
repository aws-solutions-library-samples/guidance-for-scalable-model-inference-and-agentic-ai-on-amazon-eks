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

log "Installing Langfuse service account..."
kubectl create -f langfuse-sa.yaml 

log "Installing Langfuse deployment..."
kubectl create -f langfuse.yaml 

# helm repo add langfuse https://langfuse.github.io/langfuse-k8s
# helm repo update

# # SALT=$(openssl rand -hex 16)
# SALT="NOT_SALTY"

# helm install langfuse langfuse/langfuse --create-namespace -n genai -f values.yaml

log "Waiting for Langfuse pods to be ready..."
kubectl wait --for=condition=ready pods --selector=app.kubernetes.io/instance=langfuse --timeout=300s 

success "Langfuse deployment completed successfully!"

log "Installing Langfuse web ingress..."
if [ -f "langfuse-web-ingress.yaml" ]; then
  kubectl apply -f langfuse-web-ingress.yaml
  success "Langfuse web ingress installed successfully!"
else
  error "langfuse-web-ingress.yaml not found"
fi

log "Verifying Langfuse installation..."
kubectl get pods -l app.kubernetes.io/instance=langfuse
kubectl get service -l app.kubernetes.io/instance=langfuse
kubectl get ingress langfuse-web-ingress 2>/dev/null || warn "Langfuse ingress not found"

success "Model observability setup completed!"
log "Refer to README.md to access Langfuse and define Public/Private Keys"


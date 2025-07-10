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
  log "Installing Langfuse service account..."
  if kubectl apply -f langfuse-sa.yaml --dry-run=client > /dev/null 2>&1; then
    kubectl apply -f langfuse-sa.yaml
    success "Langfuse service accounts applied successfully!"
  else
    warn "Failed to validate langfuse-sa.yaml, skipping..."
  fi

  log "Installing Langfuse deployment..."
  if kubectl apply -f langfuse.yaml --dry-run=client > /dev/null 2>&1; then
    kubectl apply -f langfuse.yaml
    success "Langfuse deployment applied successfully!"
  else
    warn "Failed to validate langfuse.yaml, skipping..."
  fi

  # helm repo add langfuse https://langfuse.github.io/langfuse-k8s
  # helm repo update

  # # SALT=$(openssl rand -hex 16)
  # SALT="NOT_SALTY"

  # helm install langfuse langfuse/langfuse --create-namespace -n genai -f values.yaml

  log "Waiting for Langfuse pods to be ready..."
  kubectl wait --for=condition=ready pods --selector=app.kubernetes.io/instance=langfuse --timeout=300s 

  success "Langfuse deployment completed successfully!"
fi

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

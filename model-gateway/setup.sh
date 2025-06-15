#!/bin/bash

# Script to deploy model gateway services

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
  
  # Check kubectl
  if ! command -v kubectl &> /dev/null; then
    error "kubectl is not installed. Please install it first."
  fi
  
  # Check if kubectl is configured to access a cluster
  if ! kubectl cluster-info &> /dev/null; then
    error "Cannot access Kubernetes cluster. Please check your kubeconfig."
  fi
  
  success "All prerequisites satisfied."
}

# Install LiteLLM deployment
install_litellm_deployment() {
  log "Installing LiteLLM deployment..."
  
  if [ -f "litellm-deployment.yaml" ]; then
    kubectl apply -f litellm-deployment.yaml
    success "LiteLLM deployment applied successfully!"
  else
    error "litellm-deployment.yaml not found"
  fi
}

# Wait for LiteLLM service to be running
wait_for_litellm_service() {
  log "Waiting for LiteLLM service to be ready..."
  
  # Wait for deployment to be available
  kubectl wait --for=condition=available --timeout=600s deployment/litellm-deployment 2>/dev/null || {
    warn "LiteLLM deployment might still be initializing. Checking pod status..."
    kubectl get pods -l app=litellm
  }
  
  # Check if pods are running
  local max_attempts=30
  local attempt=1
  
  while [ $attempt -le $max_attempts ]; do
    local running_pods=$(kubectl get pods -l app=litellm --field-selector=status.phase=Running --no-headers | wc -l)
    
    if [ "$running_pods" -gt 0 ]; then
      success "LiteLLM service is running!"
      kubectl get pods -l app=litellm
      return 0
    fi
    
    log "Attempt $attempt/$max_attempts: Waiting for LiteLLM pods to be running..."
    sleep 10
    ((attempt++))
  done
  
  error "LiteLLM service failed to start within the expected time. Please check the logs."
}

# Install LiteLLM ingress
install_litellm_ingress() {
  log "Installing LiteLLM ingress..."
  
  if [ -f "litellm-ingress.yaml" ]; then
    kubectl apply -f litellm-ingress.yaml
    success "LiteLLM ingress applied successfully!"
  else
    error "litellm-ingress.yaml not found"
  fi
}

# Verify installations
verify_installations() {
  log "Verifying installations..."
  
  log "Checking LiteLLM deployment..."
  kubectl get deployment litellm-deployment
  
  log "Checking LiteLLM service..."
  kubectl get service litellm-service
  
  log "Checking LiteLLM ingress..."
  kubectl get ingress litellm-ingress
  
  log "Checking LiteLLM pods..."
  kubectl get pods -l app=litellm
  
  # Get ingress URL if available
  local ingress_url=$(kubectl get ingress litellm-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
  if [ -n "$ingress_url" ]; then
    log "LiteLLM is accessible at: https://$ingress_url"
  else
    log "Ingress URL not yet available. It may take a few minutes for the load balancer to be provisioned."
  fi
  
  success "Installation verification completed!"
}

# Main execution
main() {
  log "Starting model gateway deployment..."
  
  check_prerequisites
  install_litellm_deployment
  wait_for_litellm_service
  install_litellm_ingress
  verify_installations
  
  success "Model gateway deployed successfully!"
  log "LiteLLM proxy is now available and can route requests to your model backends."
}

# Execute main function
main

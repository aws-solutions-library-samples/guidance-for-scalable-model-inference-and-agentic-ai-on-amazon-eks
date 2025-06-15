#!/bin/bash

# Script to deploy model hosting services

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

# Install Ray service with llamacpp and embedding
install_ray_llamacpp_embedding() {
  log "Installing Ray service with llamacpp and embedding..."
  
  if [ -f "ray-services/ray-service-llamacpp-with-embedding.yaml" ]; then
    kubectl apply -f ray-services/ray-service-llamacpp-with-embedding.yaml
    success "Ray service with llamacpp and embedding deployed successfully!"
  else
    error "ray-service-llamacpp-with-embedding.yaml not found in ray-services directory"
  fi
}

# Install standalone vLLM reasoning service
install_standalone_vllm_reasoning() {
  log "Installing standalone vLLM reasoning service..."
  
  if [ -f "standalone-vllm-reasoning.yaml" ]; then
    kubectl apply -f standalone-vllm-reasoning.yaml
    success "Standalone vLLM reasoning service deployed successfully!"
  else
    error "standalone-vllm-reasoning.yaml not found"
  fi
}

# Install standalone vLLM vision service
install_standalone_vllm_vision() {
  log "Installing standalone vLLM vision service..."
  
  if [ -f "standalone-vllm-vision.yaml" ]; then
    kubectl apply -f standalone-vllm-vision.yaml
    success "Standalone vLLM vision service deployed successfully!"
  else
    error "standalone-vllm-vision.yaml not found"
  fi
}

# Wait for services to be ready
wait_for_services() {
  log "Waiting for services to be ready..."
  
  # Wait for Ray service
  log "Waiting for Ray service to be ready..."
  kubectl wait --for=condition=ready --timeout=600s rayservice --all 2>/dev/null || warn "Ray service might still be initializing"
  
  # Wait for standalone services
  log "Waiting for standalone services to be ready..."
  kubectl wait --for=condition=available --timeout=600s deployment --all 2>/dev/null || warn "Some deployments might still be initializing"
  
  success "Services are ready!"
}

# Verify installations
verify_installations() {
  log "Verifying installations..."
  
  log "Checking Ray services..."
  kubectl get rayservice
  
  log "Checking deployments..."
  kubectl get deployments
  
  log "Checking services..."
  kubectl get services
  
  log "Checking pods..."
  kubectl get pods
  
  success "Installation verification completed!"
}

# Main execution
main() {
  log "Starting model hosting deployment..."
  
  check_prerequisites
  install_ray_llamacpp_embedding
  install_standalone_vllm_reasoning
  install_standalone_vllm_vision
  wait_for_services
  verify_installations
  
  success "All model hosting services deployed successfully!"
  log "You can now access your model hosting services."
}

# Execute main function
main

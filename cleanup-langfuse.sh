#!/bin/bash

# Script to clean up Langfuse deployment

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

success() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log "Uninstalling Langfuse Helm release..."
helm uninstall langfuse || warn "Failed to uninstall Langfuse Helm release, it may not exist"

log "Deleting Langfuse PVCs..."
kubectl delete pvc data-langfuse-clickhouse-shard0-0 data-langfuse-clickhouse-shard0-1 data-langfuse-clickhouse-shard0-2 data-langfuse-postgresql-0 data-langfuse-zookeeper-0 data-langfuse-zookeeper-1 data-langfuse-zookeeper-2 langfuse-s3 valkey-data-langfuse-redis-primary-0 || warn "Failed to delete some PVCs, they may not exist"

log "Waiting for resources to be cleaned up (30 seconds)..."
sleep 30

success "Langfuse cleanup completed!"
log "You can now run setup.sh to reinstall Langfuse with the auto-ebs-sc storage class"

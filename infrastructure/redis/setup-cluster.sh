#!/bin/bash

# Redis Cluster Setup Script
# This script sets up a Redis cluster for distributed caching

set -e

echo "🚀 Setting up Redis Cluster for distributed caching..."

# Configuration
CLUSTER_NODES=6
REPLICAS=1
REDIS_PASSWORD="redis_cluster_password_change_me"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Redis CLI is available
if ! command -v redis-cli &> /dev/null; then
    print_warning "Redis CLI not found. Installing via Docker..."
    REDIS_CLI="docker run --rm -it --network redis_redis-cluster-network redis:7-alpine redis-cli"
else
    REDIS_CLI="redis-cli"
fi

# Start Redis cluster
print_status "Starting Redis cluster containers..."
docker-compose -f docker-compose.redis-cluster.yml up -d

# Wait for containers to be ready
print_status "Waiting for Redis nodes to be ready..."
sleep 15

# Check if all nodes are running
for i in {1..6}; do
    port=$((7000 + i))
    if ! docker exec redis-cluster-node-$i redis-cli -p 7000 ping > /dev/null 2>&1; then
        print_error "Redis node $i is not responding"
        exit 1
    fi
done

print_status "All Redis nodes are running successfully!"

# Create cluster
print_status "Creating Redis cluster..."
docker exec redis-cluster-node-1 redis-cli --cluster create \
    redis-node-1:7000 \
    redis-node-2:7000 \
    redis-node-3:7000 \
    redis-node-4:7000 \
    redis-node-5:7000 \
    redis-node-6:7000 \
    --cluster-replicas 1 \
    --cluster-yes

# Verify cluster status
print_status "Verifying cluster status..."
docker exec redis-cluster-node-1 redis-cli -p 7000 cluster info

# Test cluster functionality
print_status "Testing cluster functionality..."
docker exec redis-cluster-node-1 redis-cli -p 7000 set test_key "Hello Redis Cluster"
docker exec redis-cluster-node-2 redis-cli -p 7000 get test_key

print_status "✅ Redis cluster setup completed successfully!"
print_status "Cluster nodes are available at:"
for i in {1..6}; do
    port=$((7000 + i))
    echo "  - Node $i: localhost:$port"
done

print_status "To connect to the cluster:"
echo "  redis-cli -c -p 7001"

print_status "To monitor cluster:"
echo "  docker exec redis-cluster-node-1 redis-cli -p 7000 cluster nodes"

print_status "To stop cluster:"
echo "  docker-compose -f docker-compose.redis-cluster.yml down"
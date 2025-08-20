# Redis Cluster Setup Script for Windows PowerShell
# This script sets up a Redis cluster for distributed caching

param(
    [switch]$Force,
    [string]$Password = "redis_cluster_password_change_me"
)

# Configuration
$ClusterNodes = 6
$Replicas = 1

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Status "🚀 Setting up Redis Cluster for distributed caching..."

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker and try again."
    exit 1
}

# Start Redis cluster
Write-Status "Starting Redis cluster containers..."
docker-compose -f docker-compose.redis-cluster.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Redis cluster containers"
    exit 1
}

# Wait for containers to be ready
Write-Status "Waiting for Redis nodes to be ready..."
Start-Sleep -Seconds 15

# Check if all nodes are running
for ($i = 1; $i -le 6; $i++) {
    $port = 7000 + $i
    try {
        docker exec redis-cluster-node-$i redis-cli -p 7000 ping | Out-Null
        Write-Status "Node $i is ready"
    } catch {
        Write-Error "Redis node $i is not responding"
        exit 1
    }
}

Write-Status "All Redis nodes are running successfully!"

# Create cluster
Write-Status "Creating Redis cluster..."
$createClusterCmd = @(
    "redis-cli", "--cluster", "create",
    "redis-node-1:7000",
    "redis-node-2:7000", 
    "redis-node-3:7000",
    "redis-node-4:7000",
    "redis-node-5:7000",
    "redis-node-6:7000",
    "--cluster-replicas", "1",
    "--cluster-yes"
)

docker exec redis-cluster-node-1 @createClusterCmd

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create Redis cluster"
    exit 1
}

# Verify cluster status
Write-Status "Verifying cluster status..."
docker exec redis-cluster-node-1 redis-cli -p 7000 cluster info

# Test cluster functionality
Write-Status "Testing cluster functionality..."
docker exec redis-cluster-node-1 redis-cli -p 7000 set test_key "Hello Redis Cluster"
$testResult = docker exec redis-cluster-node-2 redis-cli -p 7000 get test_key

if ($testResult -eq "Hello Redis Cluster") {
    Write-Status "✅ Cluster test successful!"
} else {
    Write-Warning "Cluster test may have issues"
}

Write-Status "✅ Redis cluster setup completed successfully!"
Write-Status "Cluster nodes are available at:"
for ($i = 1; $i -le 6; $i++) {
    $port = 7000 + $i
    Write-Host "  - Node $i`: localhost:$port"
}

Write-Status "To connect to the cluster:"
Write-Host "  redis-cli -c -p 7001"

Write-Status "To monitor cluster:"
Write-Host "  docker exec redis-cluster-node-1 redis-cli -p 7000 cluster nodes"

Write-Status "To stop cluster:"
Write-Host "  docker-compose -f docker-compose.redis-cluster.yml down"
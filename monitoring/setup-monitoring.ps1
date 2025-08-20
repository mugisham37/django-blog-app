# Enterprise Platform Monitoring Stack Setup Script (PowerShell)
# This script sets up the complete monitoring infrastructure on Windows

Write-Host "🚀 Setting up Enterprise Platform Monitoring Stack..." -ForegroundColor Green

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not available. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating monitoring directories..." -ForegroundColor Yellow
$directories = @(
    "monitoring\prometheus",
    "monitoring\grafana\provisioning\datasources",
    "monitoring\grafana\provisioning\dashboards", 
    "monitoring\grafana\dashboards\infrastructure",
    "monitoring\grafana\dashboards\applications",
    "monitoring\grafana\dashboards\business",
    "monitoring\jaeger",
    "monitoring\loki", 
    "monitoring\alertmanager\templates",
    "monitoring\blackbox"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Gray
    }
}

# Create environment file if it doesn't exist
$envFile = "monitoring\.env"
if (!(Test-Path $envFile)) {
    Write-Host "📝 Creating monitoring environment file..." -ForegroundColor Yellow
    
    # Generate random secret key
    $secretKey = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString()))
    
    $envContent = @"
# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=admin123
GRAFANA_DB_PASSWORD=grafana_db_pass
GRAFANA_SECRET_KEY=$secretKey

# Database Configuration  
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_pass
POSTGRES_DB=enterprise_platform
POSTGRES_GRAFANA_PASSWORD=grafana_readonly_pass

# Redis Configuration
REDIS_PASSWORD=redis_pass

# Elasticsearch Configuration
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=elastic_pass

# SMTP Configuration (Update with your SMTP settings)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack Configuration (Update with your webhook URL)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# PagerDuty Configuration (Update with your integration key)  
PAGERDUTY_INTEGRATION_KEY=your-pagerduty-integration-key

# GitHub OAuth (Update with your GitHub app credentials)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
"@
    
    Set-Content -Path $envFile -Value $envContent
    Write-Host "⚠️  Please update monitoring\.env with your actual configuration values" -ForegroundColor Yellow
}

Write-Host "✅ Monitoring stack setup completed!" -ForegroundColor Green
Write-Host "📖 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Update monitoring\.env with your configuration" -ForegroundColor White
Write-Host "   2. Run: docker-compose -f monitoring\docker-compose.monitoring.yml up -d" -ForegroundColor White  
Write-Host "   3. Access services:" -ForegroundColor White
Write-Host "      - Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "      - Grafana: http://localhost:3001 (admin/admin123)" -ForegroundColor White
Write-Host "      - Jaeger: http://localhost:16686" -ForegroundColor White
Write-Host "      - AlertManager: http://localhost:9093" -ForegroundColor White
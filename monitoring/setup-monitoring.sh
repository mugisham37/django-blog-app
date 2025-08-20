#!/bin/bash

# Enterprise Platform Monitoring Stack Setup Script
# This script sets up the complete monitoring infrastructure

set -e

echo "🚀 Setting up Enterprise Platform Monitoring Stack..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/{prometheus,grafana,jaeger,loki,alertmanager,blackbox}
mkdir -p monitoring/grafana/{provisioning/{datasources,dashboards},dashboards/{infrastructure,applications,business}}
mkdir -p monitoring/alertmanager/templates

# Set proper permissions
echo "🔐 Setting permissions..."
sudo chown -R 472:472 monitoring/grafana/
sudo chown -R 65534:65534 monitoring/prometheus/
sudo chown -R 10001:10001 monitoring/loki/

# Create environment file if it doesn't exist
if [ ! -f monitoring/.env ]; then
    echo "📝 Creating monitoring environment file..."
    cat > monitoring/.env << EOF
# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=admin123
GRAFANA_DB_PASSWORD=grafana_db_pass
GRAFANA_SECRET_KEY=$(openssl rand -base64 32)

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
EOF
    echo "⚠️  Please update monitoring/.env with your actual configuration values"
fi

echo "✅ Monitoring stack setup completed!"
echo "📖 Next steps:"
echo "   1. Update monitoring/.env with your configuration"
echo "   2. Run: docker-compose -f monitoring/docker-compose.monitoring.yml up -d"
echo "   3. Access services:"
echo "      - Prometheus: http://localhost:9090"
echo "      - Grafana: http://localhost:3001 (admin/admin123)"
echo "      - Jaeger: http://localhost:16686"
echo "      - AlertManager: http://localhost:9093"
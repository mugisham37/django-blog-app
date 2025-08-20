# Enterprise Platform Monitoring Stack

Comprehensive monitoring and observability infrastructure for the Enterprise Platform, including metrics collection, log aggregation, distributed tracing, and alerting.

## 🏗️ Architecture Overview

The monitoring stack consists of:

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **Jaeger** - Distributed tracing
- **Loki** - Log aggregation
- **AlertManager** - Alert routing and notifications
- **Exporters** - Node, PostgreSQL, Redis, Nginx metrics

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available for monitoring stack
- Ports 3001, 9090, 9093, 16686, 3100 available

### Setup

1. **Run setup script:**

   ```bash
   # Linux/macOS
   chmod +x monitoring/setup-monitoring.sh
   ./monitoring/setup-monitoring.sh

   # Windows PowerShell
   .\monitoring\setup-monitoring.ps1
   ```

2. **Configure environment:**

   ```bash
   # Edit monitoring/.env with your settings
   nano monitoring/.env
   ```

3. **Start monitoring stack:**

   ```bash
   docker-compose -f monitoring/docker-compose.monitoring.yml up -d
   ```

4. **Verify services:**
   ```bash
   docker-compose -f monitoring/docker-compose.monitoring.yml ps
   ```

## 📊 Service Access

| Service      | URL                    | Credentials    |
| ------------ | ---------------------- | -------------- |
| Grafana      | http://localhost:3001  | admin/admin123 |
| Prometheus   | http://localhost:9090  | -              |
| Jaeger       | http://localhost:16686 | -              |
| AlertManager | http://localhost:9093  | -              |

## 📈 Dashboards

### Infrastructure Dashboards

- **System Overview** - CPU, Memory, Disk, Network metrics
- **Database Performance** - PostgreSQL metrics and queries
- **Cache Performance** - Redis metrics and operations
- **Network & Security** - Nginx and security metrics

### Application Dashboards

- **Django API** - Request rates, response times, errors
- **Next.js Web** - Page loads, user interactions, performance
- **WebSocket Connections** - Real-time connection metrics
- **Background Jobs** - Task queue and processing metrics

### Business Dashboards

- **User Analytics** - Registrations, active users, engagement
- **Content Metrics** - Blog posts, comments, views
- **Revenue & Growth** - Business KPIs and trends

## 🔔 Alerting

### Alert Severity Levels

- **Critical** - Service down, high error rates (PagerDuty + Slack + Email)
- **Warning** - Performance degradation, resource usage (Slack + Email)
- **Info** - Business metrics, capacity planning (Email)

### Alert Channels

- **Email** - All alerts to operations team
- **Slack** - Real-time notifications by severity
- **PagerDuty** - Critical alerts for on-call rotation

### Key Alerts

- Service availability (up/down)
- API response time > 2s (95th percentile)
- Error rate > 5%
- Database connections > 80%
- Memory usage > 90%
- Disk space < 10%

## 📝 Log Management

### Log Sources

- **Django API** - Application logs, access logs, errors
- **Next.js Web** - Server-side rendering logs, errors
- **Nginx** - Access logs, error logs, security events
- **PostgreSQL** - Query logs, slow queries, errors
- **Redis** - Operations, errors, performance
- **Kubernetes** - Pod logs, events, system logs

### Log Retention

- **Hot storage** - 7 days (fast queries)
- **Warm storage** - 30 days (standard queries)
- **Cold storage** - 90 days (archive)

## 🔍 Distributed Tracing

### Instrumented Services

- Django API endpoints
- Next.js server-side rendering
- Database queries
- Redis operations
- External API calls

### Trace Sampling

- **Production** - 10% sampling rate
- **Django API** - 50% sampling rate
- **Background tasks** - 100% sampling rate

## 🛠️ Configuration

### Environment Variables

Key configuration in `monitoring/.env`:

```bash
# Grafana
GRAFANA_ADMIN_PASSWORD=your-secure-password
GRAFANA_SECRET_KEY=your-secret-key

# Notifications
SMTP_HOST=your-smtp-server
SLACK_WEBHOOK_URL=your-slack-webhook
PAGERDUTY_INTEGRATION_KEY=your-pagerduty-key

# Security
GITHUB_CLIENT_ID=your-github-app-id
GITHUB_CLIENT_SECRET=your-github-app-secret
```

### Custom Metrics

Add custom metrics to your applications:

```python
# Django - Add to views
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('django_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('django_request_duration_seconds', 'Request latency')

@REQUEST_LATENCY.time()
def my_view(request):
    REQUEST_COUNT.labels(method=request.method, endpoint='my_view').inc()
    # Your view logic
```

## 🧪 Testing

Run monitoring integration tests:

```bash
# Install test dependencies
pip install pytest requests

# Run tests
pytest tests/monitoring/ -v

# Run specific test categories
pytest tests/monitoring/test_monitoring_stack.py::TestMonitoringStack -v
pytest tests/monitoring/test_apm_integration.py::TestAPMIntegration -v
```

## 🔧 Maintenance

### Backup & Recovery

```bash
# Backup Prometheus data
docker run --rm -v prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data

# Backup Grafana dashboards
docker exec grafana grafana-cli admin export-dashboard > grafana-backup.json

# Backup AlertManager configuration
cp monitoring/alertmanager/alertmanager.yml alertmanager-backup.yml
```

### Performance Tuning

- **Prometheus retention** - Adjust `--storage.tsdb.retention.time`
- **Grafana caching** - Configure Redis for dashboard caching
- **Log retention** - Adjust Loki retention policies
- **Trace sampling** - Optimize Jaeger sampling rates

## 📚 Documentation

- [Prometheus Configuration](./prometheus/README.md)
- [Grafana Setup Guide](./grafana/README.md)
- [Jaeger Tracing Guide](./jaeger/README.md)
- [Loki Logging Guide](./loki/README.md)
- [AlertManager Configuration](./alertmanager/README.md)

## 🆘 Troubleshooting

### Common Issues

1. **Services not starting**

   ```bash
   # Check logs
   docker-compose -f monitoring/docker-compose.monitoring.yml logs

   # Check resource usage
   docker stats
   ```

2. **No metrics appearing**

   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets

   # Check service discovery
   docker-compose -f monitoring/docker-compose.monitoring.yml exec prometheus cat /etc/prometheus/prometheus.yml
   ```

3. **Alerts not firing**

   ```bash
   # Check AlertManager status
   curl http://localhost:9093/api/v1/status

   # Check alert rules
   curl http://localhost:9090/api/v1/rules
   ```

### Support

- Check logs: `docker-compose logs [service-name]`
- Verify configuration: Review YAML files for syntax errors
- Resource limits: Ensure adequate CPU/memory allocation
- Network connectivity: Verify service-to-service communication

## 🔄 Updates

To update the monitoring stack:

```bash
# Pull latest images
docker-compose -f monitoring/docker-compose.monitoring.yml pull

# Restart services
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Verify health
docker-compose -f monitoring/docker-compose.monitoring.yml ps
```

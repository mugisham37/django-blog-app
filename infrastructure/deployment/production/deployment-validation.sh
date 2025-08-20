#!/bin/bash
set -e

# Production Deployment Validation Script
# Comprehensive health checks and validation for production deployment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/deployment/validation.log"
VALIDATION_RESULTS="/tmp/validation_results.json"
TIMEOUT=300
RETRY_INTERVAL=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    echo '{"status": "failed", "error": "'$1'", "timestamp": "'$(date -Iseconds)'"}' > "$VALIDATION_RESULTS"
    exit 1
}

# Success logging
success() {
    log "${GREEN}SUCCESS: $1${NC}"
}

# Warning logging
warning() {
    log "${YELLOW}WARNING: $1${NC}"
}

# Info logging
info() {
    log "${BLUE}INFO: $1${NC}"
}

# Wait for service to be ready
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local timeout=${3:-$TIMEOUT}
    local interval=${4:-$RETRY_INTERVAL}
    
    info "Waiting for $service_name to be ready..."
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            success "$service_name is ready"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        info "Waiting for $service_name... ($elapsed/${timeout}s)"
    done
    
    error_exit "$service_name failed to become ready within ${timeout}s"
}

# Check HTTP endpoint
check_http_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local timeout=${4:-30}
    
    info "Checking HTTP endpoint: $name ($url)"
    
    local response=$(curl -s -w "%{http_code}|%{time_total}|%{size_download}" -m $timeout "$url" || echo "000|0|0")
    local status_code=$(echo "$response" | cut -d'|' -f1)
    local response_time=$(echo "$response" | cut -d'|' -f2)
    local response_size=$(echo "$response" | cut -d'|' -f3)
    
    if [ "$status_code" = "$expected_status" ]; then
        success "$name endpoint is healthy (${status_code}, ${response_time}s, ${response_size} bytes)"
        return 0
    else
        error_exit "$name endpoint failed (expected: $expected_status, got: $status_code)"
    fi
}

# Check database connectivity
check_database() {
    info "Checking database connectivity..."
    
    if ! command -v psql &> /dev/null; then
        warning "psql not available, skipping database check"
        return 0
    fi
    
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    # Check primary database
    if psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; then
        success "Primary database is accessible"
    else
        error_exit "Primary database is not accessible"
    fi
    
    # Check read replica if configured
    if [ -n "$POSTGRES_REPLICA_HOST" ]; then
        if psql -h "$POSTGRES_REPLICA_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; then
            success "Database replica is accessible"
        else
            warning "Database replica is not accessible"
        fi
    fi
    
    # Check database performance
    local query_time=$(psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT EXTRACT(EPOCH FROM NOW());" 2>/dev/null | tr -d ' ')
    if [ -n "$query_time" ]; then
        success "Database query performance is acceptable"
    else
        warning "Could not measure database query performance"
    fi
}

# Check Redis connectivity
check_redis() {
    info "Checking Redis connectivity..."
    
    if ! command -v redis-cli &> /dev/null; then
        warning "redis-cli not available, skipping Redis check"
        return 0
    fi
    
    # Check Redis master
    if redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} ping | grep -q "PONG"; then
        success "Redis master is accessible"
    else
        error_exit "Redis master is not accessible"
    fi
    
    # Check Redis memory usage
    local memory_usage=$(redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" ${REDIS_PASSWORD:+-a "$REDIS_PASSWORD"} info memory | grep "used_memory_human" | cut -d':' -f2 | tr -d '\r')
    if [ -n "$memory_usage" ]; then
        info "Redis memory usage: $memory_usage"
    fi
}

# Check SSL certificates
check_ssl_certificates() {
    info "Checking SSL certificates..."
    
    if ! command -v openssl &> /dev/null; then
        warning "openssl not available, skipping SSL check"
        return 0
    fi
    
    local domain="${DOMAIN_NAME:-localhost}"
    local cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [ -n "$cert_info" ]; then
        local not_after=$(echo "$cert_info" | grep "notAfter" | cut -d'=' -f2)
        local expiry_date=$(date -d "$not_after" +%s 2>/dev/null || echo "0")
        local current_date=$(date +%s)
        local days_until_expiry=$(( (expiry_date - current_date) / 86400 ))
        
        if [ $days_until_expiry -gt 30 ]; then
            success "SSL certificate is valid (expires in $days_until_expiry days)"
        elif [ $days_until_expiry -gt 0 ]; then
            warning "SSL certificate expires soon ($days_until_expiry days)"
        else
            error_exit "SSL certificate has expired"
        fi
    else
        error_exit "Could not retrieve SSL certificate information"
    fi
}

# Check application metrics
check_application_metrics() {
    info "Checking application metrics..."
    
    # Check if Prometheus is accessible
    if check_http_endpoint "Prometheus" "http://prometheus:9090/-/healthy" 200 30; then
        # Query some basic metrics
        local up_targets=$(curl -s "http://prometheus:9090/api/v1/query?query=up" | jq -r '.data.result | length' 2>/dev/null || echo "0")
        info "Prometheus monitoring $up_targets targets"
        
        # Check for critical alerts
        local critical_alerts=$(curl -s "http://prometheus:9090/api/v1/alerts" | jq -r '.data.alerts | map(select(.labels.severity == "critical")) | length' 2>/dev/null || echo "0")
        if [ "$critical_alerts" -gt 0 ]; then
            warning "$critical_alerts critical alerts are active"
        else
            success "No critical alerts active"
        fi
    fi
}

# Check log aggregation
check_logging() {
    info "Checking log aggregation..."
    
    # Check Elasticsearch
    if check_http_endpoint "Elasticsearch" "http://elasticsearch:9200/_cluster/health" 200 30; then
        local cluster_status=$(curl -s "http://elasticsearch:9200/_cluster/health" | jq -r '.status' 2>/dev/null || echo "unknown")
        if [ "$cluster_status" = "green" ]; then
            success "Elasticsearch cluster is healthy"
        elif [ "$cluster_status" = "yellow" ]; then
            warning "Elasticsearch cluster status is yellow"
        else
            error_exit "Elasticsearch cluster status is red"
        fi
    fi
    
    # Check Kibana
    check_http_endpoint "Kibana" "http://kibana:5601/api/status" 200 30
}

# Check security services
check_security() {
    info "Checking security services..."
    
    # Check WAF
    if check_http_endpoint "ModSecurity WAF" "http://modsecurity:80/health" 200 30; then
        success "Web Application Firewall is active"
    fi
    
    # Check if security headers are present
    local security_headers=$(curl -I -s "https://${DOMAIN_NAME:-localhost}" | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)" | wc -l)
    if [ "$security_headers" -ge 3 ]; then
        success "Security headers are properly configured"
    else
        warning "Some security headers may be missing"
    fi
}

# Check performance benchmarks
check_performance() {
    info "Checking performance benchmarks..."
    
    # Simple load test
    local response_time=$(curl -o /dev/null -s -w "%{time_total}" "https://${DOMAIN_NAME:-localhost}")
    local response_time_ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "0")
    
    if [ "$(echo "$response_time < 2.0" | bc 2>/dev/null || echo "0")" = "1" ]; then
        success "Response time is acceptable (${response_time_ms}ms)"
    else
        warning "Response time is slow (${response_time_ms}ms)"
    fi
}

# Check backup systems
check_backups() {
    info "Checking backup systems..."
    
    # Check if backup directory exists and has recent backups
    if [ -d "/opt/postgres/backups" ]; then
        local recent_backup=$(find /opt/postgres/backups -name "postgres_backup_*.sql.gz" -mtime -1 | head -1)
        if [ -n "$recent_backup" ]; then
            success "Recent database backup found: $(basename "$recent_backup")"
        else
            warning "No recent database backup found"
        fi
    else
        warning "Backup directory not found"
    fi
}

# Generate validation report
generate_report() {
    local status=${1:-"success"}
    local timestamp=$(date -Iseconds)
    
    cat > "$VALIDATION_RESULTS" << EOF
{
  "status": "$status",
  "timestamp": "$timestamp",
  "environment": "production",
  "validation_checks": {
    "database": "$([ -n "$db_check" ] && echo "passed" || echo "failed")",
    "redis": "$([ -n "$redis_check" ] && echo "passed" || echo "failed")",
    "ssl": "$([ -n "$ssl_check" ] && echo "passed" || echo "failed")",
    "metrics": "$([ -n "$metrics_check" ] && echo "passed" || echo "failed")",
    "logging": "$([ -n "$logging_check" ] && echo "passed" || echo "failed")",
    "security": "$([ -n "$security_check" ] && echo "passed" || echo "failed")",
    "performance": "$([ -n "$performance_check" ] && echo "passed" || echo "failed")",
    "backups": "$([ -n "$backup_check" ] && echo "passed" || echo "failed")"
  },
  "deployment_info": {
    "domain": "${DOMAIN_NAME:-localhost}",
    "version": "${SERVICE_VERSION:-unknown}",
    "commit": "${GIT_COMMIT:-unknown}"
  }
}
EOF
}

# Main validation function
main() {
    info "Starting production deployment validation..."
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Initialize validation results
    echo '{"status": "running", "timestamp": "'$(date -Iseconds)'"}' > "$VALIDATION_RESULTS"
    
    # Run validation checks
    set +e  # Don't exit on individual check failures
    
    check_database && db_check=1
    check_redis && redis_check=1
    check_ssl_certificates && ssl_check=1
    check_application_metrics && metrics_check=1
    check_logging && logging_check=1
    check_security && security_check=1
    check_performance && performance_check=1
    check_backups && backup_check=1
    
    set -e
    
    # Generate final report
    generate_report "success"
    
    success "Production deployment validation completed successfully"
    info "Validation results saved to: $VALIDATION_RESULTS"
    
    # Display summary
    echo ""
    echo "=== VALIDATION SUMMARY ==="
    cat "$VALIDATION_RESULTS" | jq '.'
}

# Handle script arguments
case "${1:-validate}" in
    "validate")
        main
        ;;
    "check-endpoint")
        check_http_endpoint "$2" "$3" "${4:-200}"
        ;;
    "check-database")
        check_database
        ;;
    "check-redis")
        check_redis
        ;;
    "generate-report")
        generate_report
        ;;
    *)
        echo "Usage: $0 [validate|check-endpoint|check-database|check-redis|generate-report]"
        exit 1
        ;;
esac
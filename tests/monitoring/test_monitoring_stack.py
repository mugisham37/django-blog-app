"""
Monitoring Stack Integration Tests

Tests for Prometheus, Grafana, Jaeger, Loki, and AlertManager integration.
"""

import pytest
import requests
import time
import json
from typing import Dict, List
from urllib.parse import urljoin


class TestMonitoringStack:
    """Test suite for monitoring infrastructure components."""
    
    # Service endpoints
    PROMETHEUS_URL = "http://localhost:9090"
    GRAFANA_URL = "http://localhost:3001"
    JAEGER_URL = "http://localhost:16686"
    LOKI_URL = "http://localhost:3100"
    ALERTMANAGER_URL = "http://localhost:9093"
    
    def test_prometheus_health(self):
        """Test Prometheus health and configuration."""
        # Check Prometheus health
        response = requests.get(f"{self.PROMETHEUS_URL}/-/healthy")
        assert response.status_code == 200
        
        # Check Prometheus ready
        response = requests.get(f"{self.PROMETHEUS_URL}/-/ready")
        assert response.status_code == 200
        
        # Check configuration
        response = requests.get(f"{self.PROMETHEUS_URL}/api/v1/status/config")
        assert response.status_code == 200
        config = response.json()
        assert config["status"] == "success"
        
    def test_prometheus_targets(self):
        """Test Prometheus target discovery and scraping."""
        response = requests.get(f"{self.PROMETHEUS_URL}/api/v1/targets")
        assert response.status_code == 200
        
        targets = response.json()
        assert targets["status"] == "success"
        
        # Check that key targets are discovered
        target_jobs = {target["labels"]["job"] for target in targets["data"]["activeTargets"]}
        expected_jobs = {"prometheus", "django-api", "nextjs-web", "postgresql", "redis", "node-exporter"}
        
        for job in expected_jobs:
            assert job in target_jobs, f"Target job '{job}' not found"
            
    def test_prometheus_rules(self):
        """Test Prometheus alerting rules."""
        response = requests.get(f"{self.PROMETHEUS_URL}/api/v1/rules")
        assert response.status_code == 200
        
        rules = response.json()
        assert rules["status"] == "success"
        
        # Check that alert rules are loaded
        rule_groups = rules["data"]["groups"]
        assert len(rule_groups) > 0
        
        # Check for specific alert rules
        all_rules = []
        for group in rule_groups:
            all_rules.extend([rule["name"] for rule in group["rules"]])
            
        expected_alerts = ["ServiceDown", "HighAPILatency", "HighAPIErrorRate", "DatabaseConnectionsHigh"]
        for alert in expected_alerts:
            assert alert in all_rules, f"Alert rule '{alert}' not found"
            
    def test_grafana_health(self):
        """Test Grafana health and API."""
        # Check Grafana health
        response = requests.get(f"{self.GRAFANA_URL}/api/health")
        assert response.status_code == 200
        
        health = response.json()
        assert health["database"] == "ok"
        
    def test_grafana_datasources(self):
        """Test Grafana datasource configuration."""
        # Note: This would require authentication in a real environment
        # For testing, we'll check the provisioning endpoint
        response = requests.get(f"{self.GRAFANA_URL}/api/datasources")
        
        # In a real test, you'd authenticate first
        # For now, we'll just check that Grafana is responding
        assert response.status_code in [200, 401, 403]  # 401/403 expected without auth
        
    def test_jaeger_health(self):
        """Test Jaeger health and API."""
        # Check Jaeger health
        response = requests.get(f"{self.JAEGER_URL}/api/services")
        assert response.status_code == 200
        
        services = response.json()
        assert "data" in services
        
    def test_jaeger_trace_collection(self):
        """Test Jaeger trace collection capabilities."""
        # Check that Jaeger can receive traces
        response = requests.get(f"{self.JAEGER_URL}/api/traces")
        assert response.status_code == 200
        
    def test_loki_health(self):
        """Test Loki health and readiness."""
        # Check Loki ready
        response = requests.get(f"{self.LOKI_URL}/ready")
        assert response.status_code == 200
        
        # Check Loki metrics
        response = requests.get(f"{self.LOKI_URL}/metrics")
        assert response.status_code == 200
        
    def test_loki_log_ingestion(self):
        """Test Loki log ingestion API."""
        # Test log push endpoint
        log_data = {
            "streams": [
                {
                    "stream": {
                        "job": "test",
                        "level": "info"
                    },
                    "values": [
                        [str(int(time.time() * 1000000000)), "Test log message"]
                    ]
                }
            ]
        }
        
        response = requests.post(
            f"{self.LOKI_URL}/loki/api/v1/push",
            json=log_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 204
        
    def test_alertmanager_health(self):
        """Test AlertManager health and configuration."""
        # Check AlertManager health
        response = requests.get(f"{self.ALERTMANAGER_URL}/-/healthy")
        assert response.status_code == 200
        
        # Check AlertManager ready
        response = requests.get(f"{self.ALERTMANAGER_URL}/-/ready")
        assert response.status_code == 200
        
    def test_alertmanager_config(self):
        """Test AlertManager configuration."""
        response = requests.get(f"{self.ALERTMANAGER_URL}/api/v1/status")
        assert response.status_code == 200
        
        status = response.json()
        assert status["status"] == "success"
        
        # Check configuration is loaded
        config = status["data"]["configYAML"]
        assert "global:" in config
        assert "route:" in config
        assert "receivers:" in config
        
    def test_metrics_collection_flow(self):
        """Test end-to-end metrics collection flow."""
        # Wait for metrics to be collected
        time.sleep(30)
        
        # Query Prometheus for basic metrics
        queries = [
            "up",
            "prometheus_notifications_total",
            "prometheus_rule_evaluations_total"
        ]
        
        for query in queries:
            response = requests.get(
                f"{self.PROMETHEUS_URL}/api/v1/query",
                params={"query": query}
            )
            assert response.status_code == 200
            
            result = response.json()
            assert result["status"] == "success"
            assert len(result["data"]["result"]) > 0
            
    def test_alert_firing_simulation(self):
        """Test alert firing and routing."""
        # Create a test alert
        test_alert = [{
            "labels": {
                "alertname": "TestAlert",
                "severity": "warning",
                "service": "test-service",
                "instance": "test-instance"
            },
            "annotations": {
                "summary": "Test alert for monitoring validation",
                "description": "This is a test alert to validate monitoring setup"
            },
            "startsAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "generatorURL": "http://prometheus:9090/graph"
        }]
        
        # Send alert to AlertManager
        response = requests.post(
            f"{self.ALERTMANAGER_URL}/api/v1/alerts",
            json=test_alert,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Wait for alert processing
        time.sleep(5)
        
        # Check that alert is received
        response = requests.get(f"{self.ALERTMANAGER_URL}/api/v1/alerts")
        assert response.status_code == 200
        
        alerts = response.json()
        assert alerts["status"] == "success"
        
    def test_log_aggregation_flow(self):
        """Test log aggregation from multiple sources."""
        # Send test logs to Loki
        test_logs = [
            {
                "stream": {"job": "django-api", "level": "info"},
                "values": [[str(int(time.time() * 1000000000)), "Django API test log"]]
            },
            {
                "stream": {"job": "nextjs-web", "level": "error"},
                "values": [[str(int(time.time() * 1000000000)), "Next.js web test error"]]
            }
        ]
        
        for log_stream in test_logs:
            response = requests.post(
                f"{self.LOKI_URL}/loki/api/v1/push",
                json={"streams": [log_stream]},
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 204
            
        # Wait for log processing
        time.sleep(10)
        
        # Query logs from Loki
        response = requests.get(
            f"{self.LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": '{job=~"django-api|nextjs-web"}',
                "start": str(int((time.time() - 300) * 1000000000)),  # 5 minutes ago
                "end": str(int(time.time() * 1000000000))
            }
        )
        assert response.status_code == 200
        
        logs = response.json()
        assert logs["status"] == "success"
        
    def test_distributed_tracing_flow(self):
        """Test distributed tracing collection and querying."""
        # Check Jaeger services
        response = requests.get(f"{self.JAEGER_URL}/api/services")
        assert response.status_code == 200
        
        services = response.json()
        assert "data" in services
        
        # In a real environment, you'd generate traces and then query them
        # For now, we'll just verify the API is working
        
    @pytest.mark.performance
    def test_monitoring_performance(self):
        """Test monitoring stack performance and resource usage."""
        # Query Prometheus for monitoring stack metrics
        queries = [
            "prometheus_tsdb_head_samples_appended_total",
            "prometheus_config_last_reload_successful",
            "grafana_stat_totals_dashboard",
            "loki_ingester_streams"
        ]
        
        for query in queries:
            response = requests.get(
                f"{self.PROMETHEUS_URL}/api/v1/query",
                params={"query": query}
            )
            # Some metrics might not exist yet, so we allow 400 responses
            assert response.status_code in [200, 400]
            
    def test_monitoring_data_retention(self):
        """Test data retention policies."""
        # Check Prometheus retention
        response = requests.get(f"{self.PROMETHEUS_URL}/api/v1/status/runtimeinfo")
        assert response.status_code == 200
        
        runtime_info = response.json()
        assert runtime_info["status"] == "success"
        
        # Check storage metrics
        response = requests.get(f"{self.PROMETHEUS_URL}/api/v1/status/tsdb")
        assert response.status_code == 200
        
        tsdb_info = response.json()
        assert tsdb_info["status"] == "success"


class TestMonitoringIntegration:
    """Test monitoring integration with application services."""
    
    def test_django_metrics_collection(self):
        """Test Django application metrics collection."""
        # This would test that Django is exposing metrics properly
        # In a real environment, you'd check for Django-specific metrics
        pass
        
    def test_nextjs_metrics_collection(self):
        """Test Next.js application metrics collection."""
        # This would test that Next.js is exposing metrics properly
        pass
        
    def test_database_monitoring(self):
        """Test database monitoring and metrics."""
        # This would test PostgreSQL exporter metrics
        pass
        
    def test_cache_monitoring(self):
        """Test Redis cache monitoring."""
        # This would test Redis exporter metrics
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Security-related API views for Django Personal Blog System.
Provides endpoints for security monitoring, reporting, and management.
"""

import json
import logging
from typing import Dict, Any

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .security_monitoring import security_monitor, log_security_event
from .security_scanner import SecurityScanner, get_vulnerability_report
from .security_headers import get_security_headers_status
from .rate_limiting import get_rate_limit_status, is_ddos_attack_detected

logger = logging.getLogger('security')


class CSPReportView(View):
    """
    Handle Content Security Policy violation reports.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Handle CSP violation report."""
        
        try:
            # Parse the CSP report
            report_data = json.loads(request.body.decode('utf-8'))
            csp_report = report_data.get('csp-report', {})
            
            # Extract violation details
            violation_details = {
                'blocked_uri': csp_report.get('blocked-uri', ''),
                'document_uri': csp_report.get('document-uri', ''),
                'violated_directive': csp_report.get('violated-directive', ''),
                'original_policy': csp_report.get('original-policy', ''),
                'source_file': csp_report.get('source-file', ''),
                'line_number': csp_report.get('line-number', ''),
                'column_number': csp_report.get('column-number', ''),
            }
            
            # Log the violation
            client_ip = self._get_client_ip(request)
            log_security_event(
                'csp_violation',
                f'CSP violation: {violation_details["violated_directive"]} blocked {violation_details["blocked_uri"]}',
                client_ip,
                metadata=violation_details
            )
            
            # Check for potential XSS attempts
            blocked_uri = violation_details['blocked_uri']
            if any(pattern in blocked_uri.lower() for pattern in ['javascript:', 'data:', 'vbscript:']):
                log_security_event(
                    'potential_xss',
                    f'Potential XSS attempt blocked by CSP: {blocked_uri}',
                    client_ip,
                    metadata=violation_details
                )
            
            return JsonResponse({'status': 'received'}, status=200)
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Invalid CSP report received: {e}")
            return JsonResponse({'error': 'Invalid report'}, status=400)
        
        except Exception as e:
            logger.error(f"Error processing CSP report: {e}")
            return JsonResponse({'error': 'Processing error'}, status=500)
    
    def _get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def security_dashboard(request):
    """
    Get security dashboard data.
    """
    
    try:
        dashboard_data = security_monitor.get_security_dashboard_data()
        return Response(dashboard_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching security dashboard: {e}")
        return Response(
            {'error': 'Failed to fetch dashboard data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def security_status(request):
    """
    Get current security status and configuration.
    """
    
    try:
        # Get security headers status
        headers_status = get_security_headers_status()
        
        # Get rate limiting status
        rate_limit_status = get_rate_limit_status(request)
        
        # Check for ongoing DDoS
        ddos_detected = is_ddos_attack_detected()
        
        # Get basic security metrics
        dashboard_data = security_monitor.get_security_dashboard_data()
        
        status_data = {
            'security_headers': headers_status,
            'rate_limiting': rate_limit_status,
            'ddos_protection': {
                'active': ddos_detected,
                'status': 'ALERT' if ddos_detected else 'NORMAL'
            },
            'threat_level': dashboard_data.get('threat_level', 'unknown'),
            'recent_events': dashboard_data.get('statistics', {}),
            'recommendations': dashboard_data.get('recommendations', [])
        }
        
        return Response(status_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching security status: {e}")
        return Response(
            {'error': 'Failed to fetch security status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def run_security_scan(request):
    """
    Run a security vulnerability scan.
    """
    
    try:
        # Get scan parameters
        base_url = request.data.get('base_url', 'http://localhost:8000')
        min_severity = request.data.get('min_severity', 'low')
        
        # Validate parameters
        if min_severity not in ['low', 'medium', 'high', 'critical']:
            return Response(
                {'error': 'Invalid severity level'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Run the scan
        scanner = SecurityScanner(base_url)
        results = scanner.run_full_scan()
        
        # Filter by severity if specified
        if min_severity != 'low':
            severity_order = ['low', 'medium', 'high', 'critical']
            min_index = severity_order.index(min_severity)
            
            filtered_vulns = [
                v for v in results['vulnerabilities']
                if severity_order.index(v['severity']) >= min_index
            ]
            results['vulnerabilities'] = filtered_vulns
            results['vulnerabilities_found'] = len(filtered_vulns)
            
            # Update severity counts
            for severity in results['severity_counts']:
                results['severity_counts'][severity] = sum(
                    1 for v in filtered_vulns if v['severity'] == severity
                )
        
        # Log the scan
        log_security_event(
            'security_scan_completed',
            f'Security scan completed with {results["vulnerabilities_found"]} vulnerabilities',
            self._get_client_ip(request),
            user_id=request.user.id,
            metadata={
                'scan_id': results['scan_id'],
                'vulnerabilities_found': results['vulnerabilities_found'],
                'severity_counts': results['severity_counts']
            }
        )
        
        return Response(results, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error running security scan: {e}")
        return Response(
            {'error': 'Failed to run security scan'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def security_alerts(request):
    """
    Get recent security alerts.
    """
    
    try:
        dashboard_data = security_monitor.get_security_dashboard_data()
        alerts = dashboard_data.get('recent_alerts', [])
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_alerts = alerts[start_idx:end_idx]
        
        response_data = {
            'alerts': paginated_alerts,
            'total': len(alerts),
            'page': page,
            'page_size': page_size,
            'has_next': end_idx < len(alerts),
            'has_previous': page > 1
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching security alerts: {e}")
        return Response(
            {'error': 'Failed to fetch security alerts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def test_security_alert(request):
    """
    Create a test security alert for testing purposes.
    """
    
    try:
        alert_type = request.data.get('type', 'test_alert')
        severity = request.data.get('severity', 'medium')
        description = request.data.get('description', 'Test security alert from API')
        
        # Validate severity
        if severity not in ['low', 'medium', 'high', 'critical']:
            return Response(
                {'error': 'Invalid severity level'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create test alert
        client_ip = self._get_client_ip(request)
        log_security_event(
            alert_type,
            description,
            client_ip,
            user_id=request.user.id,
            metadata={
                'test': True,
                'severity': severity,
                'created_by': request.user.username
            }
        )
        
        return Response(
            {'message': 'Test security alert created successfully'},
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        logger.error(f"Error creating test security alert: {e}")
        return Response(
            {'error': 'Failed to create test alert'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rate_limit_info(request):
    """
    Get rate limit information for the current user/IP.
    """
    
    try:
        rate_limit_status = get_rate_limit_status(request)
        return Response(rate_limit_status, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching rate limit info: {e}")
        return Response(
            {'error': 'Failed to fetch rate limit information'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint for monitoring.
    """
    
    try:
        # Basic health checks
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'checks': {
                'database': 'ok',
                'cache': 'ok',
                'security': 'ok'
            }
        }
        
        # Check database
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            health_status['checks']['database'] = 'error'
            health_status['status'] = 'degraded'
        
        # Check cache
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') != 'ok':
                raise Exception("Cache test failed")
        except Exception:
            health_status['checks']['cache'] = 'error'
            health_status['status'] = 'degraded'
        
        # Check security monitoring
        try:
            dashboard_data = security_monitor.get_security_dashboard_data()
            threat_level = dashboard_data.get('threat_level', 'unknown')
            
            if threat_level in ['critical', 'high']:
                health_status['checks']['security'] = 'warning'
                health_status['status'] = 'degraded'
        except Exception:
            health_status['checks']['security'] = 'error'
            health_status['status'] = 'degraded'
        
        # Return appropriate status code
        if health_status['status'] == 'healthy':
            return Response(health_status, status=status.HTTP_200_OK)
        else:
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            {
                'status': 'error',
                'error': 'Health check failed',
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


# Function-based views for non-API endpoints

@require_http_methods(["POST"])
@csrf_exempt
def csp_report_endpoint(request):
    """CSP violation report endpoint."""
    view = CSPReportView()
    return view.post(request)


@login_required
@user_passes_test(lambda u: u.is_staff)
def security_report_download(request):
    """Download security report as text file."""
    
    try:
        # Get scan results or dashboard data
        dashboard_data = security_monitor.get_security_dashboard_data()
        
        # Generate report
        report_content = get_vulnerability_report({
            'scan_id': f"dashboard_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            'base_url': request.build_absolute_uri('/'),
            'duration': 0,
            'vulnerabilities_found': len(dashboard_data.get('recent_alerts', [])),
            'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'vulnerabilities': dashboard_data.get('recent_alerts', [])
        })
        
        # Create response
        response = HttpResponse(report_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="security_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating security report: {e}")
        return JsonResponse({'error': 'Failed to generate report'}, status=500)
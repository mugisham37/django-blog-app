"""
Comprehensive tests for security implementation.
Tests security headers, HTTPS enforcement, audit logging, and security middleware.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.core.middleware import SecurityMiddleware
from apps.core.security_audit import SecurityAuditLogger, SecurityEventMonitor
from apps.core.security_views import csp_report_view
from apps.core.exceptions import get_client_ip

User = get_user_model()


class SecurityMiddlewareTest(TestCase):
    """Test security middleware functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda request: HttpResponse())
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_https_enforcement_in_production(self):
        """Test HTTPS enforcement redirects HTTP to HTTPS."""
        with override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True):
            request = self.factory.get('/test/', HTTP_HOST='example.com')
            request.user = self.user
            
            response = self.middleware.process_request(request)
            
            self.assertEqual(response.status_code, 301)
            self.assertTrue(response.url.startswith('https://'))
    
    def test_https_enforcement_skipped_in_debug(self):
        """Test HTTPS enforcement is skipped in debug mode."""
        with override_settings(DEBUG=True):
            request = self.factory.get('/test/')
            request.user = self.user
            
            response = self.middleware.process_request(request)
            
            self.assertIsNone(response)
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        request = self.factory.get('/test/')
        request.user = self.user
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        # Check basic security headers
        self.assertEqual(processed_response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(processed_response['X-Frame-Options'], 'DENY')
        self.assertEqual(processed_response['X-XSS-Protection'], '1; mode=block')
        self.assertEqual(processed_response['Referrer-Policy'], 'strict-origin-when-cross-origin')
        
        # Check additional security headers
        self.assertEqual(processed_response['Cross-Origin-Embedder-Policy'], 'require-corp')
        self.assertEqual(processed_response['Cross-Origin-Opener-Policy'], 'same-origin')
        self.assertEqual(processed_response['Cross-Origin-Resource-Policy'], 'same-origin')
    
    def test_csp_header_for_public_pages(self):
        """Test CSP header for public pages."""
        request = self.factory.get('/blog/')
        request.user = self.user
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertIn('Content-Security-Policy', processed_response)
        csp = processed_response['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
    
    def test_csp_header_for_admin_pages(self):
        """Test relaxed CSP header for admin pages."""
        request = self.factory.get('/admin/')
        request.user = self.user
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertIn('Content-Security-Policy', processed_response)
        csp = processed_response['Content-Security-Policy']
        self.assertIn("script-src 'self' 'unsafe-inline' 'unsafe-eval'", csp)
    
    def test_csp_header_for_api_endpoints(self):
        """Test strict CSP header for API endpoints."""
        request = self.factory.get('/api/posts/')
        request.user = self.user
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertIn('Content-Security-Policy', processed_response)
        csp = processed_response['Content-Security-Policy']
        self.assertIn("default-src 'none'", csp)
    
    @override_settings(DEBUG=False, SECURE_HSTS_SECONDS=31536000)
    def test_hsts_header_for_https_requests(self):
        """Test HSTS header is added for HTTPS requests."""
        request = self.factory.get('/test/', secure=True)
        request.user = self.user
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertIn('Strict-Transport-Security', processed_response)
        hsts = processed_response['Strict-Transport-Security']
        self.assertIn('max-age=31536000', hsts)
        self.assertIn('includeSubDomains', hsts)
    
    def test_hsts_header_not_added_for_http_requests(self):
        """Test HSTS header is not added for HTTP requests."""
        request = self.factory.get('/test/')
        request.user = self.user
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertNotIn('Strict-Transport-Security', processed_response)
    
    def test_suspicious_request_detection(self):
        """Test detection of suspicious request patterns."""
        # Test SQL injection pattern
        request = self.factory.get('/test/?id=1\' OR 1=1--')
        request.user = self.user
        
        with patch('apps.core.middleware.log_security_event') as mock_log:
            response = self.middleware.process_request(request)
            
            self.assertEqual(response.status_code, 403)
            mock_log.assert_called()
    
    def test_suspicious_user_agent_detection(self):
        """Test detection of suspicious user agents."""
        request = self.factory.get('/test/', HTTP_USER_AGENT='sqlmap/1.0')
        request.user = self.user
        
        with patch('apps.core.middleware.log_security_event') as mock_log:
            response = self.middleware.process_request(request)
            
            self.assertEqual(response.status_code, 403)
            mock_log.assert_called()
    
    def test_static_files_skip_security_checks(self):
        """Test that static files skip security checks."""
        request = self.factory.get('/static/css/style.css')
        request.user = self.user
        
        response = self.middleware.process_request(request)
        
        self.assertIsNone(response)


class SecurityAuditLoggerTest(TestCase):
    """Test security audit logging functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('apps.core.security_audit.security_logger')
    def test_authentication_event_logging(self, mock_logger):
        """Test authentication event logging."""
        request = self.factory.post('/login/')
        request.session = {}
        request.session.session_key = 'test_session'
        
        SecurityAuditLogger.log_authentication_event(
            'user_login',
            self.user,
            request,
            extra_data={'login_method': 'standard'}
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        self.assertIn('Authentication event: user_login', call_args[0])
        
        extra_data = call_args[1]['extra']
        self.assertEqual(extra_data['event_type'], 'user_login')
        self.assertEqual(extra_data['user_id'], self.user.id)
        self.assertEqual(extra_data['username'], self.user.username)
        self.assertEqual(extra_data['login_method'], 'standard')
    
    @patch('apps.core.security_audit.security_logger')
    def test_permission_event_logging(self, mock_logger):
        """Test permission event logging."""
        request = self.factory.get('/admin/')
        
        SecurityAuditLogger.log_permission_event(
            'access_denied',
            self.user,
            'admin_panel',
            'view',
            request,
            success=False
        )
        
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        
        # Check log level (should be WARNING for failed access)
        self.assertEqual(call_args[0][0], 30)  # WARNING level
        
        extra_data = call_args[1]['extra']
        self.assertEqual(extra_data['event_type'], 'access_denied')
        self.assertEqual(extra_data['resource'], 'admin_panel')
        self.assertEqual(extra_data['action'], 'view')
        self.assertFalse(extra_data['success'])
    
    @patch('apps.core.security_audit.security_logger')
    def test_security_violation_logging(self, mock_logger):
        """Test security violation logging."""
        request = self.factory.get('/test/')
        
        SecurityAuditLogger.log_security_violation(
            'brute_force_attempt',
            self.user,
            request,
            severity='high',
            extra_data={'attempt_count': 5}
        )
        
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        
        # Check log level (should be ERROR for high severity)
        self.assertEqual(call_args[0][0], 40)  # ERROR level
        
        extra_data = call_args[1]['extra']
        self.assertEqual(extra_data['event_type'], 'security_violation')
        self.assertEqual(extra_data['violation_type'], 'brute_force_attempt')
        self.assertEqual(extra_data['severity'], 'high')
        self.assertEqual(extra_data['attempt_count'], 5)
    
    def test_security_event_caching(self):
        """Test that security events are cached for monitoring."""
        request = self.factory.get('/test/')
        
        SecurityAuditLogger.log_authentication_event(
            'user_login',
            self.user,
            request
        )
        
        # Check that event is cached
        cache_key = f"security_events_user_login_{get_client_ip(request)}"
        cached_events = cache.get(cache_key, [])
        
        self.assertEqual(len(cached_events), 1)
        self.assertEqual(cached_events[0]['event_type'], 'user_login')
        self.assertEqual(cached_events[0]['user_id'], self.user.id)


class SecurityEventMonitorTest(TestCase):
    """Test security event monitoring functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()
    
    def test_brute_force_detection(self):
        """Test brute force attempt detection."""
        ip_address = '192.168.1.100'
        
        # Simulate multiple failed login attempts
        cache_key = f"failed_logins_{ip_address}"
        failed_attempts = []
        
        for i in range(6):  # Exceed threshold of 5
            failed_attempts.append({
                'timestamp': timezone.now().isoformat(),
                'username': f'user{i}',
            })
        
        cache.set(cache_key, failed_attempts, 900)  # 15 minutes
        
        # Check brute force detection
        is_brute_force = SecurityEventMonitor.check_brute_force_attempts(
            ip_address, threshold=5, window_minutes=15
        )
        
        self.assertTrue(is_brute_force)
    
    def test_suspicious_activity_pattern_detection(self):
        """Test suspicious activity pattern detection."""
        ip_address = '192.168.1.100'
        
        # Simulate multiple suspicious events
        cache_key = f"security_events_suspicious_activity_{ip_address}"
        events = []
        
        for i in range(12):  # Exceed threshold of 10
            events.append({
                'timestamp': timezone.now().isoformat(),
                'event_type': 'suspicious_activity',
                'ip_address': ip_address,
            })
        
        cache.set(cache_key, events, 300)  # 5 minutes
        
        # Check suspicious activity detection
        is_suspicious = SecurityEventMonitor.check_suspicious_activity_pattern(
            ip_address, threshold=10, window_minutes=5
        )
        
        self.assertTrue(is_suspicious)


class CSPReportViewTest(TestCase):
    """Test CSP report handling."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    @patch('apps.core.security_views.SecurityAuditLogger.log_security_violation')
    def test_csp_report_processing(self, mock_log):
        """Test CSP violation report processing."""
        csp_report = {
            'csp-report': {
                'document-uri': 'https://example.com/page',
                'blocked-uri': 'https://evil.com/script.js',
                'violated-directive': 'script-src',
                'effective-directive': 'script-src',
                'original-policy': "default-src 'self'",
                'disposition': 'enforce',
                'status-code': 200,
            }
        }
        
        request = self.factory.post(
            '/security/csp-report/',
            data=json.dumps(csp_report),
            content_type='application/json'
        )
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        response = csp_report_view(request)
        
        self.assertEqual(response.status_code, 204)
        mock_log.assert_called_once()
        
        # Check logged violation data
        call_args = mock_log.call_args
        self.assertEqual(call_args[0][0], 'csp_violation')
        self.assertEqual(call_args[1]['severity'], 'medium')
        
        extra_data = call_args[1]['extra_data']
        self.assertEqual(extra_data['blocked_uri'], 'https://evil.com/script.js')
        self.assertEqual(extra_data['violated_directive'], 'script-src')
    
    def test_invalid_csp_report(self):
        """Test handling of invalid CSP reports."""
        request = self.factory.post(
            '/security/csp-report/',
            data='invalid json',
            content_type='application/json'
        )
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        response = csp_report_view(request)
        
        self.assertEqual(response.status_code, 400)


class SecurityConfigurationTest(TestCase):
    """Test security configuration settings."""
    
    def test_security_headers_configuration(self):
        """Test that security headers are properly configured."""
        # Test basic security settings
        self.assertTrue(getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False))
        self.assertTrue(getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False))
        self.assertEqual(getattr(settings, 'X_FRAME_OPTIONS', ''), 'DENY')
    
    def test_https_configuration(self):
        """Test HTTPS configuration."""
        # These should be properly configured in production
        if not settings.DEBUG:
            self.assertTrue(getattr(settings, 'SECURE_SSL_REDIRECT', False))
            self.assertGreater(getattr(settings, 'SECURE_HSTS_SECONDS', 0), 0)
            self.assertTrue(getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False))
    
    def test_cookie_security_configuration(self):
        """Test cookie security configuration."""
        if not settings.DEBUG:
            self.assertTrue(getattr(settings, 'SESSION_COOKIE_SECURE', False))
            self.assertTrue(getattr(settings, 'CSRF_COOKIE_SECURE', False))
        
        self.assertTrue(getattr(settings, 'SESSION_COOKIE_HTTPONLY', False))
        self.assertTrue(getattr(settings, 'CSRF_COOKIE_HTTPONLY', False))
    
    def test_csp_configuration(self):
        """Test Content Security Policy configuration."""
        csp_default_src = getattr(settings, 'CSP_DEFAULT_SRC', None)
        if csp_default_src:
            self.assertIn("'self'", csp_default_src)
    
    def test_security_monitoring_configuration(self):
        """Test security monitoring configuration."""
        security_monitoring = getattr(settings, 'SECURITY_MONITORING', {})
        
        if security_monitoring:
            self.assertIn('ENABLE_CSP_REPORTING', security_monitoring)
            self.assertIn('ENABLE_AUDIT_LOGGING', security_monitoring)
            self.assertIn('ENABLE_HTTPS_ENFORCEMENT', security_monitoring)


class SecurityIntegrationTest(TestCase):
    """Integration tests for security features."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_security_headers_in_response(self):
        """Test that security headers are present in actual responses."""
        response = self.client.get('/')
        
        # Check for security headers
        self.assertEqual(response.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.get('X-XSS-Protection'), '1; mode=block')
        self.assertIn('Content-Security-Policy', response)
    
    def test_csp_report_endpoint_accessibility(self):
        """Test that CSP report endpoint is accessible."""
        csp_report = {
            'csp-report': {
                'document-uri': 'https://example.com/page',
                'blocked-uri': 'https://evil.com/script.js',
                'violated-directive': 'script-src',
            }
        }
        
        response = self.client.post(
            '/security/csp-report/',
            data=json.dumps(csp_report),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 204)
    
    def test_security_health_check_endpoint(self):
        """Test security health check endpoint."""
        response = self.client.get('/security/health/')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('timestamp', data)
    
    @override_settings(DEBUG=False)
    def test_https_redirect_in_production(self):
        """Test HTTPS redirect in production mode."""
        with patch('apps.core.middleware.SecurityMiddleware._is_secure_request', return_value=False):
            response = self.client.get('/', HTTP_HOST='example.com')
            
            # Should redirect to HTTPS
            self.assertEqual(response.status_code, 301)
            self.assertTrue(response.url.startswith('https://'))
    
    def test_suspicious_request_blocking(self):
        """Test that suspicious requests are blocked."""
        # Test SQL injection attempt
        response = self.client.get('/?id=1\' OR 1=1--')
        
        self.assertEqual(response.status_code, 403)
    
    def test_malicious_user_agent_blocking(self):
        """Test that malicious user agents are blocked."""
        response = self.client.get('/', HTTP_USER_AGENT='sqlmap/1.0')
        
        self.assertEqual(response.status_code, 403)
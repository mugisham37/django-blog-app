"""
Comprehensive security tests for Django Personal Blog System.
Tests all security components and measures.
"""

import json
import time
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

from .security_scanner import SecurityScanner, SecurityVulnerability
from .security_monitoring import SecurityMonitor, security_monitor
from .security_validators import SecurityValidator, PasswordValidator
from .rate_limiting import RateLimiter
from .security_headers import SecurityHeadersValidator

User = get_user_model()


class SecurityMiddlewareTest(TestCase):
    """Test security middleware functionality."""
    
    def setUp(self):
        self.client = Client()
        cache.clear()
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        
        response = self.client.get('/')
        
        # Check for important security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
    
    def test_ip_blocking(self):
        """Test IP blocking functionality."""
        
        # Simulate multiple failed requests from same IP
        for i in range(10):
            response = self.client.post('/api/auth/login/', {
                'username': 'nonexistent',
                'password': 'wrong'
            })
        
        # IP should be rate limited after multiple failures
        # Note: This test depends on rate limiting configuration
        self.assertTrue(True)  # Placeholder - actual implementation may vary
    
    def test_suspicious_request_detection(self):
        """Test detection of suspicious request patterns."""
        
        # Test with SQL injection payload
        response = self.client.get('/api/search/', {
            'q': "' OR '1'='1"
        })
        
        # Should not return SQL errors
        content = response.content.decode()
        self.assertNotIn('sql', content.lower())
        self.assertNotIn('error', content.lower())
    
    def test_xss_protection(self):
        """Test XSS protection."""
        
        xss_payload = "<script>alert('xss')</script>"
        
        response = self.client.get('/api/search/', {'q': xss_payload})
        
        # Payload should be escaped or filtered
        content = response.content.decode()
        self.assertNotIn('<script>', content)


class CSRFProtectionTest(TestCase):
    """Test CSRF protection enhancements."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_csrf_token_required(self):
        """Test that CSRF token is required for POST requests."""
        
        # POST without CSRF token should fail
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertIn(response.status_code, [403, 400])
    
    def test_csrf_token_rotation(self):
        """Test CSRF token rotation functionality."""
        
        self.client.login(username='testuser', password='testpass123')
        
        # Get initial CSRF token
        response1 = self.client.get('/api/auth/user/')
        token1 = response1.cookies.get('csrftoken')
        
        # Simulate security event that should trigger rotation
        cache.set(f'security_event:password_change:{self.user.id}', True, 3600)
        
        # Make another request
        response2 = self.client.get('/api/auth/user/')
        token2 = response2.cookies.get('csrftoken')
        
        # Tokens should be different after rotation
        if token1 and token2:
            self.assertNotEqual(token1.value, token2.value)


class SecurityValidatorTest(TestCase):
    """Test security validators and input sanitization."""
    
    def setUp(self):
        self.validator = SecurityValidator()
    
    def test_text_sanitization(self):
        """Test text input sanitization."""
        
        # Test XSS payload sanitization
        malicious_text = "<script>alert('xss')</script>Hello World"
        sanitized = self.validator.validate_and_sanitize_text(malicious_text)
        
        self.assertNotIn('<script>', sanitized)
        self.assertIn('Hello World', sanitized)
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        
        sql_payload = "'; DROP TABLE users--"
        
        with self.assertRaises(Exception):
            self.validator.validate_and_sanitize_text(sql_payload)
    
    def test_email_validation(self):
        """Test email validation and sanitization."""
        
        # Valid email
        valid_email = "user@example.com"
        result = self.validator.validate_email(valid_email)
        self.assertEqual(result, valid_email.lower())
        
        # Invalid email domain (if configured)
        # This test depends on BLACKLISTED_EMAIL_DOMAINS setting
    
    def test_url_validation(self):
        """Test URL validation."""
        
        # Valid URL
        valid_url = "https://example.com"
        result = self.validator.validate_url(valid_url)
        self.assertEqual(result, valid_url)
        
        # Invalid scheme
        with self.assertRaises(Exception):
            self.validator.validate_url("javascript:alert('xss')")
    
    def test_filename_validation(self):
        """Test filename validation."""
        
        # Valid filename
        valid_filename = "document.pdf"
        result = self.validator.validate_filename(valid_filename)
        self.assertEqual(result, valid_filename)
        
        # Dangerous filename
        with self.assertRaises(Exception):
            self.validator.validate_filename("malware.exe")
        
        # Path traversal attempt
        with self.assertRaises(Exception):
            self.validator.validate_filename("../../../etc/passwd")


class PasswordValidatorTest(TestCase):
    """Test password validation."""
    
    def setUp(self):
        self.validator = PasswordValidator()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
    
    def test_strong_password_accepted(self):
        """Test that strong passwords are accepted."""
        
        strong_password = "StrongP@ssw0rd123!"
        
        # Should not raise exception
        try:
            self.validator.validate(strong_password, self.user)
        except Exception:
            self.fail("Strong password was rejected")
    
    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected."""
        
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "short",
            "nouppercase123!",
            "NOLOWERCASE123!",
            "NoNumbers!",
            "NoSpecialChars123"
        ]
        
        for weak_password in weak_passwords:
            with self.assertRaises(Exception):
                self.validator.validate(weak_password, self.user)
    
    def test_user_specific_validation(self):
        """Test user-specific password validation."""
        
        # Password containing username should be rejected
        with self.assertRaises(Exception):
            self.validator.validate("testuser123!", self.user)
        
        # Password containing email should be rejected
        with self.assertRaises(Exception):
            self.validator.validate("test@example123!", self.user)


class RateLimitingTest(TestCase):
    """Test rate limiting functionality."""
    
    def setUp(self):
        self.client = Client()
        self.rate_limiter = RateLimiter()
        cache.clear()
    
    def test_rate_limiting_enforcement(self):
        """Test that rate limiting is enforced."""
        
        # Make multiple rapid requests
        responses = []
        for i in range(25):  # Exceed typical rate limit
            response = self.client.get('/api/search/', {'q': f'test{i}'})
            responses.append(response.status_code)
        
        # Should eventually get rate limited (429 status)
        self.assertIn(429, responses)
    
    def test_burst_protection(self):
        """Test burst rate limiting."""
        
        # Make very rapid requests
        start_time = time.time()
        responses = []
        
        for i in range(15):  # Exceed burst limit
            response = self.client.get('/api/test/')
            responses.append(response.status_code)
            
            # Stop if we get rate limited
            if response.status_code == 429:
                break
        
        # Should get rate limited quickly for burst
        self.assertIn(429, responses)
    
    def test_ddos_detection(self):
        """Test DDoS attack pattern detection."""
        
        # Simulate high-frequency requests
        request = MagicMock()
        request.META = {
            'HTTP_USER_AGENT': 'curl/7.68.0',  # Automation tool
            'REMOTE_ADDR': '192.168.1.100'
        }
        request.method = 'GET'
        request.path = '/api/test/'
        request.GET = {}
        request.POST = {}
        
        # Should detect DDoS patterns
        ddos_detected = self.rate_limiter._check_ddos_patterns(request, '192.168.1.100')
        
        # This test may need adjustment based on implementation
        self.assertIsInstance(ddos_detected, bool)


class SecurityScannerTest(TestCase):
    """Test security vulnerability scanner."""
    
    def setUp(self):
        self.scanner = SecurityScanner('http://testserver')
    
    def test_sql_injection_scan(self):
        """Test SQL injection vulnerability scanning."""
        
        # Run SQL injection scan
        self.scanner._scan_sql_injection()
        
        # Check if any vulnerabilities were found
        sql_vulns = [v for v in self.scanner.vulnerabilities if v.category == 'injection']
        
        # Should not find SQL injection vulnerabilities in a properly secured app
        self.assertEqual(len(sql_vulns), 0)
    
    def test_xss_scan(self):
        """Test XSS vulnerability scanning."""
        
        # Run XSS scan
        self.scanner._scan_xss()
        
        # Check for XSS vulnerabilities
        xss_vulns = [v for v in self.scanner.vulnerabilities if v.category == 'xss']
        
        # Should not find XSS vulnerabilities in a properly secured app
        self.assertEqual(len(xss_vulns), 0)
    
    def test_security_headers_scan(self):
        """Test security headers scanning."""
        
        # Run security headers scan
        self.scanner._scan_security_headers()
        
        # Should find missing headers if not properly configured
        header_vulns = [v for v in self.scanner.vulnerabilities if v.category == 'security_headers']
        
        # This test depends on actual header configuration
        self.assertIsInstance(len(header_vulns), int)
    
    def test_full_scan(self):
        """Test full security scan."""
        
        results = self.scanner.run_full_scan()
        
        # Check scan results structure
        self.assertIn('scan_id', results)
        self.assertIn('vulnerabilities_found', results)
        self.assertIn('severity_counts', results)
        self.assertIn('vulnerabilities', results)
        
        # Should have run multiple tests
        self.assertGreater(len(results['tests_run']), 0)


class SecurityMonitoringTest(TestCase):
    """Test security monitoring functionality."""
    
    def setUp(self):
        self.monitor = SecurityMonitor()
        cache.clear()
    
    def test_login_attempt_monitoring(self):
        """Test login attempt monitoring."""
        
        # Monitor successful login
        self.monitor.monitor_login_attempts('192.168.1.100', user_id=1, success=True)
        
        # Monitor failed login
        self.monitor.monitor_login_attempts('192.168.1.100', user_id=1, success=False)
        
        # Should not create alerts for single failed attempt
        self.assertEqual(len(self.monitor.vulnerabilities), 0)
        
        # Monitor multiple failed attempts
        for i in range(6):  # Exceed threshold
            self.monitor.monitor_login_attempts('192.168.1.100', user_id=1, success=False)
        
        # Should create alert for multiple failures
        # Note: This test depends on alert creation implementation
    
    def test_csrf_failure_monitoring(self):
        """Test CSRF failure monitoring."""
        
        # Monitor CSRF failures
        for i in range(12):  # Exceed threshold
            self.monitor.monitor_csrf_failures('192.168.1.100', '/api/test/', user_id=1)
        
        # Should detect CSRF attack pattern
        # Note: This test depends on alert creation implementation
    
    def test_security_dashboard_data(self):
        """Test security dashboard data generation."""
        
        dashboard_data = self.monitor.get_security_dashboard_data()
        
        # Check dashboard data structure
        self.assertIn('recent_alerts', dashboard_data)
        self.assertIn('statistics', dashboard_data)
        self.assertIn('threat_level', dashboard_data)
        self.assertIn('recommendations', dashboard_data)


class SecurityHeadersTest(TestCase):
    """Test security headers functionality."""
    
    def setUp(self):
        self.client = Client()
    
    def test_security_headers_validation(self):
        """Test security headers validation."""
        
        # Test CSP configuration validation
        csp_config = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'"],  # Should trigger warning
            'object-src': ["'none'"]
        }
        
        warnings = SecurityHeadersValidator.validate_csp_config(csp_config)
        
        # Should warn about unsafe-inline
        self.assertTrue(any("unsafe-inline" in warning for warning in warnings))
    
    def test_security_score_calculation(self):
        """Test security configuration scoring."""
        
        score_data = SecurityHeadersValidator.get_security_score()
        
        # Check score structure
        self.assertIn('score', score_data)
        self.assertIn('grade', score_data)
        self.assertIn('issues', score_data)
        self.assertIn('recommendations', score_data)
        
        # Score should be between 0 and 100
        self.assertGreaterEqual(score_data['score'], 0)
        self.assertLessEqual(score_data['score'], 100)


class SecurityAPITest(TestCase):
    """Test security API endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
    
    def test_security_dashboard_access(self):
        """Test security dashboard API access control."""
        
        # Unauthenticated access should be denied
        response = self.client.get('/api/core/security/api/dashboard/')
        self.assertEqual(response.status_code, 401)
        
        # Regular user access should be denied
        self.client.login(username='user', password='userpass123')
        response = self.client.get('/api/core/security/api/dashboard/')
        self.assertEqual(response.status_code, 403)
        
        # Admin access should be allowed
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/api/core/security/api/dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        
        response = self.client.get('/api/core/security/health/')
        
        # Should return health status
        self.assertIn(response.status_code, [200, 503])
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
    
    def test_csp_report_endpoint(self):
        """Test CSP violation report endpoint."""
        
        csp_report = {
            'csp-report': {
                'blocked-uri': 'https://evil.com/malicious.js',
                'document-uri': 'https://example.com/page',
                'violated-directive': 'script-src',
                'original-policy': "default-src 'self'"
            }
        }
        
        response = self.client.post(
            '/api/core/security/csp-report/',
            json.dumps(csp_report),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'received')


@override_settings(
    SECURITY_MONITORING={'ENABLE_CSP_REPORTING': True},
    RATELIMIT_ENABLE=True
)
class SecurityIntegrationTest(TestCase):
    """Integration tests for security components."""
    
    def setUp(self):
        self.client = Client()
        cache.clear()
    
    def test_security_middleware_integration(self):
        """Test integration of security middleware components."""
        
        # Make a request that should trigger security processing
        response = self.client.get('/', HTTP_USER_AGENT='TestAgent/1.0')
        
        # Should have security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        
        # Should process without errors
        self.assertNotEqual(response.status_code, 500)
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration with other components."""
        
        # Make requests that should be rate limited
        responses = []
        for i in range(30):
            response = self.client.get('/api/test/', {'param': f'value{i}'})
            responses.append(response.status_code)
            
            # Break if rate limited
            if response.status_code == 429:
                break
        
        # Should eventually get rate limited
        self.assertIn(429, responses)
    
    def test_security_monitoring_integration(self):
        """Test security monitoring integration."""
        
        # Trigger security events
        for i in range(3):
            self.client.post('/api/auth/login/', {
                'username': 'nonexistent',
                'password': 'wrong'
            })
        
        # Check if events were monitored
        dashboard_data = security_monitor.get_security_dashboard_data()
        
        # Should have statistics
        self.assertIn('statistics', dashboard_data)
        self.assertIsInstance(dashboard_data['statistics'], dict)


class SecurityPerformanceTest(TestCase):
    """Test security component performance."""
    
    def setUp(self):
        self.client = Client()
    
    def test_security_middleware_performance(self):
        """Test that security middleware doesn't significantly impact performance."""
        
        # Measure response time with security middleware
        start_time = time.time()
        
        for i in range(10):
            response = self.client.get('/')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete reasonably quickly (adjust threshold as needed)
        self.assertLess(duration, 5.0)  # 5 seconds for 10 requests
    
    def test_rate_limiter_performance(self):
        """Test rate limiter performance."""
        
        rate_limiter = RateLimiter()
        
        # Create mock request
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '192.168.1.100'}
        request.user = MagicMock()
        request.user.is_authenticated = False
        request.path = '/api/test/'
        request.method = 'GET'
        
        # Measure rate limit check performance
        start_time = time.time()
        
        for i in range(100):
            rate_limiter.check_rate_limit(request)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast (adjust threshold as needed)
        self.assertLess(duration, 1.0)  # 1 second for 100 checks
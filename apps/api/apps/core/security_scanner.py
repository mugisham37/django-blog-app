"""
Security vulnerability scanner and penetration testing tools for Django Personal Blog System.
Implements automated security scanning and vulnerability assessment.
"""

import re
import json
import logging
import requests
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache

User = get_user_model()
logger = logging.getLogger('security')


@dataclass
class SecurityVulnerability:
    """Data class for security vulnerabilities."""
    id: str
    title: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str
    affected_component: str
    recommendation: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    discovered_at: Optional[datetime] = None
    status: str = 'open'  # 'open', 'fixed', 'false_positive', 'accepted_risk'


class SecurityScanner:
    """
    Comprehensive security vulnerability scanner.
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or 'http://localhost:8000'
        self.client = Client()
        self.vulnerabilities = []
        self.scan_results = {}
    
    def run_full_scan(self) -> Dict[str, Any]:
        """Run comprehensive security scan."""
        
        logger.info("Starting comprehensive security scan")
        
        # Initialize results
        self.vulnerabilities = []
        self.scan_results = {
            'scan_id': f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'started_at': datetime.now(),
            'base_url': self.base_url,
            'tests_run': [],
            'vulnerabilities_found': 0,
            'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        }
        
        # Run different types of scans
        scan_methods = [
            ('SQL Injection', self._scan_sql_injection),
            ('XSS Vulnerabilities', self._scan_xss),
            ('CSRF Protection', self._scan_csrf),
            ('Authentication', self._scan_authentication),
            ('Authorization', self._scan_authorization),
            ('Information Disclosure', self._scan_information_disclosure),
            ('Security Headers', self._scan_security_headers),
            ('SSL/TLS Configuration', self._scan_ssl_tls),
            ('Directory Traversal', self._scan_directory_traversal),
            ('File Upload Security', self._scan_file_upload),
            ('Rate Limiting', self._scan_rate_limiting),
            ('Session Security', self._scan_session_security),
        ]
        
        for test_name, scan_method in scan_methods:
            try:
                logger.info(f"Running {test_name} scan")
                scan_method()
                self.scan_results['tests_run'].append(test_name)
            except Exception as e:
                logger.error(f"Error in {test_name} scan: {e}")
                self._add_vulnerability(
                    f"scan_error_{test_name.lower().replace(' ', '_')}",
                    f"Scan Error: {test_name}",
                    f"Error occurred during {test_name} scan: {e}",
                    'medium',
                    'scanner',
                    'security_scanner',
                    f"Review and fix the {test_name} scanning method"
                )
        
        # Finalize results
        self.scan_results['completed_at'] = datetime.now()
        self.scan_results['duration'] = (
            self.scan_results['completed_at'] - self.scan_results['started_at']
        ).total_seconds()
        self.scan_results['vulnerabilities_found'] = len(self.vulnerabilities)
        
        # Count vulnerabilities by severity
        for vuln in self.vulnerabilities:
            self.scan_results['severity_counts'][vuln.severity] += 1
        
        self.scan_results['vulnerabilities'] = [asdict(v) for v in self.vulnerabilities]
        
        logger.info(f"Security scan completed. Found {len(self.vulnerabilities)} vulnerabilities")
        
        return self.scan_results
    
    def _scan_sql_injection(self) -> None:
        """Scan for SQL injection vulnerabilities."""
        
        # SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "'; DROP TABLE users--",
            "' OR 1=1#",
            "admin'--",
            "' OR 'x'='x",
            "1' OR '1'='1' /*",
        ]
        
        # Test endpoints that might be vulnerable
        test_endpoints = [
            '/api/blog/posts/',
            '/api/search/',
            '/api/comments/',
            '/admin/login/',
        ]
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                # Test GET parameters
                response = self.client.get(endpoint, {'q': payload, 'search': payload})
                
                if self._detect_sql_error(response):
                    self._add_vulnerability(
                        f"sql_injection_{endpoint.replace('/', '_')}",
                        "SQL Injection Vulnerability",
                        f"Potential SQL injection in {endpoint} with payload: {payload}",
                        'critical',
                        'injection',
                        endpoint,
                        "Use parameterized queries and input validation"
                    )
                
                # Test POST data if applicable
                if endpoint.startswith('/api/'):
                    try:
                        response = self.client.post(
                            endpoint,
                            {'title': payload, 'content': payload, 'comment': payload},
                            content_type='application/json'
                        )
                        
                        if self._detect_sql_error(response):
                            self._add_vulnerability(
                                f"sql_injection_post_{endpoint.replace('/', '_')}",
                                "SQL Injection in POST Data",
                                f"Potential SQL injection in POST to {endpoint}",
                                'critical',
                                'injection',
                                endpoint,
                                "Use parameterized queries and input validation"
                            )
                    except Exception:
                        pass  # Endpoint might not accept POST
    
    def _scan_xss(self) -> None:
        """Scan for Cross-Site Scripting vulnerabilities."""
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<<SCRIPT>alert('XSS')//<</SCRIPT>",
        ]
        
        # Test endpoints
        test_endpoints = [
            '/api/blog/posts/',
            '/api/comments/',
            '/api/search/',
        ]
        
        for endpoint in test_endpoints:
            for payload in xss_payloads:
                # Test reflected XSS
                response = self.client.get(endpoint, {'q': payload, 'search': payload})
                
                if payload in response.content.decode('utf-8', errors='ignore'):
                    self._add_vulnerability(
                        f"xss_reflected_{endpoint.replace('/', '_')}",
                        "Reflected XSS Vulnerability",
                        f"Reflected XSS found in {endpoint} with payload: {payload}",
                        'high',
                        'xss',
                        endpoint,
                        "Implement proper output encoding and CSP headers"
                    )
                
                # Test stored XSS (if POST is supported)
                if endpoint.startswith('/api/'):
                    try:
                        # Create content with XSS payload
                        post_data = {
                            'title': f"Test {payload}",
                            'content': payload,
                            'comment': payload
                        }
                        
                        response = self.client.post(endpoint, post_data)
                        
                        # Check if payload is stored and reflected
                        if response.status_code in [200, 201]:
                            get_response = self.client.get(endpoint)
                            if payload in get_response.content.decode('utf-8', errors='ignore'):
                                self._add_vulnerability(
                                    f"xss_stored_{endpoint.replace('/', '_')}",
                                    "Stored XSS Vulnerability",
                                    f"Stored XSS found in {endpoint}",
                                    'critical',
                                    'xss',
                                    endpoint,
                                    "Implement input validation and output encoding"
                                )
                    except Exception:
                        pass
    
    def _scan_csrf(self) -> None:
        """Scan for CSRF protection issues."""
        
        # Test endpoints that should have CSRF protection
        csrf_endpoints = [
            '/api/auth/login/',
            '/api/blog/posts/',
            '/api/comments/',
            '/admin/login/',
        ]
        
        for endpoint in csrf_endpoints:
            # Test POST without CSRF token
            response = self.client.post(endpoint, {'test': 'data'})
            
            # If request succeeds without CSRF token, it's vulnerable
            if response.status_code not in [403, 400]:
                # Check if it's actually processing the request
                if 'csrf' not in response.content.decode('utf-8', errors='ignore').lower():
                    self._add_vulnerability(
                        f"csrf_missing_{endpoint.replace('/', '_')}",
                        "Missing CSRF Protection",
                        f"Endpoint {endpoint} may be missing CSRF protection",
                        'high',
                        'csrf',
                        endpoint,
                        "Implement CSRF token validation for all state-changing operations"
                    )
    
    def _scan_authentication(self) -> None:
        """Scan for authentication vulnerabilities."""
        
        # Test weak password policies
        weak_passwords = ['123456', 'password', 'admin', 'test', '']
        
        for password in weak_passwords:
            try:
                # Try to create user with weak password
                response = self.client.post('/api/auth/register/', {
                    'username': f'testuser_{password}',
                    'email': f'test_{password}@example.com',
                    'password': password,
                    'password_confirm': password
                })
                
                if response.status_code in [200, 201]:
                    self._add_vulnerability(
                        f"weak_password_policy_{password}",
                        "Weak Password Policy",
                        f"System accepts weak password: {password}",
                        'medium',
                        'authentication',
                        '/api/auth/register/',
                        "Implement strong password requirements"
                    )
            except Exception:
                pass
        
        # Test for username enumeration
        try:
            # Test with existing vs non-existing usernames
            response1 = self.client.post('/api/auth/login/', {
                'username': 'admin',
                'password': 'wrongpassword'
            })
            
            response2 = self.client.post('/api/auth/login/', {
                'username': 'nonexistentuser12345',
                'password': 'wrongpassword'
            })
            
            # Different responses might indicate username enumeration
            if (response1.content != response2.content or 
                response1.status_code != response2.status_code):
                self._add_vulnerability(
                    "username_enumeration",
                    "Username Enumeration",
                    "Login endpoint reveals whether usernames exist",
                    'medium',
                    'authentication',
                    '/api/auth/login/',
                    "Return identical responses for valid and invalid usernames"
                )
        except Exception:
            pass
    
    def _scan_authorization(self) -> None:
        """Scan for authorization vulnerabilities."""
        
        # Test for insecure direct object references
        test_endpoints = [
            '/api/blog/posts/1/',
            '/api/comments/1/',
            '/api/users/1/',
        ]
        
        for endpoint in test_endpoints:
            # Test access without authentication
            response = self.client.get(endpoint)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                
                # Check if sensitive information is exposed
                sensitive_patterns = [
                    r'password',
                    r'email.*@.*\.',
                    r'token',
                    r'secret',
                    r'private'
                ]
                
                for pattern in sensitive_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self._add_vulnerability(
                            f"idor_{endpoint.replace('/', '_')}",
                            "Insecure Direct Object Reference",
                            f"Sensitive data exposed in {endpoint}",
                            'high',
                            'authorization',
                            endpoint,
                            "Implement proper access controls and data filtering"
                        )
                        break
    
    def _scan_information_disclosure(self) -> None:
        """Scan for information disclosure vulnerabilities."""
        
        # Test for debug information exposure
        debug_endpoints = [
            '/debug/',
            '/.env',
            '/config/',
            '/settings.py',
            '/manage.py',
            '/requirements.txt',
            '/.git/',
            '/admin/',
        ]
        
        for endpoint in debug_endpoints:
            response = self.client.get(endpoint)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                
                # Check for sensitive information
                if any(keyword in content.lower() for keyword in [
                    'secret_key', 'database', 'password', 'debug', 'traceback'
                ]):
                    self._add_vulnerability(
                        f"info_disclosure_{endpoint.replace('/', '_')}",
                        "Information Disclosure",
                        f"Sensitive information exposed at {endpoint}",
                        'medium',
                        'information_disclosure',
                        endpoint,
                        "Remove or restrict access to sensitive endpoints"
                    )
        
        # Test for error message information disclosure
        error_endpoints = [
            '/nonexistent/',
            '/api/nonexistent/',
            '/admin/nonexistent/',
        ]
        
        for endpoint in error_endpoints:
            response = self.client.get(endpoint)
            content = response.content.decode('utf-8', errors='ignore')
            
            # Check for detailed error messages
            if any(keyword in content.lower() for keyword in [
                'traceback', 'exception', 'django', 'python', 'file path'
            ]):
                self._add_vulnerability(
                    f"error_disclosure_{endpoint.replace('/', '_')}",
                    "Error Message Information Disclosure",
                    f"Detailed error information exposed at {endpoint}",
                    'low',
                    'information_disclosure',
                    endpoint,
                    "Configure custom error pages and disable debug mode"
                )
    
    def _scan_security_headers(self) -> None:
        """Scan for missing security headers."""
        
        response = self.client.get('/')
        
        # Required security headers
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # Should exist if HTTPS
            'Content-Security-Policy': None,
            'Referrer-Policy': None,
        }
        
        for header, expected_value in required_headers.items():
            if header not in response:
                self._add_vulnerability(
                    f"missing_header_{header.lower().replace('-', '_')}",
                    f"Missing Security Header: {header}",
                    f"Security header {header} is not set",
                    'medium',
                    'security_headers',
                    'response_headers',
                    f"Add {header} header to all responses"
                )
            elif expected_value and isinstance(expected_value, list):
                if response[header] not in expected_value:
                    self._add_vulnerability(
                        f"weak_header_{header.lower().replace('-', '_')}",
                        f"Weak Security Header: {header}",
                        f"Security header {header} has weak value: {response[header]}",
                        'low',
                        'security_headers',
                        'response_headers',
                        f"Set {header} to a secure value: {expected_value}"
                    )
    
    def _scan_ssl_tls(self) -> None:
        """Scan SSL/TLS configuration."""
        
        if not self.base_url.startswith('https://'):
            self._add_vulnerability(
                "no_https",
                "HTTPS Not Enforced",
                "Application is not using HTTPS",
                'high',
                'ssl_tls',
                'transport_security',
                "Implement HTTPS with proper SSL/TLS configuration"
            )
            return
        
        # Test SSL/TLS configuration (basic check)
        try:
            import ssl
            import socket
            
            hostname = urlparse(self.base_url).hostname
            port = urlparse(self.base_url).port or 443
            
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate validity
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    if not_after < datetime.now() + timedelta(days=30):
                        self._add_vulnerability(
                            "ssl_cert_expiring",
                            "SSL Certificate Expiring Soon",
                            f"SSL certificate expires on {not_after}",
                            'medium',
                            'ssl_tls',
                            'ssl_certificate',
                            "Renew SSL certificate before expiration"
                        )
        
        except Exception as e:
            self._add_vulnerability(
                "ssl_check_failed",
                "SSL/TLS Check Failed",
                f"Could not verify SSL/TLS configuration: {e}",
                'low',
                'ssl_tls',
                'ssl_certificate',
                "Verify SSL/TLS configuration manually"
            )
    
    def _scan_directory_traversal(self) -> None:
        """Scan for directory traversal vulnerabilities."""
        
        # Directory traversal payloads
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
            '..%252f..%252f..%252fetc%252fpasswd',
        ]
        
        # Test file serving endpoints
        file_endpoints = [
            '/media/',
            '/static/',
            '/files/',
            '/download/',
        ]
        
        for endpoint in file_endpoints:
            for payload in traversal_payloads:
                response = self.client.get(f"{endpoint}{payload}")
                content = response.content.decode('utf-8', errors='ignore')
                
                # Check for system file content
                if any(indicator in content for indicator in [
                    'root:x:', 'localhost', '# Copyright', '[boot loader]'
                ]):
                    self._add_vulnerability(
                        f"directory_traversal_{endpoint.replace('/', '_')}",
                        "Directory Traversal Vulnerability",
                        f"Directory traversal possible in {endpoint}",
                        'high',
                        'directory_traversal',
                        endpoint,
                        "Implement proper path validation and sanitization"
                    )
    
    def _scan_file_upload(self) -> None:
        """Scan for file upload vulnerabilities."""
        
        # Test file upload endpoints
        upload_endpoints = [
            '/api/upload/',
            '/api/blog/posts/',
            '/admin/upload/',
        ]
        
        # Malicious file types to test
        malicious_files = [
            ('test.php', b'<?php echo "RCE Test"; ?>', 'application/x-php'),
            ('test.jsp', b'<% out.println("RCE Test"); %>', 'application/x-jsp'),
            ('test.exe', b'MZ\x90\x00', 'application/x-executable'),
            ('test.sh', b'#!/bin/bash\necho "RCE Test"', 'application/x-sh'),
        ]
        
        for endpoint in upload_endpoints:
            for filename, content, content_type in malicious_files:
                try:
                    from django.core.files.uploadedfile import SimpleUploadedFile
                    
                    uploaded_file = SimpleUploadedFile(
                        filename, content, content_type=content_type
                    )
                    
                    response = self.client.post(endpoint, {'file': uploaded_file})
                    
                    if response.status_code in [200, 201]:
                        self._add_vulnerability(
                            f"malicious_upload_{filename.split('.')[1]}",
                            "Malicious File Upload",
                            f"Malicious file type {filename} accepted at {endpoint}",
                            'critical',
                            'file_upload',
                            endpoint,
                            "Implement file type validation and sandboxing"
                        )
                
                except Exception:
                    pass  # Endpoint might not exist or accept uploads
    
    def _scan_rate_limiting(self) -> None:
        """Scan for rate limiting implementation."""
        
        # Test rate limiting on sensitive endpoints
        rate_limit_endpoints = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/password-reset/',
        ]
        
        for endpoint in rate_limit_endpoints:
            # Make multiple rapid requests
            responses = []
            for i in range(20):
                response = self.client.post(endpoint, {'test': f'data_{i}'})
                responses.append(response.status_code)
            
            # Check if any rate limiting occurred
            if 429 not in responses:  # 429 = Too Many Requests
                self._add_vulnerability(
                    f"no_rate_limiting_{endpoint.replace('/', '_')}",
                    "Missing Rate Limiting",
                    f"No rate limiting detected on {endpoint}",
                    'medium',
                    'rate_limiting',
                    endpoint,
                    "Implement rate limiting to prevent abuse"
                )
    
    def _scan_session_security(self) -> None:
        """Scan for session security issues."""
        
        # Test session configuration
        response = self.client.get('/')
        
        # Check session cookie security
        if 'sessionid' in response.cookies:
            session_cookie = response.cookies['sessionid']
            
            if not session_cookie.get('secure'):
                self._add_vulnerability(
                    "insecure_session_cookie",
                    "Insecure Session Cookie",
                    "Session cookie is not marked as secure",
                    'medium',
                    'session_security',
                    'session_management',
                    "Set secure flag on session cookies"
                )
            
            if not session_cookie.get('httponly'):
                self._add_vulnerability(
                    "session_cookie_not_httponly",
                    "Session Cookie Not HttpOnly",
                    "Session cookie is accessible via JavaScript",
                    'medium',
                    'session_security',
                    'session_management',
                    "Set HttpOnly flag on session cookies"
                )
    
    def _detect_sql_error(self, response) -> bool:
        """Detect SQL error messages in response."""
        
        content = response.content.decode('utf-8', errors='ignore').lower()
        
        sql_error_patterns = [
            'sql syntax',
            'mysql_fetch',
            'ora-01756',
            'microsoft ole db',
            'odbc sql server driver',
            'sqlite_error',
            'postgresql error',
            'warning: mysql',
            'valid mysql result',
            'mysqlclient.cursors',
            'psycopg2.errors',
        ]
        
        return any(pattern in content for pattern in sql_error_patterns)
    
    def _add_vulnerability(self, vuln_id: str, title: str, description: str,
                          severity: str, category: str, component: str,
                          recommendation: str, cve_id: str = None,
                          cvss_score: float = None) -> None:
        """Add a vulnerability to the results."""
        
        vulnerability = SecurityVulnerability(
            id=vuln_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            affected_component=component,
            recommendation=recommendation,
            cve_id=cve_id,
            cvss_score=cvss_score,
            discovered_at=datetime.now()
        )
        
        self.vulnerabilities.append(vulnerability)
        logger.warning(f"Vulnerability found: {title} - {description}")


class SecurityTestCase(TestCase):
    """
    Security test cases for automated testing.
    """
    
    def setUp(self):
        self.scanner = SecurityScanner()
        self.client = Client()
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection."""
        
        # Test common SQL injection payloads
        payloads = ["' OR '1'='1", "'; DROP TABLE users--", "' UNION SELECT NULL--"]
        
        for payload in payloads:
            response = self.client.get('/api/search/', {'q': payload})
            
            # Should not return SQL errors
            self.assertNotIn('sql', response.content.decode().lower())
            self.assertNotIn('error', response.content.decode().lower())
    
    def test_xss_protection(self):
        """Test XSS protection."""
        
        xss_payload = "<script>alert('xss')</script>"
        
        response = self.client.get('/api/search/', {'q': xss_payload})
        
        # Payload should be escaped or filtered
        self.assertNotIn('<script>', response.content.decode())
    
    def test_csrf_protection(self):
        """Test CSRF protection."""
        
        # POST without CSRF token should fail
        response = self.client.post('/api/auth/login/', {
            'username': 'test',
            'password': 'test'
        })
        
        self.assertIn(response.status_code, [403, 400])
    
    def test_security_headers(self):
        """Test security headers presence."""
        
        response = self.client.get('/')
        
        # Check for important security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
    
    def test_authentication_security(self):
        """Test authentication security."""
        
        # Test weak password rejection
        response = self.client.post('/api/auth/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123456',
            'password_confirm': '123456'
        })
        
        # Should reject weak password
        self.assertNotEqual(response.status_code, 201)


# Management command for running security scans
class Command(BaseCommand):
    """Management command to run security scans."""
    
    help = 'Run security vulnerability scan'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='Base URL to scan'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for results (JSON format)'
        )
        parser.add_argument(
            '--severity',
            type=str,
            choices=['low', 'medium', 'high', 'critical'],
            help='Minimum severity level to report'
        )
    
    def handle(self, *args, **options):
        base_url = options['base_url']
        output_file = options.get('output')
        min_severity = options.get('severity', 'low')
        
        self.stdout.write(f"Starting security scan of {base_url}")
        
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
        
        # Output results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.stdout.write(f"Results saved to {output_file}")
        
        # Print summary
        self.stdout.write(
            self.style.SUCCESS(
                f"Scan completed in {results['duration']:.2f} seconds"
            )
        )
        self.stdout.write(f"Vulnerabilities found: {results['vulnerabilities_found']}")
        
        for severity in ['critical', 'high', 'medium', 'low']:
            count = results['severity_counts'][severity]
            if count > 0:
                style = self.style.ERROR if severity in ['critical', 'high'] else self.style.WARNING
                self.stdout.write(style(f"  {severity.capitalize()}: {count}"))


# Utility functions

def run_security_scan(base_url: str = None) -> Dict[str, Any]:
    """Run a security scan and return results."""
    scanner = SecurityScanner(base_url)
    return scanner.run_full_scan()


def get_vulnerability_report(scan_results: Dict[str, Any]) -> str:
    """Generate a human-readable vulnerability report."""
    
    report = []
    report.append("SECURITY VULNERABILITY REPORT")
    report.append("=" * 50)
    report.append(f"Scan ID: {scan_results['scan_id']}")
    report.append(f"Scanned URL: {scan_results['base_url']}")
    report.append(f"Scan Duration: {scan_results['duration']:.2f} seconds")
    report.append(f"Total Vulnerabilities: {scan_results['vulnerabilities_found']}")
    report.append("")
    
    # Severity summary
    report.append("SEVERITY BREAKDOWN:")
    for severity in ['critical', 'high', 'medium', 'low']:
        count = scan_results['severity_counts'][severity]
        report.append(f"  {severity.capitalize()}: {count}")
    report.append("")
    
    # Detailed vulnerabilities
    if scan_results['vulnerabilities']:
        report.append("DETAILED VULNERABILITIES:")
        report.append("-" * 30)
        
        for vuln in scan_results['vulnerabilities']:
            report.append(f"ID: {vuln['id']}")
            report.append(f"Title: {vuln['title']}")
            report.append(f"Severity: {vuln['severity'].upper()}")
            report.append(f"Category: {vuln['category']}")
            report.append(f"Component: {vuln['affected_component']}")
            report.append(f"Description: {vuln['description']}")
            report.append(f"Recommendation: {vuln['recommendation']}")
            report.append("")
    
    return "\n".join(report)
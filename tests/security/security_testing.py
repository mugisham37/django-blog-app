#!/usr/bin/env python3
"""
Security Testing and Vulnerability Assessment Suite
Comprehensive security testing for the entire system
"""

import json
import os
import re
import subprocess
import time
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import urljoin
import ssl
import socket
from dataclasses import dataclass


@dataclass
class SecurityTestResult:
    """Data class for security test results"""
    test_name: str
    status: str  # 'passed', 'failed', 'warning'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    details: Dict[str, Any]
    recommendations: List[str]


class SecurityTestSuite:
    """Comprehensive security testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def run_all_security_tests(self) -> List[SecurityTestResult]:
        """Run all security tests"""
        print("🔒 Starting Security Testing Suite...")
        
        test_methods = [
            self.test_ssl_tls_configuration,
            self.test_security_headers,
            self.test_authentication_security,
            self.test_authorization_controls,
            self.test_input_validation,
            self.test_sql_injection,
            self.test_xss_protection,
            self.test_csrf_protection,
            self.test_rate_limiting,
            self.test_information_disclosure,
            self.test_session_management,
            self.test_cors_configuration,
            self.test_file_upload_security,
            self.test_api_security,
            self.test_dependency_vulnerabilities,
        ]
        
        for test_method in test_methods:
            try:
                print(f"Running {test_method.__name__}...")
                result = test_method()
                if isinstance(result, list):
                    self.results.extend(result)
                else:
                    self.results.append(result)
                print(f"✅ {test_method.__name__} completed")
            except Exception as e:
                error_result = SecurityTestResult(
                    test_name=test_method.__name__,
                    status='failed',
                    severity='medium',
                    description=f"Test execution failed: {str(e)}",
                    details={'error': str(e)},
                    recommendations=['Fix test execution error and re-run']
                )
                self.results.append(error_result)
                print(f"❌ {test_method.__name__} failed: {e}")
        
        return self.results
    
    def test_ssl_tls_configuration(self) -> SecurityTestResult:
        """Test SSL/TLS configuration"""
        details = {}
        recommendations = []
        
        try:
            # Parse URL to get hostname and port
            from urllib.parse import urlparse
            parsed = urlparse(self.base_url)
            hostname = parsed.hostname or 'localhost'
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            if parsed.scheme == 'https':
                # Test SSL/TLS configuration
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        details['ssl_version'] = ssock.version()
                        details['cipher'] = ssock.cipher()
                        details['certificate'] = {
                            'subject': dict(x[0] for x in ssock.getpeercert()['subject']),
                            'issuer': dict(x[0] for x in ssock.getpeercert()['issuer']),
                            'version': ssock.getpeercert()['version'],
                            'not_after': ssock.getpeercert()['notAfter'],
                        }
                
                # Check for strong cipher suites
                if details['cipher'][1] not in ['TLSv1.2', 'TLSv1.3']:
                    recommendations.append("Upgrade to TLS 1.2 or 1.3")
                
                status = 'passed'
                severity = 'low'
                description = "SSL/TLS configuration is secure"
            else:
                status = 'failed'
                severity = 'high'
                description = "HTTPS not enabled"
                recommendations.append("Enable HTTPS with proper SSL/TLS configuration")
                
        except Exception as e:
            status = 'warning'
            severity = 'medium'
            description = f"Could not test SSL/TLS: {str(e)}"
            details['error'] = str(e)
            recommendations.append("Verify SSL/TLS configuration manually")
        
        return SecurityTestResult(
            test_name='SSL/TLS Configuration',
            status=status,
            severity=severity,
            description=description,
            details=details,
            recommendations=recommendations
        )
    
    def test_security_headers(self) -> SecurityTestResult:
        """Test security headers"""
        try:
            response = requests.get(self.base_url, timeout=10)
            headers = response.headers
            
            security_headers = {
                'X-Frame-Options': headers.get('X-Frame-Options'),
                'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
                'X-XSS-Protection': headers.get('X-XSS-Protection'),
                'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
                'Content-Security-Policy': headers.get('Content-Security-Policy'),
                'Referrer-Policy': headers.get('Referrer-Policy'),
                'Permissions-Policy': headers.get('Permissions-Policy'),
            }
            
            missing_headers = [k for k, v in security_headers.items() if not v]
            weak_headers = []
            
            # Check for weak configurations
            if security_headers.get('X-Frame-Options') not in ['DENY', 'SAMEORIGIN']:
                weak_headers.append('X-Frame-Options should be DENY or SAMEORIGIN')
            
            if security_headers.get('X-Content-Type-Options') != 'nosniff':
                weak_headers.append('X-Content-Type-Options should be nosniff')
            
            recommendations = []
            if missing_headers:
                recommendations.append(f"Add missing security headers: {', '.join(missing_headers)}")
            if weak_headers:
                recommendations.extend(weak_headers)
            
            if not missing_headers and not weak_headers:
                status = 'passed'
                severity = 'low'
                description = "All security headers are properly configured"
            elif len(missing_headers) > 3:
                status = 'failed'
                severity = 'high'
                description = f"Multiple critical security headers missing: {len(missing_headers)}"
            else:
                status = 'warning'
                severity = 'medium'
                description = f"Some security headers missing or misconfigured"
            
            return SecurityTestResult(
                test_name='Security Headers',
                status=status,
                severity=severity,
                description=description,
                details={'headers': security_headers, 'missing': missing_headers},
                recommendations=recommendations
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name='Security Headers',
                status='failed',
                severity='medium',
                description=f"Could not test security headers: {str(e)}",
                details={'error': str(e)},
                recommendations=['Fix connectivity issues and re-test']
            )
    
    def test_authentication_security(self) -> List[SecurityTestResult]:
        """Test authentication security"""
        results = []
        
        # Test 1: Password policy
        try:
            weak_passwords = ['123456', 'password', 'admin', '']
            for password in weak_passwords:
                response = requests.post(
                    f"{self.base_url}/api/v1/auth/register/",
                    json={
                        'username': 'testuser',
                        'email': 'test@example.com',
                        'password': password
                    },
                    timeout=10
                )
                
                if response.status_code == 201:
                    results.append(SecurityTestResult(
                        test_name='Password Policy',
                        status='failed',
                        severity='high',
                        description=f"Weak password '{password}' was accepted",
                        details={'password': password, 'response_code': response.status_code},
                        recommendations=['Implement strong password policy']
                    ))
                    break
            else:
                results.append(SecurityTestResult(
                    test_name='Password Policy',
                    status='passed',
                    severity='low',
                    description='Password policy rejects weak passwords',
                    details={'tested_passwords': weak_passwords},
                    recommendations=[]
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name='Password Policy',
                status='warning',
                severity='medium',
                description=f"Could not test password policy: {str(e)}",
                details={'error': str(e)},
                recommendations=['Verify password policy manually']
            ))
        
        # Test 2: Brute force protection
        try:
            login_attempts = []
            for i in range(10):
                response = requests.post(
                    f"{self.base_url}/api/v1/auth/login/",
                    json={'username': 'admin', 'password': 'wrongpassword'},
                    timeout=5
                )
                login_attempts.append(response.status_code)
                
                if response.status_code == 429:  # Rate limited
                    results.append(SecurityTestResult(
                        test_name='Brute Force Protection',
                        status='passed',
                        severity='low',
                        description='Rate limiting active for failed login attempts',
                        details={'attempts_before_limit': i + 1},
                        recommendations=[]
                    ))
                    break
            else:
                results.append(SecurityTestResult(
                    test_name='Brute Force Protection',
                    status='warning',
                    severity='medium',
                    description='No rate limiting detected for failed login attempts',
                    details={'total_attempts': len(login_attempts)},
                    recommendations=['Implement rate limiting for authentication endpoints']
                ))
        except Exception as e:
            results.append(SecurityTestResult(
                test_name='Brute Force Protection',
                status='warning',
                severity='medium',
                description=f"Could not test brute force protection: {str(e)}",
                details={'error': str(e)},
                recommendations=['Verify brute force protection manually']
            ))
        
        return results
    
    def test_authorization_controls(self) -> SecurityTestResult:
        """Test authorization controls"""
        try:
            # Test accessing protected endpoints without authentication
            protected_endpoints = [
                '/api/v1/users/',
                '/api/v1/blog/posts/',
                '/api/v1/auth/user/',
            ]
            
            unauthorized_access = []
            for endpoint in protected_endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    unauthorized_access.append(endpoint)
            
            if unauthorized_access:
                return SecurityTestResult(
                    test_name='Authorization Controls',
                    status='failed',
                    severity='high',
                    description=f"Unauthorized access to protected endpoints: {unauthorized_access}",
                    details={'vulnerable_endpoints': unauthorized_access},
                    recommendations=['Implement proper authentication checks for all protected endpoints']
                )
            else:
                return SecurityTestResult(
                    test_name='Authorization Controls',
                    status='passed',
                    severity='low',
                    description='Protected endpoints properly require authentication',
                    details={'tested_endpoints': protected_endpoints},
                    recommendations=[]
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='Authorization Controls',
                status='warning',
                severity='medium',
                description=f"Could not test authorization controls: {str(e)}",
                details={'error': str(e)},
                recommendations=['Verify authorization controls manually']
            )
    
    def test_input_validation(self) -> List[SecurityTestResult]:
        """Test input validation"""
        results = []
        
        # Test various malicious inputs
        malicious_inputs = [
            {'type': 'XSS', 'payload': '<script>alert("XSS")</script>'},
            {'type': 'SQL Injection', 'payload': "'; DROP TABLE users; --"},
            {'type': 'Command Injection', 'payload': '; cat /etc/passwd'},
            {'type': 'Path Traversal', 'payload': '../../../etc/passwd'},
            {'type': 'XXE', 'payload': '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY test SYSTEM "file:///etc/passwd">]><root>&test;</root>'},
        ]
        
        for input_test in malicious_inputs:
            try:
                # Test in different contexts
                contexts = [
                    {'endpoint': '/api/v1/auth/login/', 'field': 'username'},
                    {'endpoint': '/api/v1/blog/posts/', 'field': 'title'},
                ]
                
                vulnerable = False
                for context in contexts:
                    data = {context['field']: input_test['payload']}
                    response = requests.post(f"{self.base_url}{context['endpoint']}", 
                                           json=data, timeout=10)
                    
                    # Check if malicious input was reflected or processed
                    if (input_test['payload'] in response.text or 
                        response.status_code == 500):  # Server error might indicate injection
                        vulnerable = True
                        break
                
                if vulnerable:
                    results.append(SecurityTestResult(
                        test_name=f'Input Validation - {input_test["type"]}',
                        status='failed',
                        severity='high',
                        description=f'Potential {input_test["type"]} vulnerability detected',
                        details={'payload': input_test['payload'], 'context': context},
                        recommendations=[f'Implement proper input validation and sanitization for {input_test["type"]}']
                    ))
                else:
                    results.append(SecurityTestResult(
                        test_name=f'Input Validation - {input_test["type"]}',
                        status='passed',
                        severity='low',
                        description=f'No {input_test["type"]} vulnerability detected',
                        details={'payload': input_test['payload']},
                        recommendations=[]
                    ))
                    
            except Exception as e:
                results.append(SecurityTestResult(
                    test_name=f'Input Validation - {input_test["type"]}',
                    status='warning',
                    severity='medium',
                    description=f'Could not test {input_test["type"]}: {str(e)}',
                    details={'error': str(e)},
                    recommendations=[f'Verify {input_test["type"]} protection manually']
                ))
        
        return results
    
    def test_sql_injection(self) -> SecurityTestResult:
        """Test for SQL injection vulnerabilities"""
        try:
            sql_payloads = [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "1' OR '1'='1' --",
            ]
            
            vulnerable_endpoints = []
            
            for payload in sql_payloads:
                # Test in search parameters
                response = requests.get(f"{self.base_url}/api/v1/blog/posts/", 
                                      params={'search': payload}, timeout=10)
                
                # Look for SQL error messages or unexpected behavior
                sql_errors = [
                    'sql syntax',
                    'mysql_fetch',
                    'postgresql',
                    'ora-',
                    'microsoft jet database',
                    'sqlite_',
                ]
                
                response_lower = response.text.lower()
                if any(error in response_lower for error in sql_errors):
                    vulnerable_endpoints.append(f"/api/v1/blog/posts/?search={payload}")
            
            if vulnerable_endpoints:
                return SecurityTestResult(
                    test_name='SQL Injection',
                    status='failed',
                    severity='critical',
                    description='SQL injection vulnerabilities detected',
                    details={'vulnerable_endpoints': vulnerable_endpoints},
                    recommendations=['Use parameterized queries and ORM to prevent SQL injection']
                )
            else:
                return SecurityTestResult(
                    test_name='SQL Injection',
                    status='passed',
                    severity='low',
                    description='No SQL injection vulnerabilities detected',
                    details={'tested_payloads': sql_payloads},
                    recommendations=[]
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='SQL Injection',
                status='warning',
                severity='medium',
                description=f'Could not test SQL injection: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify SQL injection protection manually']
            )
    
    def test_xss_protection(self) -> SecurityTestResult:
        """Test XSS protection"""
        try:
            xss_payloads = [
                '<script>alert("XSS")</script>',
                '<img src="x" onerror="alert(1)">',
                'javascript:alert("XSS")',
                '<svg onload="alert(1)">',
            ]
            
            vulnerable = False
            vulnerable_contexts = []
            
            for payload in xss_payloads:
                # Test in various contexts
                contexts = [
                    {'endpoint': '/api/v1/blog/posts/', 'method': 'POST', 'data': {'title': payload}},
                    {'endpoint': '/api/v1/auth/register/', 'method': 'POST', 'data': {'username': payload}},
                ]
                
                for context in contexts:
                    try:
                        if context['method'] == 'POST':
                            response = requests.post(f"{self.base_url}{context['endpoint']}", 
                                                   json=context['data'], timeout=10)
                        else:
                            response = requests.get(f"{self.base_url}{context['endpoint']}", 
                                                  params=context['data'], timeout=10)
                        
                        # Check if payload is reflected without encoding
                        if payload in response.text and '<script>' in response.text:
                            vulnerable = True
                            vulnerable_contexts.append(context)
                    except:
                        continue
            
            if vulnerable:
                return SecurityTestResult(
                    test_name='XSS Protection',
                    status='failed',
                    severity='high',
                    description='XSS vulnerabilities detected',
                    details={'vulnerable_contexts': vulnerable_contexts},
                    recommendations=['Implement proper output encoding and Content Security Policy']
                )
            else:
                return SecurityTestResult(
                    test_name='XSS Protection',
                    status='passed',
                    severity='low',
                    description='No XSS vulnerabilities detected',
                    details={'tested_payloads': xss_payloads},
                    recommendations=[]
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='XSS Protection',
                status='warning',
                severity='medium',
                description=f'Could not test XSS protection: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify XSS protection manually']
            )
    
    def test_csrf_protection(self) -> SecurityTestResult:
        """Test CSRF protection"""
        try:
            # Test if CSRF token is required for state-changing operations
            response = requests.post(f"{self.base_url}/api/v1/auth/login/", 
                                   json={'username': 'test', 'password': 'test'}, 
                                   timeout=10)
            
            csrf_protected = False
            if 'csrf' in response.text.lower() or response.status_code == 403:
                csrf_protected = True
            
            # Check for CSRF token in forms
            response = requests.get(f"{self.base_url}/", timeout=10)
            has_csrf_token = 'csrf' in response.text.lower()
            
            if csrf_protected or has_csrf_token:
                return SecurityTestResult(
                    test_name='CSRF Protection',
                    status='passed',
                    severity='low',
                    description='CSRF protection appears to be implemented',
                    details={'csrf_protected': csrf_protected, 'has_csrf_token': has_csrf_token},
                    recommendations=[]
                )
            else:
                return SecurityTestResult(
                    test_name='CSRF Protection',
                    status='warning',
                    severity='medium',
                    description='CSRF protection not clearly implemented',
                    details={'csrf_protected': csrf_protected, 'has_csrf_token': has_csrf_token},
                    recommendations=['Implement CSRF protection for all state-changing operations']
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='CSRF Protection',
                status='warning',
                severity='medium',
                description=f'Could not test CSRF protection: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify CSRF protection manually']
            )
    
    def test_rate_limiting(self) -> SecurityTestResult:
        """Test rate limiting"""
        try:
            endpoint = f"{self.base_url}/api/v1/"
            responses = []
            
            # Make rapid requests
            for i in range(20):
                response = requests.get(endpoint, timeout=5)
                responses.append(response.status_code)
                
                if response.status_code == 429:  # Rate limited
                    return SecurityTestResult(
                        test_name='Rate Limiting',
                        status='passed',
                        severity='low',
                        description=f'Rate limiting active after {i + 1} requests',
                        details={'requests_before_limit': i + 1, 'responses': responses},
                        recommendations=[]
                    )
            
            return SecurityTestResult(
                test_name='Rate Limiting',
                status='warning',
                severity='medium',
                description='No rate limiting detected',
                details={'total_requests': len(responses), 'responses': responses},
                recommendations=['Implement rate limiting to prevent abuse']
            )
            
        except Exception as e:
            return SecurityTestResult(
                test_name='Rate Limiting',
                status='warning',
                severity='medium',
                description=f'Could not test rate limiting: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify rate limiting manually']
            )
    
    def test_information_disclosure(self) -> SecurityTestResult:
        """Test for information disclosure"""
        try:
            sensitive_endpoints = [
                '/.env',
                '/admin/',
                '/debug/',
                '/.git/',
                '/config/',
                '/backup/',
                '/phpinfo.php',
                '/server-status',
                '/server-info',
            ]
            
            disclosed_info = []
            
            for endpoint in sensitive_endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    disclosed_info.append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'content_length': len(response.text)
                    })
            
            # Check for debug information in error pages
            response = requests.get(f"{self.base_url}/nonexistent-page", timeout=10)
            debug_info = any(keyword in response.text.lower() for keyword in 
                           ['traceback', 'debug', 'stack trace', 'exception'])
            
            if disclosed_info or debug_info:
                return SecurityTestResult(
                    test_name='Information Disclosure',
                    status='failed',
                    severity='medium',
                    description='Information disclosure detected',
                    details={'disclosed_endpoints': disclosed_info, 'debug_info': debug_info},
                    recommendations=['Remove or protect sensitive endpoints and disable debug mode in production']
                )
            else:
                return SecurityTestResult(
                    test_name='Information Disclosure',
                    status='passed',
                    severity='low',
                    description='No information disclosure detected',
                    details={'tested_endpoints': sensitive_endpoints},
                    recommendations=[]
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='Information Disclosure',
                status='warning',
                severity='medium',
                description=f'Could not test information disclosure: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify information disclosure protection manually']
            )
    
    def test_session_management(self) -> SecurityTestResult:
        """Test session management security"""
        try:
            # Test session cookie security
            response = requests.get(f"{self.base_url}/", timeout=10)
            cookies = response.cookies
            
            session_security = {
                'httponly': False,
                'secure': False,
                'samesite': False,
            }
            
            for cookie in cookies:
                if 'session' in cookie.name.lower():
                    session_security['httponly'] = cookie.has_nonstandard_attr('HttpOnly')
                    session_security['secure'] = cookie.secure
                    session_security['samesite'] = cookie.has_nonstandard_attr('SameSite')
            
            issues = []
            if not session_security['httponly']:
                issues.append('Session cookies should have HttpOnly flag')
            if not session_security['secure']:
                issues.append('Session cookies should have Secure flag (HTTPS)')
            if not session_security['samesite']:
                issues.append('Session cookies should have SameSite attribute')
            
            if issues:
                return SecurityTestResult(
                    test_name='Session Management',
                    status='warning',
                    severity='medium',
                    description='Session security issues detected',
                    details={'session_security': session_security, 'issues': issues},
                    recommendations=issues
                )
            else:
                return SecurityTestResult(
                    test_name='Session Management',
                    status='passed',
                    severity='low',
                    description='Session management appears secure',
                    details={'session_security': session_security},
                    recommendations=[]
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='Session Management',
                status='warning',
                severity='medium',
                description=f'Could not test session management: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify session management manually']
            )
    
    def test_cors_configuration(self) -> SecurityTestResult:
        """Test CORS configuration"""
        try:
            # Test CORS headers
            response = requests.options(f"{self.base_url}/api/v1/", 
                                      headers={'Origin': 'http://evil.com'}, 
                                      timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
            }
            
            issues = []
            if cors_headers['Access-Control-Allow-Origin'] == '*':
                issues.append('CORS allows all origins (*) - too permissive')
            
            if cors_headers['Access-Control-Allow-Credentials'] == 'true' and cors_headers['Access-Control-Allow-Origin'] == '*':
                issues.append('Dangerous CORS configuration: credentials allowed with wildcard origin')
            
            if issues:
                return SecurityTestResult(
                    test_name='CORS Configuration',
                    status='warning',
                    severity='medium',
                    description='CORS configuration issues detected',
                    details={'cors_headers': cors_headers, 'issues': issues},
                    recommendations=['Configure CORS with specific allowed origins']
                )
            else:
                return SecurityTestResult(
                    test_name='CORS Configuration',
                    status='passed',
                    severity='low',
                    description='CORS configuration appears secure',
                    details={'cors_headers': cors_headers},
                    recommendations=[]
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='CORS Configuration',
                status='warning',
                severity='medium',
                description=f'Could not test CORS configuration: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify CORS configuration manually']
            )
    
    def test_file_upload_security(self) -> SecurityTestResult:
        """Test file upload security"""
        # This is a placeholder - actual implementation would depend on file upload endpoints
        return SecurityTestResult(
            test_name='File Upload Security',
            status='warning',
            severity='low',
            description='File upload security not tested - no upload endpoints identified',
            details={},
            recommendations=['If file uploads are implemented, ensure proper validation and security measures']
        )
    
    def test_api_security(self) -> SecurityTestResult:
        """Test API-specific security measures"""
        try:
            # Test API versioning
            response = requests.get(f"{self.base_url}/api/", timeout=10)
            has_versioning = 'v1' in response.text or response.status_code == 404
            
            # Test API documentation exposure
            doc_endpoints = ['/api/docs/', '/api/swagger/', '/api/redoc/']
            exposed_docs = []
            
            for endpoint in doc_endpoints:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    exposed_docs.append(endpoint)
            
            issues = []
            if not has_versioning:
                issues.append('API versioning not implemented')
            
            if exposed_docs:
                issues.append(f'API documentation exposed: {exposed_docs}')
            
            if issues:
                return SecurityTestResult(
                    test_name='API Security',
                    status='warning',
                    severity='low',
                    description='API security issues detected',
                    details={'has_versioning': has_versioning, 'exposed_docs': exposed_docs},
                    recommendations=['Implement API versioning and protect documentation in production']
                )
            else:
                return SecurityTestResult(
                    test_name='API Security',
                    status='passed',
                    severity='low',
                    description='API security measures appear adequate',
                    details={'has_versioning': has_versioning, 'exposed_docs': exposed_docs},
                    recommendations=[]
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='API Security',
                status='warning',
                severity='medium',
                description=f'Could not test API security: {str(e)}',
                details={'error': str(e)},
                recommendations=['Verify API security manually']
            )
    
    def test_dependency_vulnerabilities(self) -> SecurityTestResult:
        """Test for known dependency vulnerabilities"""
        try:
            # Check if safety is available for Python dependencies
            result = subprocess.run(['safety', 'check', '--json'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout) if result.stdout else []
                
                if vulnerabilities:
                    return SecurityTestResult(
                        test_name='Dependency Vulnerabilities',
                        status='failed',
                        severity='high',
                        description=f'{len(vulnerabilities)} dependency vulnerabilities found',
                        details={'vulnerabilities': vulnerabilities},
                        recommendations=['Update vulnerable dependencies immediately']
                    )
                else:
                    return SecurityTestResult(
                        test_name='Dependency Vulnerabilities',
                        status='passed',
                        severity='low',
                        description='No known dependency vulnerabilities found',
                        details={},
                        recommendations=[]
                    )
            else:
                return SecurityTestResult(
                    test_name='Dependency Vulnerabilities',
                    status='warning',
                    severity='medium',
                    description='Could not check dependency vulnerabilities - safety tool not available',
                    details={'error': result.stderr},
                    recommendations=['Install and run safety tool to check for dependency vulnerabilities']
                )
                
        except Exception as e:
            return SecurityTestResult(
                test_name='Dependency Vulnerabilities',
                status='warning',
                severity='medium',
                description=f'Could not test dependency vulnerabilities: {str(e)}',
                details={'error': str(e)},
                recommendations=['Install safety tool and check dependencies manually']
            )
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        # Categorize results by severity
        critical = [r for r in self.results if r.severity == 'critical']
        high = [r for r in self.results if r.severity == 'high']
        medium = [r for r in self.results if r.severity == 'medium']
        low = [r for r in self.results if r.severity == 'low']
        
        # Calculate security score
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'passed'])
        failed_tests = len([r for r in self.results if r.status == 'failed'])
        warning_tests = len([r for r in self.results if r.status == 'warning'])
        
        # Security score calculation (weighted by severity)
        score = 100
        score -= len(critical) * 25
        score -= len(high) * 15
        score -= len(medium) * 10
        score -= len(low) * 5
        score = max(0, score)
        
        # Security grade
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        # Collect all recommendations
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates while preserving order
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'warning_tests': warning_tests,
                'security_score': score,
                'security_grade': grade,
                'critical_issues': len(critical),
                'high_issues': len(high),
                'medium_issues': len(medium),
                'low_issues': len(low),
            },
            'results_by_severity': {
                'critical': [self._result_to_dict(r) for r in critical],
                'high': [self._result_to_dict(r) for r in high],
                'medium': [self._result_to_dict(r) for r in medium],
                'low': [self._result_to_dict(r) for r in low],
            },
            'all_results': [self._result_to_dict(r) for r in self.results],
            'recommendations': unique_recommendations,
            'next_steps': self._generate_next_steps(critical, high, medium)
        }
        
        return report
    
    def _result_to_dict(self, result: SecurityTestResult) -> Dict[str, Any]:
        """Convert SecurityTestResult to dictionary"""
        return {
            'test_name': result.test_name,
            'status': result.status,
            'severity': result.severity,
            'description': result.description,
            'details': result.details,
            'recommendations': result.recommendations
        }
    
    def _generate_next_steps(self, critical: List, high: List, medium: List) -> List[str]:
        """Generate next steps based on findings"""
        next_steps = []
        
        if critical:
            next_steps.append("🚨 IMMEDIATE ACTION REQUIRED: Address all critical security issues before deployment")
        
        if high:
            next_steps.append("⚠️ HIGH PRIORITY: Fix high-severity security issues within 24 hours")
        
        if medium:
            next_steps.append("📋 MEDIUM PRIORITY: Address medium-severity issues in next sprint")
        
        if not critical and not high and not medium:
            next_steps.append("✅ Security posture looks good! Continue monitoring and regular security testing")
        
        next_steps.extend([
            "🔄 Schedule regular security testing",
            "📚 Review and update security policies",
            "🎓 Provide security training to development team",
            "🔍 Consider professional penetration testing"
        ])
        
        return next_steps


def main():
    """Main function to run security testing"""
    print("🔒 Starting Security Testing Suite...")
    
    suite = SecurityTestSuite()
    results = suite.run_all_security_tests()
    report = suite.generate_security_report()
    
    # Save report
    os.makedirs('tests/security', exist_ok=True)
    with open('tests/security/security_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("SECURITY TEST REPORT")
    print("="*80)
    print(f"Security Grade: {report['summary']['security_grade']}")
    print(f"Security Score: {report['summary']['security_score']}/100")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Warnings: {report['summary']['warning_tests']}")
    
    print(f"\nIssues by Severity:")
    print(f"Critical: {report['summary']['critical_issues']}")
    print(f"High: {report['summary']['high_issues']}")
    print(f"Medium: {report['summary']['medium_issues']}")
    print(f"Low: {report['summary']['low_issues']}")
    
    if report['next_steps']:
        print("\nNEXT STEPS:")
        for step in report['next_steps']:
            print(f"  {step}")
    
    print(f"\nDetailed report saved to: tests/security/security_report.json")


if __name__ == "__main__":
    main()
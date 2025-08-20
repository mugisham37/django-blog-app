"""
Security headers and HTTPS enforcement for Django Personal Blog System.
Implements comprehensive security headers, CSP, and HTTPS enforcement.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

from .security_monitoring import log_security_event

logger = logging.getLogger('security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Comprehensive security headers middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.config = getattr(settings, 'SECURITY_MONITORING', {})
        self.csp_config = self._get_csp_config()
        self.permissions_policy = getattr(settings, 'PERMISSIONS_POLICY', {})
        super().__init__(get_response)
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add comprehensive security headers to response."""
        
        # Core security headers
        self._add_core_security_headers(response)
        
        # Content Security Policy
        self._add_csp_headers(request, response)
        
        # Permissions Policy (Feature Policy)
        self._add_permissions_policy(response)
        
        # HTTPS enforcement headers
        self._add_https_headers(request, response)
        
        # Additional security headers
        self._add_additional_headers(response)
        
        return response
    
    def _add_core_security_headers(self, response: HttpResponse) -> None:
        """Add core security headers."""
        
        headers = {
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # XSS protection (legacy but still useful)
            'X-XSS-Protection': '1; mode=block',
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Cross-origin policies
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
            
            # Prevent DNS prefetching
            'X-DNS-Prefetch-Control': 'off',
            
            # Disable FLoC tracking
            'Permissions-Policy': 'interest-cohort=()',
        }
        
        # Add headers if not already present
        for header, value in headers.items():
            if header not in response:
                response[header] = value
    
    def _add_csp_headers(self, request: HttpRequest, response: HttpResponse) -> None:
        """Add Content Security Policy headers."""
        
        # Build CSP directive
        csp_directives = []
        
        for directive, sources in self.csp_config.items():
            if sources:
                if isinstance(sources, list):
                    sources_str = ' '.join(sources)
                else:
                    sources_str = str(sources)
                csp_directives.append(f"{directive} {sources_str}")
        
        if csp_directives:
            csp_header = '; '.join(csp_directives)
            response['Content-Security-Policy'] = csp_header
            
            # Add report-only header for testing if configured
            if self.config.get('CSP_REPORT_ONLY', False):
                response['Content-Security-Policy-Report-Only'] = csp_header
        
        # Add CSP reporting endpoint
        if self.config.get('ENABLE_CSP_REPORTING', False):
            report_uri = self.config.get('CSP_REPORT_URI', '/security/csp-report/')
            if 'report-uri' not in csp_header:
                response['Content-Security-Policy'] += f'; report-uri {report_uri}'
    
    def _add_permissions_policy(self, response: HttpResponse) -> None:
        """Add Permissions Policy (Feature Policy) headers."""
        
        if not self.permissions_policy:
            return
        
        policy_directives = []
        
        for feature, allowlist in self.permissions_policy.items():
            if isinstance(allowlist, list):
                if not allowlist:
                    # Empty list means deny all
                    policy_directives.append(f"{feature}=()")
                else:
                    # Specific origins allowed
                    origins = ' '.join(f'"{origin}"' if origin != 'self' else origin for origin in allowlist)
                    policy_directives.append(f"{feature}=({origins})")
            elif allowlist == 'self':
                policy_directives.append(f"{feature}=(self)")
            elif allowlist == '*':
                policy_directives.append(f"{feature}=*")
            else:
                policy_directives.append(f"{feature}=()")
        
        if policy_directives:
            response['Permissions-Policy'] = ', '.join(policy_directives)
    
    def _add_https_headers(self, request: HttpRequest, response: HttpResponse) -> None:
        """Add HTTPS enforcement headers."""
        
        # Only add HTTPS headers if SSL is enabled
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            return
        
        # HTTP Strict Transport Security (HSTS)
        hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)  # 1 year
        hsts_value = f'max-age={hsts_seconds}'
        
        if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False):
            hsts_value += '; includeSubDomains'
        
        if getattr(settings, 'SECURE_HSTS_PRELOAD', False):
            hsts_value += '; preload'
        
        response['Strict-Transport-Security'] = hsts_value
        
        # Expect-CT header for certificate transparency
        if getattr(settings, 'SECURE_EXPECT_CT', False):
            ct_max_age = getattr(settings, 'SECURE_EXPECT_CT_MAX_AGE', 86400)
            ct_value = f'max-age={ct_max_age}'
            
            if getattr(settings, 'SECURE_EXPECT_CT_ENFORCE', False):
                ct_value += ', enforce'
            
            report_uri = getattr(settings, 'SECURE_EXPECT_CT_REPORT_URI', '')
            if report_uri:
                ct_value += f', report-uri="{report_uri}"'
            
            response['Expect-CT'] = ct_value
    
    def _add_additional_headers(self, response: HttpResponse) -> None:
        """Add additional security headers."""
        
        # Server header removal/modification
        if 'Server' in response:
            response['Server'] = 'WebServer'  # Generic server name
        
        # Cache control for sensitive pages
        if hasattr(response, 'url') and any(path in str(response.url) for path in ['/admin/', '/api/auth/']):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Add security headers for API responses
        if response.get('Content-Type', '').startswith('application/json'):
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
    
    def _get_csp_config(self) -> Dict[str, List[str]]:
        """Get Content Security Policy configuration."""
        
        # Default CSP configuration
        default_csp = {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Remove in production, use nonces instead
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Remove in production, use nonces instead
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:",
                "blob:"
            ],
            'font-src': [
                "'self'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'connect-src': [
                "'self'",
                "wss:",
                "https:"
            ],
            'media-src': ["'self'"],
            'object-src': ["'none'"],
            'child-src': ["'none'"],
            'worker-src': ["'self'"],
            'frame-ancestors': ["'none'"],
            'form-action': ["'self'"],
            'base-uri': ["'self'"],
            'manifest-src': ["'self'"]
        }
        
        # Merge with settings configuration
        csp_config = getattr(settings, 'CSP_CONFIG', {})
        
        # Use settings values or defaults
        final_csp = {}
        for directive in default_csp:
            setting_name = f'CSP_{directive.upper().replace("-", "_")}'
            final_csp[directive] = getattr(settings, setting_name, default_csp[directive])
        
        # Add upgrade-insecure-requests if HTTPS is enabled
        if getattr(settings, 'CSP_UPGRADE_INSECURE_REQUESTS', False):
            final_csp['upgrade-insecure-requests'] = []
        
        # Add block-all-mixed-content if configured
        if getattr(settings, 'CSP_BLOCK_ALL_MIXED_CONTENT', False):
            final_csp['block-all-mixed-content'] = []
        
        return final_csp


class HTTPSRedirectMiddleware(MiddlewareMixin):
    """
    Enhanced HTTPS redirect middleware with security features.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        self.exempt_paths = getattr(settings, 'SECURE_SSL_REDIRECT_EXEMPT', [])
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Redirect HTTP requests to HTTPS if enabled."""
        
        if not self.enabled:
            return None
        
        # Check if request is already secure
        if request.is_secure():
            return None
        
        # Check exempt paths
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return None
        
        # Check for health checks and monitoring
        if request.path in ['/health/', '/metrics/', '/status/']:
            return None
        
        # Log insecure request attempt
        log_security_event(
            'insecure_request',
            f'Insecure HTTP request to {request.path}',
            getattr(request, 'client_ip', ''),
            metadata={'path': request.path, 'method': request.method}
        )
        
        # Build secure URL
        secure_url = self._build_secure_url(request)
        
        # Return permanent redirect
        from django.http import HttpResponsePermanentRedirect
        return HttpResponsePermanentRedirect(secure_url)
    
    def _build_secure_url(self, request: HttpRequest) -> str:
        """Build secure HTTPS URL from request."""
        
        host = request.get_host()
        path = request.get_full_path()
        
        # Handle port mapping if needed
        secure_port = getattr(settings, 'SECURE_SSL_PORT', 443)
        if secure_port != 443:
            if ':' in host:
                host = host.split(':')[0]
            host = f"{host}:{secure_port}"
        
        return f"https://{host}{path}"


class CSPReportingMiddleware(MiddlewareMixin):
    """
    Middleware for handling CSP violation reports.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'SECURITY_MONITORING', {}).get('ENABLE_CSP_REPORTING', False)
        self.report_uri = getattr(settings, 'SECURITY_MONITORING', {}).get('CSP_REPORT_URI', '/security/csp-report/')
        super().__init__(get_response)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Handle CSP violation reports."""
        
        if not self.enabled or request.path != self.report_uri:
            return None
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            # Parse CSP report
            report_data = json.loads(request.body.decode('utf-8'))
            csp_report = report_data.get('csp-report', {})
            
            # Log CSP violation
            self._log_csp_violation(request, csp_report)
            
            # Return success response
            return JsonResponse({'status': 'received'}, status=200)
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Invalid CSP report received: {e}")
            return JsonResponse({'error': 'Invalid report'}, status=400)
        
        except Exception as e:
            logger.error(f"Error processing CSP report: {e}")
            return JsonResponse({'error': 'Processing error'}, status=500)
    
    def _log_csp_violation(self, request: HttpRequest, csp_report: Dict[str, Any]) -> None:
        """Log CSP violation for security monitoring."""
        
        violation_details = {
            'blocked_uri': csp_report.get('blocked-uri', ''),
            'document_uri': csp_report.get('document-uri', ''),
            'violated_directive': csp_report.get('violated-directive', ''),
            'original_policy': csp_report.get('original-policy', ''),
            'source_file': csp_report.get('source-file', ''),
            'line_number': csp_report.get('line-number', ''),
            'column_number': csp_report.get('column-number', ''),
        }
        
        # Log security event
        log_security_event(
            'csp_violation',
            f'CSP violation: {violation_details["violated_directive"]} blocked {violation_details["blocked_uri"]}',
            getattr(request, 'client_ip', ''),
            metadata=violation_details
        )
        
        # Check for potential XSS attempts
        blocked_uri = violation_details['blocked_uri']
        if any(pattern in blocked_uri.lower() for pattern in ['javascript:', 'data:', 'vbscript:']):
            log_security_event(
                'potential_xss',
                f'Potential XSS attempt blocked by CSP: {blocked_uri}',
                getattr(request, 'client_ip', ''),
                metadata=violation_details
            )


class SecurityHeadersValidator:
    """
    Validator for security headers configuration.
    """
    
    @staticmethod
    def validate_csp_config(csp_config: Dict[str, List[str]]) -> List[str]:
        """Validate CSP configuration and return warnings."""
        
        warnings = []
        
        # Check for unsafe directives
        unsafe_keywords = ["'unsafe-inline'", "'unsafe-eval'"]
        
        for directive, sources in csp_config.items():
            if isinstance(sources, list):
                for source in sources:
                    if source in unsafe_keywords:
                        warnings.append(f"Unsafe CSP source '{source}' in {directive}")
        
        # Check for missing important directives
        important_directives = ['default-src', 'script-src', 'object-src', 'base-uri']
        for directive in important_directives:
            if directive not in csp_config:
                warnings.append(f"Missing important CSP directive: {directive}")
        
        # Check for overly permissive directives
        if csp_config.get('script-src', []) == ['*']:
            warnings.append("script-src allows all sources (*) - very dangerous")
        
        if "'unsafe-eval'" in csp_config.get('script-src', []):
            warnings.append("script-src allows 'unsafe-eval' - potential XSS risk")
        
        return warnings
    
    @staticmethod
    def validate_hsts_config() -> List[str]:
        """Validate HSTS configuration."""
        
        warnings = []
        
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            warnings.append("HTTPS redirect is disabled")
        
        hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
        if hsts_seconds < 31536000:  # 1 year
            warnings.append(f"HSTS max-age is too short: {hsts_seconds} seconds")
        
        if not getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False):
            warnings.append("HSTS includeSubDomains is disabled")
        
        return warnings
    
    @staticmethod
    def get_security_score() -> Dict[str, Any]:
        """Calculate security configuration score."""
        
        score = 100
        issues = []
        
        # Check CSP configuration
        csp_config = SecurityHeadersMiddleware(None)._get_csp_config()
        csp_warnings = SecurityHeadersValidator.validate_csp_config(csp_config)
        score -= len(csp_warnings) * 5
        issues.extend(csp_warnings)
        
        # Check HSTS configuration
        hsts_warnings = SecurityHeadersValidator.validate_hsts_config()
        score -= len(hsts_warnings) * 10
        issues.extend(hsts_warnings)
        
        # Check other security settings
        if settings.DEBUG:
            score -= 20
            issues.append("DEBUG mode is enabled")
        
        if not getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False):
            score -= 5
            issues.append("XSS filter is disabled")
        
        if not getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False):
            score -= 5
            issues.append("Content type nosniff is disabled")
        
        return {
            'score': max(0, score),
            'grade': SecurityHeadersValidator._get_grade(score),
            'issues': issues,
            'recommendations': SecurityHeadersValidator._get_recommendations(issues)
        }
    
    @staticmethod
    def _get_grade(score: int) -> str:
        """Get letter grade based on score."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    @staticmethod
    def _get_recommendations(issues: List[str]) -> List[str]:
        """Get security recommendations based on issues."""
        
        recommendations = []
        
        if any('unsafe' in issue.lower() for issue in issues):
            recommendations.append("Remove unsafe CSP directives and use nonces or hashes instead")
        
        if any('hsts' in issue.lower() for issue in issues):
            recommendations.append("Configure HSTS with at least 1 year max-age and includeSubDomains")
        
        if any('debug' in issue.lower() for issue in issues):
            recommendations.append("Disable DEBUG mode in production")
        
        if not recommendations:
            recommendations.append("Security configuration looks good!")
        
        return recommendations


# Utility functions

def get_security_headers_status() -> Dict[str, Any]:
    """Get current security headers configuration status."""
    return SecurityHeadersValidator.get_security_score()


def validate_csp_policy(policy: str) -> List[str]:
    """Validate a CSP policy string."""
    
    # Parse policy into directives
    directives = {}
    for directive in policy.split(';'):
        directive = directive.strip()
        if directive:
            parts = directive.split(' ', 1)
            if len(parts) == 2:
                name, sources = parts
                directives[name] = sources.split()
    
    return SecurityHeadersValidator.validate_csp_config(directives)
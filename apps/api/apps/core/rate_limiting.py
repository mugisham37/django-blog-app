"""
Advanced rate limiting and DDoS protection for Django Personal Blog System.
Implements comprehensive rate limiting with multiple strategies and DDoS mitigation.
"""

import time
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .security_monitoring import security_monitor

User = get_user_model()
logger = logging.getLogger('security')


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    name: str
    limit: int
    window: int  # seconds
    scope: str  # 'ip', 'user', 'endpoint', 'global'
    burst_limit: Optional[int] = None
    burst_window: Optional[int] = None


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies and DDoS protection.
    """
    
    def __init__(self):
        self.global_limits = getattr(settings, 'GLOBAL_RATE_LIMITS', {})
        self.endpoint_limits = getattr(settings, 'ENDPOINT_RATE_LIMITS', {})
        self.ddos_thresholds = {
            'requests_per_second': 100,
            'unique_ips_threshold': 50,
            'suspicious_pattern_threshold': 10,
        }
        
        # Default rate limit rules
        self.default_rules = [
            RateLimitRule('anonymous_global', 100, 60, 'ip'),
            RateLimitRule('authenticated_global', 300, 60, 'user'),
            RateLimitRule('api_anonymous', 50, 60, 'ip'),
            RateLimitRule('api_authenticated', 200, 60, 'user'),
        ]
    
    def check_rate_limit(self, request: HttpRequest, endpoint: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited.
        
        Args:
            request: HTTP request object
            endpoint: Specific endpoint identifier
            
        Returns:
            Tuple of (is_limited, limit_info)
        """
        
        client_ip = getattr(request, 'client_ip', self._get_client_ip(request))
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Check DDoS patterns first
        ddos_detected = self._check_ddos_patterns(request, client_ip)
        if ddos_detected:
            return True, {
                'reason': 'DDoS protection triggered',
                'retry_after': 300,  # 5 minutes
                'limit_type': 'ddos_protection'
            }
        
        # Check endpoint-specific limits
        if endpoint and endpoint in self.endpoint_limits:
            endpoint_config = self.endpoint_limits[endpoint]
            is_limited, info = self._check_endpoint_limit(
                client_ip, user_id, endpoint, endpoint_config
            )
            if is_limited:
                return True, info
        
        # Check global limits
        for rule in self._get_applicable_rules(request):
            is_limited, info = self._check_rule_limit(request, rule, client_ip, user_id)
            if is_limited:
                return True, info
        
        # Check burst limits
        burst_limited, burst_info = self._check_burst_limits(client_ip, user_id)
        if burst_limited:
            return True, burst_info
        
        return False, {}
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _check_ddos_patterns(self, request: HttpRequest, client_ip: str) -> bool:
        """Check for DDoS attack patterns."""
        
        current_time = time.time()
        
        # Pattern 1: High request rate from single IP
        ip_requests_key = f"ddos_ip_requests:{client_ip}"
        ip_requests = cache.get(ip_requests_key, [])
        
        # Clean old requests (last 10 seconds)
        ip_requests = [req_time for req_time in ip_requests if current_time - req_time < 10]
        ip_requests.append(current_time)
        cache.set(ip_requests_key, ip_requests, 60)
        
        if len(ip_requests) > self.ddos_thresholds['requests_per_second']:
            logger.warning(f"DDoS pattern detected: High request rate from IP {client_ip}")
            security_monitor.monitor_rate_limit_violations(client_ip, 'ddos_high_rate')
            return True
        
        # Pattern 2: Distributed attack (many IPs)
        global_requests_key = "ddos_global_requests"
        global_requests = cache.get(global_requests_key, {})
        
        # Clean old requests
        cutoff_time = current_time - 60  # Last minute
        global_requests = {
            ip: req_times for ip, req_times in global_requests.items()
            if any(req_time > cutoff_time for req_time in req_times)
        }
        
        # Add current request
        if client_ip not in global_requests:
            global_requests[client_ip] = []
        global_requests[client_ip] = [
            req_time for req_time in global_requests[client_ip] 
            if req_time > cutoff_time
        ]
        global_requests[client_ip].append(current_time)
        
        cache.set(global_requests_key, global_requests, 300)
        
        # Check if too many unique IPs are making requests
        active_ips = len([ip for ip, times in global_requests.items() if len(times) > 5])
        total_requests = sum(len(times) for times in global_requests.values())
        
        if (active_ips > self.ddos_thresholds['unique_ips_threshold'] and 
            total_requests > 1000):
            logger.warning(f"DDoS pattern detected: Distributed attack with {active_ips} IPs")
            return True
        
        # Pattern 3: Suspicious request patterns
        pattern_key = f"ddos_patterns:{client_ip}"
        patterns = cache.get(pattern_key, {})
        
        # Check for suspicious patterns in request
        suspicious_indicators = self._detect_suspicious_patterns(request)
        
        for indicator in suspicious_indicators:
            patterns[indicator] = patterns.get(indicator, 0) + 1
        
        cache.set(pattern_key, patterns, 300)
        
        # If multiple suspicious patterns detected
        total_suspicious = sum(patterns.values())
        if total_suspicious > self.ddos_thresholds['suspicious_pattern_threshold']:
            logger.warning(f"DDoS pattern detected: Suspicious patterns from IP {client_ip}")
            return True
        
        return False
    
    def _detect_suspicious_patterns(self, request: HttpRequest) -> List[str]:
        """Detect suspicious patterns in request."""
        
        patterns = []
        
        # Check User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or len(user_agent) < 10:
            patterns.append('missing_user_agent')
        elif 'bot' in user_agent.lower() and 'googlebot' not in user_agent.lower():
            patterns.append('suspicious_bot')
        
        # Check for automation tools
        automation_indicators = ['curl', 'wget', 'python-requests', 'scrapy', 'selenium']
        if any(indicator in user_agent.lower() for indicator in automation_indicators):
            patterns.append('automation_tool')
        
        # Check request headers
        if not request.META.get('HTTP_ACCEPT'):
            patterns.append('missing_accept_header')
        
        if not request.META.get('HTTP_ACCEPT_LANGUAGE'):
            patterns.append('missing_language_header')
        
        # Check for unusual request patterns
        if request.method == 'POST' and not request.META.get('HTTP_REFERER'):
            patterns.append('post_without_referer')
        
        # Check query parameters
        query_params = len(request.GET)
        if query_params > 20:
            patterns.append('excessive_parameters')
        
        return patterns
    
    def _check_endpoint_limit(self, client_ip: str, user_id: Optional[int], 
                            endpoint: str, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Check endpoint-specific rate limits."""
        
        limit = config['limit']
        window = config['window']
        
        # Create key based on user or IP
        if user_id:
            key = f"endpoint_limit:user:{user_id}:{endpoint}"
        else:
            key = f"endpoint_limit:ip:{client_ip}:{endpoint}"
        
        current_requests = cache.get(key, 0)
        
        if current_requests >= limit:
            security_monitor.monitor_rate_limit_violations(client_ip, endpoint)
            return True, {
                'reason': f'Endpoint rate limit exceeded for {endpoint}',
                'retry_after': window,
                'limit': limit,
                'window': window,
                'current': current_requests,
                'limit_type': 'endpoint'
            }
        
        # Increment counter
        cache.set(key, current_requests + 1, window)
        return False, {}
    
    def _get_applicable_rules(self, request: HttpRequest) -> List[RateLimitRule]:
        """Get applicable rate limit rules for request."""
        
        rules = []
        
        # Determine request context
        is_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        is_api_request = request.path.startswith('/api/')
        
        # Add appropriate rules
        if is_api_request:
            if is_authenticated:
                rules.append(RateLimitRule('api_authenticated', 200, 60, 'user'))
            else:
                rules.append(RateLimitRule('api_anonymous', 50, 60, 'ip'))
        else:
            if is_authenticated:
                rules.append(RateLimitRule('web_authenticated', 300, 60, 'user'))
            else:
                rules.append(RateLimitRule('web_anonymous', 100, 60, 'ip'))
        
        return rules
    
    def _check_rule_limit(self, request: HttpRequest, rule: RateLimitRule, 
                         client_ip: str, user_id: Optional[int]) -> Tuple[bool, Dict[str, Any]]:
        """Check a specific rate limit rule."""
        
        # Create key based on rule scope
        if rule.scope == 'user' and user_id:
            key = f"rate_limit:user:{user_id}:{rule.name}"
        elif rule.scope == 'ip':
            key = f"rate_limit:ip:{client_ip}:{rule.name}"
        elif rule.scope == 'endpoint':
            endpoint = self._get_endpoint_identifier(request)
            key = f"rate_limit:endpoint:{endpoint}:{rule.name}"
        elif rule.scope == 'global':
            key = f"rate_limit:global:{rule.name}"
        else:
            return False, {}
        
        current_requests = cache.get(key, 0)
        
        if current_requests >= rule.limit:
            return True, {
                'reason': f'Rate limit exceeded for {rule.name}',
                'retry_after': rule.window,
                'limit': rule.limit,
                'window': rule.window,
                'current': current_requests,
                'limit_type': rule.scope
            }
        
        # Increment counter
        cache.set(key, current_requests + 1, rule.window)
        return False, {}
    
    def _check_burst_limits(self, client_ip: str, user_id: Optional[int]) -> Tuple[bool, Dict[str, Any]]:
        """Check burst rate limits (short-term high frequency)."""
        
        # Check IP burst limit (10 requests per 10 seconds)
        burst_key = f"burst_limit:ip:{client_ip}"
        burst_requests = cache.get(burst_key, 0)
        
        if burst_requests >= 10:
            return True, {
                'reason': 'Burst rate limit exceeded',
                'retry_after': 10,
                'limit': 10,
                'window': 10,
                'current': burst_requests,
                'limit_type': 'burst'
            }
        
        cache.set(burst_key, burst_requests + 1, 10)
        
        # Check user burst limit if authenticated
        if user_id:
            user_burst_key = f"burst_limit:user:{user_id}"
            user_burst_requests = cache.get(user_burst_key, 0)
            
            if user_burst_requests >= 20:  # Higher limit for authenticated users
                return True, {
                    'reason': 'User burst rate limit exceeded',
                    'retry_after': 10,
                    'limit': 20,
                    'window': 10,
                    'current': user_burst_requests,
                    'limit_type': 'user_burst'
                }
            
            cache.set(user_burst_key, user_burst_requests + 1, 10)
        
        return False, {}
    
    def _get_endpoint_identifier(self, request: HttpRequest) -> str:
        """Get endpoint identifier for rate limiting."""
        
        path = request.path
        method = request.method
        
        # Normalize path (remove IDs and dynamic parts)
        normalized_path = path
        
        # Replace numeric IDs with placeholder
        import re
        normalized_path = re.sub(r'/\d+/', '/[id]/', normalized_path)
        normalized_path = re.sub(r'/\d+$', '/[id]', normalized_path)
        
        return f"{method}:{normalized_path}"
    
    def get_rate_limit_status(self, request: HttpRequest) -> Dict[str, Any]:
        """Get current rate limit status for request."""
        
        client_ip = getattr(request, 'client_ip', self._get_client_ip(request))
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        
        status = {
            'ip': client_ip,
            'user_id': user_id,
            'limits': {},
            'remaining': {},
            'reset_times': {}
        }
        
        # Check all applicable rules
        for rule in self._get_applicable_rules(request):
            if rule.scope == 'user' and user_id:
                key = f"rate_limit:user:{user_id}:{rule.name}"
            elif rule.scope == 'ip':
                key = f"rate_limit:ip:{client_ip}:{rule.name}"
            else:
                continue
            
            current_requests = cache.get(key, 0)
            remaining = max(0, rule.limit - current_requests)
            
            status['limits'][rule.name] = rule.limit
            status['remaining'][rule.name] = remaining
            status['reset_times'][rule.name] = time.time() + rule.window
        
        return status


class RateLimitMiddleware:
    """
    Middleware for applying rate limiting to requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimiter()
        self.enabled = getattr(settings, 'RATELIMIT_ENABLE', True)
    
    def __call__(self, request):
        if self.enabled:
            # Check rate limits
            endpoint = self._get_endpoint_from_request(request)
            is_limited, limit_info = self.rate_limiter.check_rate_limit(request, endpoint)
            
            if is_limited:
                return self._create_rate_limit_response(limit_info)
        
        response = self.get_response(request)
        
        # Add rate limit headers
        if self.enabled:
            self._add_rate_limit_headers(request, response)
        
        return response
    
    def _get_endpoint_from_request(self, request) -> str:
        """Extract endpoint identifier from request."""
        
        # Map common endpoints
        endpoint_mapping = {
            '/api/auth/login/': 'login',
            '/api/auth/register/': 'register',
            '/api/auth/password-reset/': 'password_reset',
            '/api/blog/posts/': 'blog_posts',
            '/api/comments/': 'comments',
            '/api/search/': 'search',
        }
        
        # Check exact matches first
        if request.path in endpoint_mapping:
            return endpoint_mapping[request.path]
        
        # Check pattern matches
        for pattern, endpoint in endpoint_mapping.items():
            if request.path.startswith(pattern.rstrip('/')):
                return endpoint
        
        # Default endpoint based on path
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2:
            return f"{path_parts[0]}_{path_parts[1]}"
        
        return 'default'
    
    def _create_rate_limit_response(self, limit_info: Dict[str, Any]) -> JsonResponse:
        """Create rate limit exceeded response."""
        
        response_data = {
            'error': 'Rate limit exceeded',
            'message': limit_info.get('reason', 'Too many requests'),
            'retry_after': limit_info.get('retry_after', 60),
            'limit_type': limit_info.get('limit_type', 'unknown')
        }
        
        response = JsonResponse(response_data, status=429)
        
        # Add standard rate limit headers
        response['Retry-After'] = str(limit_info.get('retry_after', 60))
        response['X-RateLimit-Limit'] = str(limit_info.get('limit', 'unknown'))
        response['X-RateLimit-Remaining'] = '0'
        response['X-RateLimit-Reset'] = str(int(time.time() + limit_info.get('retry_after', 60)))
        
        return response
    
    def _add_rate_limit_headers(self, request, response):
        """Add rate limit headers to response."""
        
        try:
            status = self.rate_limiter.get_rate_limit_status(request)
            
            # Add headers for the most restrictive limit
            if status['remaining']:
                min_remaining = min(status['remaining'].values())
                response['X-RateLimit-Remaining'] = str(min_remaining)
            
            if status['limits']:
                # Use the limit for the most restrictive rule
                min_limit_rule = min(status['limits'].items(), key=lambda x: status['remaining'].get(x[0], 0))
                response['X-RateLimit-Limit'] = str(min_limit_rule[1])
                
                if min_limit_rule[0] in status['reset_times']:
                    response['X-RateLimit-Reset'] = str(int(status['reset_times'][min_limit_rule[0]]))
        
        except Exception as e:
            logger.debug(f"Failed to add rate limit headers: {e}")


# Global rate limiter instance
rate_limiter = RateLimiter()


# Utility functions

def check_rate_limit(request: HttpRequest, endpoint: str = None) -> Tuple[bool, Dict[str, Any]]:
    """Check if request should be rate limited."""
    return rate_limiter.check_rate_limit(request, endpoint)


def get_rate_limit_status(request: HttpRequest) -> Dict[str, Any]:
    """Get current rate limit status."""
    return rate_limiter.get_rate_limit_status(request)


def is_ddos_attack_detected() -> bool:
    """Check if DDoS attack is currently detected."""
    
    # Check global DDoS indicators
    global_requests = cache.get("ddos_global_requests", {})
    current_time = time.time()
    
    # Count active IPs in last minute
    active_ips = 0
    total_requests = 0
    
    for ip, req_times in global_requests.items():
        recent_requests = [t for t in req_times if current_time - t < 60]
        if len(recent_requests) > 5:
            active_ips += 1
            total_requests += len(recent_requests)
    
    # DDoS detected if many IPs are making many requests
    return active_ips > 30 and total_requests > 500
"""
Security monitoring and audit system for Django Personal Blog System.
Implements comprehensive security monitoring, alerting, and audit logging.
"""

import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from .models import AuditLog

User = get_user_model()
logger = logging.getLogger('security')


@dataclass
class SecurityAlert:
    """Data class for security alerts."""
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    source_ip: str
    user_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SecurityMonitor:
    """
    Comprehensive security monitoring system.
    """
    
    def __init__(self):
        self.config = getattr(settings, 'SECURITY_MONITORING', {})
        self.alert_thresholds = {
            'failed_logins': 5,
            'csrf_failures': 10,
            'suspicious_requests': 3,
            'rate_limit_violations': 20,
            'file_upload_failures': 5,
        }
        self.time_windows = {
            'short': 300,   # 5 minutes
            'medium': 1800, # 30 minutes
            'long': 3600,   # 1 hour
        }
    
    def monitor_login_attempts(self, ip_address: str, user_id: Optional[int] = None, 
                             success: bool = True) -> None:
        """Monitor login attempts for suspicious activity."""
        
        # Record login attempt
        attempt_key = f"login_attempts:{ip_address}"
        attempts = cache.get(attempt_key, [])
        
        attempt_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user_id,
            'success': success,
            'ip': ip_address
        }
        
        attempts.append(attempt_data)
        
        # Keep only recent attempts (last hour)
        cutoff = timezone.now() - timedelta(hours=1)
        attempts = [
            a for a in attempts 
            if datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) > cutoff
        ]
        
        cache.set(attempt_key, attempts, 3600)  # 1 hour
        
        # Check for suspicious patterns
        if not success:
            failed_attempts = [a for a in attempts if not a['success']]
            
            if len(failed_attempts) >= self.alert_thresholds['failed_logins']:
                self._create_alert(
                    alert_type='failed_login_threshold',
                    severity='high',
                    title='Multiple Failed Login Attempts',
                    description=f'IP {ip_address} has {len(failed_attempts)} failed login attempts in the last hour',
                    source_ip=ip_address,
                    user_id=user_id,
                    metadata={'failed_attempts': len(failed_attempts)}
                )
        
        # Check for brute force patterns
        self._check_brute_force_patterns(ip_address, attempts)
    
    def monitor_csrf_failures(self, ip_address: str, path: str, user_id: Optional[int] = None) -> None:
        """Monitor CSRF failures for potential attacks."""
        
        failure_key = f"csrf_failures:{ip_address}"
        failures = cache.get(failure_key, 0) + 1
        cache.set(failure_key, failures, self.time_windows['medium'])
        
        if failures >= self.alert_thresholds['csrf_failures']:
            self._create_alert(
                alert_type='csrf_attack',
                severity='high',
                title='Multiple CSRF Failures',
                description=f'IP {ip_address} has {failures} CSRF failures in 30 minutes',
                source_ip=ip_address,
                user_id=user_id,
                metadata={'failures': failures, 'path': path}
            )
    
    def monitor_suspicious_requests(self, ip_address: str, request_data: Dict[str, Any]) -> None:
        """Monitor for suspicious request patterns."""
        
        suspicious_key = f"suspicious_requests:{ip_address}"
        requests = cache.get(suspicious_key, 0) + 1
        cache.set(suspicious_key, requests, self.time_windows['short'])
        
        if requests >= self.alert_thresholds['suspicious_requests']:
            self._create_alert(
                alert_type='suspicious_activity',
                severity='medium',
                title='Suspicious Request Pattern',
                description=f'IP {ip_address} has {requests} suspicious requests in 5 minutes',
                source_ip=ip_address,
                metadata=request_data
            )
    
    def monitor_rate_limit_violations(self, ip_address: str, endpoint: str) -> None:
        """Monitor rate limit violations."""
        
        violation_key = f"rate_violations:{ip_address}"
        violations = cache.get(violation_key, 0) + 1
        cache.set(violation_key, violations, self.time_windows['medium'])
        
        if violations >= self.alert_thresholds['rate_limit_violations']:
            self._create_alert(
                alert_type='rate_limit_abuse',
                severity='medium',
                title='Excessive Rate Limit Violations',
                description=f'IP {ip_address} has {violations} rate limit violations',
                source_ip=ip_address,
                metadata={'endpoint': endpoint, 'violations': violations}
            )
    
    def monitor_file_uploads(self, ip_address: str, filename: str, success: bool = True, 
                           user_id: Optional[int] = None) -> None:
        """Monitor file upload attempts for security issues."""
        
        if not success:
            failure_key = f"upload_failures:{ip_address}"
            failures = cache.get(failure_key, 0) + 1
            cache.set(failure_key, failures, self.time_windows['medium'])
            
            if failures >= self.alert_thresholds['file_upload_failures']:
                self._create_alert(
                    alert_type='malicious_upload',
                    severity='high',
                    title='Multiple File Upload Failures',
                    description=f'IP {ip_address} has {failures} failed upload attempts',
                    source_ip=ip_address,
                    user_id=user_id,
                    metadata={'filename': filename, 'failures': failures}
                )
    
    def monitor_privilege_escalation(self, user_id: int, old_permissions: List[str], 
                                   new_permissions: List[str]) -> None:
        """Monitor for privilege escalation attempts."""
        
        added_permissions = set(new_permissions) - set(old_permissions)
        
        if added_permissions:
            # Check for critical permissions
            critical_permissions = ['is_superuser', 'is_staff', 'add_user', 'delete_user']
            critical_added = [p for p in added_permissions if any(cp in p for cp in critical_permissions)]
            
            if critical_added:
                self._create_alert(
                    alert_type='privilege_escalation',
                    severity='critical',
                    title='Privilege Escalation Detected',
                    description=f'User {user_id} gained critical permissions: {critical_added}',
                    source_ip='',
                    user_id=user_id,
                    metadata={
                        'added_permissions': list(added_permissions),
                        'critical_permissions': critical_added
                    }
                )
    
    def _check_brute_force_patterns(self, ip_address: str, attempts: List[Dict]) -> None:
        """Check for brute force attack patterns."""
        
        # Pattern 1: Rapid successive attempts
        recent_attempts = [
            a for a in attempts 
            if datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) > 
               timezone.now() - timedelta(minutes=5)
        ]
        
        if len(recent_attempts) >= 10:
            self._create_alert(
                alert_type='brute_force_attack',
                severity='critical',
                title='Brute Force Attack Detected',
                description=f'IP {ip_address} has {len(recent_attempts)} login attempts in 5 minutes',
                source_ip=ip_address,
                metadata={'attempts_count': len(recent_attempts)}
            )
        
        # Pattern 2: Multiple user targets
        unique_users = set(a.get('user_id') for a in attempts if a.get('user_id'))
        if len(unique_users) >= 5:
            self._create_alert(
                alert_type='credential_stuffing',
                severity='high',
                title='Credential Stuffing Attack',
                description=f'IP {ip_address} attempted login for {len(unique_users)} different users',
                source_ip=ip_address,
                metadata={'targeted_users': len(unique_users)}
            )
    
    def _create_alert(self, alert_type: str, severity: str, title: str, 
                     description: str, source_ip: str, user_id: Optional[int] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create and process security alert."""
        
        alert = SecurityAlert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            source_ip=source_ip,
            user_id=user_id,
            timestamp=timezone.now(),
            metadata=metadata or {}
        )
        
        # Log the alert
        logger.warning(f"Security Alert [{severity.upper()}]: {title} - {description}")
        
        # Store alert in cache for dashboard
        alert_key = f"security_alert:{timezone.now().timestamp()}"
        cache.set(alert_key, alert.__dict__, 86400)  # 24 hours
        
        # Create audit log entry
        try:
            AuditLog.objects.create(
                user_id=user_id,
                action_type=AuditLog.ActionType.SECURITY_EVENT,
                object_type='security_alert',
                object_id=alert_type,
                details=f"{title}: {description}",
                ip_address=source_ip,
                extra_data=alert.__dict__
            )
        except Exception as e:
            logger.error(f"Failed to create audit log for security alert: {e}")
        
        # Send notifications if enabled
        if self.config.get('ALERT_ON_SECURITY_VIOLATIONS', False):
            self._send_alert_notification(alert)
    
    def _send_alert_notification(self, alert: SecurityAlert) -> None:
        """Send alert notification to administrators."""
        
        try:
            # Get admin emails
            admin_emails = getattr(settings, 'SECURITY_ADMIN_EMAILS', [])
            if not admin_emails:
                # Fallback to superuser emails
                admin_emails = list(
                    User.objects.filter(is_superuser=True, is_active=True)
                    .values_list('email', flat=True)
                )
            
            if not admin_emails:
                logger.warning("No admin emails configured for security alerts")
                return
            
            # Prepare email content
            subject = f"[SECURITY ALERT] {alert.title}"
            message = f"""
Security Alert Details:

Type: {alert.alert_type}
Severity: {alert.severity.upper()}
Title: {alert.title}
Description: {alert.description}
Source IP: {alert.source_ip}
User ID: {alert.user_id or 'N/A'}
Timestamp: {alert.timestamp}

Metadata:
{json.dumps(alert.metadata, indent=2)}

Please investigate this security event immediately.
            """.strip()
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            logger.info(f"Security alert notification sent to {len(admin_emails)} administrators")
            
        except Exception as e:
            logger.error(f"Failed to send security alert notification: {e}")
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data."""
        
        now = timezone.now()
        
        # Get recent alerts
        alert_keys = cache.keys("security_alert:*")
        recent_alerts = []
        
        for key in alert_keys:
            alert_data = cache.get(key)
            if alert_data:
                recent_alerts.append(alert_data)
        
        # Sort by timestamp
        recent_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Get statistics from audit logs
        stats = self._get_security_statistics(now)
        
        return {
            'recent_alerts': recent_alerts[:20],  # Last 20 alerts
            'statistics': stats,
            'threat_level': self._calculate_threat_level(recent_alerts, stats),
            'recommendations': self._get_security_recommendations(stats)
        }
    
    def _get_security_statistics(self, now: datetime) -> Dict[str, Any]:
        """Get security statistics from audit logs."""
        
        # Time ranges
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        last_week = now - timedelta(weeks=1)
        
        # Query audit logs
        security_events = AuditLog.objects.filter(
            action_type=AuditLog.ActionType.SECURITY_EVENT
        )
        
        stats = {
            'total_security_events': security_events.count(),
            'events_last_hour': security_events.filter(timestamp__gte=last_hour).count(),
            'events_last_day': security_events.filter(timestamp__gte=last_day).count(),
            'events_last_week': security_events.filter(timestamp__gte=last_week).count(),
            'top_threat_ips': self._get_top_threat_ips(security_events, last_day),
            'event_types': self._get_event_type_distribution(security_events, last_day),
            'blocked_ips': self._get_blocked_ips_count(),
        }
        
        return stats
    
    def _get_top_threat_ips(self, queryset, since: datetime) -> List[Dict[str, Any]]:
        """Get top threat IPs from security events."""
        
        return list(
            queryset.filter(timestamp__gte=since)
            .values('ip_address')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
    
    def _get_event_type_distribution(self, queryset, since: datetime) -> Dict[str, int]:
        """Get distribution of security event types."""
        
        events = queryset.filter(timestamp__gte=since).values_list('object_id', flat=True)
        distribution = {}
        
        for event_type in events:
            distribution[event_type] = distribution.get(event_type, 0) + 1
        
        return distribution
    
    def _get_blocked_ips_count(self) -> int:
        """Get count of currently blocked IPs."""
        
        blocked_keys = cache.keys("ip_blocked:*")
        return len([key for key in blocked_keys if cache.get(key)])
    
    def _calculate_threat_level(self, alerts: List[Dict], stats: Dict[str, Any]) -> str:
        """Calculate current threat level."""
        
        # Count critical and high severity alerts in last hour
        recent_critical = sum(
            1 for alert in alerts 
            if alert.get('severity') == 'critical' and 
               self._is_recent_alert(alert, hours=1)
        )
        
        recent_high = sum(
            1 for alert in alerts 
            if alert.get('severity') == 'high' and 
               self._is_recent_alert(alert, hours=1)
        )
        
        # Determine threat level
        if recent_critical >= 3 or stats.get('events_last_hour', 0) >= 50:
            return 'critical'
        elif recent_critical >= 1 or recent_high >= 5 or stats.get('events_last_hour', 0) >= 20:
            return 'high'
        elif recent_high >= 2 or stats.get('events_last_hour', 0) >= 10:
            return 'medium'
        else:
            return 'low'
    
    def _is_recent_alert(self, alert: Dict, hours: int = 1) -> bool:
        """Check if alert is within the specified time range."""
        
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            return alert_time > timezone.now() - timedelta(hours=hours)
        except (KeyError, ValueError):
            return False
    
    def _get_security_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get security recommendations based on current statistics."""
        
        recommendations = []
        
        if stats.get('events_last_hour', 0) > 20:
            recommendations.append("High security event volume detected. Consider reviewing firewall rules.")
        
        if stats.get('blocked_ips', 0) > 50:
            recommendations.append("Many IPs are currently blocked. Review blocking criteria.")
        
        top_threats = stats.get('top_threat_ips', [])
        if top_threats and top_threats[0].get('count', 0) > 10:
            recommendations.append(f"IP {top_threats[0]['ip_address']} is generating many security events.")
        
        event_types = stats.get('event_types', {})
        if event_types.get('failed_login_threshold', 0) > 5:
            recommendations.append("Multiple failed login thresholds exceeded. Consider implementing CAPTCHA.")
        
        if event_types.get('brute_force_attack', 0) > 0:
            recommendations.append("Brute force attacks detected. Consider implementing account lockouts.")
        
        if not recommendations:
            recommendations.append("Security posture looks good. Continue monitoring.")
        
        return recommendations


# Global security monitor instance
security_monitor = SecurityMonitor()


# Utility functions for easy access

def log_security_event(event_type: str, description: str, ip_address: str = '', 
                      user_id: Optional[int] = None, metadata: Optional[Dict] = None) -> None:
    """Log a security event."""
    
    try:
        AuditLog.objects.create(
            user_id=user_id,
            action_type=AuditLog.ActionType.SECURITY_EVENT,
            object_type='security',
            object_id=event_type,
            details=description,
            ip_address=ip_address,
            extra_data=metadata or {}
        )
        
        logger.info(f"Security event logged: {event_type} - {description}")
        
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")


def monitor_login_attempt(ip_address: str, user_id: Optional[int] = None, success: bool = True) -> None:
    """Monitor a login attempt."""
    security_monitor.monitor_login_attempts(ip_address, user_id, success)


def monitor_csrf_failure(ip_address: str, path: str, user_id: Optional[int] = None) -> None:
    """Monitor a CSRF failure."""
    security_monitor.monitor_csrf_failures(ip_address, path, user_id)


def get_security_dashboard() -> Dict[str, Any]:
    """Get security dashboard data."""
    return security_monitor.get_security_dashboard_data()
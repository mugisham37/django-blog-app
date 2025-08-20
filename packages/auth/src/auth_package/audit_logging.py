"""
Security audit logging and compliance reporting system.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    
    # Authorization events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    
    # Account events
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_UPDATED = "account_updated"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    ACCOUNT_SUSPENDED = "account_suspended"
    
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    SESSION_REVOKED = "session_revoked"
    CONCURRENT_LOGIN = "concurrent_login"
    
    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    DEVICE_CHANGE = "device_change"
    LOCATION_CHANGE = "location_change"
    
    # Data events
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_DELETION = "data_deletion"
    
    # System events
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGE = "configuration_change"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"


class AuditSeverity(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Security audit event."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: str = "success"  # success, failure, error
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.event_id:
            # Generate event ID from content hash
            content = f"{self.event_type.value}:{self.timestamp.isoformat()}:{self.user_id}"
            self.event_id = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource": self.resource,
            "action": self.action,
            "result": self.result,
            "details": self.details,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert audit event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Security audit logging system.
    
    Provides comprehensive audit logging for security events,
    compliance reporting, and forensic analysis.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            "log_level": "INFO",
            "log_format": "json",  # json, text
            "log_file": "audit.log",
            "max_log_size": 100 * 1024 * 1024,  # 100MB
            "backup_count": 10,
            "enable_syslog": False,
            "syslog_facility": "LOG_AUTH",
            "enable_database": False,
            "retention_days": 365,
            "enable_real_time_alerts": True,
            "alert_thresholds": {
                "failed_logins": 5,
                "suspicious_activities": 3,
                "critical_events": 1
            }
        }
        
        if config:
            default_config.update(config)
        
        self.config = default_config
        self._setup_logging()
        self._events: List[AuditEvent] = []  # In-memory storage for analysis
        self._alert_counters: Dict[str, int] = {}
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(getattr(logging, self.config["log_level"]))
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.config["log_file"],
            maxBytes=self.config["max_log_size"],
            backupCount=self.config["backup_count"]
        )
        
        # Formatter
        if self.config["log_format"] == "json":
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Syslog handler (if enabled)
        if self.config["enable_syslog"]:
            try:
                from logging.handlers import SysLogHandler
                syslog_handler = SysLogHandler(
                    facility=getattr(SysLogHandler, self.config["syslog_facility"])
                )
                syslog_handler.setFormatter(formatter)
                self.logger.addHandler(syslog_handler)
            except Exception as e:
                print(f"Failed to setup syslog handler: {e}")
    
    def log_event(self, 
                  event_type: AuditEventType,
                  severity: AuditSeverity = AuditSeverity.MEDIUM,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  resource: Optional[str] = None,
                  action: Optional[str] = None,
                  result: str = "success",
                  details: Dict[str, Any] = None,
                  metadata: Dict[str, Any] = None) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            severity: Event severity level
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            resource: Resource being accessed
            action: Action being performed
            result: Result of the action
            details: Additional event details
            metadata: Additional metadata
            
        Returns:
            Created audit event
        """
        event = AuditEvent(
            event_id="",  # Will be generated in __post_init__
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            metadata=metadata or {}
        )
        
        # Log to file/syslog
        if self.config["log_format"] == "json":
            self.logger.info(event.to_json())
        else:
            log_message = f"[{event.event_type.value}] User: {user_id}, Result: {result}"
            if details:
                log_message += f", Details: {details}"
            self.logger.info(log_message)
        
        # Store in memory for analysis
        self._events.append(event)
        
        # Database storage (if enabled)
        if self.config["enable_database"]:
            self._store_to_database(event)
        
        # Real-time alerts (if enabled)
        if self.config["enable_real_time_alerts"]:
            self._check_alert_conditions(event)
        
        return event
    
    def log_authentication_event(self, 
                                event_type: AuditEventType,
                                user_id: str,
                                ip_address: str,
                                user_agent: str = "",
                                result: str = "success",
                                details: Dict[str, Any] = None):
        """Log authentication-related event."""
        severity = AuditSeverity.HIGH if result == "failure" else AuditSeverity.MEDIUM
        
        return self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            details=details
        )
    
    def log_authorization_event(self,
                               user_id: str,
                               resource: str,
                               action: str,
                               result: str,
                               ip_address: str = "",
                               details: Dict[str, Any] = None):
        """Log authorization-related event."""
        event_type = (AuditEventType.PERMISSION_GRANTED if result == "success" 
                     else AuditEventType.PERMISSION_DENIED)
        severity = AuditSeverity.HIGH if result == "failure" else AuditSeverity.LOW
        
        return self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            result=result,
            details=details
        )
    
    def log_security_event(self,
                          event_type: AuditEventType,
                          user_id: Optional[str] = None,
                          ip_address: Optional[str] = None,
                          details: Dict[str, Any] = None):
        """Log security-related event."""
        return self.log_event(
            event_type=event_type,
            severity=AuditSeverity.HIGH,
            user_id=user_id,
            ip_address=ip_address,
            details=details
        )
    
    def get_events(self, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   event_types: Optional[List[AuditEventType]] = None,
                   user_id: Optional[str] = None,
                   severity: Optional[AuditSeverity] = None,
                   limit: int = 1000) -> List[AuditEvent]:
        """
        Retrieve audit events with filtering.
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            event_types: Event type filter
            user_id: User ID filter
            severity: Severity filter
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        filtered_events = self._events.copy()
        
        # Apply filters
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
        
        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        
        if severity:
            filtered_events = [e for e in filtered_events if e.severity == severity]
        
        # Sort by timestamp (newest first) and limit
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        return filtered_events[:limit]
    
    def generate_security_report(self, 
                               start_time: datetime,
                               end_time: datetime) -> Dict[str, Any]:
        """
        Generate security audit report for a time period.
        
        Args:
            start_time: Report start time
            end_time: Report end time
            
        Returns:
            Security report dictionary
        """
        events = self.get_events(start_time=start_time, end_time=end_time)
        
        # Event statistics
        event_counts = {}
        severity_counts = {}
        user_activity = {}
        failed_logins = []
        
        for event in events:
            # Event type counts
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Severity counts
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # User activity
            if event.user_id:
                if event.user_id not in user_activity:
                    user_activity[event.user_id] = {"total": 0, "failed_logins": 0}
                user_activity[event.user_id]["total"] += 1
                
                if event.event_type == AuditEventType.LOGIN_FAILURE:
                    user_activity[event.user_id]["failed_logins"] += 1
                    failed_logins.append(event)
        
        # Security metrics
        total_events = len(events)
        critical_events = len([e for e in events if e.severity == AuditSeverity.CRITICAL])
        high_severity_events = len([e for e in events if e.severity == AuditSeverity.HIGH])
        
        # Top users by activity
        top_users = sorted(
            user_activity.items(),
            key=lambda x: x[1]["total"],
            reverse=True
        )[:10]
        
        # Users with most failed logins
        users_with_failures = [
            (user_id, data["failed_logins"])
            for user_id, data in user_activity.items()
            if data["failed_logins"] > 0
        ]
        users_with_failures.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "report_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "summary": {
                "total_events": total_events,
                "critical_events": critical_events,
                "high_severity_events": high_severity_events,
                "unique_users": len(user_activity)
            },
            "event_counts": event_counts,
            "severity_counts": severity_counts,
            "top_users_by_activity": top_users,
            "users_with_failed_logins": users_with_failures,
            "recent_critical_events": [
                e.to_dict() for e in events
                if e.severity == AuditSeverity.CRITICAL
            ][:10]
        }
    
    def detect_anomalies(self, time_window: timedelta = timedelta(hours=1)) -> List[Dict[str, Any]]:
        """
        Detect security anomalies in recent events.
        
        Args:
            time_window: Time window to analyze
            
        Returns:
            List of detected anomalies
        """
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        recent_events = self.get_events(start_time=start_time, end_time=end_time)
        
        anomalies = []
        
        # Detect brute force attempts
        failed_logins_by_user = {}
        failed_logins_by_ip = {}
        
        for event in recent_events:
            if event.event_type == AuditEventType.LOGIN_FAILURE:
                # By user
                user_id = event.user_id or "unknown"
                failed_logins_by_user[user_id] = failed_logins_by_user.get(user_id, 0) + 1
                
                # By IP
                ip_address = event.ip_address or "unknown"
                failed_logins_by_ip[ip_address] = failed_logins_by_ip.get(ip_address, 0) + 1
        
        # Check thresholds
        threshold = self.config["alert_thresholds"]["failed_logins"]
        
        for user_id, count in failed_logins_by_user.items():
            if count >= threshold:
                anomalies.append({
                    "type": "brute_force_user",
                    "user_id": user_id,
                    "failed_attempts": count,
                    "time_window": time_window.total_seconds()
                })
        
        for ip_address, count in failed_logins_by_ip.items():
            if count >= threshold:
                anomalies.append({
                    "type": "brute_force_ip",
                    "ip_address": ip_address,
                    "failed_attempts": count,
                    "time_window": time_window.total_seconds()
                })
        
        # Detect unusual activity patterns
        # (This could be expanded with more sophisticated ML-based detection)
        
        return anomalies
    
    def _store_to_database(self, event: AuditEvent):
        """Store audit event to database (placeholder)."""
        # This would implement database storage
        # Could use SQLAlchemy, MongoDB, or other database systems
        pass
    
    def _check_alert_conditions(self, event: AuditEvent):
        """Check if event triggers real-time alerts."""
        # Critical events always trigger alerts
        if event.severity == AuditSeverity.CRITICAL:
            self._send_alert(event, "Critical security event detected")
        
        # Count-based alerts
        event_key = f"{event.event_type.value}:{event.user_id}"
        self._alert_counters[event_key] = self._alert_counters.get(event_key, 0) + 1
        
        thresholds = self.config["alert_thresholds"]
        
        if (event.event_type == AuditEventType.LOGIN_FAILURE and
            self._alert_counters[event_key] >= thresholds["failed_logins"]):
            self._send_alert(event, f"Multiple failed login attempts: {self._alert_counters[event_key]}")
        
        if (event.event_type == AuditEventType.SUSPICIOUS_ACTIVITY and
            self._alert_counters[event_key] >= thresholds["suspicious_activities"]):
            self._send_alert(event, f"Multiple suspicious activities: {self._alert_counters[event_key]}")
    
    def _send_alert(self, event: AuditEvent, message: str):
        """Send real-time security alert."""
        # This would implement alert sending (email, SMS, webhook, etc.)
        alert_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "event": event.to_dict()
        }
        
        # Log the alert
        self.logger.critical(f"SECURITY ALERT: {message}")
        
        # Could integrate with:
        # - Email notifications
        # - Slack/Teams webhooks
        # - SIEM systems
        # - Incident management systems
    
    def cleanup_old_events(self) -> int:
        """Remove old events based on retention policy."""
        retention_days = self.config["retention_days"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        initial_count = len(self._events)
        self._events = [e for e in self._events if e.timestamp > cutoff_date]
        
        return initial_count - len(self._events)


# Global audit logger instance
default_audit_logger = AuditLogger()
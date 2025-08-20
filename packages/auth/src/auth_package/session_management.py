"""
Advanced session management with concurrent login handling and security features.
"""

import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


@dataclass
class DeviceInfo:
    """Device information for session tracking."""
    device_id: str
    user_agent: str
    ip_address: str
    device_type: str = "unknown"  # mobile, desktop, tablet
    browser: str = "unknown"
    os: str = "unknown"
    location: str = "unknown"
    is_trusted: bool = False
    
    def fingerprint(self) -> str:
        """Generate device fingerprint."""
        data = f"{self.user_agent}:{self.ip_address}:{self.device_type}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class Session:
    """User session with security tracking."""
    session_id: str
    user_id: str
    device_info: DeviceInfo
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Security tracking
    login_method: str = "password"  # password, mfa, oauth2, etc.
    risk_score: float = 0.0  # 0.0 = low risk, 1.0 = high risk
    security_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Session metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        if self.status != SessionStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    @property
    def duration(self) -> timedelta:
        """Get session duration."""
        return self.last_activity - self.created_at
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def add_security_event(self, event_type: str, details: Dict[str, Any]):
        """Add security event to session."""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        self.security_events.append(event)
    
    def calculate_risk_score(self) -> float:
        """Calculate session risk score based on various factors."""
        risk_factors = []
        
        # Location-based risk
        if not self.device_info.is_trusted:
            risk_factors.append(0.2)
        
        # Time-based risk (unusual login times)
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Late night/early morning
            risk_factors.append(0.1)
        
        # Session duration risk
        if self.duration > timedelta(hours=12):
            risk_factors.append(0.1)
        
        # Security events risk
        suspicious_events = [
            event for event in self.security_events
            if event["type"] in ["failed_mfa", "suspicious_activity", "location_change"]
        ]
        if suspicious_events:
            risk_factors.append(min(0.3, len(suspicious_events) * 0.1))
        
        # Calculate final risk score
        self.risk_score = min(1.0, sum(risk_factors))
        return self.risk_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "device_info": {
                "device_id": self.device_info.device_id,
                "user_agent": self.device_info.user_agent,
                "ip_address": self.device_info.ip_address,
                "device_type": self.device_info.device_type,
                "browser": self.device_info.browser,
                "os": self.device_info.os,
                "location": self.device_info.location,
                "is_trusted": self.device_info.is_trusted
            },
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "login_method": self.login_method,
            "risk_score": self.risk_score,
            "security_events": self.security_events,
            "metadata": self.metadata
        }


class SessionManager:
    """
    Advanced session management with concurrent login handling.
    
    Provides session creation, validation, and security monitoring
    with support for concurrent sessions and device tracking.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            "max_concurrent_sessions": 5,
            "session_timeout": 3600,  # 1 hour
            "idle_timeout": 1800,  # 30 minutes
            "remember_me_duration": 2592000,  # 30 days
            "max_session_duration": 86400,  # 24 hours
            "risk_threshold": 0.7,  # Sessions above this risk are flagged
            "enable_device_tracking": True,
            "enable_location_tracking": True,
            "suspicious_activity_threshold": 3
        }
        
        if config:
            default_config.update(config)
        
        self.config = default_config
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids
        self._device_sessions: Dict[str, Set[str]] = {}  # device_id -> session_ids
    
    def create_session(self, 
                      user_id: str, 
                      device_info: DeviceInfo,
                      login_method: str = "password",
                      remember_me: bool = False,
                      metadata: Dict[str, Any] = None) -> Session:
        """
        Create new user session.
        
        Args:
            user_id: User identifier
            device_info: Device information
            login_method: Authentication method used
            remember_me: Whether to extend session duration
            metadata: Additional session metadata
            
        Returns:
            Created session
        """
        # Generate session ID
        session_id = secrets.token_urlsafe(32)
        
        # Calculate session expiration
        if remember_me:
            expires_at = datetime.utcnow() + timedelta(seconds=self.config["remember_me_duration"])
        else:
            expires_at = datetime.utcnow() + timedelta(seconds=self.config["session_timeout"])
        
        # Create session
        session = Session(
            session_id=session_id,
            user_id=user_id,
            device_info=device_info,
            expires_at=expires_at,
            login_method=login_method,
            metadata=metadata or {}
        )
        
        # Check concurrent session limits
        self._enforce_concurrent_session_limits(user_id)
        
        # Store session
        self._sessions[session_id] = session
        
        # Update user sessions index
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = set()
        self._user_sessions[user_id].add(session_id)
        
        # Update device sessions index
        device_id = device_info.device_id
        if device_id not in self._device_sessions:
            self._device_sessions[device_id] = set()
        self._device_sessions[device_id].add(session_id)
        
        # Calculate initial risk score
        session.calculate_risk_score()
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        
        if session and session.is_active:
            # Update activity and check for suspicious behavior
            self._update_session_activity(session)
            return session
        
        return None
    
    def validate_session(self, session_id: str, device_info: DeviceInfo = None) -> bool:
        """
        Validate session and check for security issues.
        
        Args:
            session_id: Session identifier
            device_info: Current device information for validation
            
        Returns:
            True if session is valid and secure
        """
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        # Device validation
        if device_info and self.config["enable_device_tracking"]:
            if not self._validate_device(session, device_info):
                session.add_security_event("device_mismatch", {
                    "expected_device": session.device_info.device_id,
                    "actual_device": device_info.device_id
                })
                session.status = SessionStatus.SUSPICIOUS
                return False
        
        # Check session timeout
        idle_time = datetime.utcnow() - session.last_activity
        if idle_time > timedelta(seconds=self.config["idle_timeout"]):
            self.revoke_session(session_id, "idle_timeout")
            return False
        
        # Check maximum session duration
        if session.duration > timedelta(seconds=self.config["max_session_duration"]):
            self.revoke_session(session_id, "max_duration_exceeded")
            return False
        
        # Check risk score
        session.calculate_risk_score()
        if session.risk_score > self.config["risk_threshold"]:
            session.status = SessionStatus.SUSPICIOUS
            session.add_security_event("high_risk_score", {
                "risk_score": session.risk_score,
                "threshold": self.config["risk_threshold"]
            })
            return False
        
        return True
    
    def revoke_session(self, session_id: str, reason: str = "manual"):
        """
        Revoke a session.
        
        Args:
            session_id: Session to revoke
            reason: Reason for revocation
        """
        session = self._sessions.get(session_id)
        
        if session:
            session.status = SessionStatus.REVOKED
            session.add_security_event("session_revoked", {"reason": reason})
            
            # Remove from indexes
            self._remove_session_from_indexes(session)
    
    def revoke_user_sessions(self, user_id: str, exclude_session: str = None) -> int:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id: User identifier
            exclude_session: Session ID to exclude from revocation
            
        Returns:
            Number of sessions revoked
        """
        user_session_ids = self._user_sessions.get(user_id, set()).copy()
        revoked_count = 0
        
        for session_id in user_session_ids:
            if session_id != exclude_session:
                self.revoke_session(session_id, "user_logout_all")
                revoked_count += 1
        
        return revoked_count
    
    def revoke_device_sessions(self, device_id: str, exclude_session: str = None) -> int:
        """
        Revoke all sessions for a device.
        
        Args:
            device_id: Device identifier
            exclude_session: Session ID to exclude from revocation
            
        Returns:
            Number of sessions revoked
        """
        device_session_ids = self._device_sessions.get(device_id, set()).copy()
        revoked_count = 0
        
        for session_id in device_session_ids:
            if session_id != exclude_session:
                self.revoke_session(session_id, "device_logout_all")
                revoked_count += 1
        
        return revoked_count
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        session_ids = self._user_sessions.get(user_id, set())
        sessions = []
        
        for session_id in session_ids:
            session = self._sessions.get(session_id)
            if session and session.is_active:
                sessions.append(session)
        
        return sessions
    
    def get_suspicious_sessions(self) -> List[Session]:
        """Get all sessions flagged as suspicious."""
        suspicious_sessions = []
        
        for session in self._sessions.values():
            if (session.status == SessionStatus.SUSPICIOUS or 
                session.risk_score > self.config["risk_threshold"]):
                suspicious_sessions.append(session)
        
        return suspicious_sessions
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count."""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if not session.is_active:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            session = self._sessions[session_id]
            self._remove_session_from_indexes(session)
            del self._sessions[session_id]
        
        return len(expired_sessions)
    
    def _enforce_concurrent_session_limits(self, user_id: str):
        """Enforce concurrent session limits for user."""
        user_sessions = self.get_user_sessions(user_id)
        max_sessions = self.config["max_concurrent_sessions"]
        
        if len(user_sessions) >= max_sessions:
            # Sort by last activity and revoke oldest sessions
            user_sessions.sort(key=lambda s: s.last_activity)
            sessions_to_revoke = len(user_sessions) - max_sessions + 1
            
            for i in range(sessions_to_revoke):
                self.revoke_session(user_sessions[i].session_id, "concurrent_limit_exceeded")
    
    def _update_session_activity(self, session: Session):
        """Update session activity and check for suspicious behavior."""
        previous_activity = session.last_activity
        session.update_activity()
        
        # Check for suspicious activity patterns
        time_gap = session.last_activity - previous_activity
        
        if time_gap < timedelta(seconds=1):  # Very rapid requests
            session.add_security_event("rapid_requests", {
                "time_gap_seconds": time_gap.total_seconds()
            })
        
        # Check for location changes (if enabled)
        if self.config["enable_location_tracking"]:
            # This would integrate with IP geolocation services
            pass
    
    def _validate_device(self, session: Session, current_device: DeviceInfo) -> bool:
        """Validate device information against session."""
        stored_device = session.device_info
        
        # Check device fingerprint
        if stored_device.fingerprint() != current_device.fingerprint():
            return False
        
        # Check IP address (allow some flexibility for mobile users)
        if stored_device.ip_address != current_device.ip_address:
            # Could implement IP range checking here
            pass
        
        return True
    
    def _remove_session_from_indexes(self, session: Session):
        """Remove session from all indexes."""
        session_id = session.session_id
        user_id = session.user_id
        device_id = session.device_info.device_id
        
        # Remove from user sessions
        if user_id in self._user_sessions:
            self._user_sessions[user_id].discard(session_id)
            if not self._user_sessions[user_id]:
                del self._user_sessions[user_id]
        
        # Remove from device sessions
        if device_id in self._device_sessions:
            self._device_sessions[device_id].discard(session_id)
            if not self._device_sessions[device_id]:
                del self._device_sessions[device_id]
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sessions = len(self._sessions)
        active_sessions = len([s for s in self._sessions.values() if s.is_active])
        suspicious_sessions = len(self.get_suspicious_sessions())
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "suspicious_sessions": suspicious_sessions,
            "total_users": len(self._user_sessions),
            "total_devices": len(self._device_sessions)
        }


# Global session manager instance
default_session_manager = SessionManager()
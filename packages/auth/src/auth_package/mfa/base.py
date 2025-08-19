"""
Base classes and interfaces for MFA providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum


class MFAStatus(Enum):
    """MFA challenge status."""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class MFAChallenge:
    """MFA challenge data structure."""
    challenge_id: str
    user_id: str
    provider_type: str
    status: MFAStatus
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 3
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_expired(self) -> bool:
        """Check if challenge has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if challenge is still valid."""
        return (
            self.status == MFAStatus.PENDING and
            not self.is_expired and
            self.attempts < self.max_attempts
        )


@dataclass
class MFAResult:
    """MFA operation result."""
    success: bool
    message: str
    challenge_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MFAProvider(ABC):
    """
    Abstract base class for MFA providers.
    
    Defines the interface that all MFA providers must implement.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self._challenges = {}  # In production, use Redis or database
    
    @abstractmethod
    def generate_challenge(self, user_id: str, contact_info: str, **kwargs) -> MFAResult:
        """
        Generate and send MFA challenge to user.
        
        Args:
            user_id: Unique user identifier
            contact_info: User's contact information (phone, email, etc.)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            MFAResult with challenge information
        """
        pass
    
    @abstractmethod
    def verify_challenge(self, challenge_id: str, code: str) -> MFAResult:
        """
        Verify MFA challenge response.
        
        Args:
            challenge_id: Challenge identifier
            code: User-provided verification code
            
        Returns:
            MFAResult with verification status
        """
        pass
    
    def get_challenge(self, challenge_id: str) -> Optional[MFAChallenge]:
        """Get challenge by ID."""
        return self._challenges.get(challenge_id)
    
    def store_challenge(self, challenge: MFAChallenge):
        """Store challenge in memory/database."""
        self._challenges[challenge.challenge_id] = challenge
    
    def cleanup_expired_challenges(self):
        """Remove expired challenges."""
        current_time = datetime.utcnow()
        expired_ids = [
            challenge_id for challenge_id, challenge in self._challenges.items()
            if challenge.expires_at < current_time
        ]
        
        for challenge_id in expired_ids:
            del self._challenges[challenge_id]
    
    def revoke_challenge(self, challenge_id: str) -> bool:
        """
        Revoke an active challenge.
        
        Args:
            challenge_id: Challenge to revoke
            
        Returns:
            True if challenge was revoked
        """
        if challenge_id in self._challenges:
            self._challenges[challenge_id].status = MFAStatus.FAILED
            return True
        return False
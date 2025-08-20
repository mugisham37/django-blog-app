"""
Comprehensive tests for advanced authentication features.
"""

import pytest
import secrets
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from auth_package import (
    SessionManager, DeviceInfo, Session,
    AuditLogger, AuditEventType, AuditSeverity,
    PasswordValidator, PasswordPolicy, AccountLockoutManager,
    TOTPProvider, SMSProvider, EmailProvider
)
from auth_package.session_management import SessionStatus
from auth_package.password_policies import PasswordStrength, LockoutReason
from auth_package.mfa.base import MFAStatus


class TestSessionManagement:
    """Test session management functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.session_manager = SessionManager()
        self.device_info = DeviceInfo(
            device_id="test_device",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.100",
            device_type="desktop"
        )
    
    def test_create_session(self):
        """Test session creation."""
        session = self.session_manager.create_session(
            "user123", self.device_info, "password"
        )
        
        assert session.user_id == "user123"
        assert session.device_info.device_id == "test_device"
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active
        assert session.login_method == "password"
    
    def test_session_validation(self):
        """Test session validation."""
        session = self.session_manager.create_session(
            "user123", self.device_info, "password"
        )
        
        # Valid session
        assert self.session_manager.validate_session(session.session_id, self.device_info)
        
        # Invalid session ID
        assert not self.session_manager.validate_session("invalid_id", self.device_info)
    
    def test_concurrent_session_limits(self):
        """Test concurrent session limits."""
        user_id = "user123"
        
        # Create maximum allowed sessions
        sessions = []
        for i in range(6):  # Exceeds default limit of 5
            device = DeviceInfo(
                device_id=f"device_{i}",
                user_agent="Test Browser",
                ip_address=f"192.168.1.{i}",
                device_type="desktop"
            )
            session = self.session_manager.create_session(user_id, device, "password")
            sessions.append(session)
        
        # Check that old sessions were revoked
        active_sessions = self.session_manager.get_user_sessions(user_id)
        assert len(active_sessions) <= 5
    
    def test_session_revocation(self):
        """Test session revocation."""
        session = self.session_manager.create_session(
            "user123", self.device_info, "password"
        )
        
        # Revoke session
        self.session_manager.revoke_session(session.session_id, "test_revocation")
        
        # Session should no longer be active
        assert not self.session_manager.validate_session(session.session_id, self.device_info)
    
    def test_risk_score_calculation(self):
        """Test session risk score calculation."""
        session = self.session_manager.create_session(
            "user123", self.device_info, "password"
        )
        
        # Add security events
        session.add_security_event("failed_mfa", {"attempts": 2})
        session.add_security_event("location_change", {"new_location": "Unknown"})
        
        # Calculate risk score
        risk_score = session.calculate_risk_score()
        assert risk_score > 0
        assert session.risk_score == risk_score


class TestAuditLogging:
    """Test audit logging functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.audit_logger = AuditLogger()
    
    def test_log_authentication_event(self):
        """Test authentication event logging."""
        event = self.audit_logger.log_authentication_event(
            AuditEventType.LOGIN_SUCCESS,
            "user123",
            "192.168.1.100",
            "Mozilla/5.0 Test Browser",
            "success",
            {"method": "password"}
        )
        
        assert event.event_type == AuditEventType.LOGIN_SUCCESS
        assert event.user_id == "user123"
        assert event.ip_address == "192.168.1.100"
        assert event.result == "success"
        assert event.details["method"] == "password"
    
    def test_security_report_generation(self):
        """Test security report generation."""
        # Log some events
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        self.audit_logger.log_authentication_event(
            AuditEventType.LOGIN_SUCCESS, "user1", "192.168.1.100"
        )
        self.audit_logger.log_authentication_event(
            AuditEventType.LOGIN_FAILURE, "user2", "192.168.1.101"
        )
        
        report = self.audit_logger.generate_security_report(start_time, end_time)
        
        assert "summary" in report
        assert "event_counts" in report
        assert report["summary"]["total_events"] >= 2
    
    def test_anomaly_detection(self):
        """Test security anomaly detection."""
        # Simulate multiple failed logins
        for i in range(6):
            self.audit_logger.log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                "user123",
                "192.168.1.100",
                result="failure"
            )
        
        anomalies = self.audit_logger.detect_anomalies(timedelta(hours=1))
        
        # Should detect brute force attempt
        brute_force_anomalies = [
            a for a in anomalies 
            if a["type"] in ["brute_force_user", "brute_force_ip"]
        ]
        assert len(brute_force_anomalies) > 0


class TestPasswordPolicies:
    """Test password policy enforcement."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.password_validator = PasswordValidator()
        self.lockout_manager = AccountLockoutManager()
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Weak password
        result = self.password_validator.validate_password("123456")
        assert not result["valid"]
        assert result["strength"] == PasswordStrength.VERY_WEAK
        
        # Strong password
        result = self.password_validator.validate_password("MyStr0ng!P@ssw0rd")
        assert result["valid"]
        assert result["strength"].value >= PasswordStrength.GOOD.value
    
    def test_password_policy_compliance(self):
        """Test password policy compliance."""
        # Test various policy violations
        test_cases = [
            ("short", False),  # Too short
            ("nouppercase123!", False),  # No uppercase
            ("NOLOWERCASE123!", False),  # No lowercase
            ("NoNumbers!", False),  # No numbers
            ("NoSpecialChars123", False),  # No special chars
            ("ValidP@ssw0rd123", True),  # Valid password
        ]
        
        for password, should_be_valid in test_cases:
            result = self.password_validator.validate_password(password)
            assert result["valid"] == should_be_valid
    
    def test_user_info_prevention(self):
        """Test prevention of user info in passwords."""
        user_info = {
            "username": "johndoe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Password containing username
        result = self.password_validator.validate_password("johndoe123!", user_info)
        assert not result["valid"]
        
        # Password not containing user info
        result = self.password_validator.validate_password("SecureP@ss123", user_info)
        assert result["valid"]
    
    def test_account_lockout(self):
        """Test account lockout functionality."""
        user_id = "user123"
        ip_address = "192.168.1.100"
        
        # Simulate failed login attempts
        for i in range(5):
            result = self.lockout_manager.record_login_attempt(
                user_id, ip_address, False
            )
        
        # Account should be locked after 5 failed attempts
        assert self.lockout_manager.is_account_locked(user_id)
        
        # Get lockout info
        lockout_info = self.lockout_manager.get_lockout_info(user_id)
        assert lockout_info is not None
        assert lockout_info["reason"] == "failed_attempts"
    
    def test_successful_login_resets_attempts(self):
        """Test that successful login resets failed attempts."""
        user_id = "user123"
        ip_address = "192.168.1.100"
        
        # Failed attempts
        for i in range(3):
            self.lockout_manager.record_login_attempt(user_id, ip_address, False)
        
        # Successful login
        self.lockout_manager.record_login_attempt(user_id, ip_address, True)
        
        # Failed attempts should be reset
        failed_count = self.lockout_manager.get_failed_attempts_count(user_id)
        assert failed_count == 0


class TestMFAProviders:
    """Test MFA provider functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.totp_provider = TOTPProvider()
        self.sms_provider = SMSProvider()
        self.email_provider = EmailProvider()
    
    def test_totp_setup(self):
        """Test TOTP setup."""
        setup_data = self.totp_provider.setup_user_totp("user123", "user@example.com")
        
        assert "secret" in setup_data
        assert "qr_code" in setup_data
        assert "setup_instructions" in setup_data
        assert len(setup_data["secret"]) > 0
    
    def test_totp_challenge_generation(self):
        """Test TOTP challenge generation."""
        secret = self.totp_provider.generate_secret()
        result = self.totp_provider.generate_challenge("user123", secret)
        
        assert result.success
        assert result.challenge_id is not None
        assert "expires_in" in result.metadata
    
    def test_totp_code_verification(self):
        """Test TOTP code verification."""
        secret = self.totp_provider.generate_secret()
        challenge_result = self.totp_provider.generate_challenge("user123", secret)
        
        # Generate valid TOTP code
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        # Verify code
        verify_result = self.totp_provider.verify_challenge(
            challenge_result.challenge_id, valid_code
        )
        
        assert verify_result.success
    
    def test_sms_challenge_generation(self):
        """Test SMS challenge generation."""
        with patch.object(self.sms_provider, '_send_sms', return_value={"success": True}):
            result = self.sms_provider.generate_challenge("user123", "+1234567890")
            
            assert result.success
            assert result.challenge_id is not None
    
    def test_sms_rate_limiting(self):
        """Test SMS rate limiting."""
        user_id = "user123"
        phone_number = "+1234567890"
        
        with patch.object(self.sms_provider, '_send_sms', return_value={"success": True}):
            # Send multiple SMS within rate limit
            for i in range(6):  # Exceeds default limit of 5
                result = self.sms_provider.generate_challenge(user_id, phone_number)
                
                if i >= 5:  # Should be rate limited
                    assert not result.success
                    assert "rate limit" in result.message.lower()
    
    def test_email_challenge_generation(self):
        """Test email challenge generation."""
        with patch.object(self.email_provider, '_send_email', return_value={"success": True}):
            result = self.email_provider.generate_challenge("user123", "user@example.com")
            
            assert result.success
            assert result.challenge_id is not None
    
    def test_mfa_challenge_expiration(self):
        """Test MFA challenge expiration."""
        # Create challenge with short expiration
        config = {"code_lifetime": 1}  # 1 second
        provider = TOTPProvider(config)
        
        secret = provider.generate_secret()
        challenge_result = provider.generate_challenge("user123", secret)
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Challenge should be expired
        challenge = provider.get_challenge(challenge_result.challenge_id)
        assert not challenge.is_valid
    
    def test_backup_codes_generation(self):
        """Test backup codes generation."""
        backup_codes = self.totp_provider.generate_backup_codes(10)
        
        assert len(backup_codes) == 10
        assert all(len(code) > 0 for code in backup_codes)
        assert len(set(backup_codes)) == 10  # All codes should be unique


class TestIntegration:
    """Integration tests for combined functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.session_manager = SessionManager()
        self.audit_logger = AuditLogger()
        self.lockout_manager = AccountLockoutManager()
        self.totp_provider = TOTPProvider()
    
    def test_complete_authentication_flow(self):
        """Test complete authentication flow with MFA."""
        user_id = "user123"
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0 Test Browser"
        
        # 1. Initial login attempt (password only)
        device_info = DeviceInfo(
            device_id="test_device",
            user_agent=user_agent,
            ip_address=ip_address,
            device_type="desktop"
        )
        
        # Record successful password authentication
        self.lockout_manager.record_login_attempt(user_id, ip_address, True, user_agent)
        
        # 2. Setup MFA
        secret = self.totp_provider.generate_secret()
        setup_data = self.totp_provider.setup_user_totp(user_id, "user@example.com")
        
        # 3. Verify MFA setup
        challenge_result = self.totp_provider.generate_challenge(user_id, secret)
        
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        verify_result = self.totp_provider.verify_challenge(
            challenge_result.challenge_id, valid_code
        )
        assert verify_result.success
        
        # 4. Create authenticated session
        session = self.session_manager.create_session(
            user_id, device_info, "password_mfa"
        )
        
        # 5. Log successful authentication
        self.audit_logger.log_authentication_event(
            AuditEventType.LOGIN_SUCCESS,
            user_id,
            ip_address,
            user_agent,
            "success",
            {"method": "password_mfa", "session_id": session.session_id}
        )
        
        # Verify complete flow
        assert session.is_active
        assert session.login_method == "password_mfa"
        assert not self.lockout_manager.is_account_locked(user_id)
    
    def test_security_incident_response(self):
        """Test security incident detection and response."""
        user_id = "user123"
        ip_address = "192.168.1.100"
        
        # Simulate brute force attack
        for i in range(10):
            self.lockout_manager.record_login_attempt(user_id, ip_address, False)
            
            self.audit_logger.log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                user_id,
                ip_address,
                result="failure"
            )
        
        # Check that account is locked
        assert self.lockout_manager.is_account_locked(user_id)
        
        # Check that anomalies are detected
        anomalies = self.audit_logger.detect_anomalies(timedelta(hours=1))
        assert len(anomalies) > 0
        
        # Verify security events are logged
        events = self.audit_logger.get_events(
            user_id=user_id,
            event_types=[AuditEventType.LOGIN_FAILURE]
        )
        assert len(events) >= 10


if __name__ == "__main__":
    pytest.main([__file__])
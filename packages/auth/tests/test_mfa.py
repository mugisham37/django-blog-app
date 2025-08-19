"""
Tests for Multi-Factor Authentication providers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from auth_package.mfa import TOTPProvider, SMSProvider, EmailProvider
from auth_package.mfa.base import MFAProvider, MFAChallenge, MFAResult, MFAStatus


class TestTOTPProvider:
    """Test TOTP MFA provider."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.totp = TOTPProvider()
    
    def test_generate_secret(self):
        """Test TOTP secret generation."""
        secret = self.totp.generate_secret()
        
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded secret
    
    @patch('qrcode.QRCode')
    def test_generate_qr_code(self, mock_qr):
        """Test QR code generation."""
        mock_qr_instance = Mock()
        mock_img = Mock()
        mock_qr_instance.make_image.return_value = mock_img
        mock_qr.return_value = mock_qr_instance
        
        secret = "JBSWY3DPEHPK3PXP"
        qr_code = self.totp.generate_qr_code(secret, "user@example.com")
        
        mock_qr.assert_called_once()
        mock_qr_instance.add_data.assert_called_once()
        mock_qr_instance.make.assert_called_once()
    
    def test_generate_challenge(self):
        """Test TOTP challenge generation."""
        secret = "JBSWY3DPEHPK3PXP"
        result = self.totp.generate_challenge("user123", secret)
        
        assert result.success is True
        assert result.challenge_id is not None
        assert "TOTP challenge generated" in result.message
        assert result.metadata["expires_in"] == 300
        assert result.metadata["digits"] == 6
    
    @patch('pyotp.TOTP.verify')
    def test_verify_challenge_success(self, mock_verify):
        """Test successful TOTP verification."""
        mock_verify.return_value = True
        
        secret = "JBSWY3DPEHPK3PXP"
        challenge_result = self.totp.generate_challenge("user123", secret)
        
        result = self.totp.verify_challenge(challenge_result.challenge_id, "123456")
        
        assert result.success is True
        assert "verified successfully" in result.message
        mock_verify.assert_called_once_with("123456", valid_window=1)
    
    @patch('pyotp.TOTP.verify')
    def test_verify_challenge_failure(self, mock_verify):
        """Test failed TOTP verification."""
        mock_verify.return_value = False
        
        secret = "JBSWY3DPEHPK3PXP"
        challenge_result = self.totp.generate_challenge("user123", secret)
        
        result = self.totp.verify_challenge(challenge_result.challenge_id, "wrong_code")
        
        assert result.success is False
        assert "Invalid TOTP code" in result.message
    
    def test_verify_invalid_challenge(self):
        """Test verification with invalid challenge ID."""
        result = self.totp.verify_challenge("invalid_id", "123456")
        
        assert result.success is False
        assert "Invalid challenge ID" in result.message
    
    def test_setup_user_totp(self):
        """Test TOTP setup for user."""
        with patch.object(self.totp, 'generate_secret', return_value="TESTSECRET"):
            with patch.object(self.totp, 'generate_qr_code', return_value=b"qr_data"):
                setup_data = self.totp.setup_user_totp("user123", "user@example.com")
                
                assert setup_data["secret"] == "TESTSECRET"
                assert "qr_code" in setup_data
                assert "setup_instructions" in setup_data
                assert len(setup_data["setup_instructions"]) > 0
    
    def test_validate_backup_codes(self):
        """Test backup code validation."""
        backup_codes = ["ABCD-1234", "EFGH-5678"]
        
        # Valid code
        assert self.totp.validate_backup_codes("user123", backup_codes, "ABCD-1234") is True
        
        # Invalid code
        assert self.totp.validate_backup_codes("user123", backup_codes, "WRONG-CODE") is False
        
        # Case insensitive
        assert self.totp.validate_backup_codes("user123", backup_codes, "abcd-1234") is True
    
    def test_generate_backup_codes(self):
        """Test backup code generation."""
        codes = self.totp.generate_backup_codes(5)
        
        assert len(codes) == 5
        for code in codes:
            assert len(code) == 9  # Format: XXXX-XXXX
            assert "-" in code


class TestSMSProvider:
    """Test SMS MFA provider."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.sms_config = {
            "provider": "custom",  # Use custom for testing
            "code_length": 6,
            "rate_limit": 5
        }
        self.sms = SMSProvider(self.sms_config)
    
    def test_validate_phone_number(self):
        """Test phone number validation."""
        # Valid numbers
        assert self.sms._validate_phone_number("+1234567890") is True
        assert self.sms._validate_phone_number("+447700900123") is True
        
        # Invalid numbers
        assert self.sms._validate_phone_number("1234567890") is False  # No +
        assert self.sms._validate_phone_number("+0123456789") is False  # Starts with 0
        assert self.sms._validate_phone_number("invalid") is False
    
    def test_check_rate_limit(self):
        """Test SMS rate limiting."""
        user_id = "user123"
        
        # Should be within limit initially
        assert self.sms._check_rate_limit(user_id) is True
        
        # Simulate sending multiple SMS
        for _ in range(5):
            self.sms._record_sms_sent(user_id)
        
        # Should exceed limit
        assert self.sms._check_rate_limit(user_id) is False
    
    def test_generate_code(self):
        """Test SMS code generation."""
        code = self.sms._generate_code()
        
        assert len(code) == 6
        assert code.isdigit()
    
    @patch.object(SMSProvider, '_send_sms')
    def test_generate_challenge_success(self, mock_send):
        """Test successful SMS challenge generation."""
        mock_send.return_value = True
        
        result = self.sms.generate_challenge("user123", "+1234567890")
        
        assert result.success is True
        assert result.challenge_id is not None
        assert "Verification code sent" in result.message
        mock_send.assert_called_once()
    
    @patch.object(SMSProvider, '_send_sms')
    def test_generate_challenge_failure(self, mock_send):
        """Test failed SMS challenge generation."""
        mock_send.return_value = False
        
        result = self.sms.generate_challenge("user123", "+1234567890")
        
        assert result.success is False
        assert "Failed to send SMS" in result.message
    
    def test_generate_challenge_invalid_phone(self):
        """Test SMS challenge with invalid phone number."""
        result = self.sms.generate_challenge("user123", "invalid_phone")
        
        assert result.success is False
        assert "Invalid phone number format" in result.message
    
    @patch.object(SMSProvider, '_send_sms')
    def test_verify_challenge_success(self, mock_send):
        """Test successful SMS verification."""
        mock_send.return_value = True
        
        # Generate challenge
        challenge_result = self.sms.generate_challenge("user123", "+1234567890")
        
        # Get the generated code from the challenge
        challenge = self.sms.get_challenge(challenge_result.challenge_id)
        correct_code = challenge.metadata["code"]
        
        result = self.sms.verify_challenge(challenge_result.challenge_id, correct_code)
        
        assert result.success is True
        assert "verified successfully" in result.message
    
    @patch.object(SMSProvider, '_send_sms')
    def test_verify_challenge_failure(self, mock_send):
        """Test failed SMS verification."""
        mock_send.return_value = True
        
        challenge_result = self.sms.generate_challenge("user123", "+1234567890")
        
        result = self.sms.verify_challenge(challenge_result.challenge_id, "wrong_code")
        
        assert result.success is False
        assert "Invalid SMS code" in result.message
    
    @patch.object(SMSProvider, '_send_sms')
    def test_resend_code(self, mock_send):
        """Test SMS code resending."""
        mock_send.return_value = True
        
        challenge_result = self.sms.generate_challenge("user123", "+1234567890")
        
        result = self.sms.resend_code(challenge_result.challenge_id)
        
        assert result.success is True
        assert "resent successfully" in result.message


class TestEmailProvider:
    """Test Email MFA provider."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.email_config = {
            "smtp_host": "localhost",
            "smtp_port": 587,
            "from_email": "test@example.com",
            "code_length": 6,
            "rate_limit": 10
        }
        self.email = EmailProvider(self.email_config)
    
    def test_validate_email(self):
        """Test email validation."""
        # Valid emails
        assert self.email._validate_email("user@example.com") is True
        assert self.email._validate_email("test.user+tag@domain.co.uk") is True
        
        # Invalid emails
        assert self.email._validate_email("invalid_email") is False
        assert self.email._validate_email("@example.com") is False
        assert self.email._validate_email("user@") is False
    
    def test_generate_code(self):
        """Test email code generation."""
        code = self.email._generate_code()
        
        assert len(code) == 6
        assert code.isalnum()
        assert code.isupper()
    
    def test_mask_email(self):
        """Test email masking for security."""
        assert self.email._mask_email("user@example.com") == "u**r@example.com"
        assert self.email._mask_email("a@example.com") == "*@example.com"
        assert self.email._mask_email("ab@example.com") == "**@example.com"
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        message = self.email._create_email_message("user@example.com", "123456")
        result = self.email._send_email("user@example.com", message)
        
        assert result is True
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test failed email sending."""
        mock_smtp.side_effect = Exception("SMTP Error")
        
        message = self.email._create_email_message("user@example.com", "123456")
        result = self.email._send_email("user@example.com", message)
        
        assert result is False
    
    @patch.object(EmailProvider, '_send_email')
    def test_generate_challenge_success(self, mock_send):
        """Test successful email challenge generation."""
        mock_send.return_value = True
        
        result = self.email.generate_challenge("user123", "user@example.com")
        
        assert result.success is True
        assert result.challenge_id is not None
        assert "Verification code sent" in result.message
        mock_send.assert_called_once()
    
    def test_generate_challenge_invalid_email(self):
        """Test email challenge with invalid email."""
        result = self.email.generate_challenge("user123", "invalid_email")
        
        assert result.success is False
        assert "Invalid email address format" in result.message
    
    def test_set_templates(self):
        """Test setting custom email templates."""
        html_template = "<p>Your code is: {code}</p>"
        text_template = "Your code is: {code}"
        
        self.email.set_html_template(html_template)
        self.email.set_text_template(text_template)
        
        assert self.email.config["html_template"] == html_template
        assert self.email.config["text_template"] == text_template


class TestMFAChallenge:
    """Test MFA challenge data structure."""
    
    def test_challenge_creation(self):
        """Test MFA challenge creation."""
        challenge = MFAChallenge(
            challenge_id="test_id",
            user_id="user123",
            provider_type="totp",
            status=MFAStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        assert challenge.challenge_id == "test_id"
        assert challenge.user_id == "user123"
        assert challenge.provider_type == "totp"
        assert challenge.status == MFAStatus.PENDING
        assert challenge.attempts == 0
        assert challenge.max_attempts == 3
        assert challenge.metadata == {}
    
    def test_challenge_expiration(self):
        """Test challenge expiration logic."""
        # Not expired
        challenge = MFAChallenge(
            challenge_id="test_id",
            user_id="user123",
            provider_type="totp",
            status=MFAStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        assert challenge.is_expired is False
        assert challenge.is_valid is True
        
        # Expired
        expired_challenge = MFAChallenge(
            challenge_id="test_id",
            user_id="user123",
            provider_type="totp",
            status=MFAStatus.PENDING,
            created_at=datetime.utcnow() - timedelta(minutes=10),
            expires_at=datetime.utcnow() - timedelta(minutes=5)
        )
        
        assert expired_challenge.is_expired is True
        assert expired_challenge.is_valid is False


class TestMFAResult:
    """Test MFA result data structure."""
    
    def test_result_creation(self):
        """Test MFA result creation."""
        result = MFAResult(
            success=True,
            message="Operation successful",
            challenge_id="test_id",
            metadata={"key": "value"}
        )
        
        assert result.success is True
        assert result.message == "Operation successful"
        assert result.challenge_id == "test_id"
        assert result.metadata == {"key": "value"}
    
    def test_result_defaults(self):
        """Test MFA result with defaults."""
        result = MFAResult(
            success=False,
            message="Operation failed"
        )
        
        assert result.success is False
        assert result.message == "Operation failed"
        assert result.challenge_id is None
        assert result.metadata == {}
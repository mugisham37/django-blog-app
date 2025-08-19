"""
SMS-based MFA provider.
"""

import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .base import MFAProvider, MFAChallenge, MFAResult, MFAStatus


class SMSProvider(MFAProvider):
    """
    SMS-based MFA provider.
    
    Sends verification codes via SMS using configurable SMS gateway.
    Supports multiple SMS providers (Twilio, AWS SNS, etc.).
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            "provider": "twilio",  # twilio, aws_sns, custom
            "code_length": 6,
            "code_lifetime": 300,  # 5 minutes
            "max_attempts": 3,
            "rate_limit": 5,  # max SMS per hour per user
            "message_template": "Your verification code is: {code}. Valid for {minutes} minutes."
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("sms", default_config)
        self._rate_limits = {}  # Track SMS sending rates
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            True if phone number is valid
        """
        # Basic E.164 format validation
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number))
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded SMS rate limit.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if within rate limit
        """
        current_time = datetime.utcnow()
        hour_ago = current_time - timedelta(hours=1)
        
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []
        
        # Clean old entries
        self._rate_limits[user_id] = [
            timestamp for timestamp in self._rate_limits[user_id]
            if timestamp > hour_ago
        ]
        
        # Check current count
        return len(self._rate_limits[user_id]) < self.config["rate_limit"]
    
    def _record_sms_sent(self, user_id: str):
        """Record SMS sent for rate limiting."""
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []
        
        self._rate_limits[user_id].append(datetime.utcnow())
    
    def _generate_code(self) -> str:
        """Generate random verification code."""
        code_length = self.config["code_length"]
        # Generate numeric code
        code = ''.join([str(secrets.randbelow(10)) for _ in range(code_length)])
        return code
    
    def _send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS message.
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            
        Returns:
            True if SMS was sent successfully
        """
        provider = self.config["provider"]
        
        if provider == "twilio":
            return self._send_twilio_sms(phone_number, message)
        elif provider == "aws_sns":
            return self._send_aws_sns_sms(phone_number, message)
        elif provider == "custom":
            return self._send_custom_sms(phone_number, message)
        else:
            raise ValueError(f"Unsupported SMS provider: {provider}")
    
    def _send_twilio_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via Twilio."""
        try:
            from twilio.rest import Client
            
            account_sid = self.config.get("twilio_account_sid")
            auth_token = self.config.get("twilio_auth_token")
            from_number = self.config.get("twilio_from_number")
            
            if not all([account_sid, auth_token, from_number]):
                raise ValueError("Missing Twilio configuration")
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            
            return message.sid is not None
            
        except Exception as e:
            print(f"Error sending Twilio SMS: {e}")
            return False
    
    def _send_aws_sns_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via AWS SNS."""
        try:
            import boto3
            
            sns = boto3.client(
                'sns',
                aws_access_key_id=self.config.get("aws_access_key_id"),
                aws_secret_access_key=self.config.get("aws_secret_access_key"),
                region_name=self.config.get("aws_region", "us-east-1")
            )
            
            response = sns.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            
            return response.get("MessageId") is not None
            
        except Exception as e:
            print(f"Error sending AWS SNS SMS: {e}")
            return False
    
    def _send_custom_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS via custom provider."""
        # Implement custom SMS provider logic here
        # For demo purposes, we'll just log the message
        print(f"SMS to {phone_number}: {message}")
        return True
    
    def generate_challenge(self, user_id: str, phone_number: str, **kwargs) -> MFAResult:
        """
        Generate SMS challenge.
        
        Args:
            user_id: User identifier
            phone_number: User's phone number
            **kwargs: Additional parameters
            
        Returns:
            MFAResult with challenge information
        """
        # Validate phone number
        if not self._validate_phone_number(phone_number):
            return MFAResult(
                success=False,
                message="Invalid phone number format. Use E.164 format (+1234567890)"
            )
        
        # Check rate limit
        if not self._check_rate_limit(user_id):
            return MFAResult(
                success=False,
                message=f"SMS rate limit exceeded. Maximum {self.config['rate_limit']} SMS per hour."
            )
        
        # Generate challenge
        challenge_id = secrets.token_urlsafe(32)
        code = self._generate_code()
        
        challenge = MFAChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            provider_type=self.name,
            status=MFAStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.config["code_lifetime"]),
            max_attempts=self.config["max_attempts"],
            metadata={
                "code": code,
                "phone_number": phone_number
            }
        )
        
        # Send SMS
        minutes = self.config["code_lifetime"] // 60
        message = self.config["message_template"].format(
            code=code,
            minutes=minutes
        )
        
        if self._send_sms(phone_number, message):
            self.store_challenge(challenge)
            self._record_sms_sent(user_id)
            
            return MFAResult(
                success=True,
                message=f"Verification code sent to {phone_number[-4:].rjust(len(phone_number), '*')}",
                challenge_id=challenge_id,
                metadata={
                    "expires_in": self.config["code_lifetime"],
                    "code_length": self.config["code_length"]
                }
            )
        else:
            return MFAResult(
                success=False,
                message="Failed to send SMS. Please try again later."
            )
    
    def verify_challenge(self, challenge_id: str, code: str) -> MFAResult:
        """
        Verify SMS code.
        
        Args:
            challenge_id: Challenge identifier
            code: SMS verification code
            
        Returns:
            MFAResult with verification status
        """
        challenge = self.get_challenge(challenge_id)
        
        if not challenge:
            return MFAResult(
                success=False,
                message="Invalid challenge ID"
            )
        
        if not challenge.is_valid:
            return MFAResult(
                success=False,
                message="Challenge has expired or exceeded maximum attempts"
            )
        
        # Increment attempt counter
        challenge.attempts += 1
        
        # Verify code
        expected_code = challenge.metadata["code"]
        entered_code = code.strip()
        
        if expected_code == entered_code:
            challenge.status = MFAStatus.VERIFIED
            return MFAResult(
                success=True,
                message="SMS code verified successfully",
                challenge_id=challenge_id
            )
        else:
            if challenge.attempts >= challenge.max_attempts:
                challenge.status = MFAStatus.FAILED
                return MFAResult(
                    success=False,
                    message="Invalid SMS code. Maximum attempts exceeded."
                )
            else:
                return MFAResult(
                    success=False,
                    message=f"Invalid SMS code. {challenge.max_attempts - challenge.attempts} attempts remaining."
                )
    
    def resend_code(self, challenge_id: str) -> MFAResult:
        """
        Resend SMS code for existing challenge.
        
        Args:
            challenge_id: Challenge identifier
            
        Returns:
            MFAResult with resend status
        """
        challenge = self.get_challenge(challenge_id)
        
        if not challenge:
            return MFAResult(
                success=False,
                message="Invalid challenge ID"
            )
        
        if not challenge.is_valid:
            return MFAResult(
                success=False,
                message="Challenge has expired or exceeded maximum attempts"
            )
        
        # Check rate limit
        if not self._check_rate_limit(challenge.user_id):
            return MFAResult(
                success=False,
                message=f"SMS rate limit exceeded. Maximum {self.config['rate_limit']} SMS per hour."
            )
        
        # Resend SMS
        phone_number = challenge.metadata["phone_number"]
        code = challenge.metadata["code"]
        minutes = self.config["code_lifetime"] // 60
        
        message = self.config["message_template"].format(
            code=code,
            minutes=minutes
        )
        
        if self._send_sms(phone_number, message):
            self._record_sms_sent(challenge.user_id)
            return MFAResult(
                success=True,
                message="Verification code resent successfully"
            )
        else:
            return MFAResult(
                success=False,
                message="Failed to resend SMS. Please try again later."
            )
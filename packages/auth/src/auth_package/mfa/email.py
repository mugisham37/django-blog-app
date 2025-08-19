"""
Email-based MFA provider.
"""

import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from .base import MFAProvider, MFAChallenge, MFAResult, MFAStatus


class EmailProvider(MFAProvider):
    """
    Email-based MFA provider.
    
    Sends verification codes via email using configurable SMTP settings.
    Supports HTML and plain text email templates.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            "smtp_host": "localhost",
            "smtp_port": 587,
            "smtp_use_tls": True,
            "smtp_username": "",
            "smtp_password": "",
            "from_email": "noreply@example.com",
            "from_name": "Enterprise App",
            "code_length": 6,
            "code_lifetime": 600,  # 10 minutes
            "max_attempts": 3,
            "rate_limit": 10,  # max emails per hour per user
            "subject_template": "Your verification code",
            "html_template": None,
            "text_template": "Your verification code is: {code}\n\nThis code will expire in {minutes} minutes."
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("email", default_config)
        self._rate_limits = {}  # Track email sending rates
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded email rate limit.
        
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
    
    def _record_email_sent(self, user_id: str):
        """Record email sent for rate limiting."""
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []
        
        self._rate_limits[user_id].append(datetime.utcnow())
    
    def _generate_code(self) -> str:
        """Generate random verification code."""
        code_length = self.config["code_length"]
        # Generate alphanumeric code
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        code = ''.join([secrets.choice(chars) for _ in range(code_length)])
        return code
    
    def _create_email_message(self, to_email: str, code: str) -> MIMEMultipart:
        """
        Create email message with verification code.
        
        Args:
            to_email: Recipient email address
            code: Verification code
            
        Returns:
            Email message object
        """
        minutes = self.config["code_lifetime"] // 60
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.config["subject_template"]
        msg['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
        msg['To'] = to_email
        
        # Plain text version
        text_content = self.config["text_template"].format(
            code=code,
            minutes=minutes
        )
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # HTML version (if template provided)
        if self.config.get("html_template"):
            html_content = self.config["html_template"].format(
                code=code,
                minutes=minutes
            )
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
        
        return msg
    
    def _send_email(self, to_email: str, message: MIMEMultipart) -> bool:
        """
        Send email message via SMTP.
        
        Args:
            to_email: Recipient email address
            message: Email message object
            
        Returns:
            True if email was sent successfully
        """
        try:
            # Create SMTP connection
            if self.config["smtp_use_tls"]:
                server = smtplib.SMTP(self.config["smtp_host"], self.config["smtp_port"])
                server.starttls()
            else:
                server = smtplib.SMTP(self.config["smtp_host"], self.config["smtp_port"])
            
            # Login if credentials provided
            if self.config["smtp_username"] and self.config["smtp_password"]:
                server.login(self.config["smtp_username"], self.config["smtp_password"])
            
            # Send email
            server.send_message(message, to_addrs=[to_email])
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def generate_challenge(self, user_id: str, email: str, **kwargs) -> MFAResult:
        """
        Generate email challenge.
        
        Args:
            user_id: User identifier
            email: User's email address
            **kwargs: Additional parameters
            
        Returns:
            MFAResult with challenge information
        """
        # Validate email
        if not self._validate_email(email):
            return MFAResult(
                success=False,
                message="Invalid email address format"
            )
        
        # Check rate limit
        if not self._check_rate_limit(user_id):
            return MFAResult(
                success=False,
                message=f"Email rate limit exceeded. Maximum {self.config['rate_limit']} emails per hour."
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
                "email": email
            }
        )
        
        # Send email
        message = self._create_email_message(email, code)
        
        if self._send_email(email, message):
            self.store_challenge(challenge)
            self._record_email_sent(user_id)
            
            # Mask email for security
            masked_email = self._mask_email(email)
            
            return MFAResult(
                success=True,
                message=f"Verification code sent to {masked_email}",
                challenge_id=challenge_id,
                metadata={
                    "expires_in": self.config["code_lifetime"],
                    "code_length": self.config["code_length"]
                }
            )
        else:
            return MFAResult(
                success=False,
                message="Failed to send email. Please try again later."
            )
    
    def verify_challenge(self, challenge_id: str, code: str) -> MFAResult:
        """
        Verify email code.
        
        Args:
            challenge_id: Challenge identifier
            code: Email verification code
            
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
        
        # Verify code (case-insensitive)
        expected_code = challenge.metadata["code"].upper()
        entered_code = code.strip().upper()
        
        if expected_code == entered_code:
            challenge.status = MFAStatus.VERIFIED
            return MFAResult(
                success=True,
                message="Email code verified successfully",
                challenge_id=challenge_id
            )
        else:
            if challenge.attempts >= challenge.max_attempts:
                challenge.status = MFAStatus.FAILED
                return MFAResult(
                    success=False,
                    message="Invalid email code. Maximum attempts exceeded."
                )
            else:
                return MFAResult(
                    success=False,
                    message=f"Invalid email code. {challenge.max_attempts - challenge.attempts} attempts remaining."
                )
    
    def resend_code(self, challenge_id: str) -> MFAResult:
        """
        Resend email code for existing challenge.
        
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
                message=f"Email rate limit exceeded. Maximum {self.config['rate_limit']} emails per hour."
            )
        
        # Resend email
        email = challenge.metadata["email"]
        code = challenge.metadata["code"]
        message = self._create_email_message(email, code)
        
        if self._send_email(email, message):
            self._record_email_sent(challenge.user_id)
            masked_email = self._mask_email(email)
            return MFAResult(
                success=True,
                message=f"Verification code resent to {masked_email}"
            )
        else:
            return MFAResult(
                success=False,
                message="Failed to resend email. Please try again later."
            )
    
    def _mask_email(self, email: str) -> str:
        """
        Mask email address for security.
        
        Args:
            email: Email address to mask
            
        Returns:
            Masked email address
        """
        if '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    def set_html_template(self, template: str):
        """
        Set custom HTML email template.
        
        Args:
            template: HTML template with {code} and {minutes} placeholders
        """
        self.config["html_template"] = template
    
    def set_text_template(self, template: str):
        """
        Set custom text email template.
        
        Args:
            template: Text template with {code} and {minutes} placeholders
        """
        self.config["text_template"] = template
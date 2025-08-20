"""
Email-based MFA provider.
"""

import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .base import MFAProvider, MFAChallenge, MFAResult, MFAStatus


class EmailProvider(MFAProvider):
    """
    Email-based MFA provider.
    
    Sends verification codes via email using configurable email services
    like SMTP, SendGrid, AWS SES, or other email gateways.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            "service": "smtp",  # smtp, sendgrid, aws_ses, custom
            "code_length": 6,
            "code_lifetime": 600,  # 10 minutes
            "max_attempts": 3,
            "rate_limit": 3,  # max emails per hour per user
            "subject_template": "Your verification code",
            "message_template": """
Your verification code is: {code}

This code will expire in {minutes} minutes.

If you didn't request this code, please ignore this email.
            """.strip(),
            "html_template": """
<html>
<body>
    <h2>Email Verification</h2>
    <p>Your verification code is: <strong>{code}</strong></p>
    <p>This code will expire in {minutes} minutes.</p>
    <p>If you didn't request this code, please ignore this email.</p>
</body>
</html>
            """.strip()
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
        characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        code = ''.join([secrets.choice(characters) for _ in range(code_length)])
        return code
    
    def _send_email(self, email: str, subject: str, text_body: str, html_body: str = None) -> Dict[str, Any]:
        """
        Send email message.
        
        Args:
            email: Recipient email address
            subject: Email subject
            text_body: Plain text email body
            html_body: HTML email body (optional)
            
        Returns:
            Dictionary with success status and details
        """
        service = self.config["service"]
        
        try:
            if service == "smtp":
                return self._send_smtp_email(email, subject, text_body, html_body)
            elif service == "sendgrid":
                return self._send_sendgrid_email(email, subject, text_body, html_body)
            elif service == "aws_ses":
                return self._send_aws_ses_email(email, subject, text_body, html_body)
            elif service == "custom":
                return self._send_custom_email(email, subject, text_body, html_body)
            else:
                return {"success": False, "error": f"Unsupported email service: {service}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_smtp_email(self, email: str, subject: str, text_body: str, html_body: str = None) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_host = self.config.get("smtp_host")
            smtp_port = self.config.get("smtp_port", 587)
            smtp_username = self.config.get("smtp_username")
            smtp_password = self.config.get("smtp_password")
            from_email = self.config.get("from_email", smtp_username)
            
            if not all([smtp_host, smtp_username, smtp_password]):
                return {"success": False, "error": "Missing SMTP configuration"}
            
            # Create message
            if html_body:
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(text_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))
            else:
                msg = MIMEText(text_body, "plain")
            
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = email
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            return {"success": True, "message_id": f"smtp_{datetime.utcnow().timestamp()}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_sendgrid_email(self, email: str, subject: str, text_body: str, html_body: str = None) -> Dict[str, Any]:
        """Send email via SendGrid."""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            api_key = self.config.get("sendgrid_api_key")
            from_email = self.config.get("from_email")
            
            if not all([api_key, from_email]):
                return {"success": False, "error": "Missing SendGrid configuration"}
            
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            
            mail = Mail(
                from_email=from_email,
                to_emails=email,
                subject=subject,
                plain_text_content=text_body,
                html_content=html_body
            )
            
            response = sg.send(mail)
            
            return {
                "success": True,
                "message_id": response.headers.get("X-Message-Id"),
                "status_code": response.status_code
            }
            
        except ImportError:
            return {"success": False, "error": "SendGrid library not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_aws_ses_email(self, email: str, subject: str, text_body: str, html_body: str = None) -> Dict[str, Any]:
        """Send email via AWS SES."""
        try:
            import boto3
            
            region = self.config.get("aws_region", "us-east-1")
            access_key = self.config.get("aws_access_key_id")
            secret_key = self.config.get("aws_secret_access_key")
            from_email = self.config.get("from_email")
            
            if not from_email:
                return {"success": False, "error": "Missing from_email configuration"}
            
            if access_key and secret_key:
                ses = boto3.client(
                    'ses',
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
            else:
                # Use default credentials
                ses = boto3.client('ses', region_name=region)
            
            # Prepare email content
            destination = {"ToAddresses": [email]}
            message = {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": text_body}}
            }
            
            if html_body:
                message["Body"]["Html"] = {"Data": html_body}
            
            response = ses.send_email(
                Source=from_email,
                Destination=destination,
                Message=message
            )
            
            return {"success": True, "message_id": response["MessageId"]}
            
        except ImportError:
            return {"success": False, "error": "boto3 library not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_custom_email(self, email: str, subject: str, text_body: str, html_body: str = None) -> Dict[str, Any]:
        """Send email via custom service."""
        # Implement custom email service integration here
        # For demo purposes, we'll just log the email
        print(f"Email to {email}: {subject}\n{text_body}")
        return {"success": True, "message_id": f"custom_{datetime.utcnow().timestamp()}"}
    
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
        
        # Prepare email content
        minutes = self.config["code_lifetime"] // 60
        subject = self.config["subject_template"]
        
        text_body = self.config["message_template"].format(
            code=code,
            minutes=minutes
        )
        
        html_body = self.config["html_template"].format(
            code=code,
            minutes=minutes
        )
        
        # Send email
        email_result = self._send_email(email, subject, text_body, html_body)
        
        if email_result["success"]:
            self.store_challenge(challenge)
            self._record_email_sent(user_id)
            
            # Mask email for privacy
            masked_email = self._mask_email(email)
            
            return MFAResult(
                success=True,
                message=f"Verification code sent to {masked_email}",
                challenge_id=challenge_id,
                metadata={
                    "expires_in": self.config["code_lifetime"],
                    "code_length": self.config["code_length"],
                    "message_id": email_result.get("message_id")
                }
            )
        else:
            return MFAResult(
                success=False,
                message=f"Failed to send email: {email_result['error']}"
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
        
        if self._constant_time_compare(expected_code, entered_code):
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
        minutes = self.config["code_lifetime"] // 60
        
        subject = self.config["subject_template"]
        text_body = self.config["message_template"].format(
            code=code,
            minutes=minutes
        )
        html_body = self.config["html_template"].format(
            code=code,
            minutes=minutes
        )
        
        email_result = self._send_email(email, subject, text_body, html_body)
        
        if email_result["success"]:
            self._record_email_sent(challenge.user_id)
            return MFAResult(
                success=True,
                message="Verification code resent successfully",
                metadata={"message_id": email_result.get("message_id")}
            )
        else:
            return MFAResult(
                success=False,
                message=f"Failed to resend email: {email_result['error']}"
            )
    
    def _mask_email(self, email: str) -> str:
        """Mask email address for privacy."""
        if "@" not in email:
            return "***@***.***"
        
        local, domain = email.split("@", 1)
        
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        
        if "." in domain:
            domain_parts = domain.split(".")
            masked_domain = domain_parts[0][0] + "*" * (len(domain_parts[0]) - 1)
            if len(domain_parts) > 1:
                masked_domain += "." + domain_parts[-1]
        else:
            masked_domain = domain[0] + "*" * (len(domain) - 1)
        
        return f"{masked_local}@{masked_domain}"
    
    def _constant_time_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison."""
        import hmac
        return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))
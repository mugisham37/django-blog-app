"""
Time-based One-Time Password (TOTP) MFA provider.
"""

import secrets
import base64
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pyotp

from .base import MFAProvider, MFAChallenge, MFAResult, MFAStatus


class TOTPProvider(MFAProvider):
    """
    TOTP (Time-based One-Time Password) MFA provider.
    
    Implements RFC 6238 TOTP algorithm for generating time-based codes
    compatible with authenticator apps like Google Authenticator, Authy, etc.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            "issuer_name": "Enterprise App",
            "digits": 6,
            "interval": 30,  # seconds
            "challenge_lifetime": 300,  # 5 minutes
            "max_attempts": 3
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("totp", default_config)
    
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key.
        
        Returns:
            Base32-encoded secret key
        """
        return pyotp.random_base32()
    
    def generate_qr_code(self, secret: str, user_email: str) -> bytes:
        """
        Generate QR code for TOTP setup.
        
        Args:
            secret: TOTP secret key
            user_email: User's email address
            
        Returns:
            QR code image as bytes
        """
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.config["issuer_name"]
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        return img_buffer.getvalue()
    
    def generate_challenge(self, user_id: str, secret: str, **kwargs) -> MFAResult:
        """
        Generate TOTP challenge.
        
        Args:
            user_id: User identifier
            secret: User's TOTP secret key
            **kwargs: Additional parameters
            
        Returns:
            MFAResult with challenge information
        """
        challenge_id = secrets.token_urlsafe(32)
        
        challenge = MFAChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            provider_type=self.name,
            status=MFAStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.config["challenge_lifetime"]),
            max_attempts=self.config["max_attempts"],
            metadata={
                "secret": secret,
                "digits": self.config["digits"],
                "interval": self.config["interval"]
            }
        )
        
        self.store_challenge(challenge)
        
        return MFAResult(
            success=True,
            message="TOTP challenge generated. Enter code from your authenticator app.",
            challenge_id=challenge_id,
            metadata={
                "expires_in": self.config["challenge_lifetime"],
                "digits": self.config["digits"]
            }
        )
    
    def verify_challenge(self, challenge_id: str, code: str) -> MFAResult:
        """
        Verify TOTP code.
        
        Args:
            challenge_id: Challenge identifier
            code: TOTP code from authenticator app
            
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
        
        try:
            secret = challenge.metadata["secret"]
            totp = pyotp.TOTP(
                secret,
                digits=challenge.metadata["digits"],
                interval=challenge.metadata["interval"]
            )
            
            # Verify code with window for clock skew
            is_valid = totp.verify(code, valid_window=1)
            
            if is_valid:
                challenge.status = MFAStatus.VERIFIED
                return MFAResult(
                    success=True,
                    message="TOTP code verified successfully",
                    challenge_id=challenge_id
                )
            else:
                if challenge.attempts >= challenge.max_attempts:
                    challenge.status = MFAStatus.FAILED
                    return MFAResult(
                        success=False,
                        message="Invalid TOTP code. Maximum attempts exceeded."
                    )
                else:
                    return MFAResult(
                        success=False,
                        message=f"Invalid TOTP code. {challenge.max_attempts - challenge.attempts} attempts remaining."
                    )
                    
        except Exception as e:
            challenge.status = MFAStatus.FAILED
            return MFAResult(
                success=False,
                message=f"Error verifying TOTP code: {str(e)}"
            )
    
    def setup_user_totp(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """
        Setup TOTP for a new user.
        
        Args:
            user_id: User identifier
            user_email: User's email address
            
        Returns:
            Dictionary with secret, QR code, and setup instructions
        """
        secret = self.generate_secret()
        qr_code = self.generate_qr_code(secret, user_email)
        
        return {
            "secret": secret,
            "qr_code": base64.b64encode(qr_code).decode('utf-8'),
            "manual_entry_key": secret,
            "issuer": self.config["issuer_name"],
            "digits": self.config["digits"],
            "interval": self.config["interval"],
            "setup_instructions": [
                "1. Install an authenticator app (Google Authenticator, Authy, etc.)",
                "2. Scan the QR code or manually enter the secret key",
                "3. Enter the 6-digit code from your app to verify setup"
            ]
        }
    
    def validate_backup_codes(self, user_id: str, backup_codes: list, entered_code: str) -> bool:
        """
        Validate backup recovery codes.
        
        Args:
            user_id: User identifier
            backup_codes: List of valid backup codes
            entered_code: Code entered by user
            
        Returns:
            True if code is valid
        """
        # Hash comparison to prevent timing attacks
        entered_hash = hash(entered_code.strip().lower())
        
        for code in backup_codes:
            if hash(code.strip().lower()) == entered_hash:
                return True
        
        return False
    
    def generate_backup_codes(self, count: int = 10) -> list:
        """
        Generate backup recovery codes.
        
        Args:
            count: Number of codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        
        return codes
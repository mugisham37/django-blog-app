"""
Django views for advanced authentication features.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from rest_framework import status, permissions
    from rest_framework.decorators import action
    from rest_framework.response import Response
    from rest_framework.views import APIView
    from rest_framework.viewsets import ViewSet
    from django.contrib.auth import get_user_model, authenticate
    from django.utils.decorators import method_decorator
    from django.views.decorators.csrf import csrf_exempt
    from django.http import JsonResponse
    from django.conf import settings
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Create dummy classes for non-Django environments
    class APIView:
        pass
    class ViewSet:
        pass
    class Response:
        pass

from .mfa import TOTPProvider, SMSProvider, EmailProvider
from .session_management import DeviceInfo, default_session_manager
from .audit_logging import AuditEventType, AuditSeverity, default_audit_logger
from .password_policies import default_password_validator, default_lockout_manager
from .strategies import JWTStrategy, JWTConfig
from .security import TokenManager


class MFAViewSet(ViewSet):
    """
    ViewSet for Multi-Factor Authentication operations.
    
    Provides endpoints for TOTP setup, SMS/Email verification,
    and MFA challenge management.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if DJANGO_AVAILABLE:
            self.totp_provider = TOTPProvider()
            self.sms_provider = SMSProvider()
            self.email_provider = EmailProvider()
            self.audit_logger = default_audit_logger
    
    @action(detail=False, methods=['post'])
    def setup_totp(self, request):
        """Setup TOTP for user."""
        user = request.user
        user_email = user.email
        
        try:
            setup_data = self.totp_provider.setup_user_totp(str(user.pk), user_email)
            
            # Log MFA setup
            self.audit_logger.log_event(
                AuditEventType.MFA_ENABLED,
                user_id=str(user.pk),
                ip_address=self._get_client_ip(request),
                details={"mfa_type": "totp"}
            )
            
            return Response({
                "success": True,
                "setup_data": setup_data,
                "message": "TOTP setup initiated. Scan QR code with authenticator app."
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_totp_setup(self, request):
        """Verify TOTP setup with code from authenticator app."""
        user = request.user
        code = request.data.get('code')
        secret = request.data.get('secret')
        
        if not code or not secret:
            return Response({
                "success": False,
                "error": "Code and secret are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Generate challenge to verify setup
            challenge_result = self.totp_provider.generate_challenge(str(user.pk), secret)
            
            if challenge_result.success:
                verify_result = self.totp_provider.verify_challenge(
                    challenge_result.challenge_id, code
                )
                
                if verify_result.success:
                    # Save TOTP secret to user profile (implement based on your user model)
                    # user.totp_secret = secret
                    # user.mfa_enabled = True
                    # user.save()
                    
                    # Generate backup codes
                    backup_codes = self.totp_provider.generate_backup_codes()
                    
                    self.audit_logger.log_event(
                        AuditEventType.MFA_ENABLED,
                        user_id=str(user.pk),
                        ip_address=self._get_client_ip(request),
                        details={"mfa_type": "totp", "setup_completed": True}
                    )
                    
                    return Response({
                        "success": True,
                        "backup_codes": backup_codes,
                        "message": "TOTP setup completed successfully"
                    })
                else:
                    return Response({
                        "success": False,
                        "error": verify_result.message
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "success": False,
                    "error": challenge_result.message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def send_sms_code(self, request):
        """Send SMS verification code."""
        user = request.user
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                "success": False,
                "error": "Phone number is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = self.sms_provider.generate_challenge(str(user.pk), phone_number)
            
            self.audit_logger.log_event(
                AuditEventType.MFA_SUCCESS if result.success else AuditEventType.MFA_FAILURE,
                user_id=str(user.pk),
                ip_address=self._get_client_ip(request),
                details={"mfa_type": "sms", "phone_number": phone_number}
            )
            
            if result.success:
                return Response({
                    "success": True,
                    "challenge_id": result.challenge_id,
                    "message": result.message,
                    "expires_in": result.metadata.get("expires_in")
                })
            else:
                return Response({
                    "success": False,
                    "error": result.message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def send_email_code(self, request):
        """Send email verification code."""
        user = request.user
        email = request.data.get('email', user.email)
        
        try:
            result = self.email_provider.generate_challenge(str(user.pk), email)
            
            self.audit_logger.log_event(
                AuditEventType.MFA_SUCCESS if result.success else AuditEventType.MFA_FAILURE,
                user_id=str(user.pk),
                ip_address=self._get_client_ip(request),
                details={"mfa_type": "email", "email": email}
            )
            
            if result.success:
                return Response({
                    "success": True,
                    "challenge_id": result.challenge_id,
                    "message": result.message,
                    "expires_in": result.metadata.get("expires_in")
                })
            else:
                return Response({
                    "success": False,
                    "error": result.message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_code(self, request):
        """Verify MFA code (SMS, Email, or TOTP)."""
        challenge_id = request.data.get('challenge_id')
        code = request.data.get('code')
        mfa_type = request.data.get('type', 'totp')
        
        if not code:
            return Response({
                "success": False,
                "error": "Verification code is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Select appropriate provider
            if mfa_type == 'sms':
                provider = self.sms_provider
            elif mfa_type == 'email':
                provider = self.email_provider
            else:
                provider = self.totp_provider
            
            if challenge_id:
                result = provider.verify_challenge(challenge_id, code)
            else:
                # For TOTP, generate challenge first
                user = request.user
                # Get user's TOTP secret (implement based on your user model)
                # secret = user.totp_secret
                secret = "dummy_secret"  # Replace with actual secret retrieval
                
                challenge_result = provider.generate_challenge(str(user.pk), secret)
                if challenge_result.success:
                    result = provider.verify_challenge(challenge_result.challenge_id, code)
                else:
                    result = challenge_result
            
            self.audit_logger.log_event(
                AuditEventType.MFA_SUCCESS if result.success else AuditEventType.MFA_FAILURE,
                user_id=str(request.user.pk),
                ip_address=self._get_client_ip(request),
                details={"mfa_type": mfa_type, "challenge_id": challenge_id}
            )
            
            if result.success:
                return Response({
                    "success": True,
                    "message": result.message
                })
            else:
                return Response({
                    "success": False,
                    "error": result.message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class SessionManagementViewSet(ViewSet):
    """
    ViewSet for session management operations.
    
    Provides endpoints for viewing active sessions, revoking sessions,
    and managing device trust.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if DJANGO_AVAILABLE:
            self.session_manager = default_session_manager
            self.audit_logger = default_audit_logger
    
    @action(detail=False, methods=['get'])
    def active_sessions(self, request):
        """Get all active sessions for current user."""
        user = request.user
        
        try:
            sessions = self.session_manager.get_user_sessions(str(user.pk))
            
            session_data = []
            for session in sessions:
                session_info = session.to_dict()
                # Remove sensitive information
                session_info.pop('security_events', None)
                session_data.append(session_info)
            
            return Response({
                "success": True,
                "sessions": session_data,
                "total_count": len(session_data)
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def revoke_session(self, request):
        """Revoke a specific session."""
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                "success": False,
                "error": "Session ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.session_manager.revoke_session(session_id, "user_revoked")
            
            self.audit_logger.log_event(
                AuditEventType.SESSION_REVOKED,
                user_id=str(request.user.pk),
                session_id=session_id,
                ip_address=self._get_client_ip(request),
                details={"reason": "user_revoked"}
            )
            
            return Response({
                "success": True,
                "message": "Session revoked successfully"
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def revoke_all_sessions(self, request):
        """Revoke all sessions except current one."""
        user = request.user
        current_session_id = request.session.get('auth_session_id')
        
        try:
            revoked_count = self.session_manager.revoke_user_sessions(
                str(user.pk), exclude_session=current_session_id
            )
            
            self.audit_logger.log_event(
                AuditEventType.SESSION_REVOKED,
                user_id=str(user.pk),
                ip_address=self._get_client_ip(request),
                details={"reason": "revoke_all", "revoked_count": revoked_count}
            )
            
            return Response({
                "success": True,
                "message": f"Revoked {revoked_count} sessions",
                "revoked_count": revoked_count
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class PasswordPolicyViewSet(ViewSet):
    """
    ViewSet for password policy and validation operations.
    
    Provides endpoints for password validation, strength checking,
    and policy information.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if DJANGO_AVAILABLE:
            self.password_validator = default_password_validator
            self.lockout_manager = default_lockout_manager
    
    @action(detail=False, methods=['post'])
    def validate_password(self, request):
        """Validate password against policy."""
        password = request.data.get('password')
        
        if not password:
            return Response({
                "success": False,
                "error": "Password is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = request.user
            user_info = {
                "username": user.username,
                "email": user.email,
                "first_name": getattr(user, 'first_name', ''),
                "last_name": getattr(user, 'last_name', '')
            }
            
            validation_result = self.password_validator.validate_password(
                password, user_info
            )
            
            return Response({
                "success": True,
                "validation": validation_result
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def policy_info(self, request):
        """Get password policy information."""
        try:
            policy_dict = self.password_validator.policy.to_dict()
            
            return Response({
                "success": True,
                "policy": policy_dict
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def lockout_status(self, request):
        """Get account lockout status."""
        user = request.user
        
        try:
            is_locked = self.lockout_manager.is_account_locked(str(user.pk))
            lockout_info = None
            
            if is_locked:
                lockout_info = self.lockout_manager.get_lockout_info(str(user.pk))
            
            failed_attempts = self.lockout_manager.get_failed_attempts_count(str(user.pk))
            
            return Response({
                "success": True,
                "is_locked": is_locked,
                "lockout_info": lockout_info,
                "failed_attempts": failed_attempts
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SecurityAuditViewSet(ViewSet):
    """
    ViewSet for security audit and monitoring operations.
    
    Provides endpoints for viewing audit logs, security reports,
    and anomaly detection (admin only).
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if DJANGO_AVAILABLE:
            self.audit_logger = default_audit_logger
    
    @action(detail=False, methods=['get'])
    def recent_events(self, request):
        """Get recent audit events."""
        try:
            limit = int(request.query_params.get('limit', 100))
            user_id = request.query_params.get('user_id')
            event_type = request.query_params.get('event_type')
            
            # Convert event_type string to enum if provided
            event_types = None
            if event_type:
                try:
                    event_types = [AuditEventType(event_type)]
                except ValueError:
                    pass
            
            events = self.audit_logger.get_events(
                user_id=user_id,
                event_types=event_types,
                limit=limit
            )
            
            event_data = [event.to_dict() for event in events]
            
            return Response({
                "success": True,
                "events": event_data,
                "total_count": len(event_data)
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def security_report(self, request):
        """Generate security report for specified time period."""
        try:
            # Default to last 24 hours
            hours = int(request.query_params.get('hours', 24))
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            report = self.audit_logger.generate_security_report(start_time, end_time)
            
            return Response({
                "success": True,
                "report": report
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """Detect security anomalies."""
        try:
            hours = int(request.query_params.get('hours', 1))
            time_window = timedelta(hours=hours)
            
            anomalies = self.audit_logger.detect_anomalies(time_window)
            
            return Response({
                "success": True,
                "anomalies": anomalies,
                "time_window_hours": hours
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# Utility function for getting client IP
def get_client_ip(request) -> str:
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip
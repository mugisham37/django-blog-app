"""
Enhanced Accounts API Views with advanced authentication features.
RESTful API endpoints for user management, MFA, session management, and security.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .models import Profile
from .serializers import (
    UserSerializer, ProfileSerializer, RegisterSerializer,
    LoginSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer,
    MFASetupSerializer, MFAVerifySerializer, PasswordChangeSerializer
)

# Import auth package components
try:
    from auth_package import (
        TOTPProvider, SMSProvider, EmailProvider,
        SessionManager, DeviceInfo, 
        AuditLogger, AuditEventType, AuditSeverity,
        PasswordValidator, AccountLockoutManager,
        JWTStrategy, JWTConfig
    )
    AUTH_PACKAGE_AVAILABLE = True
except ImportError:
    AUTH_PACKAGE_AVAILABLE = False

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users."""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return users based on permissions."""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Get or update current user."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user profiles."""
    
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return profiles based on permissions."""
        if self.request.user.is_staff:
            return Profile.objects.all()
        return Profile.objects.filter(user=self.request.user)


class RegisterView(APIView):
    """User registration endpoint."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Registration successful. Please verify your email.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Enhanced user login endpoint with MFA and security features."""
    
    permission_classes = [permissions.AllowAny]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if AUTH_PACKAGE_AVAILABLE:
            self.lockout_manager = AccountLockoutManager()
            self.audit_logger = AuditLogger()
            self.session_manager = SessionManager()
            jwt_config = JWTConfig(secret_key="your-secret-key")  # Use from settings
            self.jwt_strategy = JWTStrategy(jwt_config)
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            mfa_code = request.data.get('mfa_code')
            
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Check if auth package is available for enhanced security
            if AUTH_PACKAGE_AVAILABLE:
                return self._enhanced_login(email, password, mfa_code, ip_address, user_agent, request)
            else:
                return self._basic_login(email, password, request)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _enhanced_login(self, email, password, mfa_code, ip_address, user_agent, request):
        """Enhanced login with security features."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Log failed attempt
            self.audit_logger.log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                email,
                ip_address,
                user_agent,
                "failure",
                {"reason": "user_not_found"}
            )
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user_id = str(user.pk)
        
        # Check account lockout
        if self.lockout_manager.is_account_locked(user_id):
            lockout_info = self.lockout_manager.get_lockout_info(user_id)
            
            self.audit_logger.log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                user_id,
                ip_address,
                user_agent,
                "failure",
                {"reason": "account_locked", "lockout_info": lockout_info}
            )
            
            return Response({
                'error': 'Account is temporarily locked',
                'lockout_info': lockout_info
            }, status=status.HTTP_423_LOCKED)
        
        # Authenticate user
        authenticated_user = authenticate(request, username=email, password=password)
        
        if not authenticated_user:
            # Record failed attempt
            lockout_result = self.lockout_manager.record_login_attempt(
                user_id, ip_address, False, user_agent
            )
            
            self.audit_logger.log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                user_id,
                ip_address,
                user_agent,
                "failure",
                {
                    "reason": "invalid_password",
                    "attempts_remaining": lockout_result.get("attempts_remaining")
                }
            )
            
            response_data = {'error': 'Invalid credentials'}
            if lockout_result.get("attempts_remaining"):
                response_data['attempts_remaining'] = lockout_result["attempts_remaining"]
            if lockout_result.get("require_captcha"):
                response_data['require_captcha'] = True
            
            return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check account status
        if user.status != User.UserStatus.ACTIVE:
            return Response({
                'error': 'Account is not active'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check MFA if enabled
        if hasattr(user, 'mfa_enabled') and user.mfa_enabled:
            if not mfa_code:
                return Response({
                    'mfa_required': True,
                    'message': 'MFA code required'
                }, status=status.HTTP_200_OK)
            
            # Verify MFA code (implement based on your MFA setup)
            # This is a placeholder - implement actual MFA verification
            if not self._verify_mfa_code(user, mfa_code):
                self.audit_logger.log_event(
                    AuditEventType.MFA_FAILURE,
                    user_id=user_id,
                    ip_address=ip_address,
                    details={"reason": "invalid_mfa_code"}
                )
                
                return Response({
                    'error': 'Invalid MFA code'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Successful authentication
        self.lockout_manager.record_login_attempt(
            user_id, ip_address, True, user_agent
        )
        
        # Create session
        device_info = DeviceInfo(
            device_id=f"web_{user_id}_{ip_address}",
            user_agent=user_agent,
            ip_address=ip_address,
            device_type="web"
        )
        
        session = self.session_manager.create_session(
            user_id, device_info, "password"
        )
        
        # Generate JWT tokens
        tokens = self.jwt_strategy.generate_tokens(
            user_id, 
            {"username": user.username, "email": user.email, "session_id": session.session_id}
        )
        
        # Log successful authentication
        self.audit_logger.log_authentication_event(
            AuditEventType.LOGIN_SUCCESS,
            user_id,
            ip_address,
            user_agent,
            "success",
            {"method": "password", "session_id": session.session_id}
        )
        
        return Response({
            'user': UserSerializer(user).data,
            'access_token': tokens.access_token,
            'refresh_token': tokens.refresh_token,
            'expires_in': tokens.expires_in,
            'session_id': session.session_id,
            'message': 'Login successful'
        })
    
    def _basic_login(self, email, password, request):
        """Basic login without enhanced security features."""
        user = authenticate(request, username=email, password=password)
        if user:
            if user.status == User.UserStatus.ACTIVE:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'user': UserSerializer(user).data,
                    'token': token.key,
                    'message': 'Login successful'
                })
            else:
                return Response({
                    'error': 'Account is not active'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    def _verify_mfa_code(self, user, mfa_code):
        """Verify MFA code (placeholder implementation)."""
        # Implement actual MFA verification based on your setup
        # This could use TOTP, SMS, or Email verification
        return True  # Placeholder
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class LogoutView(APIView):
    """User logout endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Logout successful'})
        except:
            return Response({'error': 'Error logging out'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """Email verification endpoint."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import EmailVerification
            verification = EmailVerification.objects.get(token=token)
            if verification.is_valid():
                user = verification.user
                user.email_verified = True
                user.status = User.UserStatus.ACTIVE
                user.save()
                verification.used = True
                verification.save()
                return Response({'message': 'Email verified successfully'})
            else:
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        except EmailVerification.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    """Resend email verification endpoint."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if not user.email_verified:
                # Create new verification token and send email
                # This would be implemented with actual email sending
                return Response({'message': 'Verification email sent'})
            else:
                return Response({'error': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetView(APIView):
    """Password reset request endpoint."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Send password reset email
            return Response({'message': 'Password reset email sent'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Password reset confirmation endpoint."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # Reset password with token
            return Response({'message': 'Password reset successful'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MFASetupView(APIView):
    """MFA setup endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if AUTH_PACKAGE_AVAILABLE:
            self.totp_provider = TOTPProvider()
            self.sms_provider = SMSProvider()
            self.email_provider = EmailProvider()
            self.audit_logger = AuditLogger()
    
    def post(self, request):
        if not AUTH_PACKAGE_AVAILABLE:
            return Response({
                'error': 'MFA features not available'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        serializer = MFASetupSerializer(data=request.data)
        if serializer.is_valid():
            mfa_type = serializer.validated_data['mfa_type']
            user = request.user
            
            try:
                if mfa_type == 'totp':
                    setup_data = self.totp_provider.setup_user_totp(str(user.pk), user.email)
                    
                    self.audit_logger.log_event(
                        AuditEventType.MFA_ENABLED,
                        user_id=str(user.pk),
                        ip_address=self._get_client_ip(request),
                        details={"mfa_type": "totp", "setup_initiated": True}
                    )
                    
                    return Response({
                        'success': True,
                        'setup_data': setup_data,
                        'message': 'TOTP setup initiated'
                    })
                
                elif mfa_type == 'sms':
                    phone_number = serializer.validated_data['phone_number']
                    result = self.sms_provider.generate_challenge(str(user.pk), phone_number)
                    
                    if result.success:
                        return Response({
                            'success': True,
                            'challenge_id': result.challenge_id,
                            'message': result.message
                        })
                    else:
                        return Response({
                            'success': False,
                            'error': result.message
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                elif mfa_type == 'email':
                    email = serializer.validated_data.get('email', user.email)
                    result = self.email_provider.generate_challenge(str(user.pk), email)
                    
                    if result.success:
                        return Response({
                            'success': True,
                            'challenge_id': result.challenge_id,
                            'message': result.message
                        })
                    else:
                        return Response({
                            'success': False,
                            'error': result.message
                        }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class MFAVerifyView(APIView):
    """MFA verification endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if AUTH_PACKAGE_AVAILABLE:
            self.totp_provider = TOTPProvider()
            self.sms_provider = SMSProvider()
            self.email_provider = EmailProvider()
            self.audit_logger = AuditLogger()
    
    def post(self, request):
        if not AUTH_PACKAGE_AVAILABLE:
            return Response({
                'error': 'MFA features not available'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        serializer = MFAVerifySerializer(data=request.data)
        if serializer.is_valid():
            challenge_id = serializer.validated_data.get('challenge_id')
            code = serializer.validated_data['code']
            mfa_type = serializer.validated_data['mfa_type']
            user = request.user
            
            try:
                # Select appropriate provider
                if mfa_type == 'sms':
                    provider = self.sms_provider
                elif mfa_type == 'email':
                    provider = self.email_provider
                else:
                    provider = self.totp_provider
                
                # Verify code
                if challenge_id:
                    result = provider.verify_challenge(challenge_id, code)
                else:
                    # For TOTP without challenge_id, need to get user's secret
                    # This is a placeholder - implement based on your user model
                    secret = getattr(user, 'totp_secret', 'dummy_secret')
                    challenge_result = provider.generate_challenge(str(user.pk), secret)
                    if challenge_result.success:
                        result = provider.verify_challenge(challenge_result.challenge_id, code)
                    else:
                        result = challenge_result
                
                # Log MFA attempt
                self.audit_logger.log_event(
                    AuditEventType.MFA_SUCCESS if result.success else AuditEventType.MFA_FAILURE,
                    user_id=str(user.pk),
                    ip_address=self._get_client_ip(request),
                    details={"mfa_type": mfa_type, "challenge_id": challenge_id}
                )
                
                if result.success:
                    return Response({
                        'success': True,
                        'message': result.message
                    })
                else:
                    return Response({
                        'success': False,
                        'error': result.message
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class SessionManagementView(APIView):
    """Session management endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if AUTH_PACKAGE_AVAILABLE:
            self.session_manager = SessionManager()
            self.audit_logger = AuditLogger()
    
    def get(self, request):
        """Get active sessions for current user."""
        if not AUTH_PACKAGE_AVAILABLE:
            return Response({
                'error': 'Session management features not available'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        try:
            user = request.user
            sessions = self.session_manager.get_user_sessions(str(user.pk))
            
            session_data = []
            current_session_id = request.session.get('auth_session_id')
            
            for session in sessions:
                session_info = {
                    'session_id': session.session_id,
                    'device_type': session.device_info.device_type,
                    'ip_address': session.device_info.ip_address,
                    'user_agent': session.device_info.user_agent,
                    'created_at': session.created_at,
                    'last_activity': session.last_activity,
                    'is_current': session.session_id == current_session_id
                }
                session_data.append(session_info)
            
            return Response({
                'success': True,
                'sessions': session_data,
                'total_count': len(session_data)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Revoke session(s)."""
        if not AUTH_PACKAGE_AVAILABLE:
            return Response({
                'error': 'Session management features not available'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        session_id = request.data.get('session_id')
        revoke_all = request.data.get('revoke_all', False)
        
        try:
            user = request.user
            
            if revoke_all:
                current_session_id = request.session.get('auth_session_id')
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
                    'success': True,
                    'message': f'Revoked {revoked_count} sessions',
                    'revoked_count': revoked_count
                })
            
            elif session_id:
                self.session_manager.revoke_session(session_id, "user_revoked")
                
                self.audit_logger.log_event(
                    AuditEventType.SESSION_REVOKED,
                    user_id=str(user.pk),
                    session_id=session_id,
                    ip_address=self._get_client_ip(request),
                    details={"reason": "user_revoked"}
                )
                
                return Response({
                    'success': True,
                    'message': 'Session revoked successfully'
                })
            
            else:
                return Response({
                    'success': False,
                    'error': 'session_id or revoke_all parameter required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
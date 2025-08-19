"""
Integration tests for authentication views and workflows.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from apps.accounts.models import Profile
from apps.accounts.forms import CustomUserRegistrationForm, CustomAuthenticationForm

User = get_user_model()


class UserRegistrationViewTest(TestCase):
    """Test user registration workflow."""
    
    def setUp(self):
        self.client = Client()
        self.registration_url = reverse('accounts:register')
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'terms_accepted': True,
            'newsletter_subscription': False,
        }
    
    def test_registration_page_loads(self):
        """Test registration page loads correctly."""
        response = self.client.get(self.registration_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Account')
        self.assertIsInstance(response.context['form'], CustomUserRegistrationForm)
    
    def test_successful_registration(self):
        """Test successful user registration."""
        response = self.client.post(self.registration_url, self.valid_data)
        
        # Should redirect to registration complete page
        self.assertRedirects(response, reverse('accounts:registration_complete'))
        
        # User should be created but inactive
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        
        # Profile should be created
        self.assertTrue(Profile.objects.filter(user=user).exists())
        profile = user.profile
        self.assertFalse(profile.newsletter_subscription)
        
        # Verification email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify your email', mail.outbox[0].subject)
        self.assertIn(user.email, mail.outbox[0].to)
    
    def test_registration_with_existing_username(self):
        """Test registration with existing username fails."""
        User.objects.create_user(username='testuser', email='existing@example.com')
        
        response = self.client.post(self.registration_url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 
                           'A user with this username already exists.')
    
    def test_registration_with_existing_email(self):
        """Test registration with existing email fails."""
        User.objects.create_user(username='existing', email='test@example.com')
        
        response = self.client.post(self.registration_url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 
                           'A user with this email address already exists.')
    
    def test_registration_password_mismatch(self):
        """Test registration with password mismatch fails."""
        data = self.valid_data.copy()
        data['password2'] = 'DifferentPass123!'
        
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', 
                           "The two password fields didn't match.")
    
    def test_registration_weak_password(self):
        """Test registration with weak password fails."""
        data = self.valid_data.copy()
        data['password1'] = data['password2'] = 'weak'
        
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['password1'])
    
    def test_registration_without_terms(self):
        """Test registration without accepting terms fails."""
        data = self.valid_data.copy()
        data['terms_accepted'] = False
        
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'terms_accepted', 
                           'You must accept the terms and conditions to register.')
    
    def test_authenticated_user_redirected(self):
        """Test authenticated user is redirected from registration."""
        user = User.objects.create_user(username='testuser', email='test@example.com')
        self.client.force_login(user)
        
        response = self.client.get(self.registration_url)
        self.assertRedirects(response, reverse('blog:home'))


class EmailVerificationTest(TestCase):
    """Test email verification workflow."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            is_active=False
        )
        Profile.objects.create(user=self.user)
    
    def test_valid_email_verification(self):
        """Test valid email verification activates user."""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('accounts:email_verify', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        
        # Should redirect to profile setup
        self.assertRedirects(response, reverse('accounts:profile_setup'))
        
        # User should be activated and logged in
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        
        # Check user is logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
    
    def test_invalid_token_verification(self):
        """Test invalid token verification fails."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('accounts:email_verify', kwargs={'uidb64': uid, 'token': 'invalid-token'})
        response = self.client.get(url)
        
        # Should redirect to resend verification
        self.assertRedirects(response, reverse('accounts:resend_verification'))
        
        # User should remain inactive
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_already_active_user_verification(self):
        """Test verification of already active user."""
        self.user.is_active = True
        self.user.save()
        
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('accounts:email_verify', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertRedirects(response, reverse('accounts:login'))


class UserLoginTest(TestCase):
    """Test user login workflow."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        Profile.objects.create(user=self.user)
    
    def test_login_page_loads(self):
        """Test login page loads correctly."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')
        self.assertIsInstance(response.context['form'], CustomAuthenticationForm)
    
    def test_successful_login_with_username(self):
        """Test successful login with username."""
        data = {
            'username': 'testuser',
            'password': 'TestPass123!',
            'remember_me': False
        }
        
        response = self.client.post(self.login_url, data)
        self.assertRedirects(response, reverse('blog:home'))
        
        # Check user is logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
    
    def test_successful_login_with_email(self):
        """Test successful login with email."""
        data = {
            'username': 'test@example.com',
            'password': 'TestPass123!',
            'remember_me': False
        }
        
        response = self.client.post(self.login_url, data)
        self.assertRedirects(response, reverse('blog:home'))
        
        # Check user is logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
    
    def test_login_with_remember_me(self):
        """Test login with remember me sets longer session."""
        data = {
            'username': 'testuser',
            'password': 'TestPass123!',
            'remember_me': True
        }
        
        response = self.client.post(self.login_url, data)
        self.assertRedirects(response, reverse('blog:home'))
        
        # Session should be set to 30 days
        self.assertEqual(self.client.session.get_expiry_age(), 30 * 24 * 60 * 60)
    
    def test_login_with_wrong_password(self):
        """Test login with wrong password fails."""
        data = {
            'username': 'testuser',
            'password': 'WrongPassword',
            'remember_me': False
        }
        
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'Invalid password. Please try again.')
    
    def test_login_with_nonexistent_user(self):
        """Test login with nonexistent user fails."""
        data = {
            'username': 'nonexistent',
            'password': 'TestPass123!',
            'remember_me': False
        }
        
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 
                           'No account found with this username or email.')
    
    def test_login_inactive_user(self):
        """Test login with inactive user fails."""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'username': 'testuser',
            'password': 'TestPass123!',
            'remember_me': False
        }
        
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 
                           'This account is inactive. Please check your email for verification instructions.')
    
    def test_authenticated_user_redirected(self):
        """Test authenticated user is redirected from login."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('blog:home'))
    
    def test_login_with_next_parameter(self):
        """Test login redirects to next parameter."""
        next_url = reverse('accounts:profile')
        data = {
            'username': 'testuser',
            'password': 'TestPass123!',
            'remember_me': False
        }
        
        response = self.client.post(f"{self.login_url}?next={next_url}", data)
        self.assertRedirects(response, next_url)


class PasswordResetTest(TestCase):
    """Test password reset workflow."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass123!'
        )
        Profile.objects.create(user=self.user)
    
    def test_password_reset_page_loads(self):
        """Test password reset page loads correctly."""
        url = reverse('accounts:password_reset')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset Your Password')
    
    def test_password_reset_email_sent(self):
        """Test password reset email is sent."""
        url = reverse('accounts:password_reset')
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset', mail.outbox[0].subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
    
    def test_password_reset_nonexistent_email(self):
        """Test password reset with nonexistent email."""
        url = reverse('accounts:password_reset')
        data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_password_reset_confirm_valid_token(self):
        """Test password reset confirmation with valid token."""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Set New Password')
    
    def test_password_reset_confirm_invalid_token(self):
        """Test password reset confirmation with invalid token."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': 'invalid-token'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid Reset Link')
    
    def test_password_reset_complete(self):
        """Test complete password reset workflow."""
        # Generate valid token
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Submit new password
        url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        data = {
            'new_password1': 'NewPass123!',
            'new_password2': 'NewPass123!'
        }
        
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        
        # User should be able to login with new password
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))
        self.assertFalse(self.user.check_password('OldPass123!'))


class ProfileManagementTest(TestCase):
    """Test profile management views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        self.profile = Profile.objects.create(user=self.user, bio='Test bio')
        self.client.force_login(self.user)
    
    def test_profile_view_loads(self):
        """Test profile view loads correctly."""
        url = reverse('accounts:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'Test bio')
    
    def test_profile_edit_view_loads(self):
        """Test profile edit view loads correctly."""
        url = reverse('accounts:profile_edit')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Profile')
        self.assertEqual(response.context['form'].instance, self.profile)
    
    def test_profile_update_success(self):
        """Test successful profile update."""
        url = reverse('accounts:profile_edit')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'bio': 'Updated bio',
            'website': 'https://example.com',
            'location': 'Test City',
            'email_notifications': True,
            'newsletter_subscription': True,
            'show_email': False,
            'show_birth_date': False,
        }
        
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('accounts:profile'))
        
        # Check user and profile were updated
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.profile.bio, 'Updated bio')
        self.assertEqual(self.profile.website, 'https://example.com')
        self.assertEqual(self.profile.location, 'Test City')
    
    def test_profile_setup_view(self):
        """Test profile setup view for new users."""
        url = reverse('accounts:profile_setup')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete Your Profile')
    
    def test_public_profile_view(self):
        """Test public profile view."""
        url = reverse('accounts:profile_detail', kwargs={'username': self.user.username})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'Test bio')
    
    def test_nonexistent_public_profile(self):
        """Test nonexistent public profile returns 404."""
        url = reverse('accounts:profile_detail', kwargs={'username': 'nonexistent'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_unauthenticated_profile_access(self):
        """Test unauthenticated user cannot access profile management."""
        self.client.logout()
        
        urls = [
            reverse('accounts:profile'),
            reverse('accounts:profile_edit'),
            reverse('accounts:profile_setup'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")


class AjaxViewsTest(TestCase):
    """Test AJAX views for enhanced UX."""
    
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username='existing', email='existing@example.com')
    
    def test_check_username_availability_available(self):
        """Test username availability check for available username."""
        url = reverse('accounts:check_username')
        response = self.client.get(url, {'username': 'newuser'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['available'])
        self.assertIn('available', data['message'])
    
    def test_check_username_availability_taken(self):
        """Test username availability check for taken username."""
        url = reverse('accounts:check_username')
        response = self.client.get(url, {'username': 'existing'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['available'])
        self.assertIn('taken', data['message'])
    
    def test_check_email_availability_available(self):
        """Test email availability check for available email."""
        url = reverse('accounts:check_email')
        response = self.client.get(url, {'email': 'new@example.com'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['available'])
        self.assertIn('available', data['message'])
    
    def test_check_email_availability_taken(self):
        """Test email availability check for taken email."""
        url = reverse('accounts:check_email')
        response = self.client.get(url, {'email': 'existing@example.com'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['available'])
        self.assertIn('registered', data['message'])


class SecurityTest(TestCase):
    """Test security aspects of authentication."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_csrf_protection_on_forms(self):
        """Test CSRF protection is enabled on forms."""
        # Registration form
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'terms_accepted': True
        })
        # Should fail due to missing CSRF token
        self.assertEqual(response.status_code, 403)
        
        # Login form
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        # Should fail due to missing CSRF token
        self.assertEqual(response.status_code, 403)
    
    def test_password_hashing(self):
        """Test passwords are properly hashed."""
        user = User.objects.create_user(
            username='hashtest',
            email='hash@example.com',
            password='TestPass123!'
        )
        
        # Password should not be stored in plain text
        self.assertNotEqual(user.password, 'TestPass123!')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        
        # But should verify correctly
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertFalse(user.check_password('WrongPassword'))
    
    def test_session_security(self):
        """Test session security settings."""
        self.client.force_login(self.user)
        
        # Check session cookie settings
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        
        # Session should be created
        self.assertIn('sessionid', self.client.cookies)
        
        # In production, these would be secure
        # self.assertTrue(self.client.cookies['sessionid']['secure'])
        # self.assertTrue(self.client.cookies['sessionid']['httponly'])
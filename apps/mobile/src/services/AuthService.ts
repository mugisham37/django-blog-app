import {ApiClient} from '@services/ApiClient';
import {User, LoginCredentials, RegisterData, AuthResponse} from '@types/auth';

class AuthServiceClass {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await ApiClient.post('/auth/login/', credentials);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  }

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response = await ApiClient.post('/auth/register/', data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  }

  /**
   * Logout user
   */
  async logout(accessToken: string): Promise<void> {
    try {
      await ApiClient.post(
        '/auth/logout/',
        {},
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
    } catch (error: any) {
      // Don't throw error for logout - we want to clear local state regardless
      console.error('Logout API call failed:', error);
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<{accessToken: string; refreshToken: string}> {
    try {
      const response = await ApiClient.post('/auth/refresh/', {
        refresh_token: refreshToken,
      });
      return {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
      };
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Token refresh failed');
    }
  }

  /**
   * Verify token validity
   */
  async verifyToken(accessToken: string): Promise<boolean> {
    try {
      await ApiClient.post(
        '/auth/verify/',
        {},
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current user profile
   */
  async getProfile(accessToken: string): Promise<User> {
    try {
      const response = await ApiClient.get('/auth/profile/', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get profile');
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(accessToken: string, data: Partial<User>): Promise<User> {
    try {
      const response = await ApiClient.patch('/auth/profile/', data, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update profile');
    }
  }

  /**
   * Change password
   */
  async changePassword(
    accessToken: string,
    currentPassword: string,
    newPassword: string
  ): Promise<void> {
    try {
      await ApiClient.post(
        '/auth/change-password/',
        {
          current_password: currentPassword,
          new_password: newPassword,
        },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to change password');
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    try {
      await ApiClient.post('/auth/password-reset/', {email});
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to request password reset');
    }
  }

  /**
   * Confirm password reset
   */
  async confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    try {
      await ApiClient.post('/auth/password-reset/confirm/', {
        token,
        new_password: newPassword,
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to reset password');
    }
  }

  /**
   * Social login (OAuth)
   */
  async socialLogin(provider: string, accessToken: string): Promise<AuthResponse> {
    try {
      const response = await ApiClient.post('/auth/social/', {
        provider,
        access_token: accessToken,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Social login failed');
    }
  }

  /**
   * Enable two-factor authentication
   */
  async enableTwoFactor(accessToken: string): Promise<{qr_code: string; secret: string}> {
    try {
      const response = await ApiClient.post(
        '/auth/2fa/enable/',
        {},
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to enable 2FA');
    }
  }

  /**
   * Confirm two-factor authentication setup
   */
  async confirmTwoFactor(accessToken: string, code: string): Promise<void> {
    try {
      await ApiClient.post(
        '/auth/2fa/confirm/',
        {code},
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to confirm 2FA');
    }
  }

  /**
   * Disable two-factor authentication
   */
  async disableTwoFactor(accessToken: string, code: string): Promise<void> {
    try {
      await ApiClient.post(
        '/auth/2fa/disable/',
        {code},
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to disable 2FA');
    }
  }

  /**
   * Verify two-factor authentication code
   */
  async verifyTwoFactor(email: string, password: string, code: string): Promise<AuthResponse> {
    try {
      const response = await ApiClient.post('/auth/2fa/verify/', {
        email,
        password,
        code,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || '2FA verification failed');
    }
  }

  /**
   * Get user sessions
   */
  async getSessions(accessToken: string): Promise<any[]> {
    try {
      const response = await ApiClient.get('/auth/sessions/', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to get sessions');
    }
  }

  /**
   * Revoke session
   */
  async revokeSession(accessToken: string, sessionId: string): Promise<void> {
    try {
      await ApiClient.delete(`/auth/sessions/${sessionId}/`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to revoke session');
    }
  }

  /**
   * Revoke all sessions except current
   */
  async revokeAllSessions(accessToken: string): Promise<void> {
    try {
      await ApiClient.post(
        '/auth/sessions/revoke-all/',
        {},
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to revoke sessions');
    }
  }
}

export const AuthService = new AuthServiceClass();
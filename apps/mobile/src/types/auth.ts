export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  username?: string;
  avatar?: string;
  phone?: string;
  dateOfBirth?: string;
  isEmailVerified: boolean;
  isPhoneVerified: boolean;
  isTwoFactorEnabled: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  preferences?: UserPreferences;
  profile?: UserProfile;
}

export interface UserPreferences {
  language: string;
  timezone: string;
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  theme: 'light' | 'dark' | 'auto';
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  marketing: boolean;
  security: boolean;
}

export interface PrivacyPreferences {
  profileVisibility: 'public' | 'private' | 'friends';
  showEmail: boolean;
  showPhone: boolean;
  allowSearchByEmail: boolean;
  allowSearchByPhone: boolean;
}

export interface UserProfile {
  bio?: string;
  website?: string;
  location?: string;
  company?: string;
  jobTitle?: string;
  socialLinks?: SocialLinks;
}

export interface SocialLinks {
  twitter?: string;
  linkedin?: string;
  github?: string;
  instagram?: string;
  facebook?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
  deviceId?: string;
  deviceName?: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  username?: string;
  phone?: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
  marketingConsent?: boolean;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isBiometricEnabled: boolean;
  error: string | null;
}

export interface BiometricState {
  isAvailable: boolean;
  isEnabled: boolean;
  biometricType: string | null;
  isSupported: boolean;
  hasHardware: boolean;
  isEnrolled: boolean;
  error: string | null;
}

export interface TwoFactorData {
  secret: string;
  qrCode: string;
  backupCodes: string[];
}

export interface SessionInfo {
  id: string;
  deviceName: string;
  deviceType: string;
  ipAddress: string;
  location?: string;
  userAgent: string;
  isCurrentSession: boolean;
  lastActivity: string;
  createdAt: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface SocialLoginData {
  provider: 'google' | 'facebook' | 'apple' | 'github' | 'linkedin' | 'microsoft';
  accessToken: string;
  idToken?: string;
  refreshToken?: string;
}

export interface DeviceInfo {
  id: string;
  name: string;
  type: 'mobile' | 'tablet' | 'desktop' | 'tv' | 'watch';
  os: string;
  osVersion: string;
  appVersion: string;
  isJailbroken?: boolean;
  isEmulator?: boolean;
  fingerprint: string;
}

export interface SecurityEvent {
  id: string;
  type: 'login' | 'logout' | 'password_change' | 'failed_login' | 'suspicious_activity';
  description: string;
  ipAddress: string;
  userAgent: string;
  location?: string;
  deviceInfo?: DeviceInfo;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface AuthError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: {
    pagination?: {
      page: number;
      limit: number;
      total: number;
      totalPages: number;
    };
  };
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  meta: {
    pagination: {
      page: number;
      limit: number;
      total: number;
      totalPages: number;
      hasNext: boolean;
      hasPrev: boolean;
    };
  };
}
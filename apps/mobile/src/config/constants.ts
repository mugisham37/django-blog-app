import {Platform} from 'react-native';

// API Configuration
export const API_CONFIG = {
  BASE_URL: __DEV__ 
    ? Platform.OS === 'ios' 
      ? 'http://localhost:8000' 
      : 'http://10.0.2.2:8000'
    : 'https://api.fullstackmonolith.com',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  BIOMETRIC_ENABLED: 'biometric_enabled',
  OFFLINE_DATA: 'offline_data',
  SETTINGS: 'app_settings',
  ONBOARDING_COMPLETED: 'onboarding_completed',
  PUSH_TOKEN: 'push_token',
  LAST_SYNC: 'last_sync',
  CACHE_VERSION: 'cache_version',
};

// Biometric Configuration
export const BIOMETRIC_CONFIG = {
  PROMPT_MESSAGE: 'Authenticate to access your account',
  FALLBACK_TITLE: 'Use Passcode',
  CANCEL_TITLE: 'Cancel',
  DISABLE_BACKUP: false,
  UNIFY_ERRORS: false,
};

// Offline Configuration
export const OFFLINE_CONFIG = {
  SYNC_INTERVAL: 5 * 60 * 1000, // 5 minutes
  MAX_OFFLINE_ACTIONS: 100,
  RETRY_INTERVAL: 30 * 1000, // 30 seconds
  MAX_RETRY_ATTEMPTS: 5,
};

// Push Notification Configuration
export const NOTIFICATION_CONFIG = {
  CHANNEL_ID: 'default',
  CHANNEL_NAME: 'Default',
  CHANNEL_DESCRIPTION: 'Default notification channel',
  IMPORTANCE: 'high' as const,
  VIBRATE: true,
  PLAY_SOUND: true,
  SHOW_BADGE: true,
};

// Cache Configuration
export const CACHE_CONFIG = {
  MAX_SIZE: 50 * 1024 * 1024, // 50MB
  TTL: 24 * 60 * 60 * 1000, // 24 hours
  CLEANUP_INTERVAL: 60 * 60 * 1000, // 1 hour
};

// Animation Configuration
export const ANIMATION_CONFIG = {
  DURATION: {
    SHORT: 200,
    MEDIUM: 300,
    LONG: 500,
  },
  EASING: {
    EASE_IN: 'easeIn',
    EASE_OUT: 'easeOut',
    EASE_IN_OUT: 'easeInOut',
  },
};

// Validation Rules
export const VALIDATION_RULES = {
  PASSWORD: {
    MIN_LENGTH: 8,
    REQUIRE_UPPERCASE: true,
    REQUIRE_LOWERCASE: true,
    REQUIRE_NUMBERS: true,
    REQUIRE_SPECIAL_CHARS: true,
  },
  EMAIL: {
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  },
  PHONE: {
    PATTERN: /^\+?[\d\s\-\(\)]+$/,
  },
};

// Feature Flags
export const FEATURE_FLAGS = {
  BIOMETRIC_AUTH: true,
  PUSH_NOTIFICATIONS: true,
  OFFLINE_MODE: true,
  SOCIAL_LOGIN: true,
  DARK_MODE: true,
  ANALYTICS: true,
  CRASH_REPORTING: true,
  CODE_PUSH: true,
};

// App Configuration
export const APP_CONFIG = {
  VERSION: '1.0.0',
  BUILD_NUMBER: 1,
  MIN_OS_VERSION: {
    ios: '12.0',
    android: '21',
  },
  SUPPORTED_LANGUAGES: ['en', 'es', 'fr', 'de'],
  DEFAULT_LANGUAGE: 'en',
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  AUTHENTICATION_FAILED: 'Authentication failed. Please try again.',
  BIOMETRIC_NOT_AVAILABLE: 'Biometric authentication is not available on this device.',
  BIOMETRIC_NOT_ENROLLED: 'No biometric credentials are enrolled on this device.',
  PERMISSION_DENIED: 'Permission denied. Please grant the required permissions.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Successfully logged in!',
  LOGOUT_SUCCESS: 'Successfully logged out!',
  REGISTRATION_SUCCESS: 'Account created successfully!',
  PASSWORD_RESET_SUCCESS: 'Password reset email sent!',
  PROFILE_UPDATE_SUCCESS: 'Profile updated successfully!',
  BIOMETRIC_ENABLED: 'Biometric authentication enabled!',
  BIOMETRIC_DISABLED: 'Biometric authentication disabled!',
  SYNC_SUCCESS: 'Data synchronized successfully!',
};
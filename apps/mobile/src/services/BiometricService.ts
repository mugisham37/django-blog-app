import ReactNativeBiometrics from 'react-native-biometrics';
import TouchID from 'react-native-touch-id';
import {Platform} from 'react-native';
import {BIOMETRIC_CONFIG, ERROR_MESSAGES} from '@config/constants';

export interface BiometricType {
  available: boolean;
  biometryType: string | null;
  error?: string;
}

class BiometricServiceClass {
  private rnBiometrics: ReactNativeBiometrics;

  constructor() {
    this.rnBiometrics = new ReactNativeBiometrics({
      allowDeviceCredentials: true,
    });
  }

  /**
   * Check if biometric authentication is available on the device
   */
  async isAvailable(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        const biometryType = await TouchID.isSupported();
        return biometryType !== false;
      } else {
        const {available} = await this.rnBiometrics.isSensorAvailable();
        return available;
      }
    } catch (error) {
      console.error('Biometric availability check failed:', error);
      return false;
    }
  }

  /**
   * Get detailed biometric information
   */
  async getBiometricType(): Promise<BiometricType> {
    try {
      if (Platform.OS === 'ios') {
        const biometryType = await TouchID.isSupported();
        return {
          available: biometryType !== false,
          biometryType: typeof biometryType === 'string' ? biometryType : null,
        };
      } else {
        const {available, biometryType} = await this.rnBiometrics.isSensorAvailable();
        return {
          available,
          biometryType,
        };
      }
    } catch (error: any) {
      return {
        available: false,
        biometryType: null,
        error: error.message,
      };
    }
  }

  /**
   * Authenticate user using biometric
   */
  async authenticate(reason?: string): Promise<boolean> {
    try {
      const isAvailable = await this.isAvailable();
      if (!isAvailable) {
        throw new Error(ERROR_MESSAGES.BIOMETRIC_NOT_AVAILABLE);
      }

      if (Platform.OS === 'ios') {
        await TouchID.authenticate(
          reason || BIOMETRIC_CONFIG.PROMPT_MESSAGE,
          {
            title: BIOMETRIC_CONFIG.PROMPT_MESSAGE,
            fallbackLabel: BIOMETRIC_CONFIG.FALLBACK_TITLE,
            cancelLabel: BIOMETRIC_CONFIG.CANCEL_TITLE,
            unifiedErrors: BIOMETRIC_CONFIG.UNIFY_ERRORS,
            passcodeFallback: !BIOMETRIC_CONFIG.DISABLE_BACKUP,
          }
        );
        return true;
      } else {
        const {success} = await this.rnBiometrics.simplePrompt({
          promptMessage: reason || BIOMETRIC_CONFIG.PROMPT_MESSAGE,
          cancelButtonText: BIOMETRIC_CONFIG.CANCEL_TITLE,
        });
        return success;
      }
    } catch (error: any) {
      console.error('Biometric authentication failed:', error);
      
      // Handle specific error cases
      if (error.name === 'UserCancel' || error.message.includes('cancelled')) {
        throw new Error('Authentication was cancelled by user');
      }
      
      if (error.name === 'UserFallback') {
        throw new Error('User chose to use passcode instead');
      }
      
      if (error.name === 'BiometryNotAvailable') {
        throw new Error(ERROR_MESSAGES.BIOMETRIC_NOT_AVAILABLE);
      }
      
      if (error.name === 'BiometryNotEnrolled') {
        throw new Error(ERROR_MESSAGES.BIOMETRIC_NOT_ENROLLED);
      }
      
      throw new Error(error.message || 'Biometric authentication failed');
    }
  }

  /**
   * Create biometric keys for secure storage
   */
  async createKeys(): Promise<{publicKey: string} | null> {
    try {
      if (Platform.OS === 'android') {
        const {keysExist} = await this.rnBiometrics.biometricKeysExist();
        
        if (!keysExist) {
          const {publicKey} = await this.rnBiometrics.createKeys();
          return {publicKey};
        }
        
        return null; // Keys already exist
      }
      
      return null; // iOS doesn't need key creation for basic auth
    } catch (error) {
      console.error('Biometric key creation failed:', error);
      return null;
    }
  }

  /**
   * Delete biometric keys
   */
  async deleteKeys(): Promise<boolean> {
    try {
      if (Platform.OS === 'android') {
        const {keysDeleted} = await this.rnBiometrics.deleteKeys();
        return keysDeleted;
      }
      
      return true; // iOS doesn't need key deletion for basic auth
    } catch (error) {
      console.error('Biometric key deletion failed:', error);
      return false;
    }
  }

  /**
   * Create and verify biometric signature (Android only)
   */
  async createSignature(payload: string): Promise<{signature: string} | null> {
    try {
      if (Platform.OS === 'android') {
        const {success, signature} = await this.rnBiometrics.createSignature({
          promptMessage: BIOMETRIC_CONFIG.PROMPT_MESSAGE,
          payload,
        });
        
        if (success && signature) {
          return {signature};
        }
      }
      
      return null;
    } catch (error) {
      console.error('Biometric signature creation failed:', error);
      return null;
    }
  }

  /**
   * Check if biometric keys exist (Android only)
   */
  async keysExist(): Promise<boolean> {
    try {
      if (Platform.OS === 'android') {
        const {keysExist} = await this.rnBiometrics.biometricKeysExist();
        return keysExist;
      }
      
      return true; // iOS doesn't use keys for basic auth
    } catch (error) {
      console.error('Biometric keys check failed:', error);
      return false;
    }
  }

  /**
   * Get supported biometric types as human-readable strings
   */
  getBiometricTypeDisplayName(biometryType: string | null): string {
    if (!biometryType) return 'Biometric';
    
    switch (biometryType.toLowerCase()) {
      case 'faceid':
        return 'Face ID';
      case 'touchid':
        return 'Touch ID';
      case 'fingerprint':
        return 'Fingerprint';
      case 'face':
        return 'Face Recognition';
      case 'iris':
        return 'Iris Recognition';
      default:
        return 'Biometric';
    }
  }

  /**
   * Check if device has biometric hardware but no enrolled biometrics
   */
  async hasHardwareButNotEnrolled(): Promise<boolean> {
    try {
      const biometricInfo = await this.getBiometricType();
      
      if (Platform.OS === 'ios') {
        // TouchID.isSupported() returns false if no biometrics are enrolled
        return false; // We can't distinguish between no hardware and not enrolled on iOS
      } else {
        // On Android, we can check if hardware exists but no biometrics are enrolled
        return !biometricInfo.available && biometricInfo.error?.includes('enrolled');
      }
    } catch (error) {
      return false;
    }
  }
}

export const BiometricService = new BiometricServiceClass();
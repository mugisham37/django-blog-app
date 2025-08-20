import React, {createContext, useContext, useEffect, useState, ReactNode} from 'react';
import {Alert} from 'react-native';
import TouchID from 'react-native-touch-id';
import ReactNativeBiometrics from 'react-native-biometrics';
import {BiometricService} from '@services/BiometricService';

interface BiometricContextType {
  isBiometricSupported: boolean;
  biometricType: string | null;
  isEnrolled: boolean;
  authenticateWithBiometric: () => Promise<boolean>;
  enableBiometric: () => Promise<boolean>;
  disableBiometric: () => Promise<boolean>;
  isBiometricEnabled: boolean;
  loading: boolean;
}

const BiometricContext = createContext<BiometricContextType | undefined>(undefined);

interface BiometricProviderProps {
  children: ReactNode;
}

export const BiometricProvider: React.FC<BiometricProviderProps> = ({children}) => {
  const [isBiometricSupported, setIsBiometricSupported] = useState(false);
  const [biometricType, setBiometricType] = useState<string | null>(null);
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [isBiometricEnabled, setIsBiometricEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initializeBiometric();
  }, []);

  const initializeBiometric = async () => {
    try {
      setLoading(true);
      
      // Check if biometric is supported
      const supported = await BiometricService.isBiometricSupported();
      setIsBiometricSupported(supported);

      if (supported) {
        // Get biometric type
        const type = await BiometricService.getBiometricType();
        setBiometricType(type);

        // Check if user is enrolled
        const enrolled = await BiometricService.isBiometricEnrolled();
        setIsEnrolled(enrolled);

        // Check if biometric is enabled in app settings
        const enabled = await BiometricService.isBiometricEnabled();
        setIsBiometricEnabled(enabled);
      }
    } catch (error) {
      console.error('Biometric initialization failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const authenticateWithBiometric = async (): Promise<boolean> => {
    try {
      if (!isBiometricSupported || !isEnrolled) {
        Alert.alert(
          'Biometric Authentication',
          'Biometric authentication is not available on this device.'
        );
        return false;
      }

      const result = await BiometricService.authenticate();
      return result;
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return false;
    }
  };

  const enableBiometric = async (): Promise<boolean> => {
    try {
      if (!isBiometricSupported || !isEnrolled) {
        Alert.alert(
          'Biometric Authentication',
          'Please set up biometric authentication in your device settings first.'
        );
        return false;
      }

      // First authenticate to enable biometric
      const authenticated = await authenticateWithBiometric();
      if (authenticated) {
        await BiometricService.enableBiometric();
        setIsBiometricEnabled(true);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Enable biometric failed:', error);
      return false;
    }
  };

  const disableBiometric = async (): Promise<boolean> => {
    try {
      await BiometricService.disableBiometric();
      setIsBiometricEnabled(false);
      return true;
    } catch (error) {
      console.error('Disable biometric failed:', error);
      return false;
    }
  };

  const value: BiometricContextType = {
    isBiometricSupported,
    biometricType,
    isEnrolled,
    authenticateWithBiometric,
    enableBiometric,
    disableBiometric,
    isBiometricEnabled,
    loading,
  };

  return (
    <BiometricContext.Provider value={value}>
      {children}
    </BiometricContext.Provider>
  );
};

export const useBiometric = (): BiometricContextType => {
  const context = useContext(BiometricContext);
  if (context === undefined) {
    throw new Error('useBiometric must be used within a BiometricProvider');
  }
  return context;
};
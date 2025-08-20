import React, {useState, useEffect} from 'react';
import {View, StyleSheet, Alert} from 'react-native';
import {Text, Button, Card} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import {StackNavigationProp} from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LottieView from 'lottie-react-native';
import {OnboardingStackParamList} from '@navigation/OnboardingNavigator';
import {useBiometric} from '@store/BiometricContext';
import {theme} from '@config/theme';

type BiometricSetupScreenNavigationProp = StackNavigationProp<
  OnboardingStackParamList,
  'BiometricSetup'
>;

interface Props {
  navigation: BiometricSetupScreenNavigationProp;
}

export const BiometricSetupScreen: React.FC<Props> = ({navigation}) => {
  const {
    isBiometricSupported,
    biometricType,
    isEnrolled,
    enableBiometric,
    isBiometricEnabled,
    loading,
  } = useBiometric();

  const [isEnabling, setIsEnabling] = useState(false);

  const getBiometricDisplayName = () => {
    if (!biometricType) return 'Biometric';
    
    switch (biometricType.toLowerCase()) {
      case 'faceid':
        return 'Face ID';
      case 'touchid':
        return 'Touch ID';
      case 'fingerprint':
        return 'Fingerprint';
      case 'face':
        return 'Face Recognition';
      default:
        return 'Biometric';
    }
  };

  const getBiometricIcon = () => {
    if (!biometricType) return 'fingerprint';
    
    switch (biometricType.toLowerCase()) {
      case 'faceid':
      case 'face':
        return 'face';
      case 'touchid':
      case 'fingerprint':
        return 'fingerprint';
      default:
        return 'fingerprint';
    }
  };

  const handleEnableBiometric = async () => {
    setIsEnabling(true);
    
    try {
      const success = await enableBiometric();
      
      if (success) {
        Alert.alert(
          'Success',
          `${getBiometricDisplayName()} authentication has been enabled.`,
          [
            {
              text: 'Continue',
              onPress: () => navigation.navigate('NotificationSetup'),
            },
          ]
        );
      } else {
        Alert.alert(
          'Failed',
          `Failed to enable ${getBiometricDisplayName()} authentication.`
        );
      }
    } catch (error) {
      Alert.alert(
        'Error',
        `An error occurred while setting up ${getBiometricDisplayName()} authentication.`
      );
    } finally {
      setIsEnabling(false);
    }
  };

  const handleSkip = () => {
    navigation.navigate('NotificationSetup');
  };

  const handleContinue = () => {
    navigation.navigate('NotificationSetup');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <LottieView
            source={require('../../../assets/animations/loading.json')}
            autoPlay
            loop
            style={styles.loadingAnimation}
          />
          <Text style={styles.loadingText}>Checking biometric availability...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.iconContainer}>
            <Icon
              name={getBiometricIcon()}
              size={80}
              color={theme.colors.primary}
            />
          </View>
          
          <Text style={styles.title}>
            {isBiometricSupported ? 'Secure Your Account' : 'Biometric Not Available'}
          </Text>
          
          <Text style={styles.subtitle}>
            {isBiometricSupported
              ? `Use ${getBiometricDisplayName()} for quick and secure access to your account.`
              : 'Biometric authentication is not available on this device.'}
          </Text>
        </View>

        {isBiometricSupported && (
          <Card style={styles.infoCard}>
            <View style={styles.cardContent}>
              <View style={styles.infoRow}>
                <Icon name="security" size={24} color={theme.colors.primary} />
                <Text style={styles.infoText}>Enhanced security</Text>
              </View>
              
              <View style={styles.infoRow}>
                <Icon name="speed" size={24} color={theme.colors.primary} />
                <Text style={styles.infoText}>Quick access</Text>
              </View>
              
              <View style={styles.infoRow}>
                <Icon name="privacy-tip" size={24} color={theme.colors.primary} />
                <Text style={styles.infoText}>Your data stays private</Text>
              </View>
            </View>
          </Card>
        )}

        <View style={styles.statusContainer}>
          {!isBiometricSupported && (
            <View style={styles.statusItem}>
              <Icon name="error" size={24} color={theme.colors.error} />
              <Text style={styles.statusText}>Biometric not supported</Text>
            </View>
          )}
          
          {isBiometricSupported && !isEnrolled && (
            <View style={styles.statusItem}>
              <Icon name="warning" size={24} color={theme.colors.error} />
              <Text style={styles.statusText}>
                No {getBiometricDisplayName().toLowerCase()} enrolled. Please set up {getBiometricDisplayName().toLowerCase()} in your device settings.
              </Text>
            </View>
          )}
          
          {isBiometricSupported && isEnrolled && isBiometricEnabled && (
            <View style={styles.statusItem}>
              <Icon name="check-circle" size={24} color={theme.colors.primary} />
              <Text style={styles.statusText}>
                {getBiometricDisplayName()} authentication is enabled
              </Text>
            </View>
          )}
        </View>

        <View style={styles.buttonContainer}></View>{isBiometricSupported && isEnrolled && !isBiometricEnabled && (
            <Button
              mode="contained"
              onPress={handleEnableBiometric}
              loading={isEnabling}
              disabled={isEnabling}
              style={styles.button}
              contentStyle={styles.buttonContent}>
              Enable {getBiometricDisplayName()}
            </Button>
          )}
          
          {isBiometricEnabled && (
            <Button
              mode="contained"
              onPress={handleContinue}
              style={styles.button}
              contentStyle={styles.buttonContent}>
              Continue
            </Button>
          )}
          
          <Button
            mode="outlined"
            onPress={handleSkip}
            style={[styles.button, styles.skipButton]}
            contentStyle={styles.buttonContent}>
            {isBiometricSupported && isEnrolled ? 'Skip for now' : 'Continue'}
          </Button>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'space-between',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingAnimation: {
    width: 150,
    height: 150,
  },
  loadingText: {
    fontSize: 16,
    color: theme.colors.onBackground,
    marginTop: 20,
  },
  header: {
    alignItems: 'center',
    marginTop: 60,
  },
  iconContainer: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.colors.onBackground,
    textAlign: 'center',
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: theme.colors.onSurface,
    textAlign: 'center',
    lineHeight: 24,
    marginHorizontal: 20,
  },
  infoCard: {
    marginVertical: 32,
    elevation: 2,
  },
  cardContent: {
    padding: 20,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  infoText: {
    fontSize: 16,
    color: theme.colors.onSurface,
    marginLeft: 16,
  },
  statusContainer: {
    marginVertical: 20,
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
  },
  statusText: {
    fontSize: 14,
    color: theme.colors.onSurface,
    marginLeft: 12,
    flex: 1,
  },
  buttonContainer: {
    paddingBottom: 40,
  },
  button: {
    borderRadius: 25,
    marginBottom: 12,
  },
  skipButton: {
    borderColor: theme.colors.outline,
  },
  buttonContent: {
    paddingVertical: 8,
  },
});
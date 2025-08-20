import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import {useForm, Controller} from 'react-hook-form';
import {yupResolver} from '@hookform/resolvers/yup';
import * as yup from 'yup';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {useAuth} from '@store/AuthContext';
import {useBiometric} from '@store/BiometricContext';
import {TextInput} from '@components/TextInput';
import {Button} from '@components/Button';
import {SocialLoginButton} from '@components/SocialLoginButton';
import {LoadingOverlay} from '@components/LoadingOverlay';
import {theme} from '@config/theme';
import {LoginCredentials} from '@types/auth';
import {SUCCESS_MESSAGES, ERROR_MESSAGES} from '@config/constants';

const schema = yup.object().shape({
  email: yup
    .string()
    .email('Please enter a valid email address')
    .required('Email is required'),
  password: yup
    .string()
    .min(8, 'Password must be at least 8 characters')
    .required('Password is required'),
});

interface LoginFormData {
  email: string;
  password: string;
}

export const LoginScreen: React.FC = () => {
  const {login, loginWithBiometric, state: authState} = useAuth();
  const {state: biometricState, checkBiometricAvailability} = useBiometric();
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const {
    control,
    handleSubmit,
    formState: {errors, isValid},
    setValue,
  } = useForm<LoginFormData>({
    resolver: yupResolver(schema),
    mode: 'onChange',
  });

  useEffect(() => {
    checkBiometricAvailability();
  }, []);

  const onSubmit = async (data: LoginFormData) => {
    try {
      const credentials: LoginCredentials = {
        email: data.email,
        password: data.password,
        rememberMe,
      };

      await login(credentials);
      Alert.alert('Success', SUCCESS_MESSAGES.LOGIN_SUCCESS);
    } catch (error: any) {
      Alert.alert('Login Failed', error.message || ERROR_MESSAGES.AUTHENTICATION_FAILED);
    }
  };

  const handleBiometricLogin = async () => {
    try {
      await loginWithBiometric();
      Alert.alert('Success', SUCCESS_MESSAGES.LOGIN_SUCCESS);
    } catch (error: any) {
      Alert.alert('Biometric Login Failed', error.message);
    }
  };

  const handleSocialLogin = async (provider: string) => {
    try {
      // Navigate to social login screen
      // This would typically open a web view or use a social login SDK
      console.log(`Social login with ${provider}`);
    } catch (error: any) {
      Alert.alert('Social Login Failed', error.message);
    }
  };

  const fillDemoCredentials = () => {
    setValue('email', 'demo@example.com');
    setValue('password', 'demo123456');
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled">
        <LinearGradient
          colors={theme.colors.gradientPrimary}
          style={styles.header}>
          <Icon name="account-circle" size={80} color={theme.colors.surface} />
          <Text style={styles.title}>Welcome Back</Text>
          <Text style={styles.subtitle}>Sign in to your account</Text>
        </LinearGradient>

        <View style={styles.form}>
          <Controller
            control={control}
            name="email"
            render={({field: {onChange, onBlur, value}}) => (
              <TextInput
                label="Email Address"
                placeholder="Enter your email"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.email?.message}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                leftIcon="email"
              />
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({field: {onChange, onBlur, value}}) => (
              <TextInput
                label="Password"
                placeholder="Enter your password"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.password?.message}
                secureTextEntry={!showPassword}
                autoComplete="password"
                leftIcon="lock"
                rightIcon={showPassword ? 'visibility-off' : 'visibility'}
                onRightIconPress={() => setShowPassword(!showPassword)}
              />
            )}
          />

          <View style={styles.options}>
            <TouchableOpacity
              style={styles.rememberMe}
              onPress={() => setRememberMe(!rememberMe)}>
              <Icon
                name={rememberMe ? 'check-box' : 'check-box-outline-blank'}
                size={24}
                color={theme.colors.primary}
              />
              <Text style={styles.rememberMeText}>Remember me</Text>
            </TouchableOpacity>

            <TouchableOpacity>
              <Text style={styles.forgotPassword}>Forgot Password?</Text>
            </TouchableOpacity>
          </View>

          <Button
            title="Sign In"
            onPress={handleSubmit(onSubmit)}
            disabled={!isValid || authState.isLoading}
            loading={authState.isLoading}
            style={styles.loginButton}
          />

          {biometricState.isAvailable && biometricState.isEnabled && (
            <Button
              title={`Sign in with ${biometricState.biometricType}`}
              onPress={handleBiometricLogin}
              variant="outline"
              leftIcon="fingerprint"
              style={styles.biometricButton}
            />
          )}

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>OR</Text>
            <View style={styles.dividerLine} />
          </View>

          <View style={styles.socialButtons}>
            <SocialLoginButton
              provider="google"
              onPress={() => handleSocialLogin('google')}
            />
            <SocialLoginButton
              provider="facebook"
              onPress={() => handleSocialLogin('facebook')}
            />
            <SocialLoginButton
              provider="apple"
              onPress={() => handleSocialLogin('apple')}
            />
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Don't have an account? </Text>
            <TouchableOpacity>
              <Text style={styles.signUpLink}>Sign Up</Text>
            </TouchableOpacity>
          </View>

          {__DEV__ && (
            <TouchableOpacity
              style={styles.demoButton}
              onPress={fillDemoCredentials}>
              <Text style={styles.demoButtonText}>Fill Demo Credentials</Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>

      {authState.isLoading && <LoadingOverlay />}
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContainer: {
    flexGrow: 1,
  },
  header: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.xxl,
    paddingHorizontal: theme.spacing.lg,
    borderBottomLeftRadius: theme.borderRadius.xxl,
    borderBottomRightRadius: theme.borderRadius.xxl,
  },
  title: {
    ...theme.typography.h2,
    color: theme.colors.surface,
    marginTop: theme.spacing.md,
    textAlign: 'center',
  },
  subtitle: {
    ...theme.typography.body1,
    color: theme.colors.surface,
    opacity: 0.9,
    marginTop: theme.spacing.xs,
    textAlign: 'center',
  },
  form: {
    flex: 1,
    padding: theme.spacing.lg,
  },
  options: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: theme.spacing.md,
  },
  rememberMe: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rememberMeText: {
    ...theme.typography.body2,
    color: theme.colors.text,
    marginLeft: theme.spacing.xs,
  },
  forgotPassword: {
    ...theme.typography.body2,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  loginButton: {
    marginVertical: theme.spacing.md,
  },
  biometricButton: {
    marginBottom: theme.spacing.md,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: theme.spacing.lg,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: theme.colors.border,
  },
  dividerText: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginHorizontal: theme.spacing.md,
  },
  socialButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: theme.spacing.lg,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: theme.spacing.lg,
  },
  footerText: {
    ...theme.typography.body2,
    color: theme.colors.textSecondary,
  },
  signUpLink: {
    ...theme.typography.body2,
    color: theme.colors.primary,
    fontWeight: '600',
  },
  demoButton: {
    marginTop: theme.spacing.lg,
    padding: theme.spacing.sm,
    backgroundColor: theme.colors.warning,
    borderRadius: theme.borderRadius.md,
    alignItems: 'center',
  },
  demoButtonText: {
    ...theme.typography.caption,
    color: theme.colors.surface,
    fontWeight: '600',
  },
});
import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {LoginScreen} from '@screens/auth/LoginScreen';
import {RegisterScreen} from '@screens/auth/RegisterScreen';
import {ForgotPasswordScreen} from '@screens/auth/ForgotPasswordScreen';
import {ResetPasswordScreen} from '@screens/auth/ResetPasswordScreen';
import {BiometricSetupScreen} from '@screens/auth/BiometricSetupScreen';
import {TwoFactorScreen} from '@screens/auth/TwoFactorScreen';
import {SocialLoginScreen} from '@screens/auth/SocialLoginScreen';
import {theme} from '@config/theme';

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  ResetPassword: {token: string};
  BiometricSetup: undefined;
  TwoFactor: {email: string; password: string};
  SocialLogin: {provider: string};
};

const Stack = createStackNavigator<AuthStackParamList>();

export const AuthNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      initialRouteName="Login"
      screenOptions={{
        headerShown: false,
        cardStyle: {backgroundColor: theme.colors.background},
        gestureEnabled: true,
        gestureDirection: 'horizontal',
      }}>
      <Stack.Screen 
        name="Login" 
        component={LoginScreen}
        options={{
          animationTypeForReplace: 'push',
        }}
      />
      <Stack.Screen 
        name="Register" 
        component={RegisterScreen}
        options={{
          headerShown: true,
          title: 'Create Account',
          headerStyle: {
            backgroundColor: theme.colors.surface,
            elevation: 0,
            shadowOpacity: 0,
          },
          headerTitleStyle: {
            color: theme.colors.text,
            fontSize: 18,
            fontWeight: '600',
          },
          headerTintColor: theme.colors.primary,
        }}
      />
      <Stack.Screen 
        name="ForgotPassword" 
        component={ForgotPasswordScreen}
        options={{
          headerShown: true,
          title: 'Reset Password',
          headerStyle: {
            backgroundColor: theme.colors.surface,
            elevation: 0,
            shadowOpacity: 0,
          },
          headerTitleStyle: {
            color: theme.colors.text,
            fontSize: 18,
            fontWeight: '600',
          },
          headerTintColor: theme.colors.primary,
        }}
      />
      <Stack.Screen 
        name="ResetPassword" 
        component={ResetPasswordScreen}
        options={{
          headerShown: true,
          title: 'New Password',
          headerStyle: {
            backgroundColor: theme.colors.surface,
            elevation: 0,
            shadowOpacity: 0,
          },
          headerTitleStyle: {
            color: theme.colors.text,
            fontSize: 18,
            fontWeight: '600',
          },
          headerTintColor: theme.colors.primary,
        }}
      />
      <Stack.Screen 
        name="BiometricSetup" 
        component={BiometricSetupScreen}
        options={{
          headerShown: true,
          title: 'Biometric Setup',
          headerStyle: {
            backgroundColor: theme.colors.surface,
            elevation: 0,
            shadowOpacity: 0,
          },
          headerTitleStyle: {
            color: theme.colors.text,
            fontSize: 18,
            fontWeight: '600',
          },
          headerTintColor: theme.colors.primary,
        }}
      />
      <Stack.Screen 
        name="TwoFactor" 
        component={TwoFactorScreen}
        options={{
          headerShown: true,
          title: 'Two-Factor Authentication',
          headerStyle: {
            backgroundColor: theme.colors.surface,
            elevation: 0,
            shadowOpacity: 0,
          },
          headerTitleStyle: {
            color: theme.colors.text,
            fontSize: 18,
            fontWeight: '600',
          },
          headerTintColor: theme.colors.primary,
          headerLeft: () => null, // Disable back button for 2FA
        }}
      />
      <Stack.Screen 
        name="SocialLogin" 
        component={SocialLoginScreen}
        options={{
          headerShown: true,
          title: 'Social Login',
          headerStyle: {
            backgroundColor: theme.colors.surface,
            elevation: 0,
            shadowOpacity: 0,
          },
          headerTitleStyle: {
            color: theme.colors.text,
            fontSize: 18,
            fontWeight: '600',
          },
          headerTintColor: theme.colors.primary,
        }}
      />
    </Stack.Navigator>
  );
};
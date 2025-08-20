import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createDrawerNavigator} from '@react-navigation/drawer';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {useAuth} from '@store/AuthContext';
import {AuthNavigator} from './AuthNavigator';
import {MainTabNavigator} from './MainTabNavigator';
import {OnboardingNavigator} from './OnboardingNavigator';
import {LoadingScreen} from '@screens/LoadingScreen';
import {useOnboarding} from '@hooks/useOnboarding';
import {theme} from '@config/theme';

const Stack = createStackNavigator();

export const AppNavigator: React.FC = () => {
  const {state: authState} = useAuth();
  const {isOnboardingCompleted, isLoading: onboardingLoading} = useOnboarding();

  if (authState.isLoading || onboardingLoading) {
    return <LoadingScreen />;
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: {backgroundColor: theme.colors.background},
      }}>
      {!isOnboardingCompleted ? (
        <Stack.Screen name="Onboarding" component={OnboardingNavigator} />
      ) : !authState.isAuthenticated ? (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      ) : (
        <Stack.Screen name="Main" component={MainTabNavigator} />
      )}
    </Stack.Navigator>
  );
};
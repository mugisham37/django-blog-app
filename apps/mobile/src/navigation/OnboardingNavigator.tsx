import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {WelcomeScreen} from '@screens/onboarding/WelcomeScreen';
import {PermissionsScreen} from '@screens/onboarding/PermissionsScreen';
import {BiometricSetupScreen} from '@screens/onboarding/BiometricSetupScreen';
import {NotificationSetupScreen} from '@screens/onboarding/NotificationSetupScreen';
import {OnboardingCompleteScreen} from '@screens/onboarding/OnboardingCompleteScreen';

export type OnboardingStackParamList = {
  Welcome: undefined;
  Permissions: undefined;
  BiometricSetup: undefined;
  NotificationSetup: undefined;
  OnboardingComplete: undefined;
};

const Stack = createStackNavigator<OnboardingStackParamList>();

export const OnboardingNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyleInterpolator: ({current, layouts}) => {
          return {
            cardStyle: {
              transform: [
                {
                  translateX: current.progress.interpolate({
                    inputRange: [0, 1],
                    outputRange: [layouts.screen.width, 0],
                  }),
                },
              ],
            },
          };
        },
      }}>
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="Permissions" component={PermissionsScreen} />
      <Stack.Screen name="BiometricSetup" component={BiometricSetupScreen} />
      <Stack.Screen name="NotificationSetup" component={NotificationSetupScreen} />
      <Stack.Screen name="OnboardingComplete" component={OnboardingCompleteScreen} />
    </Stack.Navigator>
  );
};
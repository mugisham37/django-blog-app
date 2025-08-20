import React, {useEffect} from 'react';
import {StatusBar, LogBox} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {QueryClient, QueryClientProvider} from 'react-query';
import {Provider as PaperProvider} from 'react-native-paper';
import SplashScreen from 'react-native-splash-screen';
import CodePush from 'react-native-code-push';

import {AppNavigator} from '@navigation/AppNavigator';
import {AuthProvider} from '@store/AuthContext';
import {OfflineProvider} from '@store/OfflineContext';
import {NotificationProvider} from '@store/NotificationContext';
import {BiometricProvider} from '@store/BiometricContext';
import {theme} from '@config/theme';
import {ErrorBoundary} from '@components/ErrorBoundary';
import {LoadingProvider} from '@store/LoadingContext';
import {initializeApp} from '@services/AppInitializer';

// Ignore specific warnings for development
LogBox.ignoreLogs([
  'Non-serializable values were found in the navigation state',
  'Remote debugger is in a background tab',
]);

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

const App: React.FC = () => {
  useEffect(() => {
    const initApp = async () => {
      try {
        await initializeApp();
      } catch (error) {
        console.error('App initialization failed:', error);
      } finally {
        // Hide splash screen after initialization
        SplashScreen.hide();
      }
    };

    initApp();
  }, []);

  return (
    <ErrorBoundary>
      <GestureHandlerRootView style={{flex: 1}}>
        <SafeAreaProvider>
          <PaperProvider theme={theme}>
            <QueryClientProvider client={queryClient}>
              <AuthProvider>
                <BiometricProvider>
                  <OfflineProvider>
                    <NotificationProvider>
                      <LoadingProvider>
                        <NavigationContainer>
                          <StatusBar
                            barStyle="dark-content"
                            backgroundColor={theme.colors.surface}
                          />
                          <AppNavigator />
                        </NavigationContainer>
                      </LoadingProvider>
                    </NotificationProvider>
                  </OfflineProvider>
                </BiometricProvider>
              </AuthProvider>
            </QueryClientProvider>
          </PaperProvider>
        </SafeAreaProvider>
      </GestureHandlerRootView>
    </ErrorBoundary>
  );
};

// Configure CodePush for over-the-air updates
const codePushOptions = {
  checkFrequency: CodePush.CheckFrequency.ON_APP_RESUME,
  mandatoryInstallMode: CodePush.InstallMode.IMMEDIATE,
  updateDialog: {
    title: 'Update Available',
    optionalUpdateMessage: 'An update is available. Would you like to install it now?',
    optionalIgnoreButtonLabel: 'Later',
    optionalInstallButtonLabel: 'Install',
    mandatoryUpdateMessage: 'A mandatory update is available and must be installed.',
    mandatoryContinueButtonLabel: 'Continue',
  },
};

export default CodePush(codePushOptions)(App);
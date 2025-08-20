import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import DeviceInfo from 'react-native-device-info';
import crashlytics from '@react-native-firebase/crashlytics';
import analytics from '@react-native-firebase/analytics';
import {ApiClient} from './ApiClient';
import {OfflineManager} from './OfflineManager';

interface AppInitializationResult {
  success: boolean;
  error?: string;
}

export const initializeApp = async (): Promise<AppInitializationResult> => {
  try {
    console.log('Starting app initialization...');

    // Initialize crash reporting
    await initializeCrashlytics();

    // Initialize analytics
    await initializeAnalytics();

    // Check device information
    await checkDeviceInfo();

    // Initialize network monitoring
    await initializeNetworkMonitoring();

    // Initialize offline manager
    await OfflineManager.initialize();

    // Initialize API client
    await ApiClient.initialize();

    // Check for app updates
    await checkForUpdates();

    // Load user preferences
    await loadUserPreferences();

    console.log('App initialization completed successfully');
    return {success: true};

  } catch (error) {
    console.error('App initialization failed:', error);
    crashlytics().recordError(error as Error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
};

const initializeCrashlytics = async () => {
  try {
    // Enable crashlytics collection
    await crashlytics().setCrashlyticsCollectionEnabled(true);
    
    // Set user properties
    const deviceId = await DeviceInfo.getUniqueId();
    crashlytics().setUserId(deviceId);
    
    console.log('Crashlytics initialized');
  } catch (error) {
    console.error('Crashlytics initialization failed:', error);
  }
};

const initializeAnalytics = async () => {
  try {
    // Enable analytics collection
    await analytics().setAnalyticsCollectionEnabled(true);
    
    // Set default parameters
    await analytics().setDefaultEventParameters({
      app_version: DeviceInfo.getVersion(),
      build_number: DeviceInfo.getBuildNumber(),
    });
    
    // Log app open event
    await analytics().logAppOpen();
    
    console.log('Analytics initialized');
  } catch (error) {
    console.error('Analytics initialization failed:', error);
  }
};

const checkDeviceInfo = async () => {
  try {
    const deviceInfo = {
      deviceId: await DeviceInfo.getUniqueId(),
      brand: DeviceInfo.getBrand(),
      model: DeviceInfo.getModel(),
      systemName: DeviceInfo.getSystemName(),
      systemVersion: DeviceInfo.getSystemVersion(),
      appVersion: DeviceInfo.getVersion(),
      buildNumber: DeviceInfo.getBuildNumber(),
      bundleId: DeviceInfo.getBundleId(),
      isEmulator: await DeviceInfo.isEmulator(),
      hasNotch: DeviceInfo.hasNotch(),
      hasDynamicIsland: DeviceInfo.hasDynamicIsland(),
    };

    // Store device info for later use
    await AsyncStorage.setItem('deviceInfo', JSON.stringify(deviceInfo));
    
    console.log('Device info collected:', deviceInfo);
  } catch (error) {
    console.error('Device info collection failed:', error);
  }
};

const initializeNetworkMonitoring = async () => {
  try {
    // Get initial network state
    const networkState = await NetInfo.fetch();
    console.log('Initial network state:', networkState);

    // Set up network state listener
    NetInfo.addEventListener(state => {
      console.log('Network state changed:', state);
      
      // Handle network changes
      if (state.isConnected) {
        // Network is available, sync offline data
        OfflineManager.syncOfflineData();
      } else {
        // Network is unavailable, enable offline mode
        OfflineManager.enableOfflineMode();
      }
    });

    console.log('Network monitoring initialized');
  } catch (error) {
    console.error('Network monitoring initialization failed:', error);
  }
};

const checkForUpdates = async () => {
  try {
    // This would typically check for CodePush updates
    // or app store updates depending on your update strategy
    console.log('Checking for updates...');
    
    // For now, just log that we're checking
    // In a real implementation, you would:
    // 1. Check CodePush for updates
    // 2. Check app store for mandatory updates
    // 3. Prompt user if updates are available
    
    console.log('Update check completed');
  } catch (error) {
    console.error('Update check failed:', error);
  }
};

const loadUserPreferences = async () => {
  try {
    // Load user preferences from storage
    const preferences = await AsyncStorage.getItem('userPreferences');
    
    if (preferences) {
      const parsedPreferences = JSON.parse(preferences);
      console.log('User preferences loaded:', parsedPreferences);
      
      // Apply preferences
      // This could include theme, language, notification settings, etc.
    } else {
      // Set default preferences
      const defaultPreferences = {
        theme: 'light',
        language: 'en',
        notifications: true,
        biometric: false,
        autoSync: true,
      };
      
      await AsyncStorage.setItem('userPreferences', JSON.stringify(defaultPreferences));
      console.log('Default preferences set');
    }
  } catch (error) {
    console.error('User preferences loading failed:', error);
  }
};

export const getDeviceInfo = async () => {
  try {
    const deviceInfoString = await AsyncStorage.getItem('deviceInfo');
    return deviceInfoString ? JSON.parse(deviceInfoString) : null;
  } catch (error) {
    console.error('Failed to get device info:', error);
    return null;
  }
};

export const getUserPreferences = async () => {
  try {
    const preferencesString = await AsyncStorage.getItem('userPreferences');
    return preferencesString ? JSON.parse(preferencesString) : null;
  } catch (error) {
    console.error('Failed to get user preferences:', error);
    return null;
  }
};

export const updateUserPreferences = async (preferences: any) => {
  try {
    const currentPreferences = await getUserPreferences();
    const updatedPreferences = {...currentPreferences, ...preferences};
    await AsyncStorage.setItem('userPreferences', JSON.stringify(updatedPreferences));
    return updatedPreferences;
  } catch (error) {
    console.error('Failed to update user preferences:', error);
    throw error;
  }
};
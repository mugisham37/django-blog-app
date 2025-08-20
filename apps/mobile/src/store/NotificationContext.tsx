import React, {createContext, useContext, useEffect, useState, ReactNode} from 'react';
import {Platform, Alert, PermissionsAndroid} from 'react-native';
import PushNotification from 'react-native-push-notification';
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface NotificationContextType {
  fcmToken: string | null;
  notificationPermission: boolean;
  requestPermission: () => Promise<boolean>;
  subscribeToTopic: (topic: string) => Promise<void>;
  unsubscribeFromTopic: (topic: string) => Promise<void>;
  showLocalNotification: (title: string, message: string, data?: any) => void;
  clearAllNotifications: () => void;
  setBadgeCount: (count: number) => void;
  isNotificationEnabled: boolean;
  setNotificationEnabled: (enabled: boolean) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({children}) => {
  const [fcmToken, setFcmToken] = useState<string | null>(null);
  const [notificationPermission, setNotificationPermission] = useState(false);
  const [isNotificationEnabled, setIsNotificationEnabledState] = useState(true);

  useEffect(() => {
    initializeNotifications();
    setupNotificationListeners();
    loadNotificationSettings();
  }, []);

  const loadNotificationSettings = async () => {
    try {
      const enabled = await AsyncStorage.getItem('notificationEnabled');
      setIsNotificationEnabledState(enabled !== 'false');
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    }
  };

  const setNotificationEnabled = async (enabled: boolean) => {
    try {
      await AsyncStorage.setItem('notificationEnabled', enabled.toString());
      setIsNotificationEnabledState(enabled);
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    }
  };

  const initializeNotifications = async () => {
    try {
      // Configure PushNotification
      PushNotification.configure({
        onRegister: function (token) {
          console.log('TOKEN:', token);
        },
        onNotification: function (notification) {
          console.log('NOTIFICATION:', notification);
          // Handle notification tap
          if (notification.userInteraction) {
            // User tapped on notification
            handleNotificationTap(notification);
          }
        },
        onAction: function (notification) {
          console.log('ACTION:', notification.action);
          console.log('NOTIFICATION:', notification);
        },
        onRegistrationError: function (err) {
          console.error(err.message, err);
        },
        permissions: {
          alert: true,
          badge: true,
          sound: true,
        },
        popInitialNotification: true,
        requestPermissions: Platform.OS === 'ios',
      });

      // Request permission and get FCM token
      const hasPermission = await requestPermission();
      if (hasPermission) {
        const token = await messaging().getToken();
        setFcmToken(token);
        console.log('FCM Token:', token);
      }

      // Listen for token refresh
      messaging().onTokenRefresh(token => {
        setFcmToken(token);
        console.log('FCM Token refreshed:', token);
      });

    } catch (error) {
      console.error('Notification initialization failed:', error);
    }
  };

  const setupNotificationListeners = () => {
    // Handle foreground messages
    messaging().onMessage(async remoteMessage => {
      if (isNotificationEnabled) {
        console.log('Foreground message:', remoteMessage);
        showLocalNotification(
          remoteMessage.notification?.title || 'New Message',
          remoteMessage.notification?.body || 'You have a new message',
          remoteMessage.data
        );
      }
    });

    // Handle background messages
    messaging().setBackgroundMessageHandler(async remoteMessage => {
      console.log('Background message:', remoteMessage);
    });

    // Handle notification opened app
    messaging().onNotificationOpenedApp(remoteMessage => {
      console.log('Notification opened app:', remoteMessage);
      handleNotificationTap(remoteMessage);
    });

    // Check if app was opened from a notification
    messaging()
      .getInitialNotification()
      .then(remoteMessage => {
        if (remoteMessage) {
          console.log('App opened from notification:', remoteMessage);
          handleNotificationTap(remoteMessage);
        }
      });
  };

  const handleNotificationTap = (notification: any) => {
    // Handle navigation based on notification data
    if (notification.data) {
      const {type, id} = notification.data;
      switch (type) {
        case 'blog_post':
          // Navigate to blog post
          break;
        case 'comment':
          // Navigate to comment
          break;
        case 'message':
          // Navigate to message
          break;
        default:
          // Navigate to home
          break;
      }
    }
  };

  const requestPermission = async (): Promise<boolean> => {
    try {
      if (Platform.OS === 'android') {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS,
        );
        const hasPermission = granted === PermissionsAndroid.RESULTS.GRANTED;
        setNotificationPermission(hasPermission);
        return hasPermission;
      } else {
        const authStatus = await messaging().requestPermission();
        const enabled =
          authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
          authStatus === messaging.AuthorizationStatus.PROVISIONAL;
        setNotificationPermission(enabled);
        return enabled;
      }
    } catch (error) {
      console.error('Permission request failed:', error);
      return false;
    }
  };

  const subscribeToTopic = async (topic: string): Promise<void> => {
    try {
      await messaging().subscribeToTopic(topic);
      console.log(`Subscribed to topic: ${topic}`);
    } catch (error) {
      console.error(`Failed to subscribe to topic ${topic}:`, error);
    }
  };

  const unsubscribeFromTopic = async (topic: string): Promise<void> => {
    try {
      await messaging().unsubscribeFromTopic(topic);
      console.log(`Unsubscribed from topic: ${topic}`);
    } catch (error) {
      console.error(`Failed to unsubscribe from topic ${topic}:`, error);
    }
  };

  const showLocalNotification = (title: string, message: string, data?: any) => {
    if (!isNotificationEnabled) return;

    PushNotification.localNotification({
      title,
      message,
      playSound: true,
      soundName: 'default',
      userInfo: data,
      actions: ['View'],
    });
  };

  const clearAllNotifications = () => {
    PushNotification.cancelAllLocalNotifications();
  };

  const setBadgeCount = (count: number) => {
    if (Platform.OS === 'ios') {
      PushNotification.setApplicationIconBadgeNumber(count);
    }
  };

  const value: NotificationContextType = {
    fcmToken,
    notificationPermission,
    requestPermission,
    subscribeToTopic,
    unsubscribeFromTopic,
    showLocalNotification,
    clearAllNotifications,
    setBadgeCount,
    isNotificationEnabled,
    setNotificationEnabled,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
import React, {useState} from 'react';
import {View, StyleSheet, Alert} from 'react-native';
import {Text, Button, Card, Switch, List} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import {StackNavigationProp} from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {OnboardingStackParamList} from '@navigation/OnboardingNavigator';
import {useNotification} from '@store/NotificationContext';
import {theme} from '@config/theme';

type NotificationSetupScreenNavigationProp = StackNavigationProp<
  OnboardingStackParamList,
  'NotificationSetup'
>;

interface Props {
  navigation: NotificationSetupScreenNavigationProp;
}

interface NotificationSetting {
  id: string;
  title: string;
  description: string;
  icon: string;
  enabled: boolean;
  required?: boolean;
}

export const NotificationSetupScreen: React.FC<Props> = ({navigation}) => {
  const {
    notificationPermission,
    requestPermission,
    isNotificationEnabled,
    setNotificationEnabled,
  } = useNotification();

  const [settings, setSettings] = useState<NotificationSetting[]>([
    {
      id: 'posts',
      title: 'New Posts',
      description: 'Get notified when new blog posts are published',
      icon: 'article',
      enabled: true,
    },
    {
      id: 'comments',
      title: 'Comments',
      description: 'Notifications for new comments on your posts',
      icon: 'comment',
      enabled: true,
    },
    {
      id: 'likes',
      title: 'Likes & Reactions',
      description: 'When someone likes or reacts to your content',
      icon: 'favorite',
      enabled: true,
    },
    {
      id: 'mentions',
      title: 'Mentions',
      description: 'When you are mentioned in posts or comments',
      icon: 'alternate-email',
      enabled: true,
      required: true,
    },
    {
      id: 'newsletter',
      title: 'Newsletter',
      description: 'Weekly digest of popular posts and updates',
      icon: 'email',
      enabled: false,
    },
    {
      id: 'marketing',
      title: 'Marketing',
      description: 'Updates about new features and promotions',
      icon: 'campaign',
      enabled: false,
    },
  ]);

  const [isEnabling, setIsEnabling] = useState(false);

  const handleToggleSetting = (id: string) => {
    setSettings(prev =>
      prev.map(setting =>
        setting.id === id ? {...setting, enabled: !setting.enabled} : setting
      )
    );
  };

  const handleEnableNotifications = async () => {
    setIsEnabling(true);
    
    try {
      const granted = await requestPermission();
      
      if (granted) {
        await setNotificationEnabled(true);
        Alert.alert(
          'Success',
          'Notifications have been enabled successfully!',
          [
            {
              text: 'Continue',
              onPress: () => navigation.navigate('OnboardingComplete'),
            },
          ]
        );
      } else {
        Alert.alert(
          'Permission Denied',
          'Notification permission was denied. You can enable it later in settings.',
          [
            {
              text: 'Continue',
              onPress: () => navigation.navigate('OnboardingComplete'),
            },
          ]
        );
      }
    } catch (error) {
      Alert.alert(
        'Error',
        'Failed to enable notifications. Please try again.'
      );
    } finally {
      setIsEnabling(false);
    }
  };

  const handleSkip = () => {
    navigation.navigate('OnboardingComplete');
  };

  const handleContinue = () => {
    navigation.navigate('OnboardingComplete');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.iconContainer}>
            <Icon
              name="notifications"
              size={80}
              color={theme.colors.primary}
            />
          </View>
          
          <Text style={styles.title}>Stay Updated</Text>
          <Text style={styles.subtitle}>
            Choose what notifications you'd like to receive to stay connected with your community.
          </Text>
        </View>

        <View style={styles.settingsContainer}>
          <Text style={styles.sectionTitle}>Notification Preferences</Text>
          
          {settings.map((setting) => (
            <Card key={setting.id} style={styles.settingCard}>
              <List.Item
                title={setting.title}
                description={setting.description}
                left={(props) => (
                  <Icon
                    name={setting.icon}
                    size={24}
                    color={theme.colors.primary}
                    style={styles.settingIcon}
                  />
                )}
                right={(props) => (
                  <View style={styles.switchContainer}>
                    {setting.required && (
                      <Text style={styles.requiredLabel}>Required</Text>
                    )}
                    <Switch
                      value={setting.enabled}
                      onValueChange={() => handleToggleSetting(setting.id)}
                      disabled={setting.required}
                    />
                  </View>
                )}
              />
            </Card>
          ))}
        </View>

        <View style={styles.statusContainer}>
          {notificationPermission ? (
            <View style={styles.statusItem}>
              <Icon name="check-circle" size={24} color={theme.colors.primary} />
              <Text style={styles.statusText}>
                Notification permission granted
              </Text>
            </View>
          ) : (
            <View style={styles.statusItem}>
              <Icon name="info" size={24} color={theme.colors.outline} />
              <Text style={styles.statusText}>
                Notification permission not granted
              </Text>
            </View>
          )}
        </View>

        <View style={styles.buttonContainer}>
          {!notificationPermission ? (
            <Button
              mode="contained"
              onPress={handleEnableNotifications}
              loading={isEnabling}
              disabled={isEnabling}
              style={styles.button}
              contentStyle={styles.buttonContent}>
              Enable Notifications
            </Button>
          ) : (
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
            Skip for now
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
  },
  header: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 32,
  },
  iconContainer: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.colors.onBackground,
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: theme.colors.onSurface,
    textAlign: 'center',
    lineHeight: 24,
    marginHorizontal: 20,
  },
  settingsContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onBackground,
    marginBottom: 16,
  },
  settingCard: {
    marginBottom: 8,
    elevation: 1,
  },
  settingIcon: {
    marginLeft: 16,
    alignSelf: 'center',
  },
  switchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  requiredLabel: {
    fontSize: 12,
    color: theme.colors.error,
    marginRight: 8,
    fontWeight: '600',
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
  },
  statusText: {
    fontSize: 14,
    color: theme.colors.onSurface,
    marginLeft: 12,
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
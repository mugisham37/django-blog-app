import React, {useState} from 'react';
import {View, StyleSheet, ScrollView, Alert} from 'react-native';
import {Text, Card, List, Switch, Button, Divider} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {theme} from '@config/theme';
import {useBiometric} from '@store/BiometricContext';
import {useNotification} from '@store/NotificationContext';
import {useAuth} from '@store/AuthContext';

export const SettingsScreen: React.FC = () => {
  const {logout} = useAuth();
  const {
    isBiometricSupported,
    isBiometricEnabled,
    enableBiometric,
    disableBiometric,
  } = useBiometric();
  const {
    isNotificationEnabled,
    setNotificationEnabled,
  } = useNotification();

  const [settings, setSettings] = useState({
    darkMode: false,
    autoSync: true,
    offlineMode: true,
    analytics: true,
    crashReporting: true,
  });

  const handleBiometricToggle = async () => {
    try {
      if (isBiometricEnabled) {
        await disableBiometric();
      } else {
        await enableBiometric();
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to update biometric settings');
    }
  };

  const handleNotificationToggle = async () => {
    try {
      await setNotificationEnabled(!isNotificationEnabled);
    } catch (error) {
      Alert.alert('Error', 'Failed to update notification settings');
    }
  };

  const handleSettingToggle = (key: keyof typeof settings) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will clear all cached data. Are you sure?',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => {
            // Clear cache logic
            Alert.alert('Success', 'Cache cleared successfully');
          },
        },
      ]
    );
  };

  const handleResetSettings = () => {
    Alert.alert(
      'Reset Settings',
      'This will reset all settings to default values. Are you sure?',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            setSettings({
              darkMode: false,
              autoSync: true,
              offlineMode: true,
              analytics: true,
              crashReporting: true,
            });
            Alert.alert('Success', 'Settings reset to default');
          },
        },
      ]
    );
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This action cannot be undone. All your data will be permanently deleted.',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            // Delete account logic
            Alert.alert('Account Deleted', 'Your account has been deleted');
            logout();
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        
        {/* Security Settings */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Security & Privacy</Text>
          
          {isBiometricSupported && (
            <List.Item
              title="Biometric Authentication"
              description="Use fingerprint or face recognition to unlock"
              left={(props) => <List.Icon {...props} icon="fingerprint" />}
              right={() => (
                <Switch
                  value={isBiometricEnabled}
                  onValueChange={handleBiometricToggle}
                />
              )}
            />
          )}
          
          <List.Item
            title="Two-Factor Authentication"
            description="Add an extra layer of security"
            left={(props) => <List.Icon {...props} icon="security" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Privacy Settings"
            description="Control who can see your content"
            left={(props) => <List.Icon {...props} icon="privacy-tip" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* Notification Settings */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          
          <List.Item
            title="Push Notifications"
            description="Receive notifications on this device"
            left={(props) => <List.Icon {...props} icon="notifications" />}
            right={() => (
              <Switch
                value={isNotificationEnabled}
                onValueChange={handleNotificationToggle}
              />
            )}
          />
          
          <List.Item
            title="Notification Preferences"
            description="Choose what notifications to receive"
            left={(props) => <List.Icon {...props} icon="tune" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Quiet Hours"
            description="Set times when notifications are muted"
            left={(props) => <List.Icon {...props} icon="do-not-disturb" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* App Settings */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>App Preferences</Text>
          
          <List.Item
            title="Dark Mode"
            description="Use dark theme"
            left={(props) => <List.Icon {...props} icon="dark-mode" />}
            right={() => (
              <Switch
                value={settings.darkMode}
                onValueChange={() => handleSettingToggle('darkMode')}
              />
            )}
          />
          
          <List.Item
            title="Auto Sync"
            description="Automatically sync data when online"
            left={(props) => <List.Icon {...props} icon="sync" />}
            right={() => (
              <Switch
                value={settings.autoSync}
                onValueChange={() => handleSettingToggle('autoSync')}
              />
            )}
          />
          
          <List.Item
            title="Offline Mode"
            description="Enable offline reading and caching"
            left={(props) => <List.Icon {...props} icon="offline-bolt" />}
            right={() => (
              <Switch
                value={settings.offlineMode}
                onValueChange={() => handleSettingToggle('offlineMode')}
              />
            )}
          />
          
          <List.Item
            title="Language"
            description="English (US)"
            left={(props) => <List.Icon {...props} icon="language" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* Data & Analytics */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Data & Analytics</Text>
          
          <List.Item
            title="Usage Analytics"
            description="Help improve the app by sharing usage data"
            left={(props) => <List.Icon {...props} icon="analytics" />}
            right={() => (
              <Switch
                value={settings.analytics}
                onValueChange={() => handleSettingToggle('analytics')}
              />
            )}
          />
          
          <List.Item
            title="Crash Reporting"
            description="Automatically send crash reports"
            left={(props) => <List.Icon {...props} icon="bug-report" />}
            right={() => (
              <Switch
                value={settings.crashReporting}
                onValueChange={() => handleSettingToggle('crashReporting')}
              />
            )}
          />
          
          <List.Item
            title="Data Usage"
            description="View and manage data consumption"
            left={(props) => <List.Icon {...props} icon="data-usage" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* Storage & Cache */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Storage & Cache</Text>
          
          <List.Item
            title="Storage Usage"
            description="View app storage usage"
            left={(props) => <List.Icon {...props} icon="storage" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Clear Cache"
            description="Free up space by clearing cached data"
            left={(props) => <List.Icon {...props} icon="clear" />}
            onPress={handleClearCache}
          />
          
          <List.Item
            title="Offline Content"
            description="Manage downloaded content"
            left={(props) => <List.Icon {...props} icon="download" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* Support & About */}
        <Card style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Support & About</Text>
          
          <List.Item
            title="Help Center"
            description="Get help and find answers"
            left={(props) => <List.Icon {...props} icon="help" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Contact Support"
            description="Get in touch with our support team"
            left={(props) => <List.Icon {...props} icon="support" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Terms of Service"
            description="Read our terms and conditions"
            left={(props) => <List.Icon {...props} icon="description" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Privacy Policy"
            description="Learn about our privacy practices"
            left={(props) => <List.Icon {...props} icon="policy" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="About"
            description="App version and information"
            left={(props) => <List.Icon {...props} icon="info" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* Danger Zone */}
        <Card style={[styles.sectionCard, styles.dangerCard]}>
          <Text style={[styles.sectionTitle, styles.dangerTitle]}>Danger Zone</Text>
          
          <List.Item
            title="Reset Settings"
            description="Reset all settings to default values"
            left={(props) => <List.Icon {...props} icon="restore" color={theme.colors.error} />}
            titleStyle={styles.dangerText}
            onPress={handleResetSettings}
          />
          
          <Divider style={styles.divider} />
          
          <List.Item
            title="Delete Account"
            description="Permanently delete your account and all data"
            left={(props) => <List.Icon {...props} icon="delete-forever" color={theme.colors.error} />}
            titleStyle={styles.dangerText}
            onPress={handleDeleteAccount}
          />
        </Card>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Fullstack Monolith Mobile v1.0.0
          </Text>
          <Text style={styles.footerText}>
            © 2024 Fullstack Monolith. All rights reserved.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollView: {
    flex: 1,
  },
  sectionCard: {
    margin: 16,
    marginBottom: 8,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onSurface,
    padding: 16,
    paddingBottom: 8,
  },
  dangerCard: {
    borderColor: theme.colors.error,
    borderWidth: 1,
  },
  dangerTitle: {
    color: theme.colors.error,
  },
  dangerText: {
    color: theme.colors.error,
  },
  divider: {
    marginHorizontal: 16,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
    marginBottom: 20,
  },
  footerText: {
    fontSize: 12,
    color: theme.colors.outline,
    textAlign: 'center',
    marginBottom: 4,
  },
});
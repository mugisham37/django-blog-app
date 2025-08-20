import React, {useState} from 'react';
import {View, StyleSheet, Alert, Platform} from 'react-native';
import {Text, Button, Card, List} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import {StackNavigationProp} from '@react-navigation/stack';
import {request, PERMISSIONS, RESULTS, Permission} from 'react-native-permissions';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {OnboardingStackParamList} from '@navigation/OnboardingNavigator';
import {theme} from '@config/theme';

type PermissionsScreenNavigationProp = StackNavigationProp<
  OnboardingStackParamList,
  'Permissions'
>;

interface Props {
  navigation: PermissionsScreenNavigationProp;
}

interface PermissionItem {
  id: string;
  title: string;
  description: string;
  icon: string;
  permission: Permission;
  required: boolean;
  granted: boolean;
}

export const PermissionsScreen: React.FC<Props> = ({navigation}) => {
  const [permissions, setPermissions] = useState<PermissionItem[]>([
    {
      id: 'camera',
      title: 'Camera',
      description: 'Take photos for profile pictures and content',
      icon: 'camera-alt',
      permission: Platform.OS === 'ios' ? PERMISSIONS.IOS.CAMERA : PERMISSIONS.ANDROID.CAMERA,
      required: false,
      granted: false,
    },
    {
      id: 'photos',
      title: 'Photo Library',
      description: 'Select images from your photo library',
      icon: 'photo-library',
      permission: Platform.OS === 'ios' 
        ? PERMISSIONS.IOS.PHOTO_LIBRARY 
        : PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE,
      required: false,
      granted: false,
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Receive updates about new posts and comments',
      icon: 'notifications',
      permission: Platform.OS === 'ios' 
        ? PERMISSIONS.IOS.NOTIFICATIONS 
        : PERMISSIONS.ANDROID.POST_NOTIFICATIONS,
      required: true,
      granted: false,
    },
  ]);

  const [isLoading, setIsLoading] = useState(false);

  const requestPermission = async (permissionItem: PermissionItem) => {
    try {
      const result = await request(permissionItem.permission);
      
      const granted = result === RESULTS.GRANTED;
      
      setPermissions(prev =>
        prev.map(p =>
          p.id === permissionItem.id ? {...p, granted} : p
        )
      );

      if (!granted && permissionItem.required) {
        Alert.alert(
          'Permission Required',
          `${permissionItem.title} permission is required for the app to function properly.`,
          [
            {text: 'Cancel', style: 'cancel'},
            {text: 'Retry', onPress: () => requestPermission(permissionItem)},
          ]
        );
      }
    } catch (error) {
      console.error('Permission request failed:', error);
      Alert.alert('Error', 'Failed to request permission. Please try again.');
    }
  };

  const requestAllPermissions = async () => {
    setIsLoading(true);
    
    for (const permission of permissions) {
      await requestPermission(permission);
    }
    
    setIsLoading(false);
  };

  const handleContinue = () => {
    const requiredPermissions = permissions.filter(p => p.required);
    const grantedRequiredPermissions = requiredPermissions.filter(p => p.granted);
    
    if (grantedRequiredPermissions.length < requiredPermissions.length) {
      Alert.alert(
        'Required Permissions',
        'Some required permissions are not granted. The app may not function properly.',
        [
          {text: 'Go Back', style: 'cancel'},
          {text: 'Continue Anyway', onPress: () => navigation.navigate('BiometricSetup')},
        ]
      );
    } else {
      navigation.navigate('BiometricSetup');
    }
  };

  const handleSkip = () => {
    navigation.navigate('BiometricSetup');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>App Permissions</Text>
          <Text style={styles.subtitle}>
            We need some permissions to provide you with the best experience.
          </Text>
        </View>

        <View style={styles.permissionsContainer}>
          {permissions.map((permission) => (
            <Card key={permission.id} style={styles.permissionCard}>
              <List.Item
                title={permission.title}
                description={permission.description}
                left={(props) => (
                  <Icon
                    name={permission.icon}
                    size={24}
                    color={theme.colors.primary}
                    style={styles.permissionIcon}
                  />
                )}
                right={(props) => (
                  <View style={styles.permissionStatus}>
                    {permission.required && (
                      <Text style={styles.requiredLabel}>Required</Text>
                    )}
                    <Icon
                      name={permission.granted ? 'check-circle' : 'radio-button-unchecked'}
                      size={24}
                      color={permission.granted ? theme.colors.primary : theme.colors.outline}
                    />
                  </View>
                )}
                onPress={() => requestPermission(permission)}
              />
            </Card>
          ))}
        </View>

        <View style={styles.buttonContainer}>
          <Button
            mode="contained"
            onPress={requestAllPermissions}
            loading={isLoading}
            disabled={isLoading}
            style={styles.button}
            contentStyle={styles.buttonContent}>
            Grant All Permissions
          </Button>
          
          <Button
            mode="outlined"
            onPress={handleContinue}
            style={[styles.button, styles.continueButton]}
            contentStyle={styles.buttonContent}>
            Continue
          </Button>
          
          <Button
            mode="text"
            onPress={handleSkip}
            style={styles.skipButton}>
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
  },
  permissionsContainer: {
    flex: 1,
  },
  permissionCard: {
    marginBottom: 12,
    elevation: 2,
  },
  permissionIcon: {
    marginLeft: 16,
    alignSelf: 'center',
  },
  permissionStatus: {
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
  buttonContainer: {
    paddingBottom: 40,
  },
  button: {
    borderRadius: 25,
    marginBottom: 12,
  },
  continueButton: {
    borderColor: theme.colors.primary,
  },
  buttonContent: {
    paddingVertical: 8,
  },
  skipButton: {
    marginTop: 8,
  },
});
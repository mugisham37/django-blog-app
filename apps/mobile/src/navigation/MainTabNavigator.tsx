import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createStackNavigator} from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {Platform} from 'react-native';

import {HomeScreen} from '@screens/main/HomeScreen';
import {BlogScreen} from '@screens/main/BlogScreen';
import {BlogDetailScreen} from '@screens/main/BlogDetailScreen';
import {ProfileScreen} from '@screens/main/ProfileScreen';
import {SettingsScreen} from '@screens/main/SettingsScreen';
import {NotificationsScreen} from '@screens/main/NotificationsScreen';
import {SearchScreen} from '@screens/main/SearchScreen';
import {theme} from '@config/theme';

export type MainTabParamList = {
  HomeTab: undefined;
  BlogTab: undefined;
  SearchTab: undefined;
  NotificationsTab: undefined;
  ProfileTab: undefined;
};

export type HomeStackParamList = {
  Home: undefined;
  Settings: undefined;
};

export type BlogStackParamList = {
  Blog: undefined;
  BlogDetail: {id: string};
};

export type ProfileStackParamList = {
  Profile: undefined;
  Settings: undefined;
};

const Tab = createBottomTabNavigator<MainTabParamList>();
const HomeStack = createStackNavigator<HomeStackParamList>();
const BlogStack = createStackNavigator<BlogStackParamList>();
const ProfileStack = createStackNavigator<ProfileStackParamList>();

const HomeStackNavigator = () => (
  <HomeStack.Navigator
    screenOptions={{
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
    }}>
    <HomeStack.Screen 
      name="Home" 
      component={HomeScreen}
      options={{
        title: 'Dashboard',
        headerRight: () => (
          <Icon 
            name="settings" 
            size={24} 
            color={theme.colors.text}
            style={{marginRight: 16}}
          />
        ),
      }}
    />
    <HomeStack.Screen 
      name="Settings" 
      component={SettingsScreen}
      options={{title: 'Settings'}}
    />
  </HomeStack.Navigator>
);

const BlogStackNavigator = () => (
  <BlogStack.Navigator
    screenOptions={{
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
    }}>
    <BlogStack.Screen 
      name="Blog" 
      component={BlogScreen}
      options={{
        title: 'Blog Posts',
        headerRight: () => (
          <Icon 
            name="search" 
            size={24} 
            color={theme.colors.text}
            style={{marginRight: 16}}
          />
        ),
      }}
    />
    <BlogStack.Screen 
      name="BlogDetail" 
      component={BlogDetailScreen}
      options={{
        title: 'Post Details',
        headerRight: () => (
          <Icon 
            name="share" 
            size={24} 
            color={theme.colors.text}
            style={{marginRight: 16}}
          />
        ),
      }}
    />
  </BlogStack.Navigator>
);

const ProfileStackNavigator = () => (
  <ProfileStack.Navigator
    screenOptions={{
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
    }}>
    <ProfileStack.Screen 
      name="Profile" 
      component={ProfileScreen}
      options={{
        title: 'Profile',
        headerRight: () => (
          <Icon 
            name="edit" 
            size={24} 
            color={theme.colors.text}
            style={{marginRight: 16}}
          />
        ),
      }}
    />
    <ProfileStack.Screen 
      name="Settings" 
      component={SettingsScreen}
      options={{title: 'Settings'}}
    />
  </ProfileStack.Navigator>
);

export const MainTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName: string;

          switch (route.name) {
            case 'HomeTab':
              iconName = focused ? 'home' : 'home';
              break;
            case 'BlogTab':
              iconName = focused ? 'article' : 'article';
              break;
            case 'SearchTab':
              iconName = focused ? 'search' : 'search';
              break;
            case 'NotificationsTab':
              iconName = focused ? 'notifications' : 'notifications-none';
              break;
            case 'ProfileTab':
              iconName = focused ? 'person' : 'person-outline';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          borderTopWidth: 1,
          paddingBottom: Platform.OS === 'ios' ? 20 : 5,
          paddingTop: 5,
          height: Platform.OS === 'ios' ? 85 : 60,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
        headerShown: false,
      })}>
      <Tab.Screen
        name="HomeTab"
        component={HomeStackNavigator}
        options={{
          tabBarLabel: 'Home',
        }}
      />
      <Tab.Screen
        name="BlogTab"
        component={BlogStackNavigator}
        options={{
          tabBarLabel: 'Blog',
        }}
      />
      <Tab.Screen
        name="SearchTab"
        component={SearchScreen}
        options={{
          tabBarLabel: 'Search',
          headerShown: true,
          headerTitle: 'Search',
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
        }}
      />
      <Tab.Screen
        name="NotificationsTab"
        component={NotificationsScreen}
        options={{
          tabBarLabel: 'Notifications',
          headerShown: true,
          headerTitle: 'Notifications',
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
          headerRight: () => (
            <Icon 
              name="mark-email-read" 
              size={24} 
              color={theme.colors.text}
              style={{marginRight: 16}}
            />
          ),
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileStackNavigator}
        options={{
          tabBarLabel: 'Profile',
        }}
      />
    </Tab.Navigator>
  );
};
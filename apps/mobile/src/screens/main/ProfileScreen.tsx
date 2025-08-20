import React, {useState} from 'react';
import {View, StyleSheet, ScrollView, RefreshControl} from 'react-native';
import {Text, Card, Button, Avatar, List, Divider} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useQuery} from 'react-query';
import {theme} from '@config/theme';
import {ApiClient} from '@services/ApiClient';
import {useAuth} from '@store/AuthContext';

interface UserProfile {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  bio?: string;
  avatar?: string;
  dateJoined: string;
  lastLogin: string;
  postsCount: number;
  commentsCount: number;
  likesReceived: number;
  followersCount: number;
  followingCount: number;
}

interface UserStats {
  totalPosts: number;
  totalComments: number;
  totalLikes: number;
  totalViews: number;
  thisMonthPosts: number;
  thisMonthViews: number;
}

export const ProfileScreen: React.FC = () => {
  const {state: authState, logout} = useAuth();
  const [refreshing, setRefreshing] = useState(false);

  const {
    data: profile,
    isLoading: profileLoading,
    refetch: refetchProfile,
  } = useQuery<UserProfile>(
    'userProfile',
    async () => {
      const response = await ApiClient.get<UserProfile>('/auth/profile/');
      return response.data;
    },
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery<UserStats>(
    'userStats',
    async () => {
      const response = await ApiClient.get<UserStats>('/auth/profile/stats/');
      return response.data;
    },
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refetchProfile(), refetchStats()]);
    setRefreshing(false);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        
        {/* Profile Header */}
        <Card style={styles.profileCard}>
          <View style={styles.profileHeader}>
            <Avatar.Text
              size={80}
              label={profile?.username?.charAt(0).toUpperCase() || 'U'}
              style={styles.avatar}
            />
            <View style={styles.profileInfo}>
              <Text style={styles.username}>
                {profile?.firstName && profile?.lastName
                  ? `${profile.firstName} ${profile.lastName}`
                  : profile?.username || 'User'}
              </Text>
              <Text style={styles.handle}>@{profile?.username || 'user'}</Text>
              <Text style={styles.email}>{profile?.email}</Text>
            </View>
          </View>
          
          {profile?.bio && (
            <Text style={styles.bio}>{profile.bio}</Text>
          )}
          
          <View style={styles.joinDate}>
            <Icon name="calendar-today" size={16} color={theme.colors.outline} />
            <Text style={styles.joinDateText}>
              Joined {profile ? formatDate(profile.dateJoined) : ''}
            </Text>
          </View>
          
          <View style={styles.profileActions}>
            <Button
              mode="contained"
              onPress={() => {}}
              style={styles.editButton}
              contentStyle={styles.buttonContent}>
              Edit Profile
            </Button>
            <Button
              mode="outlined"
              onPress={() => {}}
              style={styles.shareButton}
              contentStyle={styles.buttonContent}>
              Share Profile
            </Button>
          </View>
        </Card>

        {/* Stats Section */}
        <Card style={styles.statsCard}>
          <Text style={styles.sectionTitle}>Your Statistics</Text>
          
          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>
                {stats ? formatNumber(stats.totalPosts) : '0'}
              </Text>
              <Text style={styles.statLabel}>Posts</Text>
            </View>
            
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>
                {stats ? formatNumber(stats.totalViews) : '0'}
              </Text>
              <Text style={styles.statLabel}>Views</Text>
            </View>
            
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>
                {stats ? formatNumber(stats.totalLikes) : '0'}
              </Text>
              <Text style={styles.statLabel}>Likes</Text>
            </View>
            
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>
                {stats ? formatNumber(stats.totalComments) : '0'}
              </Text>
              <Text style={styles.statLabel}>Comments</Text>
            </View>
          </View>
          
          <Divider style={styles.divider} />
          
          <View style={styles.monthlyStats}>
            <Text style={styles.monthlyStatsTitle}>This Month</Text>
            <View style={styles.monthlyStatsRow}>
              <View style={styles.monthlyStatItem}>
                <Text style={styles.monthlyStatNumber}>
                  {stats ? stats.thisMonthPosts : 0}
                </Text>
                <Text style={styles.monthlyStatLabel}>New Posts</Text>
              </View>
              <View style={styles.monthlyStatItem}>
                <Text style={styles.monthlyStatNumber}>
                  {stats ? formatNumber(stats.thisMonthViews) : '0'}
                </Text>
                <Text style={styles.monthlyStatLabel}>Views</Text>
              </View>
            </View>
          </View>
        </Card>

        {/* Menu Section */}
        <Card style={styles.menuCard}>
          <List.Item
            title="My Posts"
            description="View and manage your posts"
            left={(props) => <List.Icon {...props} icon="article" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Drafts"
            description="Continue writing your drafts"
            left={(props) => <List.Icon {...props} icon="draft" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Bookmarks"
            description="Your saved posts"
            left={(props) => <List.Icon {...props} icon="bookmark" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Analytics"
            description="Detailed insights and metrics"
            left={(props) => <List.Icon {...props} icon="analytics" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* Settings Section */}
        <Card style={styles.menuCard}>
          <List.Item
            title="Settings"
            description="App preferences and configuration"
            left={(props) => <List.Icon {...props} icon="settings" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Privacy & Security"
            description="Manage your privacy settings"
            left={(props) => <List.Icon {...props} icon="security" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Notifications"
            description="Configure notification preferences"
            left={(props) => <List.Icon {...props} icon="notifications" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
          
          <List.Item
            title="Help & Support"
            description="Get help and contact support"
            left={(props) => <List.Icon {...props} icon="help" />}
            right={(props) => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {}}
          />
        </Card>

        {/* Logout Section */}
        <Card style={styles.logoutCard}>
          <List.Item
            title="Sign Out"
            description="Sign out of your account"
            left={(props) => <List.Icon {...props} icon="logout" color={theme.colors.error} />}
            titleStyle={styles.logoutText}
            onPress={handleLogout}
          />
        </Card>
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
  profileCard: {
    margin: 16,
    padding: 20,
    elevation: 3,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatar: {
    backgroundColor: theme.colors.primary,
  },
  profileInfo: {
    marginLeft: 16,
    flex: 1,
  },
  username: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.onSurface,
  },
  handle: {
    fontSize: 14,
    color: theme.colors.primary,
    marginTop: 2,
  },
  email: {
    fontSize: 14,
    color: theme.colors.outline,
    marginTop: 4,
  },
  bio: {
    fontSize: 14,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 20,
    marginBottom: 12,
  },
  joinDate: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  joinDateText: {
    fontSize: 14,
    color: theme.colors.outline,
    marginLeft: 8,
  },
  profileActions: {
    flexDirection: 'row',
    gap: 12,
  },
  editButton: {
    flex: 1,
    borderRadius: 20,
  },
  shareButton: {
    flex: 1,
    borderRadius: 20,
  },
  buttonContent: {
    paddingVertical: 4,
  },
  statsCard: {
    margin: 16,
    marginTop: 0,
    padding: 20,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  statLabel: {
    fontSize: 12,
    color: theme.colors.outline,
    marginTop: 4,
  },
  divider: {
    marginVertical: 16,
  },
  monthlyStats: {
    alignItems: 'center',
  },
  monthlyStatsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 12,
  },
  monthlyStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  monthlyStatItem: {
    alignItems: 'center',
  },
  monthlyStatNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.secondary,
  },
  monthlyStatLabel: {
    fontSize: 12,
    color: theme.colors.outline,
    marginTop: 4,
  },
  menuCard: {
    margin: 16,
    marginTop: 0,
    elevation: 3,
  },
  logoutCard: {
    margin: 16,
    marginTop: 0,
    marginBottom: 40,
    elevation: 3,
  },
  logoutText: {
    color: theme.colors.error,
  },
});
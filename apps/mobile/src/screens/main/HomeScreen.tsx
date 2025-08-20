import React, {useEffect, useState} from 'react';
import {View, StyleSheet, ScrollView, RefreshControl, Dimensions} from 'react-native';
import {Text, Card, Button, Avatar, Chip} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useQuery} from 'react-query';
import {LineChart} from 'react-native-chart-kit';
import {theme} from '@config/theme';
import {ApiClient} from '@services/ApiClient';
import {useAuth} from '@store/AuthContext';

const {width} = Dimensions.get('window');

interface DashboardStats {
  totalPosts: number;
  totalComments: number;
  totalViews: number;
  totalLikes: number;
}

interface RecentPost {
  id: string;
  title: string;
  excerpt: string;
  publishedAt: string;
  viewCount: number;
  commentCount: number;
}

interface AnalyticsData {
  labels: string[];
  datasets: [{
    data: number[];
    color?: (opacity: number) => string;
    strokeWidth?: number;
  }];
}

export const HomeScreen: React.FC = () => {
  const {state: authState} = useAuth();
  const [refreshing, setRefreshing] = useState(false);

  const {
    data: dashboardStats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery<DashboardStats>(
    'dashboardStats',
    async () => {
      const response = await ApiClient.get<DashboardStats>('/dashboard/stats/');
      return response.data;
    },
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const {
    data: recentPosts,
    isLoading: postsLoading,
    refetch: refetchPosts,
  } = useQuery<RecentPost[]>(
    'recentPosts',
    async () => {
      const response = await ApiClient.get<RecentPost[]>('/posts/recent/', {limit: 5});
      return response.data;
    },
    {
      staleTime: 2 * 60 * 1000, // 2 minutes
    }
  );

  const {
    data: analyticsData,
    isLoading: analyticsLoading,
    refetch: refetchAnalytics,
  } = useQuery<AnalyticsData>(
    'weeklyAnalytics',
    async () => {
      const response = await ApiClient.get<any>('/analytics/weekly/');
      return {
        labels: response.data.labels,
        datasets: [{
          data: response.data.views,
          color: (opacity = 1) => `rgba(134, 65, 244, ${opacity})`,
          strokeWidth: 2,
        }],
      };
    },
    {
      staleTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      refetchStats(),
      refetchPosts(),
      refetchAnalytics(),
    ]);
    setRefreshing(false);
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

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        
        {/* Welcome Section */}
        <View style={styles.welcomeSection}>
          <View style={styles.welcomeHeader}>
            <Avatar.Text
              size={50}
              label={authState.user?.username?.charAt(0).toUpperCase() || 'U'}
              style={styles.avatar}
            />
            <View style={styles.welcomeText}>
              <Text style={styles.welcomeTitle}>
                Welcome back, {authState.user?.username || 'User'}!
              </Text>
              <Text style={styles.welcomeSubtitle}>
                Here's what's happening with your blog
              </Text>
            </View>
          </View>
        </View>

        {/* Stats Cards */}
        <View style={styles.statsContainer}>
          <View style={styles.statsRow}>
            <Card style={[styles.statCard, styles.statCardLeft]}>
              <View style={styles.statContent}>
                <Icon name="article" size={24} color={theme.colors.primary} />
                <Text style={styles.statNumber}>
                  {dashboardStats ? formatNumber(dashboardStats.totalPosts) : '0'}
                </Text>
                <Text style={styles.statLabel}>Posts</Text>
              </View>
            </Card>
            
            <Card style={[styles.statCard, styles.statCardRight]}>
              <View style={styles.statContent}>
                <Icon name="comment" size={24} color={theme.colors.secondary} />
                <Text style={styles.statNumber}></Text>             {dashboardStats ? formatNumber(dashboardStats.totalComments) : '0'}
                </Text>
                <Text style={styles.statLabel}>Comments</Text>
              </View>
            </Card>
          </View>
          
          <View style={styles.statsRow}>
            <Card style={[styles.statCard, styles.statCardLeft]}>
              <View style={styles.statContent}>
                <Icon name="visibility" size={24} color={theme.colors.tertiary} />
                <Text style={styles.statNumber}>
                  {dashboardStats ? formatNumber(dashboardStats.totalViews) : '0'}
                </Text>
                <Text style={styles.statLabel}>Views</Text>
              </View>
            </Card>
            
            <Card style={[styles.statCard, styles.statCardRight]}>
              <View style={styles.statContent}>
                <Icon name="favorite" size={24} color={theme.colors.error} />
                <Text style={styles.statNumber}>
                  {dashboardStats ? formatNumber(dashboardStats.totalLikes) : '0'}
                </Text>
                <Text style={styles.statLabel}>Likes</Text>
              </View>
            </Card>
          </View>
        </View>

        {/* Analytics Chart */}
        {analyticsData && (
          <Card style={styles.chartCard}>
            <View style={styles.chartHeader}>
              <Text style={styles.chartTitle}>Weekly Views</Text>
              <Chip icon="trending-up" mode="outlined" compact>
                Last 7 days
              </Chip>
            </View>
            <LineChart
              data={analyticsData}
              width={width - 48}
              height={200}
              chartConfig={{
                backgroundColor: theme.colors.surface,
                backgroundGradientFrom: theme.colors.surface,
                backgroundGradientTo: theme.colors.surface,
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(134, 65, 244, ${opacity})`,
                labelColor: (opacity = 1) => theme.colors.onSurface,
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '4',
                  strokeWidth: '2',
                  stroke: theme.colors.primary,
                },
              }}
              bezier
              style={styles.chart}
            />
          </Card>
        )}

        {/* Recent Posts */}
        <Card style={styles.recentPostsCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Posts</Text>
            <Button mode="text" compact onPress={() => {}}>
              View All
            </Button>
          </View>
          
          {recentPosts?.map((post) => (
            <View key={post.id} style={styles.postItem}>
              <View style={styles.postContent}>
                <Text style={styles.postTitle} numberOfLines={2}>
                  {post.title}
                </Text>
                <Text style={styles.postExcerpt} numberOfLines={2}>
                  {post.excerpt}
                </Text>
                <View style={styles.postMeta}>
                  <Text style={styles.postDate}>
                    {formatDate(post.publishedAt)}
                  </Text>
                  <View style={styles.postStats}>
                    <View style={styles.postStat}>
                      <Icon name="visibility" size={14} color={theme.colors.outline} />
                      <Text style={styles.postStatText}>{post.viewCount}</Text>
                    </View>
                    <View style={styles.postStat}>
                      <Icon name="comment" size={14} color={theme.colors.outline} />
                      <Text style={styles.postStatText}>{post.commentCount}</Text>
                    </View>
                  </View>
                </View>
              </View>
            </View>
          ))}
          
          {(!recentPosts || recentPosts.length === 0) && (
            <View style={styles.emptyState}>
              <Icon name="article" size={48} color={theme.colors.outline} />
              <Text style={styles.emptyStateText}>No recent posts</Text>
              <Button mode="contained" onPress={() => {}} style={styles.createPostButton}>
                Create Your First Post
              </Button>
            </View>
          )}
        </Card>

        {/* Quick Actions */}
        <Card style={styles.quickActionsCard}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActions}>
            <Button
              mode="contained"
              icon="add"
              onPress={() => {}}
              style={styles.quickActionButton}>
              New Post
            </Button>
            <Button
              mode="outlined"
              icon="analytics"
              onPress={() => {}}
              style={styles.quickActionButton}>
              Analytics
            </Button>
          </View>
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
  welcomeSection: {
    padding: 20,
  },
  welcomeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    backgroundColor: theme.colors.primary,
  },
  welcomeText: {
    marginLeft: 16,
    flex: 1,
  },
  welcomeTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.onBackground,
  },
  welcomeSubtitle: {
    fontSize: 14,
    color: theme.colors.onSurface,
    marginTop: 4,
  },
  statsContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  statCard: {
    flex: 1,
    elevation: 2,
  },
  statCardLeft: {
    marginRight: 6,
  },
  statCardRight: {
    marginLeft: 6,
  },
  statContent: {
    padding: 16,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.onSurface,
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: theme.colors.outline,
    marginTop: 4,
  },
  chartCard: {
    margin: 20,
    padding: 16,
    elevation: 2,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onSurface,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  recentPostsCard: {
    margin: 20,
    padding: 16,
    elevation: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onSurface,
  },
  postItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.outline,
  },
  postContent: {
    flex: 1,
  },
  postTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 4,
  },
  postExcerpt: {
    fontSize: 14,
    color: theme.colors.outline,
    marginBottom: 8,
  },
  postMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  postDate: {
    fontSize: 12,
    color: theme.colors.outline,
  },
  postStats: {
    flexDirection: 'row',
  },
  postStat: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 12,
  },
  postStatText: {
    fontSize: 12,
    color: theme.colors.outline,
    marginLeft: 4,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    fontSize: 16,
    color: theme.colors.outline,
    marginTop: 16,
    marginBottom: 20,
  },
  createPostButton: {
    borderRadius: 20,
  },
  quickActionsCard: {
    margin: 20,
    padding: 16,
    elevation: 2,
    marginBottom: 40,
  },
  quickActions: {
    flexDirection: 'row',
    marginTop: 16,
  },
  quickActionButton: {
    flex: 1,
    marginHorizontal: 6,
    borderRadius: 20,
  },
});
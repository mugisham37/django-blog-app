import React, {useState} from 'react';
import {View, StyleSheet, FlatList, RefreshControl} from 'react-native';
import {Text, Card, Avatar, Button, Chip} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useQuery} from 'react-query';
import {theme} from '@config/theme';
import {ApiClient} from '@services/ApiClient';

interface Notification {
  id: string;
  type: 'like' | 'comment' | 'follow' | 'post' | 'mention';
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
  actor?: {
    id: string;
    username: string;
    avatar?: string;
  };
  target?: {
    id: string;
    title: string;
    type: 'post' | 'comment';
  };
}

export const NotificationsScreen: React.FC = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const {
    data: notifications,
    isLoading,
    refetch,
  } = useQuery<Notification[]>(
    ['notifications', filter],
    async () => {
      const response = await ApiClient.get<Notification[]>('/notifications/', {
        filter: filter === 'all' ? undefined : 'unread',
      });
      return response.data;
    },
    {
      staleTime: 30 * 1000, // 30 seconds
    }
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await ApiClient.patch(`/notifications/${notificationId}/`, {
        isRead: true,
      });
      refetch();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await ApiClient.post('/notifications/mark-all-read/');
      refetch();
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'like':
        return 'favorite';
      case 'comment':
        return 'comment';
      case 'follow':
        return 'person-add';
      case 'post':
        return 'article';
      case 'mention':
        return 'alternate-email';
      default:
        return 'notifications';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'like':
        return theme.colors.error;
      case 'comment':
        return theme.colors.primary;
      case 'follow':
        return theme.colors.secondary;
      case 'post':
        return theme.colors.tertiary;
      case 'mention':
        return theme.colors.primary;
      default:
        return theme.colors.outline;
    }
  };

  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes}m ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours}h ago`;
    } else if (diffInSeconds < 604800) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days}d ago`;
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    }
  };

  const renderNotification = ({item}: {item: Notification}) => (
    <Card
      style={[
        styles.notificationCard,
        !item.isRead && styles.unreadCard,
      ]}
      onPress={() => {
        if (!item.isRead) {
          markAsRead(item.id);
        }
        // Navigate to relevant screen based on notification type
      }}>
      <View style={styles.notificationContent}>
        <View style={styles.notificationHeader}>
          <View style={styles.iconContainer}>
            <Icon
              name={getNotificationIcon(item.type)}
              size={20}
              color={getNotificationColor(item.type)}
            />
          </View>
          
          {item.actor && (
            <Avatar.Text
              size={40}
              label={item.actor.username.charAt(0).toUpperCase()}
              style={styles.actorAvatar}
            />
          )}
          
          <View style={styles.notificationText}>
            <Text style={styles.notificationTitle} numberOfLines={2}>
              {item.title}
            </Text>
            <Text style={styles.notificationMessage} numberOfLines={3}>
              {item.message}
            </Text>
          </View>
          
          <View style={styles.notificationMeta}>
            <Text style={styles.timeAgo}>
              {formatTimeAgo(item.createdAt)}
            </Text>
            {!item.isRead && <View style={styles.unreadDot} />}
          </View>
        </View>
        
        {item.target && (
          <View style={styles.targetInfo}>
            <Icon
              name={item.target.type === 'post' ? 'article' : 'comment'}
              size={16}
              color={theme.colors.outline}
            />
            <Text style={styles.targetText} numberOfLines={1}>
              {item.target.title}
            </Text>
          </View>
        )}
      </View>
    </Card>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.filterContainer}>
        <Chip
          mode={filter === 'all' ? 'flat' : 'outlined'}
          onPress={() => setFilter('all')}
          style={styles.filterChip}>
          All
        </Chip>
        <Chip
          mode={filter === 'unread' ? 'flat' : 'outlined'}
          onPress={() => setFilter('unread')}
          style={styles.filterChip}>
          Unread
        </Chip>
      </View>
      
      {notifications && notifications.some(n => !n.isRead) && (
        <Button
          mode="text"
          onPress={markAllAsRead}
          compact
          style={styles.markAllButton}>
          Mark all as read
        </Button>
      )}
    </View>
  );

  const renderEmpty = () => (
    <View style={styles.emptyState}>
      <Icon name="notifications-none" size={64} color={theme.colors.outline} />
      <Text style={styles.emptyStateTitle}>
        {filter === 'unread' ? 'No unread notifications' : 'No notifications'}
      </Text>
      <Text style={styles.emptyStateText}>
        {filter === 'unread'
          ? 'All caught up! You have no unread notifications.'
          : 'When you get notifications, they will appear here.'}
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={notifications || []}
        renderItem={renderNotification}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={!isLoading ? renderEmpty : null}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
        contentContainerStyle={
          (!notifications || notifications.length === 0) ? styles.emptyContainer : undefined
        }
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    padding: 16,
    backgroundColor: theme.colors.surface,
    elevation: 1,
  },
  filterContainer: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  filterChip: {
    marginRight: 8,
  },
  markAllButton: {
    alignSelf: 'flex-end',
  },
  notificationCard: {
    margin: 16,
    marginBottom: 8,
    elevation: 2,
  },
  unreadCard: {
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.primary,
  },
  notificationContent: {
    padding: 16,
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  iconContainer: {
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  actorAvatar: {
    backgroundColor: theme.colors.primary,
    marginRight: 12,
  },
  notificationText: {
    flex: 1,
    marginRight: 12,
  },
  notificationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 4,
  },
  notificationMessage: {
    fontSize: 13,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 18,
  },
  notificationMeta: {
    alignItems: 'flex-end',
  },
  timeAgo: {
    fontSize: 12,
    color: theme.colors.outline,
    marginBottom: 4,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: theme.colors.primary,
  },
  targetInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: theme.colors.outline,
  },
  targetText: {
    fontSize: 12,
    color: theme.colors.outline,
    marginLeft: 8,
    flex: 1,
  },
  emptyContainer: {
    flexGrow: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.onSurface,
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 14,
    color: theme.colors.outline,
    textAlign: 'center',
    lineHeight: 20,
  },
});
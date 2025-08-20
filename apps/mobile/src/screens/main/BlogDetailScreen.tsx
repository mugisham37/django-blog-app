import React, {useState} from 'react';
import {View, StyleSheet, ScrollView, Dimensions, Share} from 'react-native';
import {Text, Card, Button, Avatar, Chip, FAB} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import {StackNavigationProp} from '@react-navigation/stack';
import {RouteProp} from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useQuery} from 'react-query';
import FastImage from 'react-native-fast-image';
import {BlogStackParamList} from '@navigation/MainTabNavigator';
import {theme} from '@config/theme';
import {ApiClient} from '@services/ApiClient';

const {width} = Dimensions.get('window');

type BlogDetailScreenNavigationProp = StackNavigationProp<BlogStackParamList, 'BlogDetail'>;
type BlogDetailScreenRouteProp = RouteProp<BlogStackParamList, 'BlogDetail'>;

interface Props {
  navigation: BlogDetailScreenNavigationProp;
  route: BlogDetailScreenRouteProp;
}

interface BlogPost {
  id: string;
  title: string;
  content: string;
  author: {
    id: string;
    username: string;
    avatar?: string;
    bio?: string;
  };
  category: {
    id: string;
    name: string;
    slug: string;
  };
  tags: Array<{
    id: string;
    name: string;
    slug: string;
  }>;
  featuredImage?: string;
  publishedAt: string;
  updatedAt: string;
  viewCount: number;
  commentCount: number;
  likeCount: number;
  isLiked: boolean;
  readingTime: number;
}

export const BlogDetailScreen: React.FC<Props> = ({navigation, route}) => {
  const {id} = route.params;
  const [isLiked, setIsLiked] = useState(false);

  const {data: post, isLoading, error} = useQuery<BlogPost>(
    ['post', id],
    async () => {
      const response = await ApiClient.get<BlogPost>(`/posts/${id}/`);
      setIsLiked(response.data.isLiked);
      return response.data;
    },
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const handleLike = async () => {
    try {
      await ApiClient.post(`/posts/${id}/like/`);
      setIsLiked(!isLiked);
    } catch (error) {
      console.error('Failed to like post:', error);
    }
  };

  const handleShare = async () => {
    if (!post) return;
    
    try {
      await Share.share({
        message: `Check out this post: ${post.title}`,
        url: `https://yourapp.com/posts/${post.id}`,
        title: post.title,
      });
    } catch (error) {
      console.error('Failed to share post:', error);
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

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text>Loading post...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !post) {
    return (
      <SafeAreaView style={styles.container}></SafeAreaView>   <View style={styles.errorContainer}>
          <Icon name="error" size={48} color={theme.colors.error} />
          <Text style={styles.errorText}>Failed to load post</Text>
          <Button mode="outlined" onPress={() => navigation.goBack()}>
            Go Back
          </Button>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Featured Image */}
        {post.featuredImage && (
          <FastImage
            source={{uri: post.featuredImage}}
            style={styles.featuredImage}
            resizeMode={FastImage.resizeMode.cover}
          />
        )}

        <View style={styles.content}>
          {/* Category and Reading Time */}
          <View style={styles.metaHeader}>
            <Chip
              mode="flat"
              style={styles.categoryChip}
              textStyle={styles.categoryChipText}>
              {post.category.name}
            </Chip>
            <Text style={styles.readingTime}>{post.readingTime} min read</Text>
          </View>

          {/* Title */}
          <Text style={styles.title}>{post.title}</Text>

          {/* Author Info */}
          <View style={styles.authorSection}>
            <Avatar.Text
              size={40}
              label={post.author.username.charAt(0).toUpperCase()}
              style={styles.authorAvatar}
            />
            <View style={styles.authorInfo}>
              <Text style={styles.authorName}>{post.author.username}</Text>
              <Text style={styles.publishDate}>
                Published on {formatDate(post.publishedAt)}
              </Text>
            </View>
          </View>

          {/* Post Stats */}
          <View style={styles.statsSection}>
            <View style={styles.statItem}>
              <Icon name="visibility" size={20} color={theme.colors.outline} />
              <Text style={styles.statText}>{post.viewCount} views</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="comment" size={20} color={theme.colors.outline} />
              <Text style={styles.statText}>{post.commentCount} comments</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="favorite" size={20} color={theme.colors.outline} />
              <Text style={styles.statText}>{post.likeCount} likes</Text>
            </View>
          </View>

          {/* Content */}
          <Card style={styles.contentCard}>
            <View style={styles.contentContainer}>
              <Text style={styles.contentText}>{post.content}</Text>
            </View>
          </Card>

          {/* Tags */}
          {post.tags.length > 0 && (
            <View style={styles.tagsSection}>
              <Text style={styles.tagsTitle}>Tags</Text>
              <View style={styles.tagsContainer}>
                {post.tags.map((tag) => (
                  <Chip
                    key={tag.id}
                    mode="outlined"
                    style={styles.tagChip}
                    textStyle={styles.tagChipText}>
                    #{tag.name}
                  </Chip>
                ))}
              </View>
            </View>
          )}

          {/* Action Buttons */}
          <View style={styles.actionsSection}>
            <Button
              mode={isLiked ? 'contained' : 'outlined'}
              icon={isLiked ? 'favorite' : 'favorite-border'}
              onPress={handleLike}
              style={[styles.actionButton, isLiked && styles.likedButton]}
              contentStyle={styles.actionButtonContent}>
              {isLiked ? 'Liked' : 'Like'}
            </Button>
            
            <Button
              mode="outlined"
              icon="comment"
              onPress={() => {}}
              style={styles.actionButton}
              contentStyle={styles.actionButtonContent}>
              Comment
            </Button>
            
            <Button
              mode="outlined"
              icon="share"
              onPress={handleShare}
              style={styles.actionButton}
              contentStyle={styles.actionButtonContent}>
              Share
            </Button>
          </View>

          {/* Author Bio */}
          {post.author.bio && (
            <Card style={styles.authorBioCard}>
              <View style={styles.authorBioContent}>
                <Text style={styles.authorBioTitle}>About the Author</Text>
                <View style={styles.authorBioHeader}>
                  <Avatar.Text
                    size={50}
                    label={post.author.username.charAt(0).toUpperCase()}
                    style={styles.authorBioAvatar}
                  />
                  <View style={styles.authorBioInfo}>
                    <Text style={styles.authorBioName}>{post.author.username}</Text>
                    <Text style={styles.authorBioText}>{post.author.bio}</Text>
                  </View>
                </View>
              </View>
            </Card>
          )}
        </View>
      </ScrollView>

      {/* Floating Action Button */}
      <FAB
        icon="comment"
        style={styles.fab}
        onPress={() => {
          // Navigate to comments screen or show comment modal
        }}
      />
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorText: {
    fontSize: 16,
    color: theme.colors.error,
    marginVertical: 16,
    textAlign: 'center',
  },
  featuredImage: {
    width: '100%',
    height: 250,
  },
  content: {
    padding: 20,
  },
  metaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  categoryChip: {
    backgroundColor: theme.colors.primaryContainer,
  },
  categoryChipText: {
    color: theme.colors.primary,
    fontSize: 12,
  },
  readingTime: {
    fontSize: 14,
    color: theme.colors.outline,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.onSurface,
    lineHeight: 32,
    marginBottom: 20,
  },
  authorSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  authorAvatar: {
    backgroundColor: theme.colors.primary,
  },
  authorInfo: {
    marginLeft: 12,
    flex: 1,
  },
  authorName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.onSurface,
  },
  publishDate: {
    fontSize: 14,
    color: theme.colors.outline,
    marginTop: 2,
  },
  statsSection: {
    flexDirection: 'row',
    marginBottom: 24,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: theme.colors.outline,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 24,
  },
  statText: {
    fontSize: 14,
    color: theme.colors.outline,
    marginLeft: 6,
  },
  contentCard: {
    marginBottom: 24,
    elevation: 2,
  },
  contentContainer: {
    padding: 20,
  },
  contentText: {
    fontSize: 16,
    lineHeight: 24,
    color: theme.colors.onSurface,
  },
  tagsSection: {
    marginBottom: 24,
  },
  tagsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 12,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tagChip: {
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: theme.colors.surfaceVariant,
  },
  tagChipText: {
    fontSize: 12,
    color: theme.colors.onSurfaceVariant,
  },
  actionsSection: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 32,
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 4,
    borderRadius: 20,
  },
  likedButton: {
    backgroundColor: theme.colors.error,
  },
  actionButtonContent: {
    paddingVertical: 4,
  },
  authorBioCard: {
    elevation: 2,
    marginBottom: 40,
  },
  authorBioContent: {
    padding: 20,
  },
  authorBioTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 16,
  },
  authorBioHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  authorBioAvatar: {
    backgroundColor: theme.colors.primary,
  },
  authorBioInfo: {
    marginLeft: 16,
    flex: 1,
  },
  authorBioName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 8,
  },
  authorBioText: {
    fontSize: 14,
    lineHeight: 20,
    color: theme.colors.onSurfaceVariant,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: theme.colors.primary,
  },
});
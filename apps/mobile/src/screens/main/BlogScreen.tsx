import React, {useState, useCallback} from 'react';
import {View, StyleSheet, FlatList, RefreshControl, Dimensions} from 'react-native';
import {Text, Card, Chip, Button, Searchbar, FAB} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import {StackNavigationProp} from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useQuery, useInfiniteQuery} from 'react-query';
import FastImage from 'react-native-fast-image';
import {BlogStackParamList} from '@navigation/MainTabNavigator';
import {theme} from '@config/theme';
import {ApiClient} from '@services/ApiClient';

const {width} = Dimensions.get('window');

type BlogScreenNavigationProp = StackNavigationProp<BlogStackParamList, 'Blog'>;

interface Props {
  navigation: BlogScreenNavigationProp;
}

interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  content: string;
  author: {
    id: string;
    username: string;
    avatar?: string;
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

interface Category {
  id: string;
  name: string;
  slug: string;
  postCount: number;
}

export const BlogScreen: React.FC<Props> = ({navigation}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch categories
  const {data: categories} = useQuery<Category[]>(
    'categories',
    async () => {
      const response = await ApiClient.get<Category[]>('/categories/');
      return response.data;
    },
    {
      staleTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Fetch posts with infinite scroll
  const {
    data: postsData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
    isLoading,
  } = useInfiniteQuery(
    ['posts', selectedCategory, searchQuery],
    async ({pageParam = 1}) => {
      const params: any = {
        page: pageParam,
        limit: 10,
      };
      
      if (selectedCategory) {
        params.category = selectedCategory;
      }
      
      if (searchQuery) {
        params.search = searchQuery;
      }

      const response = await ApiClient.get<{
        results: BlogPost[];
        next: string | null;
        count: number;
      }>('/posts/', params);
      
      return response.data;
    },
    {
      getNextPageParam: (lastPage, pages) => {
        return lastPage.next ? pages.length + 1 : undefined;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const posts = postsData?.pages.flatMap(page => page.results) || [];

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const handleCategorySelect = (categoryId: string | null) => {
    setSelectedCategory(categoryId);
  };

  const handlePostPress = (post: BlogPost) => {
    navigation.navigate('BlogDetail', {id: post.id});
  };

  const handleLikePost = async (postId: string) => {
    try {
      await ApiClient.post(`/posts/${postId}/like/`);
      // Refetch posts to update like status
      refetch();
    } catch (error) {
      console.error('Failed to like post:', error);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const renderPost = ({item: post}: {item: BlogPost}) => (
    <Card style={styles.postCard} onPress={() => handlePostPress(post)}>
      {post.featuredImage && (
        <FastImage
          source={{uri: post.featuredImage}}
          style={styles.postImage}
          resizeMode={FastImage.resizeMode.cover}
        />
      )}
      
      <View style={styles.postContent}>
        <View style={styles.postHeader}>
          <Chip
            mode="outlined"
            compact
            style={styles.categoryChip}
            textStyle={styles.categoryChipText}>
            {post.category.name}
          </Chip>
          <Text style={styles.readingTime}>{post.readingTime} min read</Text>
        </View>
        
        <Text style={styles.postTitle} numberOfLines={2}>
          {post.title}
        </Text>
        
        <Text style={styles.postExcerpt} numberOfLines={3}>
          {post.excerpt}
        </Text>
        
        <View style={styles.postMeta}>
          <View style={styles.authorInfo}>
            <Text style={styles.authorName}>By {post.author.username}</Text>
            <Text style={styles.postDate}>{formatDate(post.publishedAt)}</Text>
          </View>
          
          <View style={styles.postStats}>
            <View style={styles.statItem}>
              <Icon name="visibility" size={16} color={theme.colors.outline} />
              <Text style={styles.statText}>{post.viewCount}</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="comment" size={16} color={theme.colors.outline} />
              <Text style={styles.statText}>{post.commentCount}</Text>
            </View>
            <Button
              mode="text"
              compact
              icon={post.isLiked ? 'favorite' : 'favorite-border'}
              onPress={() => handleLikePost(post.id)}
              contentStyle={styles.likeButtonContent}
              labelStyle={styles.likeButtonLabel}>
              {post.likeCount}
            </Button>
          </View>
        </View>
        
        {post.tags.length > 0 && (
          <View style={styles.tagsContainer}>
            {post.tags.slice(0, 3).map((tag) => (
              <Chip
                key={tag.id}
                mode="outlined"
                compact
                style={styles.tagChip}
                textStyle={styles.tagChipText}>
                {tag.name}
              </Chip>
            ))}
            {post.tags.length > 3 && (
              <Text style={styles.moreTags}>+{post.tags.length - 3} more</Text>
            )}
          </View>
        )}
      </View>
    </Card>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <Searchbar
        placeholder="Search posts..."
        onChangeText={setSearchQuery}
        value={searchQuery}
        style={styles.searchBar}
        inputStyle={styles.searchInput}
      />
      
      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={[{id: 'all', name: 'All', slug: 'all', postCount: 0}, ...(categories || [])]}
        keyExtractor={(item) => item.id}
        renderItem={({item}) => (
          <Chip
            mode={selectedCategory === (item.id === 'all' ? null : item.id) ? 'flat' : 'outlined'}
            onPress={() => handleCategorySelect(item.id === 'all' ? null : item.id)}
            style={styles.categoryFilterChip}
            textStyle={styles.categoryFilterChipText}>
            {item.name}
          </Chip>
        )}
        contentContainerStyle={styles.categoriesContainer}
      />
    </View>
  );

  const renderFooter = () => {
    if (!isFetchingNextPage) return null;
    
    return (
      <View style={styles.loadingFooter}>
        <Text style={styles.loadingText}>Loading more posts...</Text>
      </View>
    );
  };

  const renderEmpty = () => (
    <View style={styles.emptyState}>
      <Icon name="article" size={64} color={theme.colors.outline} />
      <Text style={styles.emptyStateTitle}>No posts found</Text>
      <Text style={styles.emptyStateText}>
        {searchQuery
          ? `No posts match "${searchQuery}"`
          : selectedCategory
          ? 'No posts in this category'
          : 'No posts available'}
      </Text>
      {(searchQuery || selectedCategory) && (
        <Button
          mode="outlined"
          onPress={() => {
            setSearchQuery('');
            setSelectedCategory(null);
          }}
          style={styles.clearFiltersButton}>
          Clear Filters
        </Button>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={posts}
        renderItem={renderPost}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={renderHeader}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={!isLoading ? renderEmpty : null}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        onEndReached={() => {
          if (hasNextPage && !isFetchingNextPage) {
            fetchNextPage();
          }
        }}
        onEndReachedThreshold={0.5}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={posts.length === 0 ? styles.emptyContainer : undefined}
      />
      
      <FAB
        icon="add"
        style={styles.fab}
        onPress={() => {
          // Navigate to create post screen
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
  header: {
    padding: 16,
    backgroundColor: theme.colors.surface,
  },
  searchBar: {
    marginBottom: 16,
    elevation: 2,
  },
  searchInput: {
    fontSize: 16,
  },
  categoriesContainer: {
    paddingVertical: 8,
  },
  categoryFilterChip: {
    marginRight: 8,
  },
  categoryFilterChipText: {
    fontSize: 12,
  },
  postCard: {
    margin: 16,
    marginBottom: 8,
    elevation: 3,
    borderRadius: 12,
    overflow: 'hidden',
  },
  postImage: {
    width: '100%',
    height: 200,
  },
  postContent: {
    padding: 16,
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryChip: {
    backgroundColor: theme.colors.primaryContainer,
  },
  categoryChipText: {
    fontSize: 12,
    color: theme.colors.primary,
  },
  readingTime: {
    fontSize: 12,
    color: theme.colors.outline,
  },
  postTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.onSurface,
    marginBottom: 8,
    lineHeight: 24,
  },
  postExcerpt: {
    fontSize: 14,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 20,
    marginBottom: 16,
  },
  postMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  authorInfo: {
    flex: 1,
  },
  authorName: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.onSurface,
  },
  postDate: {
    fontSize: 12,
    color: theme.colors.outline,
    marginTop: 2,
  },
  postStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  statText: {
    fontSize: 12,
    color: theme.colors.outline,
    marginLeft: 4,
  },
  likeButtonContent: {
    paddingHorizontal: 4,
  },
  likeButtonLabel: {
    fontSize: 12,
    marginLeft: 4,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  tagChip: {
    marginRight: 6,
    marginBottom: 4,
    backgroundColor: theme.colors.surfaceVariant,
  },
  tagChipText: {
    fontSize: 10,
    color: theme.colors.onSurfaceVariant,
  },
  moreTags: {
    fontSize: 12,
    color: theme.colors.outline,
    marginLeft: 4,
  },
  loadingFooter: {
    padding: 20,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: theme.colors.outline,
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
    marginBottom: 24,
  },
  clearFiltersButton: {
    borderRadius: 20,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: theme.colors.primary,
  },
});
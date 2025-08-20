import React, {useState, useCallback} from 'react';
import {View, StyleSheet, FlatList} from 'react-native';
import {Text, Searchbar, Card, Chip, Button} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useQuery} from 'react-query';
import {theme} from '@config/theme';
import {ApiClient} from '@services/ApiClient';

interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  type: 'post' | 'user' | 'category';
  author?: {
    username: string;
  };
  category?: {
    name: string;
  };
  publishedAt?: string;
}

export const SearchScreen: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'all' | 'posts' | 'users' | 'categories'>('all');

  const {data: searchResults, isLoading} = useQuery(
    ['search', searchQuery, searchType],
    async () => {
      if (!searchQuery.trim()) return [];
      
      const response = await ApiClient.get<SearchResult[]>('/search/', {
        q: searchQuery,
        type: searchType === 'all' ? undefined : searchType,
      });
      return response.data;
    },
    {
      enabled: searchQuery.length > 2,
      staleTime: 30 * 1000, // 30 seconds
    }
  );

  const renderSearchResult = ({item}: {item: SearchResult}) => (
    <Card style={styles.resultCard} onPress={() => {}}>
      <View style={styles.resultContent}>
        <View style={styles.resultHeader}>
          <Icon
            name={
              item.type === 'post' ? 'article' :
              item.type === 'user' ? 'person' : 'category'
            }
            size={20}
            color={theme.colors.primary}
          />
          <Chip
            mode="outlined"
            compact
            style={styles.typeChip}
            textStyle={styles.typeChipText}>
            {item.type}
          </Chip>
        </View>
        
        <Text style={styles.resultTitle} numberOfLines={2}>
          {item.title}
        </Text>
        
        {item.excerpt && (
          <Text style={styles.resultExcerpt} numberOfLines={3}>
            {item.excerpt}
          </Text>
        )}
        
        <View style={styles.resultMeta}>
          {item.author && (
            <Text style={styles.metaText}>By {item.author.username}</Text>
          )}
          {item.category && (
            <Text style={styles.metaText}>in {item.category.name}</Text>
          )}
        </View>
      </View>
    </Card>
  );

  const renderEmpty = () => {
    if (isLoading) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>Searching...</Text>
        </View>
      );
    }

    if (!searchQuery.trim()) {
      return (
        <View style={styles.emptyState}>
          <Icon name="search" size={64} color={theme.colors.outline} />
          <Text style={styles.emptyStateTitle}>Search Content</Text>
          <Text style={styles.emptyStateText}>
            Find posts, users, and categories by typing in the search box above.
          </Text>
        </View>
      );
    }

    if (searchQuery.length <= 2) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>
            Type at least 3 characters to search
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.emptyState}>
        <Icon name="search-off" size={64} color={theme.colors.outline} />
        <Text style={styles.emptyStateTitle}>No Results Found</Text>
        <Text style={styles.emptyStateText}>
          No results found for "{searchQuery}". Try different keywords.
        </Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.searchContainer}>
        <Searchbar
          placeholder="Search posts, users, categories..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchBar}
          inputStyle={styles.searchInput}
        />
        
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={[
            {key: 'all', label: 'All'},
            {key: 'posts', label: 'Posts'},
            {key: 'users', label: 'Users'},
            {key: 'categories', label: 'Categories'},
          ]}
          keyExtractor={(item) => item.key}
          renderItem={({item}) => (
            <Chip
              mode={searchType === item.key ? 'flat' : 'outlined'}
              onPress={() => setSearchType(item.key as any)}
              style={styles.filterChip}
              textStyle={styles.filterChipText}>
              {item.label}
            </Chip>
          )}
          contentContainerStyle={styles.filtersContainer}
        />
      </View>

      <FlatList
        data={searchResults || []}
        renderItem={renderSearchResult}
        keyExtractor={(item) => `${item.type}-${item.id}`}
        ListEmptyComponent={renderEmpty}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={
          (!searchResults || searchResults.length === 0) ? styles.emptyContainer : undefined
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
  searchContainer: {
    padding: 16,
    backgroundColor: theme.colors.surface,
    elevation: 2,
  },
  searchBar: {
    marginBottom: 16,
    elevation: 1,
  },
  searchInput: {
    fontSize: 16,
  },
  filtersContainer: {
    paddingVertical: 8,
  },
  filterChip: {
    marginRight: 8,
  },
  filterChipText: {
    fontSize: 12,
  },
  resultCard: {
    margin: 16,
    marginBottom: 8,
    elevation: 2,
  },
  resultContent: {
    padding: 16,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  typeChip: {
    backgroundColor: theme.colors.surfaceVariant,
  },
  typeChipText: {
    fontSize: 10,
    color: theme.colors.onSurfaceVariant,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.onSurface,
    marginBottom: 8,
  },
  resultExcerpt: {
    fontSize: 14,
    color: theme.colors.onSurfaceVariant,
    lineHeight: 20,
    marginBottom: 8,
  },
  resultMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  metaText: {
    fontSize: 12,
    color: theme.colors.outline,
    marginRight: 12,
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
"""
Advanced search functionality with Elasticsearch integration.
"""

from django.db.models import Q, F, Count, Avg
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, TrigramSimilarity
)
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import re
import logging

logger = logging.getLogger(__name__)


class AdvancedSearchFilter(filters.BaseFilterBackend):
    """Advanced search filter with multiple search strategies."""
    
    search_param = 'search'
    search_title_param = 'search_title'
    search_content_param = 'search_content'
    search_author_param = 'search_author'
    search_tags_param = 'search_tags'
    
    def filter_queryset(self, request, queryset, view):
        """Apply advanced search filtering."""
        search_terms = request.query_params.get(self.search_param)
        
        if not search_terms:
            return queryset
        
        # Clean and prepare search terms
        search_terms = self.clean_search_terms(search_terms)
        
        if not search_terms:
            return queryset
        
        # Apply different search strategies based on model
        model_name = queryset.model.__name__.lower()
        
        if model_name == 'post':
            return self.search_posts(queryset, search_terms, request)
        elif model_name == 'user':
            return self.search_users(queryset, search_terms, request)
        elif model_name == 'comment':
            return self.search_comments(queryset, search_terms, request)
        else:
            return self.generic_search(queryset, search_terms, request)
    
    def clean_search_terms(self, search_terms):
        """Clean and validate search terms."""
        if not search_terms:
            return ""
        
        # Remove special characters and normalize
        search_terms = re.sub(r'[^\w\s-]', '', search_terms)
        search_terms = ' '.join(search_terms.split())  # Normalize whitespace
        
        # Limit length
        if len(search_terms) > 200:
            search_terms = search_terms[:200]
        
        return search_terms
    
    def search_posts(self, queryset, search_terms, request):
        """Advanced search for blog posts."""
        # Use PostgreSQL full-text search if available
        try:
            # Create search vector
            search_vector = (
                SearchVector('title', weight='A') +
                SearchVector('content', weight='B') +
                SearchVector('excerpt', weight='C') +
                SearchVector('tags__name', weight='D')
            )
            
            search_query = SearchQuery(search_terms)
            
            queryset = queryset.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(search=search_query).order_by('-rank', '-published_at')
            
        except Exception:
            # Fallback to basic search
            queryset = self.basic_post_search(queryset, search_terms)
        
        # Apply specific field searches
        title_search = request.query_params.get(self.search_title_param)
        if title_search:
            queryset = queryset.filter(title__icontains=title_search)
        
        content_search = request.query_params.get(self.search_content_param)
        if content_search:
            queryset = queryset.filter(content__icontains=content_search)
        
        author_search = request.query_params.get(self.search_author_param)
        if author_search:
            queryset = queryset.filter(
                Q(author__username__icontains=author_search) |
                Q(author__first_name__icontains=author_search) |
                Q(author__last_name__icontains=author_search)
            )
        
        tags_search = request.query_params.get(self.search_tags_param)
        if tags_search:
            queryset = queryset.filter(tags__name__icontains=tags_search)
        
        return queryset
    
    def basic_post_search(self, queryset, search_terms):
        """Basic search for posts without PostgreSQL features."""
        return queryset.filter(
            Q(title__icontains=search_terms) |
            Q(content__icontains=search_terms) |
            Q(excerpt__icontains=search_terms) |
            Q(tags__name__icontains=search_terms) |
            Q(category__name__icontains=search_terms)
        ).distinct()
    
    def search_users(self, queryset, search_terms, request):
        """Search for users."""
        return queryset.filter(
            Q(username__icontains=search_terms) |
            Q(first_name__icontains=search_terms) |
            Q(last_name__icontains=search_terms) |
            Q(email__icontains=search_terms)
        ).distinct()
    
    def search_comments(self, queryset, search_terms, request):
        """Search for comments."""
        return queryset.filter(
            Q(content__icontains=search_terms) |
            Q(author__username__icontains=search_terms)
        ).distinct()
    
    def generic_search(self, queryset, search_terms, request):
        """Generic search for other models."""
        # Try to find text fields to search
        text_fields = []
        for field in queryset.model._meta.fields:
            if field.get_internal_type() in ['CharField', 'TextField']:
                text_fields.append(f"{field.name}__icontains")
        
        if text_fields:
            q_objects = Q()
            for field in text_fields:
                q_objects |= Q(**{field: search_terms})
            return queryset.filter(q_objects)
        
        return queryset


class SearchSuggestionMixin:
    """Mixin to provide search suggestions."""
    
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """Get search suggestions based on query."""
        query = request.query_params.get('q', '').strip()
        
        if len(query) < 2:
            return Response({'suggestions': []})
        
        # Check cache first
        cache_key = f"search_suggestions_{query.lower()}"
        cached_suggestions = cache.get(cache_key)
        if cached_suggestions:
            return Response({'suggestions': cached_suggestions})
        
        suggestions = []
        
        # Get suggestions from different sources
        model_name = self.queryset.model.__name__.lower()
        
        if model_name == 'post':
            suggestions = self.get_post_suggestions(query)
        elif model_name == 'user':
            suggestions = self.get_user_suggestions(query)
        
        # Cache suggestions for 1 hour
        cache.set(cache_key, suggestions, 3600)
        
        return Response({'suggestions': suggestions})
    
    def get_post_suggestions(self, query):
        """Get post-related search suggestions."""
        suggestions = []
        
        # Title suggestions
        title_matches = self.queryset.filter(
            title__icontains=query
        ).values_list('title', flat=True)[:5]
        suggestions.extend([{'type': 'title', 'text': title} for title in title_matches])
        
        # Tag suggestions
        from apps.blog.models import Tag
        tag_matches = Tag.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:5]
        suggestions.extend([{'type': 'tag', 'text': tag} for tag in tag_matches])
        
        # Category suggestions
        from apps.blog.models import Category
        category_matches = Category.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:5]
        suggestions.extend([{'type': 'category', 'text': cat} for cat in category_matches])
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    def get_user_suggestions(self, query):
        """Get user-related search suggestions."""
        suggestions = []
        
        # Username suggestions
        username_matches = self.queryset.filter(
            username__icontains=query
        ).values_list('username', flat=True)[:5]
        suggestions.extend([{'type': 'username', 'text': username} for username in username_matches])
        
        return suggestions


class SearchAnalyticsMixin:
    """Mixin to track search analytics."""
    
    def track_search(self, query, results_count, user=None):
        """Track search query for analytics."""
        try:
            from apps.analytics.models import SearchQuery
            
            SearchQuery.objects.create(
                query=query,
                user=user if user and user.is_authenticated else None,
                results_count=results_count,
                timestamp=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error tracking search: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def search_analytics(self, request):
        """Get search analytics data."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from apps.analytics.models import SearchQuery
            
            # Get popular searches
            popular_searches = SearchQuery.objects.values('query').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Get recent searches
            recent_searches = SearchQuery.objects.order_by('-timestamp')[:20]
            
            # Get search trends (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            daily_searches = SearchQuery.objects.filter(
                timestamp__gte=thirty_days_ago
            ).extra(
                select={'day': 'date(timestamp)'}
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            return Response({
                'popular_searches': list(popular_searches),
                'recent_searches': [
                    {
                        'query': sq.query,
                        'results_count': sq.results_count,
                        'timestamp': sq.timestamp,
                        'user': sq.user.username if sq.user else 'Anonymous'
                    }
                    for sq in recent_searches
                ],
                'daily_trends': list(daily_searches)
            })
        
        except Exception as e:
            logger.error(f"Error getting search analytics: {str(e)}")
            return Response(
                {'error': 'Failed to get analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FacetedSearchMixin:
    """Mixin for faceted search functionality."""
    
    @action(detail=False, methods=['get'])
    def faceted_search(self, request):
        """Perform faceted search with filters."""
        query = request.query_params.get('q', '')
        
        # Apply base search
        queryset = self.filter_queryset(self.get_queryset())
        
        if query:
            # Apply search filter
            search_filter = AdvancedSearchFilter()
            queryset = search_filter.filter_queryset(request, queryset, self)
        
        # Get facets
        facets = self.get_facets(queryset, request)
        
        # Apply facet filters
        queryset = self.apply_facet_filters(queryset, request)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            response_data['facets'] = facets
            return Response(response_data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'facets': facets
        })
    
    def get_facets(self, queryset, request):
        """Get facet data for search results."""
        facets = {}
        
        model_name = queryset.model.__name__.lower()
        
        if model_name == 'post':
            # Category facets
            facets['categories'] = list(
                queryset.values('category__name', 'category__slug')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            
            # Tag facets
            facets['tags'] = list(
                queryset.values('tags__name', 'tags__slug')
                .annotate(count=Count('id'))
                .order_by('-count')[:20]
            )
            
            # Author facets
            facets['authors'] = list(
                queryset.values('author__username', 'author__id')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            
            # Date facets
            facets['years'] = list(
                queryset.extra(
                    select={'year': 'EXTRACT(year FROM published_at)'}
                ).values('year')
                .annotate(count=Count('id'))
                .order_by('-year')
            )
        
        return facets
    
    def apply_facet_filters(self, queryset, request):
        """Apply facet filters to queryset."""
        # Category filter
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Tag filter
        tags = request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)
        
        # Author filter
        author = request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__username=author)
        
        # Date range filter
        year = request.query_params.get('year')
        if year:
            queryset = queryset.filter(published_at__year=year)
        
        return queryset


class ElasticsearchMixin:
    """Mixin for Elasticsearch integration (optional)."""
    
    def elasticsearch_search(self, query, filters=None):
        """Perform Elasticsearch search."""
        try:
            from elasticsearch import Elasticsearch
            from django.conf import settings
            
            es = Elasticsearch([settings.ELASTICSEARCH_URL])
            
            # Build search query
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "content^2", "excerpt", "tags"]
                    }
                },
                "highlight": {
                    "fields": {
                        "title": {},
                        "content": {},
                        "excerpt": {}
                    }
                }
            }
            
            # Add filters if provided
            if filters:
                search_body["query"] = {
                    "bool": {
                        "must": search_body["query"],
                        "filter": filters
                    }
                }
            
            # Execute search
            response = es.search(
                index=self.get_elasticsearch_index(),
                body=search_body
            )
            
            return self.process_elasticsearch_results(response)
        
        except Exception as e:
            logger.error(f"Elasticsearch search error: {str(e)}")
            return None
    
    def get_elasticsearch_index(self):
        """Get Elasticsearch index name."""
        model_name = self.queryset.model.__name__.lower()
        return f"blog_{model_name}"
    
    def process_elasticsearch_results(self, response):
        """Process Elasticsearch response."""
        results = []
        
        for hit in response['hits']['hits']:
            result = hit['_source']
            result['_score'] = hit['_score']
            
            # Add highlights if available
            if 'highlight' in hit:
                result['_highlights'] = hit['highlight']
            
            results.append(result)
        
        return {
            'results': results,
            'total': response['hits']['total']['value'],
            'max_score': response['hits']['max_score']
        }


class SearchHistoryMixin:
    """Mixin to track user search history."""
    
    def save_search_history(self, user, query, results_count):
        """Save search to user's history."""
        if not user.is_authenticated:
            return
        
        try:
            from apps.analytics.models import UserSearchHistory
            
            # Limit history to last 50 searches per user
            UserSearchHistory.objects.filter(user=user).order_by('-timestamp')[50:].delete()
            
            UserSearchHistory.objects.create(
                user=user,
                query=query,
                results_count=results_count,
                timestamp=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error saving search history: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def search_history(self, request):
        """Get user's search history."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            from apps.analytics.models import UserSearchHistory
            
            history = UserSearchHistory.objects.filter(
                user=request.user
            ).order_by('-timestamp')[:20]
            
            return Response({
                'history': [
                    {
                        'query': h.query,
                        'results_count': h.results_count,
                        'timestamp': h.timestamp
                    }
                    for h in history
                ]
            })
        
        except Exception as e:
            logger.error(f"Error getting search history: {str(e)}")
            return Response(
                {'error': 'Failed to get search history'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
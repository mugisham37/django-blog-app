"""
Blog API Views
RESTful API endpoints for blog functionality with advanced features.
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import Post, Category, Tag, PostView
from .serializers import (
    PostSerializer, PostDetailSerializer, PostCreateUpdateSerializer,
    CategorySerializer, TagSerializer, PostViewSerializer
)
from .filters import PostFilter

# Import advanced features
from apps.core.permissions import (
    IsAuthorOrReadOnly, RoleBasedPermission, IsStaffOrReadOnly
)
from apps.core.throttling import (
    BurstRateThrottle, SearchRateThrottle, UploadRateThrottle,
    DynamicRateThrottle, EndpointSpecificThrottle
)
from apps.core.caching import (
    SmartCacheMixin, ConditionalCacheMixin, ETagCacheMixin,
    cache_api_response, CacheInvalidator
)
from apps.core.bulk_operations import BulkOperationMixin, BulkImportExportMixin
from apps.core.search import (
    AdvancedSearchFilter, SearchSuggestionMixin, SearchAnalyticsMixin,
    FacetedSearchMixin, SearchHistoryMixin
)
from apps.core.export_import import (
    DataExportMixin, DataImportMixin, AdvancedExportMixin,
    ImportValidationMixin
)


class PostViewSet(SmartCacheMixin, ConditionalCacheMixin, ETagCacheMixin,
                  BulkOperationMixin, BulkImportExportMixin,
                  SearchSuggestionMixin, SearchAnalyticsMixin, FacetedSearchMixin,
                  SearchHistoryMixin, DataExportMixin, DataImportMixin,
                  AdvancedExportMixin, ImportValidationMixin,
                  viewsets.ModelViewSet):
    """Enhanced ViewSet for managing blog posts with advanced features."""
    
    filter_backends = [AdvancedSearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['created_at', 'published_at', 'view_count', 'title']
    ordering = ['-published_at']
    
    # Caching configuration
    cache_timeout = 300  # 5 minutes
    cache_per_user = True
    
    # Throttling configuration
    throttle_classes = [DynamicRateThrottle, SearchRateThrottle, UploadRateThrottle]
    
    def get_queryset(self):
        """Return posts based on user permissions."""
        if self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            self.request.user.has_perm('blog.view_post')
        ):
            return Post.objects.all()
        return Post.objects.published()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return PostDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PostCreateUpdateSerializer
        return PostSerializer
    
    def get_permissions(self):
        """Set permissions based on action with role-based access control."""
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
        elif self.action in ['destroy']:
            permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
        elif self.action in ['bulk_create', 'bulk_update', 'bulk_delete']:
            permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
        elif self.action in ['import_csv', 'import_json', 'import_excel']:
            permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set author when creating post."""
        serializer.save(author=self.request.user)
        # Invalidate related caches
        CacheInvalidator.invalidate_model_cache('post')
        CacheInvalidator.invalidate_view_cache('PostViewSet')
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a draft post."""
        post = self.get_object()
        if post.author != request.user and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        post.status = Post.PostStatus.PUBLISHED
        post.published_at = timezone.now()
        post.save()
        
        return Response({'message': 'Post published successfully'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a post."""
        post = self.get_object()
        if post.author != request.user and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        post.status = Post.PostStatus.DRAFT
        post.save()
        
        return Response({'message': 'Post unpublished successfully'})
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get related posts."""
        post = self.get_object()
        related_posts = post.get_related_posts()
        serializer = PostSerializer(related_posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @cache_api_response(timeout=600)  # Cache for 10 minutes
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending posts based on recent views."""
        from datetime import timedelta
        
        # Get posts with high view counts in the last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        trending_posts = self.get_queryset().filter(
            published_at__gte=week_ago
        ).order_by('-view_count')[:10]
        
        serializer = self.get_serializer(trending_posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def advanced_search(self, request):
        """Advanced search with analytics tracking."""
        query = request.query_params.get('q', '')
        
        if query:
            # Apply advanced search
            queryset = self.filter_queryset(self.get_queryset())
            
            # Track search
            self.track_search(query, queryset.count(), request.user)
            self.save_search_history(request.user, query, queryset.count())
            
            # Paginate results
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response({'results': []})
    
    # Export/Import field configuration
    def get_export_fields(self):
        """Get fields to include in export."""
        return [
            'id', 'title', 'slug', 'excerpt', 'content', 'status',
            'author.username', 'category.name', 'view_count',
            'created_at', 'published_at', 'updated_at'
        ]
    
    def get_required_import_fields(self):
        """Get required fields for import."""
        return ['title', 'content', 'author']
    
    def transform_import_row(self, row, file_format):
        """Transform import row data."""
        # Handle author field - convert username to user ID
        if 'author' in row:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                if isinstance(row['author'], str):
                    user = User.objects.get(username=row['author'])
                    row['author'] = user.id
            except User.DoesNotExist:
                row['author'] = self.request.user.id
        
        # Handle category field
        if 'category' in row and isinstance(row['category'], str):
            try:
                category = Category.objects.get(name=row['category'])
                row['category'] = category.id
            except Category.DoesNotExist:
                row.pop('category', None)
        
        return row


class CategoryViewSet(SmartCacheMixin, BulkOperationMixin, DataExportMixin,
                     viewsets.ModelViewSet):
    """Enhanced ViewSet for managing categories."""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [AdvancedSearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']
    
    # Caching configuration
    cache_timeout = 600  # 10 minutes (categories change less frequently)
    throttle_classes = [DynamicRateThrottle]
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts in this category."""
        category = self.get_object()
        posts = Post.objects.published().filter(category=category)
        
        # Apply pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class TagViewSet(SmartCacheMixin, BulkOperationMixin, DataExportMixin,
                viewsets.ModelViewSet):
    """Enhanced ViewSet for managing tags."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'
    filter_backends = [AdvancedSearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    # Caching configuration
    cache_timeout = 600  # 10 minutes
    throttle_classes = [DynamicRateThrottle]
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts with this tag."""
        tag = self.get_object()
        posts = Post.objects.published().filter(tags=tag)
        
        # Apply pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class PostSearchView(SearchAnalyticsMixin, SearchHistoryMixin, ListAPIView):
    """Enhanced search posts endpoint with analytics."""
    
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [SearchRateThrottle]
    filter_backends = [AdvancedSearchFilter]
    
    def get_queryset(self):
        """Search posts with advanced filtering and analytics."""
        queryset = Post.objects.published()
        query = self.request.query_params.get('q', '')
        
        if query:
            # Apply advanced search filter
            search_filter = AdvancedSearchFilter()
            queryset = search_filter.filter_queryset(self.request, queryset, self)
            
            # Track search analytics
            self.track_search(query, queryset.count(), self.request.user)
            self.save_search_history(self.request.user, query, queryset.count())
        
        return queryset
    
    @cache_api_response(timeout=300)
    def list(self, request, *args, **kwargs):
        """Override list to add caching."""
        return super().list(request, *args, **kwargs)


class FeaturedPostsView(ListAPIView):
    """Get featured posts."""
    
    queryset = Post.objects.featured()
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]


class PostPreviewView(APIView):
    """Preview unpublished posts with token."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, slug):
        token = request.query_params.get('token')
        if not token:
            return Response({'error': 'Preview token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import PostPreviewToken
            preview_token = PostPreviewToken.objects.get(token=token, post__slug=slug)
            
            if preview_token.is_valid():
                preview_token.use_token()
                serializer = PostDetailSerializer(preview_token.post, context={'request': request})
                return Response(serializer.data)
            else:
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        except PostPreviewToken.DoesNotExist:
            return Response({'error': 'Invalid preview token'}, status=status.HTTP_404_NOT_FOUND)


class PostViewCreateView(CreateAPIView):
    """Track post views."""
    
    serializer_class = PostViewSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        """Save post view with IP and user agent."""
        post_slug = self.kwargs['slug']
        try:
            post = Post.objects.get(slug=post_slug)
            
            # Get client IP
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            
            # Check if this IP already viewed this post recently (within 1 hour)
            from datetime import timedelta
            recent_view = PostView.objects.filter(
                post=post,
                ip_address=ip,
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).exists()
            
            if not recent_view:
                serializer.save(
                    post=post,
                    ip_address=ip,
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    user=self.request.user if self.request.user.is_authenticated else None
                )
                
                # Increment post view count
                post.view_count += 1
                post.save(update_fields=['view_count'])
        except Post.DoesNotExist:
            pass
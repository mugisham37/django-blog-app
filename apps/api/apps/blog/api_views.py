"""
Blog API Views
RESTful API endpoints for blog functionality.
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


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for managing blog posts."""
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['created_at', 'published_at', 'view_count', 'title']
    ordering = ['-published_at']
    
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
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set author when creating post."""
        serializer.save(author=self.request.user)
    
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


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing categories."""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']
    
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


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tags."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
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


class PostSearchView(ListAPIView):
    """Search posts endpoint."""
    
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Search posts based on query parameters."""
        queryset = Post.objects.published()
        query = self.request.query_params.get('q', '')
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(tags__name__icontains=query) |
                Q(category__name__icontains=query)
            ).distinct()
        
        return queryset


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
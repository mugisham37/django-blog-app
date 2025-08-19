"""
Comments API Views
RESTful API endpoints for comment functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Comment, CommentLike, CommentReport
from .serializers import (
    CommentSerializer, CommentCreateSerializer, CommentLikeSerializer,
    CommentReportSerializer
)
from apps.blog.models import Post


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing comments."""
    
    def get_queryset(self):
        """Return comments based on user permissions."""
        if self.request.user.is_staff:
            return Comment.objects.all()
        return Comment.objects.approved()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set author and metadata when creating comment."""
        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        serializer.save(
            author=self.request.user if self.request.user.is_authenticated else None,
            ip_address=ip,
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def update(self, request, *args, **kwargs):
        """Update comment with edit tracking."""
        comment = self.get_object()
        
        # Check if user can edit
        if not comment.can_be_edited_by(request.user):
            return Response(
                {'error': 'You cannot edit this comment'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark as edited
        comment.is_edited = True
        comment.save()
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a comment (staff only)."""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        comment = self.get_object()
        comment.approve()
        
        return Response({'message': 'Comment approved successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_spam(self, request, pk=None):
        """Mark comment as spam (staff only)."""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        comment = self.get_object()
        comment.mark_as_spam()
        
        return Response({'message': 'Comment marked as spam'})
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get replies to a comment."""
        comment = self.get_object()
        replies = comment.get_replies()
        serializer = CommentSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)


class PostCommentsView(ListCreateAPIView):
    """Get comments for a specific post or create a new comment."""
    
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get comments for the specified post."""
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, id=post_id)
        
        # Only show approved comments to non-staff users
        if self.request.user.is_staff:
            return Comment.objects.filter(post=post, parent=None)
        return Comment.objects.approved().filter(post=post, parent=None)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on method."""
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        """Create comment for the specified post."""
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, id=post_id)
        
        # Check if post allows comments
        if not post.allow_comments:
            raise serializers.ValidationError('Comments are not allowed on this post')
        
        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        serializer.save(
            post=post,
            author=self.request.user if self.request.user.is_authenticated else None,
            ip_address=ip,
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )


class CommentLikeView(APIView):
    """Like or unlike a comment."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, comment_id):
        """Toggle like/dislike on a comment."""
        comment = get_object_or_404(Comment, id=comment_id)
        is_like = request.data.get('is_like', True)
        
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user,
            defaults={'is_like': is_like}
        )
        
        if not created:
            if like.is_like == is_like:
                # Remove like/dislike if same action
                like.delete()
                return Response({'message': 'Like removed'})
            else:
                # Toggle like/dislike
                like.is_like = is_like
                like.save()
                return Response({'message': 'Like updated'})
        
        return Response({'message': 'Like added'})
    
    def get(self, request, comment_id):
        """Get like status for a comment."""
        comment = get_object_or_404(Comment, id=comment_id)
        
        like_count = comment.likes.filter(is_like=True).count()
        dislike_count = comment.likes.filter(is_like=False).count()
        
        user_like = None
        if request.user.is_authenticated:
            try:
                user_like_obj = comment.likes.get(user=request.user)
                user_like = user_like_obj.is_like
            except CommentLike.DoesNotExist:
                pass
        
        return Response({
            'like_count': like_count,
            'dislike_count': dislike_count,
            'user_like': user_like
        })


class CommentReportView(APIView):
    """Report a comment."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, comment_id):
        """Report a comment."""
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if user already reported this comment
        if CommentReport.objects.filter(comment=comment, reporter=request.user).exists():
            return Response(
                {'error': 'You have already reported this comment'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CommentReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(comment=comment, reporter=request.user)
            return Response({'message': 'Comment reported successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
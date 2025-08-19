"""
Blog API Filters
"""

import django_filters
from django.db.models import Q
from .models import Post, Category, Tag


class PostFilter(django_filters.FilterSet):
    """Filter for Post model."""
    
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())
    author = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Post.PostStatus.choices)
    post_type = django_filters.ChoiceFilter(choices=Post.PostType.choices)
    is_featured = django_filters.BooleanFilter()
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    
    class Meta:
        model = Post
        fields = ['category', 'tags', 'author', 'status', 'post_type', 'is_featured']
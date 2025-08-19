"""
Blog API Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, Category, Tag, PostView

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for post authors."""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories."""
    
    post_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'color', 'icon',
            'meta_title', 'meta_description', 'parent', 'order',
            'is_active', 'post_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""
    
    post_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'description', 'color',
            'post_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for post list view."""
    
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author', 'category', 'tags',
            'featured_image', 'featured_image_alt', 'status', 'post_type',
            'is_featured', 'published_at', 'created_at', 'updated_at',
            'view_count', 'reading_time', 'comment_count', 'is_published'
        ]


class PostDetailSerializer(serializers.ModelSerializer):
    """Serializer for post detail view."""
    
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content', 'author',
            'category', 'tags', 'featured_image', 'featured_image_alt',
            'status', 'post_type', 'is_featured', 'allow_comments',
            'published_at', 'created_at', 'updated_at', 'meta_title',
            'meta_description', 'meta_keywords', 'view_count',
            'reading_time', 'comment_count', 'is_published'
        ]


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating posts."""
    
    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Post
        fields = [
            'title', 'slug', 'excerpt', 'content', 'category_id', 'tag_ids',
            'featured_image', 'featured_image_alt', 'status', 'post_type',
            'is_featured', 'allow_comments', 'published_at', 'meta_title',
            'meta_description', 'meta_keywords'
        ]
    
    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', [])
        
        post = Post.objects.create(**validated_data)
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                post.category = category
                post.save()
            except Category.DoesNotExist:
                pass
        
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            post.tags.set(tags)
        
        return post
    
    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if category_id is not None:
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    instance.category = category
                except Category.DoesNotExist:
                    instance.category = None
            else:
                instance.category = None
            instance.save()
        
        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)
        
        return instance


class PostViewSerializer(serializers.ModelSerializer):
    """Serializer for post views."""
    
    class Meta:
        model = PostView
        fields = ['timestamp']
        read_only_fields = ['timestamp']
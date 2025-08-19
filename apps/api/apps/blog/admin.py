"""
Blog admin configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Tag, Post, PostView, PostPreviewToken


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin."""
    
    list_display = ('name', 'slug', 'parent', 'post_count', 'color_display', 'is_active', 'order')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'post_count')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Display', {
            'fields': ('color', 'icon', 'order', 'is_active')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def color_display(self, obj):
        """Display color as colored box."""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag admin."""
    
    list_display = ('name', 'slug', 'post_count', 'color_display', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'post_count')
    
    def color_display(self, obj):
        """Display color as colored box."""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post admin."""
    
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'published_at', 'view_count')
    list_filter = ('status', 'post_type', 'is_featured', 'allow_comments', 'category', 'created_at')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'reading_time', 'comment_count')
    filter_horizontal = ('tags',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Classification', {
            'fields': ('author', 'category', 'tags', 'post_type')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'is_featured', 'allow_comments')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'reading_time', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Set author if not set."""
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    """Post view admin."""
    
    list_display = ('post', 'user', 'ip_address', 'timestamp')
    list_filter = ('timestamp', 'post__category')
    search_fields = ('post__title', 'user__username', 'ip_address')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PostPreviewToken)
class PostPreviewTokenAdmin(admin.ModelAdmin):
    """Post preview token admin."""
    
    list_display = ('post', 'created_by', 'created_at', 'expires_at', 'used_count', 'max_uses')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('post__title', 'created_by__username')
    readonly_fields = ('token', 'created_at', 'used_count')
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
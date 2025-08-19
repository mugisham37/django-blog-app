"""
Blog Models
Core blog functionality including posts, categories, and tags.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
# from versatileimagefield.fields import VersatileImageField
import uuid

User = get_user_model()


class Category(models.Model):
    """Blog post categories."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, max_length=120)
    description = models.TextField(blank=True, help_text=_('Category description'))
    color = models.CharField(max_length=7, default='#007bff', help_text=_('Hex color code'))
    icon = models.CharField(max_length=50, blank=True, help_text=_('Font Awesome icon class'))
    
    # SEO fields
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Hierarchy
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # Ordering and visibility
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blog_category'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})
    
    @property
    def post_count(self):
        """Get number of published posts in this category."""
        return self.posts.filter(status=Post.PostStatus.PUBLISHED).count()


class Tag(models.Model):
    """Blog post tags."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=60)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6c757d')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blog_tag'
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'slug': self.slug})
    
    @property
    def post_count(self):
        """Get number of published posts with this tag."""
        return self.posts.filter(status=Post.PostStatus.PUBLISHED).count()


class PostManager(models.Manager):
    """Custom manager for Post model."""
    
    def published(self):
        """Get published posts."""
        return self.filter(
            status=Post.PostStatus.PUBLISHED,
            published_at__lte=timezone.now()
        )
    
    def featured(self):
        """Get featured posts."""
        return self.published().filter(is_featured=True)
    
    def by_author(self, author):
        """Get posts by specific author."""
        return self.published().filter(author=author)


class Post(models.Model):
    """Blog post model."""
    
    class PostStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        SCHEDULED = 'scheduled', _('Scheduled')
        ARCHIVED = 'archived', _('Archived')
    
    class PostType(models.TextChoices):
        ARTICLE = 'article', _('Article')
        TUTORIAL = 'tutorial', _('Tutorial')
        NEWS = 'news', _('News')
        REVIEW = 'review', _('Review')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    excerpt = models.TextField(max_length=300, blank=True, help_text=_('Short description'))
    content = RichTextUploadingField()
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    
    # Media
    featured_image = models.ImageField(
        upload_to='blog/featured/',
        blank=True,
        null=True,
        help_text=_('Featured image for the post')
    )
    featured_image_alt = models.CharField(max_length=200, blank=True)
    
    # Status and publishing
    status = models.CharField(max_length=20, choices=PostStatus.choices, default=PostStatus.DRAFT)
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.ARTICLE)
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    
    # Publishing dates
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=0, help_text=_('Estimated reading time in minutes'))
    
    objects = PostManager()
    
    class Meta:
        db_table = 'blog_post'
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['published_at']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-set published_at when status changes to published
        if self.status == self.PostStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        # Calculate reading time
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        """Check if post is published and visible."""
        return (
            self.status == self.PostStatus.PUBLISHED and
            self.published_at and
            self.published_at <= timezone.now()
        )
    
    @property
    def comment_count(self):
        """Get number of approved comments."""
        return self.comments.filter(is_approved=True).count()
    
    def get_related_posts(self, limit=3):
        """Get related posts based on tags and category."""
        related = Post.objects.published().exclude(id=self.id)
        
        if self.category:
            related = related.filter(category=self.category)
        
        if self.tags.exists():
            related = related.filter(tags__in=self.tags.all()).distinct()
        
        return related[:limit]


class PostView(models.Model):
    """Track post views for analytics."""
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blog_post_view'
        verbose_name = _('Post View')
        verbose_name_plural = _('Post Views')
        indexes = [
            models.Index(fields=['post', 'timestamp']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"View of {self.post.title} at {self.timestamp}"


class PostPreviewToken(models.Model):
    """Tokens for previewing unpublished posts."""
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='preview_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_count = models.PositiveIntegerField(default=0)
    max_uses = models.PositiveIntegerField(default=10)
    
    class Meta:
        db_table = 'blog_post_preview_token'
        verbose_name = _('Post Preview Token')
        verbose_name_plural = _('Post Preview Tokens')
        indexes = [
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"Preview token for {self.post.title}"
    
    def is_valid(self):
        """Check if token is still valid."""
        return (
            timezone.now() < self.expires_at and
            self.used_count < self.max_uses
        )
    
    def use_token(self):
        """Increment usage count."""
        if self.is_valid():
            self.used_count += 1
            self.save()
            return True
        return False
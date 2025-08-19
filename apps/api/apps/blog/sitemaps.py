"""
Blog sitemaps for SEO.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post, Category, Tag


class PostSitemap(Sitemap):
    """Sitemap for blog posts."""
    
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        """Return published posts."""
        return Post.objects.published()
    
    def lastmod(self, obj):
        """Return last modification date."""
        return obj.updated_at
    
    def location(self, obj):
        """Return post URL."""
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    """Sitemap for categories."""
    
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        """Return active categories."""
        return Category.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        """Return last modification date."""
        return obj.updated_at
    
    def location(self, obj):
        """Return category URL."""
        return obj.get_absolute_url()


class TagSitemap(Sitemap):
    """Sitemap for tags."""
    
    changefreq = 'monthly'
    priority = 0.5
    
    def items(self):
        """Return all tags."""
        return Tag.objects.all()
    
    def lastmod(self, obj):
        """Return last modification date."""
        return obj.updated_at
    
    def location(self, obj):
        """Return tag URL."""
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    """Sitemap for static views."""
    
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        """Return static view names."""
        return ['blog:home', 'blog:about', 'blog:contact']
    
    def location(self, item):
        """Return static view URL."""
        return reverse(item)


class NewsSitemap(Sitemap):
    """News sitemap for recent posts."""
    
    changefreq = 'daily'
    priority = 0.9
    
    def items(self):
        """Return recent published posts."""
        return Post.objects.published()[:100]  # Last 100 posts
    
    def lastmod(self, obj):
        """Return last modification date."""
        return obj.updated_at
    
    def location(self, obj):
        """Return post URL."""
        return obj.get_absolute_url()
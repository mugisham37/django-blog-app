"""
Blog signals for automatic tasks.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Post, Category, Tag


@receiver(pre_save, sender=Post)
def generate_post_slug(sender, instance, **kwargs):
    """Generate unique slug for post if not provided."""
    if not instance.slug:
        base_slug = slugify(instance.title)
        slug = base_slug
        counter = 1
        
        while Post.objects.filter(slug=slug).exclude(id=instance.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug


@receiver(pre_save, sender=Category)
def generate_category_slug(sender, instance, **kwargs):
    """Generate unique slug for category if not provided."""
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        while Category.objects.filter(slug=slug).exclude(id=instance.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug


@receiver(pre_save, sender=Tag)
def generate_tag_slug(sender, instance, **kwargs):
    """Generate unique slug for tag if not provided."""
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        while Tag.objects.filter(slug=slug).exclude(id=instance.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug
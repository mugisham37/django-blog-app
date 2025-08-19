"""
Blog-related Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from .common_types import BaseEntity, Timestamps, Visibility
from .user_types import UserListItem


class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ContentFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    RICH_TEXT = "rich_text"
    PLAIN_TEXT = "plain_text"


@dataclass
class Category(BaseEntity, Timestamps):
    """Category entity"""
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    parent: Optional['Category'] = None
    children: Optional[List['Category']] = None
    posts_count: int = 0
    is_featured: bool = False
    sort_order: int = 0


@dataclass
class Tag(BaseEntity, Timestamps):
    """Tag entity"""
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    posts_count: int = 0
    is_trending: bool = False


@dataclass
class PostSEO:
    """Post SEO metadata"""
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[List[str]] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    twitter_title: Optional[str] = None
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = None
    canonical_url: Optional[str] = None
    robots_index: bool = True
    robots_follow: bool = True


@dataclass
class PostMedia(BaseEntity, Timestamps):
    """Post media attachment"""
    post_id: int
    type: str  # image, video, audio, document
    url: str
    thumbnail_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    alt_text: Optional[str] = None
    file_size: int = 0
    mime_type: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    sort_order: int = 0


@dataclass
class Post(BaseEntity, Timestamps):
    """Post entity"""
    title: str
    slug: str
    content: str
    content_format: ContentFormat = ContentFormat.MARKDOWN
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    featured_image_alt: Optional[str] = None
    author_id: int = 0
    author: Optional[UserListItem] = None
    category_id: Optional[int] = None
    category: Optional[Category] = None
    tags: List[Tag] = None
    status: PostStatus = PostStatus.DRAFT
    visibility: Visibility = Visibility.PUBLIC
    is_featured: bool = False
    is_pinned: bool = False
    allow_comments: bool = True
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    reading_time: int = 0
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    seo: PostSEO = None
    media: List[PostMedia] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.seo is None:
            self.seo = PostSEO()
        if self.media is None:
            self.media = []


@dataclass
class PostListItem:
    """Post list item for listings"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    author: Optional[UserListItem] = None
    category: Optional[Category] = None
    tags: List[Tag] = None
    status: PostStatus = PostStatus.DRAFT
    is_featured: bool = False
    published_at: Optional[datetime] = None
    reading_time: int = 0
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class PostCreateRequest:
    """Post creation request"""
    title: str
    content: str
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content_format: ContentFormat = ContentFormat.MARKDOWN
    featured_image_alt: Optional[str] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    status: PostStatus = PostStatus.DRAFT
    visibility: Visibility = Visibility.PUBLIC
    is_featured: bool = False
    allow_comments: bool = True
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    seo: Optional[PostSEO] = None


@dataclass
class PostUpdateRequest:
    """Post update request"""
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    content_format: Optional[ContentFormat] = None
    featured_image_alt: Optional[str] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    status: Optional[PostStatus] = None
    visibility: Optional[Visibility] = None
    is_featured: Optional[bool] = None
    allow_comments: Optional[bool] = None
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    seo: Optional[PostSEO] = None


@dataclass
class PostSearchFilters:
    """Post search filters"""
    author_id: Optional[int] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    status: Optional[List[PostStatus]] = None
    visibility: Optional[List[Visibility]] = None
    is_featured: Optional[bool] = None
    published_after: Optional[datetime] = None
    published_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@dataclass
class CategoryCreateRequest:
    """Category creation request"""
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    is_featured: bool = False
    sort_order: int = 0


@dataclass
class TagCreateRequest:
    """Tag creation request"""
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
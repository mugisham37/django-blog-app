"""
Django-specific test configuration and fixtures.
"""
import pytest
import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from faker import Faker

fake = Faker()
User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    is_active = True
    is_staff = False
    is_superuser = False

class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f"admin{n}")

class GroupFactory(factory.django.DjangoModelFactory):
    """Factory for creating test groups."""
    class Meta:
        model = Group
    
    name = factory.Sequence(lambda n: f"group{n}")

@pytest.fixture
def user_factory():
    """Provide user factory."""
    return UserFactory

@pytest.fixture
def admin_user_factory():
    """Provide admin user factory."""
    return AdminUserFactory

@pytest.fixture
def group_factory():
    """Provide group factory."""
    return GroupFactory

@pytest.fixture
def user(user_factory):
    """Create a test user."""
    return user_factory()

@pytest.fixture
def admin_user(admin_user_factory):
    """Create an admin user."""
    return admin_user_factory()

@pytest.fixture
def group(group_factory):
    """Create a test group."""
    return group_factory()

# Blog-specific factories (if blog app exists)
try:
    from apps.api.apps.blog.models import Post, Category, Tag, Comment
    
    class CategoryFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Category
        
        name = factory.LazyFunction(fake.word)
        slug = factory.LazyAttribute(lambda obj: obj.name.lower())
        description = factory.LazyFunction(fake.text)
    
    class TagFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Tag
        
        name = factory.LazyFunction(fake.word)
        slug = factory.LazyAttribute(lambda obj: obj.name.lower())
    
    class PostFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Post
        
        title = factory.LazyFunction(fake.sentence)
        slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
        content = factory.LazyFunction(fake.text)
        author = factory.SubFactory(UserFactory)
        category = factory.SubFactory(CategoryFactory)
        status = 'published'
        is_featured = False
    
    class CommentFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Comment
        
        post = factory.SubFactory(PostFactory)
        author = factory.SubFactory(UserFactory)
        content = factory.LazyFunction(fake.text)
        is_approved = True
    
    @pytest.fixture
    def category_factory():
        return CategoryFactory
    
    @pytest.fixture
    def tag_factory():
        return TagFactory
    
    @pytest.fixture
    def post_factory():
        return PostFactory
    
    @pytest.fixture
    def comment_factory():
        return CommentFactory

except ImportError:
    # Blog models don't exist yet
    pass
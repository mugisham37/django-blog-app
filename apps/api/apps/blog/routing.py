"""
Blog WebSocket routing
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/blog/posts/(?P<post_id>[0-9a-f-]+)/$', consumers.PostConsumer.as_asgi()),
    re_path(r'ws/blog/comments/(?P<post_id>[0-9a-f-]+)/$', consumers.CommentConsumer.as_asgi()),
]
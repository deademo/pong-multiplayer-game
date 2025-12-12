"""WebSocket URL routing for Pong game."""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<room_code>[^/]+)/$', consumers.PongConsumer.as_asgi()),
]

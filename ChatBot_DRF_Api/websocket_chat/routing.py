# websocket_chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Company-based chat rooms for real-time messaging
    re_path(r'ws/chat/(?P<company_id>\w+)/$', consumers.CompanyChatConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<company_id>\w+)/(?P<session_id>[\w-]+)/$', consumers.CompanyChatConsumer.as_asgi()),
    
    # Agent dashboard WebSocket for real-time updates
    re_path(r'ws/agents/$', consumers.AgentChatConsumer.as_asgi()),
]

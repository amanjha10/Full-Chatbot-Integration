"""
WebSocket routing for chatbot app
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat WebSocket - matches: ws://localhost:8000/ws/chat/COMPANY_ID/SESSION_ID/
    re_path(r'ws/chat/(?P<company_id>\w+)/(?P<session_id>[\w-]+)/$', consumers.ChatConsumer.as_asgi()),
    
    # Configuration updates WebSocket - matches: ws://localhost:8000/ws/config/COMPANY_ID/
    re_path(r'ws/config/(?P<company_id>\w+)/$', consumers.ConfigConsumer.as_asgi()),
    
    # User management updates WebSocket - matches: ws://localhost:8000/ws/users/COMPANY_ID/
    re_path(r'ws/users/(?P<company_id>\w+)/$', consumers.UserManagementConsumer.as_asgi()),
]

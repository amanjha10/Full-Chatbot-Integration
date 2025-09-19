"""
WebSocket routing for human handoff app
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Human handoff WebSocket - matches: ws://localhost:8000/ws/handoff/COMPANY_ID/
    re_path(r'ws/handoff/(?P<company_id>\w+)/$', consumers.HumanHandoffConsumer.as_asgi()),

    # Agent dashboard WebSocket - matches: ws://localhost:8000/ws/agent/AGENT_ID/
    re_path(r'ws/agent/(?P<agent_id>\w+)/$', consumers.AgentDashboardConsumer.as_asgi()),

    # Chatbot user WebSocket - matches: ws://localhost:8000/ws/chat/COMPANY_ID/SESSION_ID/
    re_path(r'ws/chat/(?P<company_id>\w+)/(?P<session_id>[\w-]+)/$', consumers.ChatbotUserConsumer.as_asgi()),
]

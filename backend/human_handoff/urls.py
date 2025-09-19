# human_handoff/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Session management
    path('escalate/', views.escalate_session_view, name='escalate_session'),
    path('assign/', views.assign_session_view, name='assign_session'),
    path('resolve/', views.resolve_session_view, name='resolve_session'),
    path('sessions/', views.list_handoff_sessions_view, name='list_handoff_sessions'),
    
    # Agent functionality
    path('dashboard/', views.agent_dashboard_view, name='agent_dashboard'),
    path('send-message/', views.send_message_view, name='send_message'),
    path('activities/', views.agent_activities_view, name='agent_activities'),
    
    # Company-based agent APIs
    path('agent/sessions/', views.agent_sessions_view, name='agent_sessions'),
    path('agent/sessions/<str:session_id>/messages/', views.agent_session_messages_view, name='agent_session_messages'),
    path('agent/send-message/', views.agent_send_message_view, name='agent_send_message'),
    path('agent/upload/', views.agent_upload_file_view, name='agent_upload_file'),
    path('agent/upload/', views.agent_upload_file_view, name='agent_upload_file'),
]

from django.urls import path
from . import views

urlpatterns = [
    # Agent Dashboard Statistics
    path('stats/', views.agent_stats_view, name='agent_stats'),
    path('profile/', views.agent_profile_view, name='agent_profile'),
    
    # Session Management
    path('pending-sessions/', views.agent_pending_sessions_view, name='agent_pending_sessions'),
    path('active-sessions/', views.agent_active_sessions_view, name='agent_active_sessions'),
    path('accept-session/', views.accept_session_view, name='accept_session'),
    path('complete-session/', views.complete_session_view, name='complete_session'),
]

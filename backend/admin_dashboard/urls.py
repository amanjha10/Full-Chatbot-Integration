from django.urls import path
from . import views

urlpatterns = [
    # User Profile Management (Admin/SuperAdmin only)
    path('user-profiles/', views.user_profiles_list_view, name='user_profiles_list'),
    path('user-profiles/<int:profile_id>/', views.user_profile_detail_view, name='user_profile_detail'),
    path('user-profiles/stats/', views.user_profiles_stats_view, name='user_profiles_stats'),
    path('user-profiles/<int:profile_id>/delete/', views.delete_user_profile_view, name='delete_user_profile'),
    path('user-profiles/toggle-favorite/', views.toggle_user_favorite_view, name='toggle_user_favorite'),
    path('user-profiles/clear-non-favorites/', views.clear_user_profiles_view, name='clear_user_profiles'),
    
    # Agent Management (Admin/SuperAdmin only)
    path('check-agent-limit/', views.check_agent_limit_view, name='check_agent_limit'),
    path('create-agent/', views.create_agent_view, name='create_agent'),
    path('list-agents/', views.list_agents_view, name='list_agents'),
    path('update-agent/<int:agent_id>/', views.update_agent_view, name='update_agent'),
    path('delete-agent/<int:agent_id>/', views.delete_agent_view, name='delete_agent'),
    path('reset-agent-password/', views.reset_agent_password_view, name='reset_agent_password'),
    
    # Agent Authentication
    path('agent-first-login/', views.agent_first_login_view, name='agent_first_login'),
    path('agent-login/', views.agent_login_view, name='agent_login'),
    path('agent-logout/', views.agent_logout_view, name='agent_logout'),
    
    # Agent Status Management
    path('update-agent-status/', views.update_agent_status_view, name='update_agent_status'),
    
    # Agent Sessions (Analytics)
    path('agent-sessions/', views.agent_sessions_view, name='agent_sessions'),
    
    # Plan Upgrade Requests
    path('request-plan-upgrade/', views.request_plan_upgrade, name='request_plan_upgrade'),
    path('cancel-plan-upgrade/', views.cancel_plan_upgrade, name='cancel_plan_upgrade'),
    path('my-plan-upgrade-status/', views.get_my_plan_upgrade_status, name='get_my_plan_upgrade_status'),
    path('plan-upgrade-requests/', views.get_plan_upgrade_requests, name='get_plan_upgrade_requests'),
    path('plan-upgrade-requests/<int:request_id>/review/', views.review_plan_upgrade_request, name='review_plan_upgrade_request'),

    # Debug (temporary)
    path('debug-agent/<int:agent_id>/', views.debug_agent_view, name='debug_agent'),

    # Dashboard Statistics
    path('dashboard-stats/', views.dashboard_stats_view, name='dashboard_stats'),
    path('available-agents/', views.available_agents_view, name='available_agents'),

    # Session Assignment
    path('assign-session/', views.assign_session_view, name='assign_session'),
    path('pending-sessions/', views.pending_sessions_view, name='pending_sessions'),

    # Agent Dashboard APIs
    path('agent-dashboard/stats/', views.agent_dashboard_stats_view, name='agent_dashboard_stats'),
    path('agent-dashboard/pending-sessions/', views.agent_pending_sessions_view, name='agent_pending_sessions'),
    path('agent-send-message/', views.agent_send_message_view, name='agent_send_message'),

    # Debug endpoints
    path('debug-company-isolation/', views.debug_company_isolation_view, name='debug_company_isolation'),
    path('fix-agent-status/', views.fix_agent_status_view, name='fix_agent_status'),
]

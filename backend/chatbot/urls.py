# chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Chat endpoints
    path('chat/', views.chat_message_view, name='chat_message'),
    path('upload/', views.file_upload_view, name='file_upload'),  # Legacy endpoint
    path('files/', views.file_list_view, name='file_list'),  # New file list endpoint
    path('session-status/', views.session_status_view, name='session_status'),
    path('chat-history/', views.chat_history_view, name='chat_history'),

    # Plan Management
    path('plans/', views.plans_list_view, name='plans_list'),
    path('plans/<int:plan_id>/', views.plan_update_view, name='plan_update'),
    path('company-plan/', views.company_plan_view, name='company_plan'),
    path('request-plan-upgrade/', views.request_plan_upgrade_view, name='request_plan_upgrade'),
    path('cancel-plan-upgrade/', views.cancel_plan_upgrade_view, name='cancel_plan_upgrade'),
    path('check-agent-limit/', views.check_agent_limit_chatbot_view, name='check_agent_limit_chatbot'),

    # SuperAdmin Plan Management
    path('superadmin/plans/', views.superadmin_plans_list_view, name='superadmin_plans_list'),
    path('superadmin/plans/<int:plan_id>/', views.superadmin_plan_update_view, name='superadmin_plan_update'),

    # SuperAdmin Upgrade Requests
    path('superadmin/upgrade-requests/', views.superadmin_upgrade_requests_view, name='superadmin_upgrade_requests'),
    path('superadmin/upgrade-requests/<int:request_id>/approve/', views.superadmin_approve_upgrade_request_view, name='superadmin_approve_upgrade_request'),
    path('superadmin/upgrade-requests/<int:request_id>/decline/', views.superadmin_decline_upgrade_request_view, name='superadmin_decline_upgrade_request'),

    # SuperAdmin Company Management
    path('superadmin/company-subscriptions/', views.superadmin_company_subscriptions_view, name='superadmin_company_subscriptions'),
    path('superadmin/company/<str:company_id>/change-plan/', views.superadmin_change_company_plan_view, name='superadmin_change_company_plan'),

    # SuperAdmin FAQ Management
    path('superadmin/faqs/', views.superadmin_faq_list_view, name='superadmin_faq_list'),
    path('superadmin/faqs/refresh-vectors/', views.superadmin_refresh_vectors_view, name='superadmin_refresh_vectors'),
    path('superadmin/faqs/<str:faq_id>/', views.superadmin_faq_detail_view, name='superadmin_faq_detail'),

    # Company Subscription Management
    path('company/<str:company_id>/subscription/', views.company_subscription_view, name='company_subscription'),
    path('company/<str:company_id>/upgrade-request/', views.company_upgrade_request_view, name='company_upgrade_request'),

    # Admin Plans (read-only for upgrade modal)
    path('admin/plans/', views.admin_plans_view, name='admin_plans'),

    # Company-specific FAQ Management (Admin only)
    path('admin/company-faqs/', views.admin_company_faq_list_view, name='admin_company_faq_list'),
    path('admin/company-faqs/create/', views.admin_company_faq_create_view, name='admin_company_faq_create'),
    path('admin/company-faqs/refresh-vectors/', views.admin_company_refresh_vectors_view, name='admin_company_refresh_vectors'),
    path('admin/company-faqs/<str:faq_id>/', views.admin_company_faq_detail_view, name='admin_company_faq_detail'),
    path('admin/company-faqs/<str:faq_id>/update/', views.admin_company_faq_update_view, name='admin_company_faq_update'),
    path('admin/company-faqs/<str:faq_id>/delete/', views.admin_company_faq_delete_view, name='admin_company_faq_delete'),
    
    # Profile management
    path('create-profile/', views.create_profile_view, name='create_profile'),
    path('validate-phone/', views.validate_phone_view, name='validate_phone'),
    path('country-codes/', views.country_codes_view, name='country_codes'),
    
    # RAG system
    path('load-rag-documents/', views.load_rag_documents_view, name='load_rag_documents'),

    # Chatbot configuration
    path('configuration/', views.chatbot_configuration_view, name='chatbot_configuration'),
    path('configuration/update/', views.update_chatbot_configuration_view, name='update_chatbot_configuration'),

    # Test endpoints
    path('test-data/', views.test_data_view, name='test_data'),

    # Embed widget endpoints
    path('company-config/<str:company_id>/', views.company_config_view, name='company_config'),
    path('company/<str:company_id>/status/', views.company_subscription_status_view, name='company_subscription_status'),
    path('update-chatbot-config/', views.update_chatbot_config_view, name='update_chatbot_config'),
    path('detection-report/', views.chatbot_detection_report_view, name='chatbot_detection_report'),
    path('detection-status/<str:company_id>/', views.chatbot_detection_status_view, name='chatbot_detection_status'),

    # Static file serving
    path('chatbot.js', views.serve_chatbot_js, name='serve_chatbot_js'),
]

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login_view, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.profile_view, name='profile'),

    # Admin Management endpoints (SuperAdmin only)
    path('create-admin/', views.create_admin_view, name='create_admin'),
    path('list-admins/', views.list_admins_view, name='list_admins'),
    path('update-admin/<int:admin_id>/', views.update_admin_view, name='update_admin'),
    path('delete-admin/<int:admin_id>/', views.delete_admin_view, name='delete_admin'),
    path('change-admin-plan/<int:admin_id>/', views.change_admin_plan_view, name='change_admin_plan'),

    # Admin First Login & Password Reset
    path('reset-admin-password/', views.reset_admin_password_view, name='reset_admin_password'),
    path('admin-first-login/', views.admin_first_login_view, name='admin_first_login'),

    # Plan Management endpoints (SuperAdmin only)
    path('create-plan/', views.create_plan_view, name='create_plan'),
    path('assign-plan/', views.assign_plan_view, name='assign_plan'),
    path('list-plans/', views.list_plans_view, name='list_plans'),
    path('plan-types/', views.plan_types_view, name='plan_types'),
    path('plan-history/<int:plan_id>/', views.plan_history_view, name='plan_history'),
    path('list-user-plan-assignments/', views.list_user_plan_assignments_view, name='list_user_plan_assignments'),

    # Subscription Management endpoints (SuperAdmin only)
    path('cancel-subscription/', views.cancel_subscription_view, name='cancel_subscription'),
    path('renew-subscription/', views.renew_subscription_view, name='renew_subscription'),
    path('upgrade-plan/', views.upgrade_plan_view, name='upgrade_plan'),

    # Super Admin Statistics
    path('super-admin-stats/', views.super_admin_stats_view, name='super_admin_stats'),
    
    # New Company Subscription Management endpoints
    path('company-subscriptions/', views.company_subscriptions_view, name='company_subscriptions'),
    path('cancel-subscription/<int:company_id>/', views.cancel_company_subscription_view, name='cancel_company_subscription'),
    path('reactivate-subscription/<int:company_id>/', views.reactivate_company_subscription_view, name='reactivate_company_subscription'),
    path('cancel-subscription-by-assignment/<int:assignment_id>/', views.cancel_subscription_by_assignment_view, name='cancel_subscription_by_assignment'),
    path('create-enhanced-company/', views.create_enhanced_company_view, name='create_enhanced_company'),
    
    # Plan Upgrade Request Management (SuperAdmin only)
    path('upgrade-requests/', views.list_upgrade_requests, name='list_upgrade_requests'),
    path('upgrade-requests/<int:request_id>/review/', views.review_upgrade_request, name='review_upgrade_request'),
]

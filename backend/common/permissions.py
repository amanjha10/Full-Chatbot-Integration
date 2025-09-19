"""
Common permission classes to eliminate duplicate permission logic across the project.
"""
from rest_framework.permissions import BasePermission
from authentication.models import User


class IsAdminOrSuperAdmin(BasePermission):
    """
    Permission class for Admin and SuperAdmin access.
    Consolidates duplicate permission logic from admin_dashboard/views.py
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.Role.ADMIN, User.Role.SUPERADMIN])
        )


class IsAgent(BasePermission):
    """
    Permission class for Agent access only.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.AGENT
        )


class IsCompanyMember(BasePermission):
    """
    Permission class to check if user belongs to the same company.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Extract company_id from request (query params, data, or URL)
        company_id = (
            request.GET.get('company_id') or
            request.data.get('company_id') if hasattr(request, 'data') else None or
            view.kwargs.get('company_id')
        )
        
        if not company_id:
            return True  # If no company_id specified, allow access
        
        return request.user.company_id == company_id


def check_agent_role(user):
    """
    Helper function to check if user is an agent.
    Consolidates duplicate role checking logic.
    """
    return user and user.is_authenticated and user.role == User.Role.AGENT


def check_admin_role(user):
    """
    Helper function to check if user is admin or superadmin.
    Consolidates duplicate role checking logic.
    """
    return (
        user and 
        user.is_authenticated and 
        user.role in [User.Role.ADMIN, User.Role.SUPERADMIN]
    )


def check_superadmin_role(user):
    """
    Helper function to check if user is superadmin.
    """
    return user and user.is_authenticated and user.role == User.Role.SUPERADMIN

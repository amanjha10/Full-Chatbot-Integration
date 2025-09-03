from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Custom permission to only allow SuperAdmins to access the view.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superadmin
        )


class IsAdminOrSuperAdmin(BasePermission):
    """
    Custom permission to allow Admins and SuperAdmins to access the view.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'SUPERADMIN']
        )




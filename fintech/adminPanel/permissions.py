# adminPanel/permissions.py
from rest_framework.permissions import BasePermission


class IsAdminOrSuperAdmin(BasePermission):
    """Full access to admin users."""
    message = "Access restricted to admin users only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'admin'
        )


class IsSuperAdmin(BasePermission):
    """Alias for admin — kept for compatibility."""
    message = "Access restricted to admin users only."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'admin'
        )


class IsAdminSupportOrAbove(BasePermission):
    """Admin only — support role removed to match Supabase."""
    message = "Access restricted to admin users."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'admin'
        )


class IsOwnerOrAdminAbove(BasePermission):
    """Clients/hustlers see only their own data. Admins see everything."""
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'admin':
            return True
        return obj == request.user
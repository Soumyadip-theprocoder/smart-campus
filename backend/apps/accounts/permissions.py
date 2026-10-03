"""
Reusable DRF permission classes for role-based access control.
"""

from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """Allow access only to authenticated admins (role=admin or staff)."""

    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_staff or getattr(user, "role", None) == "admin")
        )

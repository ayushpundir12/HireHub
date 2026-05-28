from rest_framework.permissions import BasePermission


class IsProUser(BasePermission):
    """Allow access only to users with role='pro'."""

    message = 'Only verified pro accounts can access this.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'pro'
        )
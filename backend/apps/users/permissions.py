from rest_framework.permissions import BasePermission

class IsFullyVerified(BasePermission):
    """
    Blocks access if user hasn't verified
    both email and phone number
    """
    message = 'Please verify your email and phone number to continue.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_email_verified and
            request.user.is_number_verified
        )


class IsEmailVerified(BasePermission):
    """
    Only checks email verification
    Used for phone verify endpoint
    """
    message = 'Please verify your email first.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_email_verified
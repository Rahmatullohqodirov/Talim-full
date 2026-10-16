from rest_framework.permissions import BasePermission


class IsPremiumUser(BasePermission):
    """Voice cloning, ko'p avatar tanlash kabi premium-only endpointlar uchun."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_premium)

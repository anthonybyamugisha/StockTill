from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role == "admin"
        )


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role in ("admin", "manager")
        )


class IsCashier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

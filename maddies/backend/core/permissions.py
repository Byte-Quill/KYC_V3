from rest_framework.permissions import BasePermission

from .models import User


class IsCEO(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_ceo)


class IsSuperAdminOrAbove(BasePermission):
    """CEO or Superadmin."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.rank <= User.ROLE_RANK[User.Role.SUPERADMIN])


class IsAdminOrAbove(BasePermission):
    """CEO, Superadmin or Admin — can manage maddies and assignments."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.rank <= User.ROLE_RANK[User.Role.ADMIN])


class CanManageUsers(BasePermission):
    """May create/list users strictly below their own rank."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.rank <= User.ROLE_RANK[User.Role.ADMIN])

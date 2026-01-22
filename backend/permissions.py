from typing import Iterable, Optional

from rest_framework.permissions import BasePermission

from backend.models import UserData


def _is_authenticated(user) -> bool:
    return getattr(user, "is_authenticated", False)


def _role_in(user, roles: Iterable[str]) -> bool:
    role = getattr(user, "role", None)
    return role in roles if role else False


ADMIN_ROLES = {UserData.Roles.ADMIN, UserData.Roles.SUPERADMIN}
BUSINESS_LEADER_ROLES = ADMIN_ROLES | {UserData.Roles.BUSINESS_LEADER}
REGIONAL_MANAGER_ROLES = BUSINESS_LEADER_ROLES | {UserData.Roles.REGIONAL_MANAGER}
MANAGER_ROLES = REGIONAL_MANAGER_ROLES | {UserData.Roles.MANAGER}
VENDOR_ROLES = MANAGER_ROLES | {UserData.Roles.VENDOR}


class BaseRolePermission(BasePermission):
    allowed_roles: Iterable[str] = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        return _is_authenticated(user) and _role_in(user, self.allowed_roles)


class IsSuperAdminRole(BaseRolePermission):
    allowed_roles = {UserData.Roles.SUPERADMIN}


class IsAdminRole(BaseRolePermission):
    allowed_roles = ADMIN_ROLES


class IsBusinessLeaderRole(BaseRolePermission):
    allowed_roles = BUSINESS_LEADER_ROLES


class IsRegionalManagerRole(BaseRolePermission):
    allowed_roles = REGIONAL_MANAGER_ROLES


class IsManagerRole(BaseRolePermission):
    allowed_roles = MANAGER_ROLES


class IsVendorRole(BaseRolePermission):
    allowed_roles = VENDOR_ROLES


class IsStandardUserRole(BaseRolePermission):
    allowed_roles = {UserData.Roles.USER}

class IsAnyAuthenticatedUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.user and request.user.is_authenticated

class IsOwnerOrAdmin(BasePermission):
    """
    Allows access to admins, superadmins or to the owner of the resource
    when the URL includes an `id` kwarg.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not _is_authenticated(user):
            return False

        if _role_in(user, ADMIN_ROLES):
            return True

        target_id = _get_target_id(view)
        return target_id is not None and str(target_id) == str(user.id)


def _get_target_id(view) -> Optional[int]:
    if hasattr(view, "kwargs"):
        return view.kwargs.get("id")
    return None


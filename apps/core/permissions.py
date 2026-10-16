"""
Role-based DRF permissions.

Three layers (see README):
1. Role gate           -> IsCustomer / IsStaffRole / IsAdminRole / IsSuperAdmin
2. Model permissions   -> StaffModelPermissions (Django perms, granular per staff member)
3. Object ownership    -> customer querysets are always filtered by request.user
"""

from rest_framework.permissions import BasePermission, DjangoModelPermissions

from apps.accounts.models import Role


class _RolePermission(BasePermission):
    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.role in self.allowed_roles)


class IsCustomer(_RolePermission):
    allowed_roles = (Role.CUSTOMER,)


class IsStaffRole(_RolePermission):
    """Staff, Admin or Super Admin - i.e. anyone allowed inside the admin namespace."""

    allowed_roles = (Role.STAFF, Role.ADMIN, Role.SUPER_ADMIN)


class IsAdminRole(_RolePermission):
    allowed_roles = (Role.ADMIN, Role.SUPER_ADMIN)


class IsSuperAdmin(_RolePermission):
    allowed_roles = (Role.SUPER_ADMIN,)


class StaffModelPermissions(DjangoModelPermissions):
    """
    Admin-namespace default: user must hold a staff-level role AND the matching
    Django model permission (view/add/change/delete). Unlike the stock class,
    GET also requires ``view_<model>`` so staff cannot read what they may not see.
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    def has_permission(self, request, view):
        if not IsStaffRole().has_permission(request, view):
            return False
        return super().has_permission(request, view)

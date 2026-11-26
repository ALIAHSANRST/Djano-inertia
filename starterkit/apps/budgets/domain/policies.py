from django.core.exceptions import PermissionDenied

from .models import BudgetRole

Role = BudgetRole.Role


def role_for(actor):
    if not actor.is_authenticated or not actor.is_active:
        return None
    if actor.is_superuser:
        return Role.ADMIN
    profile = getattr(actor, "budget_profile", None)
    return profile.role if profile else Role.CLIENT


def require_role(actor, expected_role):
    if role_for(actor) != expected_role:
        raise PermissionDenied("Your account cannot open this page or perform this action.")

from decimal import Decimal

from django.db.models import BigIntegerField, F, Q, Sum
from django.db.models.functions import Cast, Round

from ..domain.models import BudgetRequest, BudgetRole

Status = BudgetRequest.Status


def request_list(requester=None):
    rows = BudgetRequest.objects.select_related("requester", "reviewer")
    return rows if requester is None else rows.filter(requester=requester)


def funding_totals():
    # SQLite can store decimal values as floats. Sum rounded cents as integers.
    cents = Cast(Round(F("amount") * 100), BigIntegerField())
    totals = BudgetRequest.objects.filter(withdrawn_at__isnull=True).aggregate(
        pending=Sum(cents, filter=Q(status=Status.PENDING), default=0),
        approved=Sum(cents, filter=Q(status=Status.APPROVED), default=0),
    )
    return {key: Decimal(value).scaleb(-2) for key, value in totals.items()}


def create_request(*, requester, fields):
    return BudgetRequest.objects.create(requester=requester, **fields)


def pending_request(request_id, revision, requester=None):
    rows = BudgetRequest.objects.filter(
        pk=request_id, status=Status.PENDING, withdrawn_at=None, revision=revision,
    )
    return rows if requester is None else rows.filter(requester=requester)


def update_pending(query, fields):
    return query.update(**fields, revision=F("revision") + 1)


def delete_request(request_id):
    return BudgetRequest.objects.filter(pk=request_id).delete()[0]


def has_elevated_budget_role(user):
    return BudgetRole.objects.filter(
        user=user, role__in=[BudgetRole.Role.MANAGER, BudgetRole.Role.ADMIN]
    ).exists()


def role_choices():
    return BudgetRole.Role.choices


def assigned_role(user):
    profile = getattr(user, "budget_profile", None)
    return profile.role if profile else BudgetRole.Role.CLIENT


def set_role(user, role):
    BudgetRole.objects.update_or_create(user=user, defaults={"role": role})

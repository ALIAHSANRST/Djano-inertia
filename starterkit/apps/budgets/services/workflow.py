from decimal import Decimal

from django import forms
from django.core.paginator import Paginator
from django.http import Http404
from django.utils import timezone

from ..domain.models import BudgetRequest
from ..domain.policies import Role, require_role, role_for
from ..dto.requests import MutationResult
from ..selectors import requests

Status = BudgetRequest.Status
STALE = MutationResult({"action": "This request changed or is no longer available. Close this form and check the updated list."})


class RequestForm(forms.Form):
    title = forms.CharField(max_length=160)
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_digits=12, decimal_places=2)
    justification = forms.CharField(max_length=4000)


class ReviewForm(forms.Form):
    status = forms.ChoiceField(choices=[(Status.APPROVED, "Approve"), (Status.REJECTED, "Reject")])
    feedback = forms.CharField(required=False, max_length=2000)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == Status.REJECTED and cleaned.get("feedback") == "":
            self.add_error("feedback", "Explain why this request is being rejected.")
        return cleaned


def _errors(form):
    return MutationResult({key: str(errors[0]) for key, errors in form.errors.items()})


def _money(value):
    return format(value, ",.2f")


def _serialize(row, role):
    pending = row.status == Status.PENDING and row.withdrawn_at is None
    return {
        "id": row.pk,
        "revision": row.revision,
        "title": row.title,
        "amount": format(row.amount, ".2f"),
        "formattedAmount": _money(row.amount),
        "justification": row.justification,
        "status": "Withdrawn" if row.withdrawn_at else row.get_status_display(),
        "feedback": row.feedback,
        "requester": row.requester.get_username(),
        "reviewer": row.reviewer.get_username() if row.reviewer else "",
        "createdAt": row.created_at.isoformat(),
        "canEdit": pending and role == Role.CLIENT,
        "canReview": pending and role == Role.MANAGER,
        "canDelete": role == Role.ADMIN,
    }


def dashboard_route(actor):
    return {
        Role.CLIENT: "budget_client",
        Role.MANAGER: "budget_manager",
        Role.ADMIN: "budget_admin",
    }.get(role_for(actor), "budget_login")


def dashboard(*, actor, role, page, history_page):
    require_role(actor, role)
    rows = requests.request_list(actor if role == Role.CLIENT else None)

    def paginate(query, number):
        result = Paginator(query, 20).get_page(number)
        return {
            "items": [_serialize(row, role) for row in result],
            "page": result.number,
            "next": result.next_page_number() if result.has_next() else None,
            "previous": result.previous_page_number() if result.has_previous() else None,
        }

    if role == Role.MANAGER:
        queue = rows.filter(status=Status.PENDING, withdrawn_at=None)
        return {"queue": paginate(queue, page),
                "history": paginate(rows.exclude(pk__in=queue.values("pk")), history_page)}
    props = {"requests": paginate(rows, page)}
    if role == Role.ADMIN:
        props["totals"] = {key: _money(value) for key, value in requests.funding_totals().items()}
    return props


def create(*, actor, data):
    require_role(actor, Role.CLIENT)
    form = RequestForm(vars(data))
    if not form.is_valid():
        return _errors(form)
    requests.create_request(requester=actor, fields=form.cleaned_data)
    return MutationResult({}, "Budget request submitted.")


def update(*, actor, request_id, data):
    require_role(actor, Role.CLIENT)
    form = RequestForm(vars(data))
    if not form.is_valid():
        return _errors(form)
    if requests.update_pending(requests.pending_request(request_id, data.revision, actor), form.cleaned_data):
        return MutationResult({}, "Budget request updated.")
    return STALE


def withdraw(*, actor, request_id, revision):
    require_role(actor, Role.CLIENT)
    if requests.update_pending(requests.pending_request(request_id, revision, actor), {"withdrawn_at": timezone.now()}):
        return MutationResult({}, "Budget request withdrawn.")
    return STALE


def review(*, actor, request_id, data):
    require_role(actor, Role.MANAGER)
    form = ReviewForm(vars(data))
    if not form.is_valid():
        return _errors(form)
    fields = dict(form.cleaned_data, reviewer=actor, decided_at=timezone.now())
    if requests.update_pending(requests.pending_request(request_id, data.revision), fields):
        return MutationResult({}, "Decision recorded.")
    return STALE


def delete(*, actor, request_id):
    require_role(actor, Role.ADMIN)
    if not requests.delete_request(request_id):
        raise Http404("The request no longer exists.")
    return MutationResult({}, "Budget request permanently deleted.")

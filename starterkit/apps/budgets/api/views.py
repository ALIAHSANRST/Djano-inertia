import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST
from inertia import render

from ..domain.policies import Role
from ..dto.requests import BudgetInput, ReviewInput
from ..services import workflow

budget_login_required = login_required(login_url="budget_login")
budget_action_login = login_required(login_url="budget_login", redirect_field_name=None)


@budget_login_required
@require_GET
def index(request):
    return redirect(workflow.dashboard_route(request.user))


def _dashboard(request, route, role, component):
    props = workflow.dashboard(
        actor=request.user, role=role, page=request.GET.get("page"),
        history_page=request.GET.get("history"),
    )
    props["errors"] = request.session.pop(f"{route}_errors", {})
    return render(request, component, props)


@budget_login_required
@require_GET
def client(request):
    return _dashboard(request, "budget_client", Role.CLIENT, "Budgets/Client")


@budget_login_required
@require_GET
def manager(request):
    return _dashboard(request, "budget_manager", Role.MANAGER, "Budgets/Manager")


@budget_login_required
@require_GET
def admin(request):
    return _dashboard(request, "budget_admin", Role.ADMIN, "Budgets/Admin")


def _fields(request):
    data = request.POST
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeError):
            data = {}
    return data if hasattr(data, "get") else {}


def _text(data, field):
    value = data.get(field)
    return value if isinstance(value, str) else ""


def _revision(data):
    value = data.get("revision")
    if isinstance(value, str) and value.isascii() and value.isdecimal() and len(value) <= 10:
        value = int(value)
    return value if type(value) is int and 0 <= value <= 2_147_483_647 else None


def _budget_input(request):
    data = _fields(request)
    return BudgetInput(_text(data, "title"), _text(data, "amount"),
                       _text(data, "justification"), _revision(data))


def _result(request, route, result):
    if result.errors:
        request.session[f"{route}_errors"] = result.errors
    else:
        request.session.pop(f"{route}_errors", None)
        messages.success(request, result.message)
    return redirect(route)


@budget_action_login
@require_POST
def create(request):
    return _result(request, "budget_client", workflow.create(
        actor=request.user, data=_budget_input(request),
    ))


@budget_action_login
@require_POST
def update(request, request_id):
    return _result(request, "budget_client", workflow.update(
        actor=request.user, request_id=request_id, data=_budget_input(request),
    ))


@budget_action_login
@require_POST
def withdraw(request, request_id):
    return _result(request, "budget_client", workflow.withdraw(
        actor=request.user, request_id=request_id, revision=_revision(_fields(request)),
    ))


@budget_action_login
@require_POST
def review(request, request_id):
    data = _fields(request)
    return _result(request, "budget_manager", workflow.review(
        actor=request.user, request_id=request_id,
        data=ReviewInput(_text(data, "status"), _text(data, "feedback"), _revision(data)),
    ))


@budget_action_login
@require_POST
def delete(request, request_id):
    return _result(request, "budget_admin", workflow.delete(actor=request.user, request_id=request_id))

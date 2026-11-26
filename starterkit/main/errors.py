from django.views.csrf import csrf_failure as django_csrf_failure
from django.views.defaults import page_not_found, permission_denied
from inertia import render


def budget_forbidden(request, exception):
    if not is_budget_route(request):
        return permission_denied(request, exception)
    return budget_error(request, 403, "Your account cannot access this page or perform this action.")


def budget_not_found(request, exception):
    if not is_budget_route(request):
        return page_not_found(request, exception)
    return budget_error(request, 404, "This budget request is no longer available.")


def csrf_failure(request, reason=""):
    if not is_budget_route(request):
        return django_csrf_failure(request, reason=reason)
    return budget_error(request, 403, "Your session could not be verified. Return to your dashboard and try again.")


def is_budget_route(request):
    return request.resolver_match and (request.resolver_match.url_name or "").startswith("budget_")


def budget_error(request, status, message):
    response = render(request, "Budgets/Error", {"status": status, "message": message})
    response.status_code = status
    return response

"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from main.views import home
from apps.budgets.api import views as budget

from apps.admin_panel.api.admin_views import dashboard
from apps.admin_panel.api.auth_views import login_view, logout_view
from apps.admin_panel.api.group_views import (
    group_create,
    group_delete,
    group_edit,
    group_list,
)
from apps.admin_panel.api.user_views import (
    user_create,
    user_delete,
    user_edit,
    user_list,
)

handler403 = 'main.errors.budget_forbidden'
handler404 = 'main.errors.budget_not_found'

urlpatterns = [
    path("", home, name="home"),
    path("budgets/", budget.index, name="budget_index"),
    path("budgets/sign-in/", login_view, {"budget": True}, name="budget_login"),
    path("budgets/mine/", budget.client, name="budget_client"),
    path("budgets/review/", budget.manager, name="budget_manager"),
    path("budgets/admin/", budget.admin, name="budget_admin"),
    path("budgets/create/", budget.create, name="budget_create"),
    path("budgets/<int:request_id>/edit/", budget.update, name="budget_update"),
    path("budgets/<int:request_id>/withdraw/", budget.withdraw, name="budget_withdraw"),
    path("budgets/<int:request_id>/review/", budget.review, name="budget_review"),
    path("budgets/<int:request_id>/delete/", budget.delete, name="budget_delete"),
    path("django-admin/", admin.site.urls),
    # Inertia-powered admin
    path("admin/login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("admin/", dashboard, name="admin_dashboard"),
    path("admin/users/", user_list, name="admin_users"),
    path("admin/users/create/", user_create, name="admin_user_create"),
    path("admin/users/<int:user_id>/edit/", user_edit, name="admin_user_edit"),
    path("admin/users/<int:user_id>/delete/", user_delete, name="admin_user_delete"),
    path("admin/groups/", group_list, name="admin_groups"),
    path("admin/groups/create/", group_create, name="admin_group_create"),
    path("admin/groups/<int:group_id>/edit/", group_edit, name="admin_group_edit"),
    path("admin/groups/<int:group_id>/delete/", group_delete, name="admin_group_delete"),
]

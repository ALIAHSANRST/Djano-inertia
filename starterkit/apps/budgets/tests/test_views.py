from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..domain.models import BudgetRequest, BudgetRole

User = get_user_model()
INERTIA = {"HTTP_X_INERTIA": "true"}


class BudgetViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.requester = User.objects.create_user("requester", password="demo-login-password")
        cls.other = User.objects.create_user("other")
        cls.manager = User.objects.create_user("manager")
        cls.admin = User.objects.create_superuser("root")
        BudgetRole.objects.create(user=cls.manager, role=BudgetRole.Role.MANAGER)

    def setUp(self):
        cache.clear()

    def test_budget_login_allows_non_staff_and_dispatches_by_role(self):
        response = self.client.get(reverse("budget_client"), **INERTIA)
        self.assertRedirects(response, f"{reverse('budget_login')}?next={reverse('budget_client')}",
                             fetch_redirect_response=False)
        response = self.client.post(reverse("budget_login"), {
            "username": "requester", "password": "demo-login-password",
        }, **INERTIA)
        self.assertRedirects(response, reverse("budget_index"), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse("budget_index")), reverse("budget_client"),
                             fetch_redirect_response=False)

    def test_budget_navigation_is_shared_across_admin_pages(self):
        self.client.force_login(self.admin)
        for route in ("admin_dashboard", "budget_admin"):
            response = self.client.get(reverse(route), **INERTIA)
            overview = [item["route"] for item in response.json()["props"]["admin_nav"]
                        if item["section"] == "Overview"]
            self.assertEqual(overview, ["admin_dashboard", "budget_admin"])

        staff = User.objects.create_user("staff-client", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("admin_dashboard"), **INERTIA)
        self.assertNotIn("budget_admin", [item["route"] for item in response.json()["props"]["admin_nav"]])


    def test_superuser_can_assign_manager_on_create_and_admin_on_edit(self):
        self.client.force_login(self.admin)
        create_url = reverse("admin_user_create")
        props = self.client.get(create_url, **INERTIA).json()["props"]
        self.assertEqual([choice["value"] for choice in props["budget_role_choices"]],
                         ["CLIENT", "MANAGER", "ADMIN"])
        fields = {
            "username": "role-picker-user", "password": "demo-password-9471",
            "is_active": True, "budget_role": "MANAGER",
        }
        response = self.client.post(create_url, fields, content_type="application/json", **INERTIA)
        manager = User.objects.get(username=fields["username"])
        edit_url = reverse("admin_user_edit", args=[manager.pk])
        self.assertRedirects(response, edit_url, fetch_redirect_response=False)
        self.assertEqual(manager.budget_profile.role, "MANAGER")
        self.assertEqual(self.client.get(edit_url, **INERTIA).json()["props"]["form"]["budget_role"], "MANAGER")

        fields.update(password="", budget_role="ADMIN")
        response = self.client.post(edit_url, fields, content_type="application/json", **INERTIA)
        self.assertRedirects(response, edit_url, fetch_redirect_response=False)
        self.assertEqual(BudgetRole.objects.get(user=manager).role, "ADMIN")

    def test_role_picker_rejects_invalid_choices_and_delegated_assignments(self):
        from django.contrib.auth.models import Permission

        create_url = reverse("admin_user_create")
        fields = {
            "username": "invalid-role-user", "password": "demo-password-9471",
            "is_active": True, "budget_role": "UNKNOWN",
        }
        self.client.force_login(self.admin)
        response = self.client.post(create_url, fields, content_type="application/json", **INERTIA)
        self.assertEqual(response.json()["props"]["errors"]["budget_role"], ["Select a valid budget role."])
        self.assertFalse(User.objects.filter(username=fields["username"]).exists())

        delegate = User.objects.create_user("delegate", is_staff=True)
        delegate.user_permissions.add(Permission.objects.get(codename="add_user", content_type__app_label="auth"))
        self.client.force_login(delegate)
        props = self.client.get(create_url, **INERTIA).json()["props"]
        self.assertEqual(props["budget_role_choices"], [])
        fields["budget_role"] = "MANAGER"
        response = self.client.post(create_url, fields, content_type="application/json", **INERTIA)
        self.assertIn("Only superusers", response.json()["props"]["errors"]["budget_role"][0])
        self.assertFalse(User.objects.filter(username=fields["username"]).exists())

    def test_wrong_role_inertia_navigation_and_post_return_403(self):
        self.client.force_login(self.requester)
        for route in ("budget_manager", "budget_admin"):
            response = self.client.get(reverse(route), **INERTIA)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["component"], "Budgets/Error")
        response = self.client.post(reverse("budget_delete", args=[1]), **INERTIA)
        self.assertEqual(response.status_code, 403)

    def test_json_mutations_require_csrf_and_keep_client_rows_private(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.requester)
        url = reverse("budget_create")
        data = {"title": "Equipment", "amount": "12.34", "justification": "Replace worn equipment"}
        self.assertEqual(browser.post(url, data, content_type="application/json", **INERTIA).status_code, 403)
        page = browser.get(reverse("budget_client"), **INERTIA)
        token = page.cookies["csrftoken"].value
        response = browser.post(url, data, content_type="application/json", HTTP_X_CSRFTOKEN=token, **INERTIA)
        self.assertRedirects(response, reverse("budget_client"), fetch_redirect_response=False)
        self.assertEqual(BudgetRequest.objects.get().requester, self.requester)
        browser.force_login(self.other)
        response = browser.get(reverse("budget_client"), **INERTIA)
        self.assertEqual(response.json()["props"]["requests"]["items"], [])

    def test_review_redirect_shares_field_error_then_success_updates_history_and_totals(self):
        row = BudgetRequest.objects.create(requester=self.requester, title="Equipment", amount="12.34",
                                           justification="Replace worn equipment")
        url = reverse("budget_review", args=[row.pk])
        self.client.force_login(self.manager)
        response = self.client.post(url, {"status": "REJECTED", "feedback": "", "revision": 0},
                                    content_type="application/json", follow=True, **INERTIA)
        self.assertIn("feedback", response.json()["props"]["errors"])
        self.assertEqual(len(response.json()["props"]["queue"]["items"]), 1)
        response = self.client.post(url, {"status": "APPROVED", "feedback": "Budgeted", "revision": 0},
                                    content_type="application/json", follow=True, **INERTIA)
        props = response.json()["props"]
        self.assertEqual(props["errors"], {})
        self.assertEqual(props["queue"]["items"], [])
        self.assertEqual(props["history"]["items"][0]["feedback"], "Budgeted")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("budget_admin"), **INERTIA)
        self.assertEqual(response.json()["props"]["totals"], {"pending": "0.00", "approved": "12.34"})

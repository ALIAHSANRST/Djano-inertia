from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from ..domain.models import BudgetRequest, BudgetRole
from ..domain.policies import Role, role_for
from ..dto.requests import BudgetInput, ReviewInput
from ..selectors.requests import funding_totals, request_list
from ..services import workflow

User = get_user_model()


class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_user = User.objects.create_user("requester")
        cls.other = User.objects.create_user("other")
        cls.manager = User.objects.create_user("manager")
        cls.admin = User.objects.create_user("budget-admin")
        BudgetRole.objects.create(user=cls.manager, role=Role.MANAGER)
        BudgetRole.objects.create(user=cls.admin, role=Role.ADMIN)

    def submit(self, actor=None, amount="0.10"):
        actor = actor or self.client_user
        result = workflow.create(actor=actor, data=BudgetInput("Equipment", amount, "Replace worn equipment"))
        self.assertFalse(result.errors)
        return BudgetRequest.objects.filter(requester=actor).first()

    def test_staff_and_budget_roles_are_independent(self):
        self.other.is_staff = True
        self.assertEqual(role_for(self.other), Role.CLIENT)
        self.assertEqual(role_for(self.manager), Role.MANAGER)
        self.assertEqual(role_for(self.admin), Role.ADMIN)
        self.admin.is_active = False
        self.assertIsNone(role_for(self.admin))

    def test_only_owned_pending_requests_can_be_changed(self):
        row = self.submit()
        fields = BudgetInput("Updated", "0.20", "Updated reason", row.revision)
        self.assertTrue(workflow.update(actor=self.other, request_id=row.pk, data=fields).errors)
        self.assertFalse(workflow.update(actor=self.client_user, request_id=row.pk, data=fields).errors)
        stale = workflow.review(actor=self.manager, request_id=row.pk,
                                data=ReviewInput("APPROVED", "", row.revision))
        self.assertTrue(stale.errors)
        row.refresh_from_db()
        self.assertEqual(row.amount, Decimal("0.20"))
        self.assertEqual(row.status, BudgetRequest.Status.PENDING)

    def test_decision_requires_valid_feedback_and_is_final(self):
        row = self.submit()
        blank = workflow.review(actor=self.manager, request_id=row.pk,
                                data=ReviewInput("REJECTED", "  ", row.revision))
        self.assertIn("feedback", blank.errors)
        rejected = workflow.review(actor=self.manager, request_id=row.pk,
                                   data=ReviewInput("REJECTED", "Duplicate request", row.revision))
        self.assertFalse(rejected.errors)
        row.refresh_from_db()
        self.assertEqual(row.reviewer, self.manager)
        self.assertEqual(row.feedback, "Duplicate request")
        self.assertTrue(workflow.review(actor=self.manager, request_id=row.pk,
                                       data=ReviewInput("APPROVED", "", row.revision)).errors)
        self.assertTrue(workflow.withdraw(actor=self.client_user, request_id=row.pk, revision=row.revision).errors)
        self.assertTrue(workflow.update(actor=self.client_user, request_id=row.pk,
                                       data=BudgetInput("New", "50", "Reason", row.revision)).errors)

    def test_selectors_scope_rows_and_total_exact_cents(self):
        first = self.submit(amount="0.10")
        second = self.submit(self.other, "0.20")
        withdrawn = self.submit(amount="1000.00")
        self.assertFalse(workflow.withdraw(
            actor=self.client_user, request_id=withdrawn.pk, revision=withdrawn.revision,
        ).errors)
        self.assertEqual(set(request_list(self.client_user)), {first, withdrawn})
        self.assertEqual(funding_totals(), {"pending": Decimal("0.30"), "approved": Decimal("0.00")})
        workflow.review(actor=self.manager, request_id=second.pk,
                        data=ReviewInput("APPROVED", "", second.revision))
        self.assertEqual(funding_totals(), {"pending": Decimal("0.10"), "approved": Decimal("0.20")})

    def test_only_budget_admin_can_permanently_delete(self):
        row = self.submit()
        for actor in (self.client_user, self.manager):
            with self.assertRaises(PermissionDenied):
                workflow.delete(actor=actor, request_id=row.pk)
        with self.assertRaises(PermissionDenied):
            workflow.review(actor=self.admin, request_id=row.pk, data=ReviewInput("APPROVED", "", row.revision))
        self.assertFalse(workflow.delete(actor=self.admin, request_id=row.pk).errors)
        self.assertFalse(BudgetRequest.objects.filter(pk=row.pk).exists())

    def test_invalid_amounts_and_blank_fields(self):
        for amount in ("0", "-1", "NaN", "1.111", "10000000000.00"):
            with self.subTest(amount=amount):
                result = workflow.create(actor=self.client_user, data=BudgetInput(" ", amount, " "))
                self.assertCountEqual(result.errors, ["title", "amount", "justification"])
        self.assertFalse(BudgetRequest.objects.exists())

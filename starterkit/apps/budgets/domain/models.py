from django.conf import settings
from django.db import models
from django.db.models import Q


class BudgetRole(models.Model):
    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        MANAGER = "MANAGER", "Manager"
        ADMIN = "ADMIN", "Admin"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="budget_profile")
    role = models.CharField(max_length=7, choices=Role.choices)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(role__in=["CLIENT", "MANAGER", "ADMIN"]),
                                   name="budget_valid_role"),
        ]


class BudgetRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    title = models.CharField(max_length=160)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    justification = models.TextField(max_length=4000)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                  related_name="budget_requests")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                 related_name="budget_reviews", null=True, blank=True)
    feedback = models.TextField(max_length=2000, blank=True)
    revision = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["status", "withdrawn_at"], name="budget_queue_idx")]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="budget_positive_amount"),
            models.CheckConstraint(
                condition=(
                    Q(status="PENDING", reviewer__isnull=True, decided_at__isnull=True, feedback="")
                    | (
                        Q(reviewer__isnull=False, decided_at__isnull=False, withdrawn_at__isnull=True)
                        & (Q(status="APPROVED") | (Q(status="REJECTED") & ~Q(feedback="")))
                    )
                ),
                name="budget_valid_lifecycle",
            ),
        ]

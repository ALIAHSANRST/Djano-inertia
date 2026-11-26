from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from ...domain.models import BudgetRole
from ...selectors.requests import set_role


class Command(BaseCommand):
    help = "Assign a budget workflow role to an existing user."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("role", type=str.upper, choices=BudgetRole.Role.values)

    def handle(self, *args, **options):
        user_model = get_user_model()
        try:
            user = user_model._default_manager.get_by_natural_key(options["username"])
        except user_model.DoesNotExist as error:
            raise CommandError("User does not exist.") from error
        if user.is_superuser and options["role"] != BudgetRole.Role.ADMIN:
            raise CommandError("Django superusers always have the budget Admin role.")
        set_role(user, options["role"])
        self.stdout.write(self.style.SUCCESS(f"{user.get_username()} is now {options['role']}."))

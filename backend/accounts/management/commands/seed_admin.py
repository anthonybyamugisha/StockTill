import os

from django.core.management.base import BaseCommand

from accounts.infrastructure.models import UserModel


class Command(BaseCommand):
    help = "Create or update the admin user from environment variables."

    def handle(self, *args: object, **options: object) -> None:
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@stocktill.com")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            self.stderr.write("DJANGO_SUPERUSER_PASSWORD not set; skipping admin seed.")
            return

        user, created = UserModel.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.role = "admin"
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.must_change_password = False
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} admin user {email}")

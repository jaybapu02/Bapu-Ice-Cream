import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Seed initial data and ensure admin user exists"

    def handle(self, *args, **options):
        User = get_user_model()
        admin_user = os.environ.get("ADMIN_USERNAME", "bapuIcecream")
        admin_pass = os.environ.get("ADMIN_PASSWORD", "icecream123")
        admin_email = os.environ.get("ADMIN_EMAIL_USER", "admin@bapuicecream.com")

        if not User.objects.filter(username=admin_user).exists():
            User.objects.create_superuser(
                username=admin_user,
                email=admin_email,
                password=admin_pass,
            )
            self.stdout.write(self.style.SUCCESS(f"Admin user '{admin_user}' created"))
        else:
            self.stdout.write(f"Admin user '{admin_user}' already exists")

        from home.models import Category
        if not Category.objects.exists():
            call_command("loaddata", "initial_data")
            self.stdout.write(self.style.SUCCESS("Seeded initial product & category data"))
        else:
            self.stdout.write("Category data already exists, skipping seed")

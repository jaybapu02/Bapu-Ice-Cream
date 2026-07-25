from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Seed initial product/category data if database is empty"

    def handle(self, *args, **options):
        from home.models import Category
        if Category.objects.exists():
            self.stdout.write("Data already exists, skipping seed")
            return
        call_command("loaddata", "initial_data")
        self.stdout.write(self.style.SUCCESS("Seeded initial product & category data"))

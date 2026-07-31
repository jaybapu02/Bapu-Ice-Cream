from django.db import migrations
from decimal import Decimal


def seed_catering_packages(apps, schema_editor):
    CateringPackage = apps.get_model("home", "CateringPackage")

    packages = [
        {
            "name": "Basic",
            "slug": "basic",
            "short_description": "Ice Cream Tub Service — 3 classic flavours for small gatherings.",
            "icon": "🍦",
            "price_per_guest": Decimal("99.00"),
            "minimum_guests": 20,
            "gst_percent": Decimal("5.00"),
            "additional_charges": Decimal("0.00"),
            "features": [
                "Ice Cream Tub Service",
                "3 Classic Flavours",
                "Disposable Cups & Spoons",
            ],
            "is_active": True,
            "sort_order": 1,
        },
        {
            "name": "Standard",
            "slug": "standard",
            "short_description": "A build-your-own sundae bar with 6 flavours and all the toppings.",
            "icon": "🍨",
            "price_per_guest": Decimal("149.00"),
            "minimum_guests": 20,
            "gst_percent": Decimal("5.00"),
            "additional_charges": Decimal("0.00"),
            "features": [
                "Ice Cream + Toppings Bar",
                "6 Flavours",
                "Premium Serving",
            ],
            "is_active": True,
            "sort_order": 2,
        },
        {
            "name": "Premium",
            "slug": "premium",
            "short_description": "Complete dessert catering with 10+ flavours and custom setup.",
            "icon": "🧁",
            "price_per_guest": Decimal("249.00"),
            "minimum_guests": 30,
            "gst_percent": Decimal("5.00"),
            "additional_charges": Decimal("0.00"),
            "features": [
                "Full Dessert Catering",
                "10+ Flavours",
                "Custom Decor & Setup",
            ],
            "is_active": True,
            "sort_order": 3,
        },
        {
            "name": "Custom",
            "slug": "custom",
            "short_description": "Fully customized for your event. We'll design the perfect menu.",
            "icon": "✨",
            "price_per_guest": Decimal("0.00"),
            "minimum_guests": 20,
            "gst_percent": Decimal("5.00"),
            "additional_charges": Decimal("0.00"),
            "features": [
                "Fully Customizable",
                "Any Flavour Combinations",
                "Dedicated Coordinator",
            ],
            "is_active": True,
            "sort_order": 4,
        },
    ]

    for data in packages:
        CateringPackage.objects.get_or_create(slug=data["slug"], defaults=data)


def reverse_seed(apps, schema_editor):
    CateringPackage = apps.get_model("home", "CateringPackage")
    CateringPackage.objects.filter(
        slug__in=["basic", "standard", "premium", "custom"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0012_cateringpackage"),
    ]

    operations = [
        migrations.RunPython(seed_catering_packages, reverse_seed),
    ]

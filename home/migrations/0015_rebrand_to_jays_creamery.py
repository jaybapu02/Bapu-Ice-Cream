from django.db import migrations

OLD_NAMES = ["Bapu Ice Cream", "Bapu Ice-Cream"]
NEW_NAME = "Jay's Creamery"


def rebrand(apps, schema_editor):
    Service = apps.get_model("home", "Service")
    ServiceCategory = apps.get_model("home", "ServiceCategory")
    CateringPackage = apps.get_model("home", "CateringPackage")
    Product = apps.get_model("home", "Product")

    text_fields = [
        (Service, ["full_description", "short_description", "title"]),
        (ServiceCategory, ["description", "name"]),
        (CateringPackage, ["short_description", "description", "name"]),
        (Product, ["description", "name"]),
    ]

    for model, fields in text_fields:
        for obj in model.objects.all():
            changed = False
            for field in fields:
                value = getattr(obj, field, None)
                if not value:
                    continue
                new_value = value
                for old in OLD_NAMES:
                    new_value = new_value.replace(old, NEW_NAME)
                if new_value != value:
                    setattr(obj, field, new_value)
                    changed = True
            if changed:
                obj.save(update_fields=fields)


def reverse_rebrand(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0014_alter_cateringenquiry_catering_package"),
    ]

    operations = [
        migrations.RunPython(rebrand, reverse_rebrand),
    ]

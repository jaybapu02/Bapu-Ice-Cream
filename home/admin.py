import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import Contact, CateringEnquiry, Order, OrderItem

def export_as_csv(modeladmin, request, queryset):
    """
    Generic export to CSV action.
    """
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name}.csv'
    writer = csv.writer(response)
    
    field_names = [field.name for field in opts.fields]
    # Write header
    writer.writerow(field_names)
    # Write rows
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response

export_as_csv.short_description = "Export Selected Items in CSV"

# ---------- Inline Order Items ----------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0   # no empty rows

# ---------- Order Admin ----------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_id",
        "name",
        "phone",
        "total_price",
        "payment_mode",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_mode", "created_at")
    search_fields = ("order_id", "name", "phone")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    actions = [export_as_csv]

# ---------- OrderItem Admin ----------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "flavour", "quantity", "price")
    list_filter = ("flavour", "created_at")
    search_fields = ("flavour",)

# ---------- Other Models ----------
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name", "email", "phone")
    date_hierarchy = "created_at"
    actions = [export_as_csv]

@admin.register(CateringEnquiry)
class CateringEnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "event_type", "event_date", "created_at")
    search_fields = ("name", "phone", "event_type")
    date_hierarchy = "created_at"
    actions = [export_as_csv]
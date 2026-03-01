from django.contrib import admin
from .models import Contact, CateringEnquiry, Order, OrderItem

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
    inlines = [OrderItemInline]

# ---------- OrderItem Admin ----------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "flavour", "quantity", "price")
    list_filter = ("flavour",)
    search_fields = ("flavour",)

# ---------- Other Models ----------
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name", "email", "phone")

@admin.register(CateringEnquiry)
class CateringEnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "event_type", "event_date", "created_at")
    search_fields = ("name", "phone", "event_type")
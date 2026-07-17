import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import (
    Contact, CateringEnquiry, Order, OrderItem,
    Product, Category, Review, Newsletter, Wishlist
)
from .cadmin import custom_admin_site


def export_as_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name}.csv'
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields]
    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response


export_as_csv.short_description = "Export Selected Items as CSV"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Category, site=custom_admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product, site=custom_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available', 'is_featured', 'created_at']
    list_filter = ['category', 'is_available', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'is_available', 'is_featured']
    actions = [export_as_csv]


@admin.register(Review, site=custom_admin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['name', 'comment']


@admin.register(Newsletter, site=custom_admin_site)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['email']
    actions = [export_as_csv]


@admin.register(Wishlist, site=custom_admin_site)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__username', 'product__name']


@admin.register(Order, site=custom_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_id', 'name', 'phone', 'total_price',
        'payment_mode', 'status', 'created_at'
    ]
    list_filter = ['status', 'payment_mode', 'created_at']
    search_fields = ['order_id', 'name', 'phone']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    actions = [export_as_csv]
    readonly_fields = ['order_id', 'created_at', 'updated_at']


@admin.register(OrderItem, site=custom_admin_site)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'flavour', 'quantity', 'price']
    list_filter = ['flavour', 'created_at']
    search_fields = ['flavour', 'order__order_id']


@admin.register(Contact, site=custom_admin_site)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    search_fields = ['name', 'email', 'phone']
    date_hierarchy = 'created_at'
    actions = [export_as_csv]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CateringEnquiry, site=custom_admin_site)
class CateringEnquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'event_type', 'event_date', 'created_at']
    search_fields = ['name', 'phone', 'event_type']
    date_hierarchy = 'created_at'
    actions = [export_as_csv]

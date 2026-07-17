from datetime import timedelta
from decimal import Decimal

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import Order, Product, Category, Contact, CateringEnquiry, Review, Newsletter, Wishlist


class CustomAdminSite(AdminSite):
    site_header = "Bapu Ice Cream Admin"
    site_title = "Bapu Ice Cream Admin Portal"
    index_title = "Welcome to Bapu Ice Cream Admin"

    def get_dashboard_stats(self):
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)

        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status="PENDING").count()
        paid_orders = Order.objects.filter(status="PAID").count()
        cancelled_orders = Order.objects.filter(status="CANCELLED").count()

        revenue_data = Order.objects.filter(status="PAID").aggregate(
            total=Sum("total_price")
        )
        total_revenue = revenue_data["total"] or Decimal("0.00")

        recent_orders = (
            Order.objects.select_related("user")
            .prefetch_related("items")
            .order_by("-created_at")[:10]
        )

        low_stock_products = Product.objects.filter(
            Q(stock__lt=5) & Q(stock__gt=0)
        ).count()
        out_of_stock = Product.objects.filter(stock=0, is_available=True).count()

        orders_30d = Order.objects.filter(created_at__gte=thirty_days_ago).count()
        revenue_30d = (
            Order.objects.filter(
                status="PAID", created_at__gte=thirty_days_ago
            ).aggregate(total=Sum("total_price"))["total"]
            or Decimal("0.00")
        )

        total_products = Product.objects.count()
        featured_products = Product.objects.filter(is_featured=True).count()
        available_products = Product.objects.filter(is_available=True).count()

        recent_reviews = Review.objects.select_related("product", "user").order_by(
            "-created_at"
        )[:10]

        total_customers = (
            User.objects.filter(
                id__in=Order.objects.values_list("user_id", flat=True).distinct()
            ).count()
            if Order.objects.exists()
            else 0
        )

        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "paid_orders": paid_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": total_revenue,
            "recent_orders": recent_orders,
            "low_stock_products": low_stock_products,
            "out_of_stock": out_of_stock,
            "orders_30d": orders_30d,
            "revenue_30d": revenue_30d,
            "total_products": total_products,
            "featured_products": featured_products,
            "available_products": available_products,
            "total_categories": Category.objects.count(),
            "total_contacts": Contact.objects.count(),
            "total_catering": CateringEnquiry.objects.count(),
            "total_reviews": Review.objects.count(),
            "recent_reviews": recent_reviews,
            "total_wishlists": Wishlist.objects.count(),
            "total_subscribers": Newsletter.objects.filter(is_active=True).count(),
            "total_users": User.objects.count(),
            "total_customers": total_customers,
        }

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(self.get_dashboard_stats())
        return super().index(request, extra_context)


custom_admin_site = CustomAdminSite(name="admin")

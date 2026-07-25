import logging
from datetime import timedelta
from decimal import Decimal

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.utils import timezone

from .models import Order, Product, Category, Contact, CateringEnquiry, Review, Newsletter, Wishlist

logger = logging.getLogger(__name__)


class CustomAdminSite(AdminSite):
    site_header = "Bapu Ice Cream Admin"
    site_title = "Bapu Ice Cream Admin Portal"
    index_title = "Welcome to Bapu Ice Cream Admin"

    def get_dashboard_stats(self):
        ctx = {}
        try:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            ctx["total_orders"] = Order.objects.count()
            ctx["pending_orders"] = Order.objects.filter(status="PENDING").count()
            ctx["cancelled_orders"] = Order.objects.filter(status="CANCELLED").count()
            ctx["total_products"] = Product.objects.count()
            ctx["featured_products"] = Product.objects.filter(is_featured=True).count()
            ctx["available_products"] = Product.objects.filter(is_available=True).count()
            ctx["total_categories"] = Category.objects.count()
            ctx["total_users"] = User.objects.count()
        except Exception as e:
            logger.warning(f"Admin dashboard stats error: {e}")
        return ctx

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(self.get_dashboard_stats())
        return super().index(request, extra_context)


custom_admin_site = CustomAdminSite(name="admin")

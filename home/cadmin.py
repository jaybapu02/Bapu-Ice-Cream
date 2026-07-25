import logging
from datetime import timedelta
from decimal import Decimal

from django.contrib.admin import AdminSite
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.http import HttpResponse
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
            import time as t2
            s0 = t2.time()
            ctx["total_orders"] = Order.objects.count()
            s1 = t2.time()
            ctx["pending_orders"] = Order.objects.filter(status="PENDING").count()
            s2 = t2.time()
            ctx["cancelled_orders"] = Order.objects.filter(status="CANCELLED").count()
            s3 = t2.time()
            ctx["total_products"] = Product.objects.count()
            s4 = t2.time()
            ctx["featured_products"] = Product.objects.filter(is_featured=True).count()
            s5 = t2.time()
            ctx["available_products"] = Product.objects.filter(is_available=True).count()
            s6 = t2.time()
            ctx["total_categories"] = Category.objects.count()
            s7 = t2.time()
            ctx["total_users"] = User.objects.count()
            s8 = t2.time()
            logger.info(f"ADMIN_STATS: orders={s1-s0:.3f}s pending={s2-s1:.3f}s cancelled={s3-s2:.3f}s products={s4-s3:.3f}s featured={s5-s4:.3f}s avail={s6-s5:.3f}s cats={s7-s6:.3f}s users={s8-s7:.3f}s TOTAL={s8-s0:.3f}s")
        except Exception as e:
            logger.warning(f"Admin dashboard stats error: {e}")
        return ctx

    def index(self, request, extra_context=None):
        import time as timer
        t0 = timer.time()
        logger.info(f"ADMIN_INDEX: called by user={request.user} is_auth={request.user.is_authenticated} is_staff={request.user.is_staff}")

        extra_context = extra_context or {}
        t1 = timer.time()
        extra_context.update(self.get_dashboard_stats())
        t2 = timer.time()
        logger.info(f"ADMIN_INDEX: get_dashboard_stats took {t2-t1:.3f}s, ctx keys={list(extra_context.keys())}")

        try:
            result = super().index(request, extra_context)
            t3 = timer.time()
            logger.info(f"ADMIN_INDEX: super().index took {t3-t2:.3f}s, total={t3-t0:.3f}s, status={result.status_code if hasattr(result, 'status_code') else 'N/A'}")
            return result
        except Exception as e:
            logger.exception(f"ADMIN_INDEX: super().index raised {type(e).__name__}: {e}")
            raise


@staff_member_required
def admin_ping(request):
    return HttpResponse(f"admin_ping OK user={request.user}")

@staff_member_required
def admin_jazzmin_test(request):
    from django.shortcuts import render
    return render(request, "admin/index.html", {"title": "Test"})

custom_admin_site = CustomAdminSite(name="admin")

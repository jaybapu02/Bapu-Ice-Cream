from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from .models import Order, Product, Category, Contact, CateringEnquiry, Review, Newsletter, Wishlist


class CustomAdminSite(AdminSite):
    site_header = "Bapu Ice Cream Admin"
    site_title = "Bapu Ice Cream Admin Portal"
    index_title = "Welcome to Bapu Ice Cream Admin"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(status='PENDING').count(),
            'paid_orders': Order.objects.filter(status='PAID').count(),
            'total_products': Product.objects.count(),
            'total_categories': Category.objects.count(),
            'total_contacts': Contact.objects.count(),
            'total_catering': CateringEnquiry.objects.count(),
            'total_reviews': Review.objects.count(),
            'total_wishlists': Wishlist.objects.count(),
            'total_subscribers': Newsletter.objects.count(),
            'total_users': User.objects.count(),
        })
        return super().index(request, extra_context)


custom_admin_site = CustomAdminSite(name='admin')

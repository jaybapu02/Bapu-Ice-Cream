import logging
import razorpay
from django.conf import settings
from django.contrib import messages
from django.db import transaction, IntegrityError, DatabaseError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.views import View
from django.views.generic import TemplateView, FormView, DetailView, ListView
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django_ratelimit.decorators import ratelimit

from .models import Order, OrderItem, Product, Category, Review, Newsletter, Wishlist
from .forms import (
    ContactForm, CateringEnquiryForm, OrderCustomerForm,
    ReviewForm, NewsletterForm, RegisterForm
)
from .exceptions import OrderProcessingError

logger = logging.getLogger('home.views')


class LandingView(TemplateView):
    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(
            is_available=True, is_featured=True
        )[:6]
        return context


class HomeView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Product.objects.filter(is_available=True).select_related('category')
        category_slug = self.request.GET.get('category')
        search_q = self.request.GET.get('q')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search_q:
            qs = qs.filter(name__icontains=search_q)
        context['all_products'] = qs
        context['categories'] = Category.objects.all()
        context['selected_category'] = category_slug or ''
        context['search_query'] = search_q or ''
        return context


class AboutView(TemplateView):
    template_name = "about.html"


class ServicesView(TemplateView):
    template_name = "services.html"


class ProductsView(ListView):
    model = Product
    template_name = "products.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_available=True)
        category_slug = self.request.GET.get('category')
        search_q = self.request.GET.get('q')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search_q:
            qs = qs.filter(name__icontains=search_q)
        return qs.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['reviews'] = product.reviews.all()[:10]
        context['review_form'] = ReviewForm()
        context['related_products'] = Product.objects.filter(
            category=product.category, is_available=True
        ).exclude(id=product.id)[:4]
        return context


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class ContactView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def form_valid(self, form):
        try:
            form.save()
            messages.success(self.request, "Your message has been sent successfully!")
            logger.info(f"New contact submission from {form.cleaned_data['email']}")
        except DatabaseError as e:
            logger.error(f"Database error while saving contact: {e}")
            messages.error(self.request, "A database error occurred. Please try again later.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class CateringView(FormView):
    template_name = "catering.html"
    form_class = CateringEnquiryForm
    success_url = reverse_lazy("catering")

    def form_valid(self, form):
        try:
            enquiry = form.save()

            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "message": "Thank you! Your catering enquiry has been submitted. We'll contact you within 30 minutes.",
                })

            messages.success(
                self.request,
                "Thank you! Your catering enquiry has been submitted. We'll contact you within 30 minutes.",
            )

            logger.info(
                f"New catering enquiry #{enquiry.id} from {enquiry.name} ({enquiry.phone})"
            )

            self._send_notifications(enquiry)

        except DatabaseError as e:
            logger.error(f"Database error saving catering enquiry: {e}")
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "success": False,
                    "message": "A database error occurred. Please try again later.",
                }, status=500)
            messages.error(self.request, "A database error occurred. Please try again later.")

        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": False,
                "errors": form.errors,
            }, status=400)
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def _send_notifications(self, enquiry):
        """Send confirmation email to customer + notification to admin."""
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            subject = f"Catering Enquiry Confirmation — {enquiry.name}"
            customer_message = (
                f"Dear {enquiry.name},\n\n"
                f"Thank you for your catering enquiry with Bapu Ice Cream!\n\n"
                f"Event: {enquiry.get_event_type_display()}\n"
                f"Date: {enquiry.event_date or 'To be decided'}\n"
                f"Venue: {enquiry.venue or 'To be decided'}\n"
                f"Guests: {enquiry.guests or 'To be decided'}\n"
                f"Package: {enquiry.get_catering_package_display()}\n\n"
                f"We will review your requirements and contact you at {enquiry.phone} "
                f"within 30 minutes during business hours (10 AM – 10 PM).\n\n"
                f"If you have any urgent requests, please call us at +91 9692244008.\n\n"
                f"Warm regards,\nBapu Ice-Cream Team"
            )

            if enquiry.email:
                send_mail(
                    subject,
                    customer_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [enquiry.email],
                    fail_silently=True,
                )

            admin_subject = f"[Admin] New Catering Enquiry from {enquiry.name}"
            admin_message = (
                f"New catering enquiry received:\n\n"
                f"Name: {enquiry.name}\n"
                f"Phone: {enquiry.phone}\n"
                f"Email: {enquiry.email or 'N/A'}\n"
                f"Event: {enquiry.get_event_type_display()}\n"
                f"Date: {enquiry.event_date or 'N/A'}\n"
                f"Venue: {enquiry.venue or 'N/A'}\n"
                f"Guests: {enquiry.guests or 'N/A'}\n"
                f"Package: {enquiry.get_catering_package_display()}\n"
                f"Budget: ₹{enquiry.budget or 'N/A'}\n"
                f"Special Requirements: {enquiry.special_requirements or 'N/A'}\n"
                f"Message: {enquiry.message or 'N/A'}\n\n"
                f"View in admin: /admin/home/cateringenquiry/{enquiry.id}/change/"
            )

            if hasattr(settings, "ADMIN_EMAIL") and settings.ADMIN_EMAIL:
                send_mail(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=True,
                )

        except Exception as e:
            logger.warning(f"Failed to send catering notification emails: {e}")


class OrderView(View):
    template_name = "order.html"

    def get(self, request):
        return render(request, self.template_name, {
            "selected_flavour": request.GET.get("flavour", ""),
            "selected_type": request.GET.get("type", "")
        })

    def post(self, request):
        form = OrderCustomerForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid details. Check phone number and retry.")
            return render(request, self.template_name, {"form": form})

        request.session["customer"] = form.cleaned_data
        action = request.POST.get("action", "direct_checkout")

        if action == "add_to_cart":
            cart = request.session.get("cart", [])
            cart.append({
                "type": request.POST.get("ice_cream_type"),
                "flavour": request.POST.get("flavour"),
                "size": request.POST.get("size"),
                "toppings": request.POST.get("toppings", ""),
                "quantity": int(request.POST.get("quantity", 1)),
                "total": float(request.POST.get("total_price", 0)),
            })
            request.session["cart"] = cart
            messages.success(request, "Added to cart successfully!")
            return redirect("cart")
        else:
            try:
                request.session["checkout_item"] = {
                    "type": request.POST.get("ice_cream_type"),
                    "flavour": request.POST.get("flavour"),
                    "size": request.POST.get("size"),
                    "toppings": request.POST.get("toppings", ""),
                    "quantity": int(request.POST.get("quantity", 1)),
                    "total": float(request.POST.get("total_price", 0)),
                }
                return redirect("payment")
            except (ValueError, TypeError):
                messages.error(request, "Invalid quantities or price. Please try again.")
                return redirect("order")


class CartView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get("cart", [])
        context['cart'] = cart
        context['grand_total'] = sum(item["total"] for item in cart)
        return context


class AddToCartView(View):
    def post(self, request):
        try:
            cart = request.session.get("cart", [])
            cart.append({
                "type": request.POST.get("ice_cream_type"),
                "flavour": request.POST.get("flavour"),
                "size": request.POST.get("size"),
                "toppings": request.POST.get("toppings", ""),
                "quantity": int(request.POST.get("quantity", 1)),
                "total": float(request.POST.get("total_price", 0)),
            })
            request.session["cart"] = cart
            messages.success(request, "Added to cart successfully!")
            logger.info("Item added to cart.")
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            messages.error(request, "Could not add item to cart.")
        return redirect("cart")


class RemoveFromCartView(View):
    def get(self, request, index):
        cart = request.session.get("cart", [])
        if 0 <= index < len(cart):
            cart.pop(index)
            request.session["cart"] = cart
            messages.success(request, "Item removed from cart.")
        return redirect("cart")


class PaymentPageView(View):
    def get(self, request):
        customer = request.session.get("customer")
        checkout_item = request.session.get("checkout_item")
        cart = request.session.get("cart", [])

        if checkout_item:
            amount = float(checkout_item["total"])
            items = [checkout_item]
        elif cart:
            amount = sum(float(item["total"]) for item in cart)
            items = cart
        else:
            messages.warning(request, "No items to checkout.")
            return redirect("order")

        try:
            client = razorpay.Client(auth=(
                settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET
            ))
            razorpay_order = client.order.create({
                "amount": int(amount * 100),
                "currency": "INR",
                "payment_capture": 1
            })
            request.session["razorpay_order_id"] = razorpay_order["id"]

            return render(request, "payment.html", {
                "items": items,
                "grand_total": amount,
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": razorpay_order["id"],
                "amount": int(amount * 100),
                "customer": customer
            })
        except Exception as e:
            logger.error(f"Razorpay Order Creation Failed: {e}")
            messages.error(request, "Payment gateway initialization failed. Try again later.")
            return redirect("order")


class PaymentSuccessView(View):
    def get(self, request):
        customer = request.session.get("customer")
        if not customer:
            messages.error(request, "Session expired. Please contact support.")
            return redirect("order")

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_id="ICE" + get_random_string(6).upper(),
                    user=request.user if request.user.is_authenticated else None,
                    name=customer["name"],
                    phone=customer["phone"],
                    address=customer["address"],
                    delivery_type=customer["delivery_type"],
                    payment_mode=customer["payment_mode"],
                    status="PAID",
                    total_price=0
                )

                total = 0
                is_direct = "checkout_item" in request.session
                raw_items = (
                    [request.session["checkout_item"]]
                    if is_direct
                    else request.session.get("cart", [])
                )

                if not raw_items:
                    raise OrderProcessingError("Cart is empty during checkout.")

                for item in raw_items:
                    OrderItem.objects.create(
                        order=order,
                        ice_cream_type=item.get("type", ""),
                        flavour=item.get("flavour", ""),
                        size=item.get("size", ""),
                        toppings=item.get("toppings", ""),
                        quantity=item.get("quantity", 1),
                        price=item.get("total", 0),
                    )
                    total += float(item.get("total", 0))

                Order.objects.filter(id=order.id).update(total_price=total)

                request.session.pop("checkout_item", None)
                request.session.pop("customer", None)
                request.session.pop("razorpay_order_id", None)
                if not is_direct:
                    request.session["cart"] = []

                logger.info(f"Order {order.order_id} successfully saved.")
                order.refresh_from_db()
                return render(request, "payment_success.html", {"order": order})

        except (IntegrityError, DatabaseError) as e:
            logger.critical(f"Database error saving order: {e}", exc_info=True)
            messages.error(request, "Payment was successful but order creation failed.")
            return redirect("order")
        except OrderProcessingError as e:
            logger.error(f"Order Processing Error: {e}")
            messages.error(request, str(e))
            return redirect("order")
        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            messages.error(request, "An unexpected error occurred. Please contact support.")
            return redirect("order")


@method_decorator(csrf_exempt, name='dispatch')
class RazorpaySuccessWebhookView(View):
    def post(self, request):
        try:
            logger.info("Webhook received from Razorpay.")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return HttpResponse(status=400)


class NewsletterSubscribeView(View):
    def post(self, request):
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscribed to newsletter successfully!")
        else:
            for error in form.errors.get('email', []):
                messages.error(request, error)
        return redirect(request.META.get('HTTP_REFERER', 'home'))


class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Your review has been posted!")
        else:
            messages.error(request, "Please correct the errors in your review.")
        return redirect('product_detail', slug=product.slug)


class WishlistToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product)
        if wishlist_item.exists():
            wishlist_item.delete()
            messages.info(request, "Removed from wishlist.")
        else:
            Wishlist.objects.create(user=request.user, product=product)
            messages.success(request, "Added to wishlist!")
        return redirect(request.META.get('HTTP_REFERER', 'product_detail'))


class WishlistView(LoginRequiredMixin, ListView):
    model = Wishlist
    template_name = "wishlist.html"
    context_object_name = "wishlist_items"

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')


class OrderTrackView(View):
    def get(self, request):
        order_id = request.GET.get("order_id", "")
        order = None
        if order_id:
            try:
                order = Order.objects.prefetch_related('items').get(order_id=order_id.upper())
            except Order.DoesNotExist:
                messages.error(request, "Order not found. Please check your order ID.")
        return render(request, "order_track.html", {"order": order, "order_id": order_id})

    def post(self, request):
        order_id = request.POST.get("order_id", "").upper().strip()
        if not order_id:
            messages.error(request, "Please enter an order ID.")
            return redirect("order_track")
        return redirect(f"{reverse_lazy('order_track')}?order_id={order_id}")


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect('landing')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return render(request, 'profile.html', {
        'orders': orders,
        'wishlist_count': wishlist_count,
    })

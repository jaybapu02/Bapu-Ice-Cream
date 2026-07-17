import json
import logging
from decimal import Decimal

import razorpay
from django.conf import settings
from django.contrib import messages
from django.db import transaction, IntegrityError, DatabaseError
from django.db.models import Q, Count
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
        qs = Product.objects.filter(is_available=True).select_related('category').prefetch_related('images')
        category_slug = self.request.GET.get('category')
        search_q = self.request.GET.get('q')
        sort = self.request.GET.get('sort', '')

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search_q:
            qs = qs.filter(name__icontains=search_q)

        if sort == 'price_low':
            qs = qs.order_by('price', 'name')
        elif sort == 'price_high':
            qs = qs.order_by('-price', 'name')
        elif sort == 'newest':
            qs = qs.order_by('-created_at', 'name')
        elif sort == 'rating':
            qs = qs.order_by('-rating', 'name')
        elif sort == 'name':
            qs = qs.order_by('name')
        else:
            qs = qs.order_by('-is_featured', '-is_best_seller', '-is_new_arrival', 'name')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_available=True))
        )
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        context['featured_products'] = Product.objects.filter(
            is_available=True, is_featured=True
        ).select_related('category')[:4]
        context['best_sellers'] = Product.objects.filter(
            is_available=True, is_best_seller=True
        ).select_related('category')[:4]
        context['new_arrivals'] = Product.objects.filter(
            is_available=True, is_new_arrival=True
        ).select_related('category')[:4]
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['reviews'] = product.reviews.select_related('user').all()[:10]
        context['review_form'] = ReviewForm()
        context['gallery_images'] = product.images.filter(is_primary=False).all()[:5]
        context['related_products'] = Product.objects.filter(
            category=product.category, is_available=True
        ).exclude(id=product.id).select_related('category')[:4]
        context['recommended_products'] = Product.objects.filter(
            is_available=True, is_featured=True
        ).exclude(id=product.id).select_related('category')[:4]
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


PRICE_TABLE = {
    "Scooped Ice Cream": 120,
    "Softy Cone": 80,
    "Family Pack": 350,
}
SIZE_PRICES = {
    "Single Scoop": 0,
    "Double Scoop": 40,
    "500 ml": 150,
    "1 Liter": 280,
}
TOPPING_PRICES = {
    "No Toppings": 0,
    "Choco Chips": 30,
    "Nuts": 40,
    "Caramel Syrup": 25,
}
DELIVERY_CHARGE = 30
FREE_DELIVERY_ABOVE = 200
TAX_RATE = Decimal("0.05")


def _calc_item_price(ice_cream_type, size, toppings, quantity):
    base = PRICE_TABLE.get(ice_cream_type, 100)
    size_extra = SIZE_PRICES.get(size, 0)
    topping_extra = TOPPING_PRICES.get(toppings, 0)
    unit = Decimal(str(base + size_extra + topping_extra))
    return unit, unit * int(quantity or 1)


def _get_cart_data(request):
    cart = request.session.get("cart", [])
    subtotal = sum(Decimal(str(item["total"])) for item in cart)
    delivery = Decimal("0") if subtotal >= FREE_DELIVERY_ABOVE else Decimal(str(DELIVERY_CHARGE))
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
    grand = subtotal + tax + delivery
    return {
        "cart": cart,
        "subtotal": subtotal,
        "tax": tax,
        "delivery_charge": delivery,
        "grand_total": grand,
        "free_delivery": FREE_DELIVERY_ABOVE,
    }


def _send_order_notifications(order):
    try:
        from django.core.mail import send_mail
        from django.conf import settings

        items_summary = "\n".join(
            f"  - {item.quantity}x {item.flavour} ({item.size}) — ₹{item.price}"
            for item in order.items.all()
        )

        subject = f"Order Confirmed — {order.order_id}"
        customer_msg = (
            f"Dear {order.name},\n\n"
            f"Your order has been placed successfully!\n\n"
            f"Order ID: {order.order_id}\n"
            f"Status: {order.get_status_display()}\n"
            f"Items:\n{items_summary}\n"
            f"Subtotal: ₹{order.subtotal}\n"
            f"Tax: ₹{order.tax}\n"
            f"Delivery: ₹{order.delivery_charge}\n"
            f"Total: ₹{order.total_price}\n\n"
            f"Delivery: {order.delivery_type}\n"
            f"Address: {order.address}\n\n"
            f"Track your order: {settings.BASE_DIR}/order/track/?order_id={order.order_id}\n\n"
            f"Thank you for choosing Bapu Ice Cream!\n"
            f"— Bapu Ice-Cream Team"
        )

        if order.email:
            send_mail(subject, customer_msg, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)

        if hasattr(settings, "ADMIN_EMAIL") and settings.ADMIN_EMAIL:
            admin_subject = f"[Admin] New Order {order.order_id} — ₹{order.total_price}"
            admin_msg = (
                f"New order received:\n\n"
                f"Order: {order.order_id}\n"
                f"Customer: {order.name}\n"
                f"Phone: {order.phone}\n"
                f"Email: {order.email or 'N/A'}\n"
                f"Payment: {order.payment_mode}\n"
                f"Total: ₹{order.total_price}\n"
                f"Items:\n{items_summary}\n"
                f"View: /admin/home/order/{order.id}/change/"
            )
            send_mail(admin_subject, admin_msg, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL], fail_silently=True)

    except Exception as e:
        logger.warning(f"Failed to send order notification: {e}")


# ──────────────────────────────────────────────
# AJAX Cart API
# ──────────────────────────────────────────────

class CartAPIView(View):
    """Generic AJAX cart endpoint — add, update, remove, get"""

    def post(self, request):
        action = request.POST.get("action", "")
        cart = request.session.get("cart", [])

        try:
            if action == "add":
                ice_cream_type = request.POST.get("ice_cream_type", "Scooped Ice Cream")
                flavour = request.POST.get("flavour", "Vanilla Classic")
                size = request.POST.get("size", "Single Scoop")
                toppings = request.POST.get("toppings", "No Toppings")
                quantity = int(request.POST.get("quantity", 1))

                unit_price, total = _calc_item_price(ice_cream_type, size, toppings, quantity)
                cart.append({
                    "type": ice_cream_type,
                    "flavour": flavour,
                    "size": size,
                    "toppings": toppings,
                    "quantity": quantity,
                    "unit_price": float(unit_price),
                    "total": float(total),
                })
                msg = f"Added {flavour} to cart!"

            elif action == "update":
                index = int(request.POST.get("index", -1))
                quantity = int(request.POST.get("quantity", 1))
                if 0 <= index < len(cart):
                    item = cart[index]
                    _, new_total = _calc_item_price(
                        item["type"], item["size"], item["toppings"], quantity
                    )
                    cart[index]["quantity"] = quantity
                    cart[index]["total"] = float(new_total)
                    msg = "Cart updated."
                else:
                    return JsonResponse({"success": False, "message": "Invalid item."}, status=400)

            elif action == "remove":
                index = int(request.POST.get("index", -1))
                if 0 <= index < len(cart):
                    removed = cart.pop(index)
                    msg = f"Removed {removed['flavour']} from cart."
                else:
                    return JsonResponse({"success": False, "message": "Invalid item."}, status=400)

            elif action == "clear":
                cart = []
                msg = "Cart cleared."

            elif action == "list":
                data = _get_cart_data(request)
                data["success"] = True
                data["cart_count"] = len(cart)
                return JsonResponse(data)

            else:
                return JsonResponse({"success": False, "message": "Unknown action."}, status=400)

            request.session["cart"] = cart
            data = _get_cart_data(request)
            data["success"] = True
            data["message"] = msg
            data["cart_count"] = len(cart)
            return JsonResponse(data)

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Cart API error: {e}")
            return JsonResponse({"success": False, "message": "Invalid request."}, status=400)


# ──────────────────────────────────────────────
# Order / Checkout Page
# ──────────────────────────────────────────────

class OrderView(View):
    template_name = "order.html"

    def get(self, request):
        flavour_options = [
            "Mango Magic", "Vanilla Classic", "Chocolate Delight", "Strawberry Bliss",
            "Butterscotch Crunch", "Kesar Pista Royal", "Black Currant Twist",
            "Dry Fruit Special", "Cookies & Cream", "Tender Coconut Fresh",
            "Coffee Mocha", "Rainbow Fantasy",
        ]
        return render(request, self.template_name, {
            "selected_flavour": request.GET.get("flavour", ""),
            "selected_type": request.GET.get("type", ""),
            "flavour_options": flavour_options,
            "prices": PRICE_TABLE,
            "prices_json": json.dumps(PRICE_TABLE),
            "size_prices": SIZE_PRICES,
            "size_prices_json": json.dumps(SIZE_PRICES),
            "topping_prices": TOPPING_PRICES,
            "topping_prices_json": json.dumps(TOPPING_PRICES),
            "delivery_charge": DELIVERY_CHARGE,
            "free_delivery_above": FREE_DELIVERY_ABOVE,
            "tax_rate": float(TAX_RATE * 100),
        })


# ──────────────────────────────────────────────
# Cart Page
# ──────────────────────────────────────────────

class CartView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_get_cart_data(self.request))
        context["delivery_charge"] = DELIVERY_CHARGE
        context["free_delivery_above"] = FREE_DELIVERY_ABOVE
        return context


# ──────────────────────────────────────────────
# Legacy cart endpoints (redirect-based)
# ──────────────────────────────────────────────

class AddToCartView(View):
    def post(self, request):
        try:
            cart = request.session.get("cart", [])
            ice_cream_type = request.POST.get("ice_cream_type", "Scooped Ice Cream")
            flavour = request.POST.get("flavour", "Vanilla Classic")
            size = request.POST.get("size", "Single Scoop")
            toppings = request.POST.get("toppings", "No Toppings")
            quantity = int(request.POST.get("quantity", 1))
            _, total = _calc_item_price(ice_cream_type, size, toppings, quantity)
            cart.append({
                "type": ice_cream_type,
                "flavour": flavour,
                "size": size,
                "toppings": toppings,
                "quantity": quantity,
                "total": float(total),
            })
            request.session["cart"] = cart
            messages.success(request, "Added to cart successfully!")
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


# ──────────────────────────────────────────────
# Checkout & Payment
# ──────────────────────────────────────────────

class CheckoutView(View):
    """Collect customer details and redirect to payment"""
    template_name = "checkout.html"

    def get(self, request):
        cart_data = _get_cart_data(request)
        if not cart_data["cart"]:
            messages.warning(request, "Your cart is empty.")
            return redirect("order")
        form = OrderCustomerForm()
        return render(request, self.template_name, {
            "form": form,
            **cart_data,
            "delivery_charge": DELIVERY_CHARGE,
            "free_delivery_above": FREE_DELIVERY_ABOVE,
        })

    def post(self, request):
        cart_data = _get_cart_data(request)
        if not cart_data["cart"]:
            messages.warning(request, "Your cart is empty.")
            return redirect("order")

        form = OrderCustomerForm(request.POST)
        if not form.is_valid():
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                first_error = next(iter(form.errors.values()))[0]
                return JsonResponse({"success": False, "message": first_error, "errors": form.errors}, status=400)
            return render(request, self.template_name, {"form": form, **cart_data})

        customer = form.cleaned_data
        request.session["customer"] = customer

        payment_mode = customer["payment_mode"]

        if payment_mode == "cod":
            return self._place_order(request, customer, cart_data, payment_mode="cod")
        else:
            return self._init_razorpay(request, customer, cart_data)

    def _place_order(self, request, customer, cart_data, payment_mode, razorpay_id=""):
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_id="ICE" + get_random_string(8).upper(),
                    user=request.user if request.user.is_authenticated else None,
                    name=customer["name"],
                    email=customer.get("email", ""),
                    phone=customer["phone"],
                    address=customer["address"],
                    delivery_type=customer["delivery_type"],
                    payment_mode=payment_mode,
                    subtotal=cart_data["subtotal"],
                    tax=cart_data["tax"],
                    delivery_charge=cart_data["delivery_charge"],
                    total_price=cart_data["grand_total"],
                    special_instructions=customer.get("special_instructions", ""),
                    status="CONFIRMED" if payment_mode == "cod" else "PENDING",
                    razorpay_order_id=razorpay_id,
                )

                for item in cart_data["cart"]:
                    OrderItem.objects.create(
                        order=order,
                        ice_cream_type=item["type"],
                        flavour=item["flavour"],
                        size=item["size"],
                        toppings=item.get("toppings", ""),
                        quantity=item["quantity"],
                        unit_price=item.get("unit_price", 0),
                        price=item["total"],
                    )

                request.session["cart"] = []
                request.session.pop("customer", None)

                logger.info(f"Order {order.order_id} created ({payment_mode})")
                _send_order_notifications(order)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True, "order_id": order.order_id, "payment_mode": payment_mode})
            return render(request, "payment_success.html", {"order": order})

        except (IntegrityError, DatabaseError) as e:
            logger.critical(f"Order creation DB error: {e}", exc_info=True)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": "Database error. Please try again."}, status=500)
            messages.error(request, "An error occurred. Please try again.")
            return redirect("cart")

    def _init_razorpay(self, request, customer, cart_data):
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount_paise = int(cart_data["grand_total"] * Decimal("100"))
            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1,
            })
            request.session["razorpay_order_id"] = razorpay_order["id"]
            request.session["razorpay_amount"] = amount_paise

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "razorpay_key": settings.RAZORPAY_KEY_ID,
                    "razorpay_order_id": razorpay_order["id"],
                    "amount": amount_paise,
                    "customer": customer,
                    "payment_mode": "razorpay",
                })

            return render(request, "payment.html", {
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": razorpay_order["id"],
                "amount": amount_paise,
                "grand_total": float(cart_data["grand_total"]),
                "customer": customer,
                "items": cart_data["cart"],
            })

        except Exception as e:
            logger.error(f"Razorpay init failed: {e}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": "Payment gateway error. Try COD."}, status=500)
            messages.error(request, "Payment gateway failed. Please try again.")
            return redirect("checkout")


class RazorpayCallbackView(View):
    """Called after successful Razorpay payment (POST) or direct success page (GET)"""

    def get(self, request):
        order_id = request.GET.get("order_id", "")
        if order_id:
            try:
                order = Order.objects.prefetch_related("items").get(order_id=order_id)
                return render(request, "payment_success.html", {"order": order})
            except Order.DoesNotExist:
                pass
        messages.success(request, "Payment completed successfully!")
        return redirect("order_track")

    def post(self, request):
        customer = request.session.get("customer")
        razorpay_order_id = request.session.get("razorpay_order_id")

        if not customer:
            return JsonResponse({"success": False, "message": "Session expired."}, status=400)

        payment_id = request.POST.get("razorpay_payment_id", "")
        signature = request.POST.get("razorpay_signature", "")

        if razorpay_order_id:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            }
            try:
                client.utility.verify_payment_signature(params_dict)
            except Exception as e:
                logger.error(f"Razorpay signature verification failed: {e}")
                return JsonResponse({"success": False, "message": "Payment verification failed."}, status=400)

        cart_data = _get_cart_data(request)
        if not cart_data["cart"]:
            return JsonResponse({"success": False, "message": "Cart empty."}, status=400)

        checkout = CheckoutView()
        response = checkout._place_order(
            request, customer, cart_data,
            payment_mode="razorpay",
            razorpay_id=razorpay_order_id or "",
        )

        request.session.pop("razorpay_order_id", None)
        request.session.pop("razorpay_amount", None)
        return response


class OrderTrackView(View):
    def get(self, request):
        order_id = request.GET.get("order_id", "")
        order = None
        if order_id:
            try:
                order = Order.objects.prefetch_related("items").get(order_id=order_id.upper())
            except Order.DoesNotExist:
                messages.error(request, "Order not found. Please check your order ID.")
        return render(request, "order_track.html", {"order": order, "order_id": order_id})

    def post(self, request):
        order_id = request.POST.get("order_id", "").upper().strip()
        if not order_id:
            messages.error(request, "Please enter an order ID.")
            return redirect("order_track")
        return redirect(f"{reverse_lazy('order_track')}?order_id={order_id}")


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


@method_decorator(csrf_exempt, name="dispatch")
class RazorpaySuccessWebhookView(View):
    def post(self, request):
        try:
            logger.info("Webhook received from Razorpay.")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return HttpResponse(status=400)


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

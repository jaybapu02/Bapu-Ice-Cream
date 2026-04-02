import logging
import razorpay
from django.conf import settings
from django.contrib import messages
from django.db import transaction, IntegrityError, DatabaseError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.crypto import get_random_string
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Order

from .models import Order, OrderItem
from .forms import ContactForm, CateringEnquiryForm, OrderCustomerForm
from .exceptions import OrderProcessingError, PaymentFailedError

logger = logging.getLogger('home.views')

# ------------------ BASIC PAGES (CBV) ------------------

@method_decorator(cache_page(60 * 15), name='dispatch')
class IndexView(TemplateView):
    template_name = "index.html"

class AboutView(TemplateView):
    template_name = "about.html"

class ServicesView(TemplateView):
    template_name = "services.html"

@method_decorator(cache_page(60 * 15), name='dispatch')
class ProductsView(TemplateView):
    template_name = "products.html"


# ------------------ FORMS (CBV) ------------------

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


@method_decorator(ratelimit(key='ip', rate='3/m', block=True), name='dispatch')
class CateringView(FormView):
    template_name = "catering.html"
    form_class = CateringEnquiryForm
    success_url = reverse_lazy('catering')

    def form_valid(self, form):
        try:
            form.save()
            messages.success(self.request, "🎉 Thank you! We will contact you shortly.")
            logger.info(f"New catering enquiry from {form.cleaned_data['phone']}")
        except DatabaseError as e:
            logger.error(f"Database error saving catering enquiry: {e}")
            messages.error(self.request, "An error occurred submitting your enquiry.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid details submitted. Please check your form.")
        return super().form_invalid(form)


# ------------------ ORDER & CART ------------------

class OrderView(View):
    def get(self, request):
        return render(request, "order.html", {
            "selected_flavour": request.GET.get("flavour", ""),
            "selected_type": request.GET.get("type", "")
        })

    def post(self, request):
        form = OrderCustomerForm(request.POST)
        if form.is_valid():
            request.session["customer"] = form.cleaned_data
            messages.info(request, "Proceed to payment to complete your order.")
            return redirect("payment")
        else:
            messages.error(request, "Invalid details. Check phone number and retry.")
            return render(request, "order.html", {"form": form})


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
            messages.success(request, "🍦 Added to cart successfully!")
            logger.info("Item added to cart.")
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            messages.error(request, "Could not add item to cart.")
        return redirect("cart")


class CartView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get("cart", [])
        context['cart'] = cart
        context['grand_total'] = sum(item["total"] for item in cart)
        return context


class RemoveFromCartView(View):
    def get(self, request, index):
        cart = request.session.get("cart", [])
        if 0 <= index < len(cart):
            cart.pop(index)
            request.session["cart"] = cart
            messages.success(request, "Item removed from cart.")
        return redirect("cart")


class DirectCheckoutView(View):
    def post(self, request):
        form = OrderCustomerForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid user details provided.")
            return redirect("order")

        request.session["customer"] = form.cleaned_data
        
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
        except ValueError:
            messages.error(request, "Invalid quantities or price. Please try again.")
            return redirect("order")


# ------------------ PAYMENT ------------------

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
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                "amount": int(amount * 100),  # paise
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


# ------------------ PAYMENT SUCCESS (SAVE TO DB) ------------------

class PaymentSuccessView(View):
    def get(self, request):
        customer = request.session.get("customer")
        if not customer:
            logger.warning("Payment success accessed without customer session.")
            messages.error(request, "Session expired. If payment was deducted, please contact support.")
            return redirect("order")

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_id="ICE" + get_random_string(6).upper(),
                    name=customer["name"],
                    phone=customer["phone"],
                    address=customer["address"],
                    delivery_type=customer["delivery_type"],
                    payment_mode=customer["payment_mode"],
                    status="PAID",
                    total_price=0
                )

                total = 0
                is_direct_checkout = "checkout_item" in request.session

                if is_direct_checkout:
                    item = request.session["checkout_item"]
                    raw_items = [item]
                else:
                    raw_items = request.session.get("cart", [])

                if not raw_items:
                    raise OrderProcessingError("Cart is empty during checkout save.")

                for item in raw_items:
                    OrderItem.objects.create(
                        order=order,
                        ice_cream_type=item["type"],
                        flavour=item["flavour"],
                        size=item["size"],
                        toppings=item["toppings"],
                        quantity=item["quantity"],
                        price=item["total"],
                    )
                    total += float(item["total"])
                
                # Server side calculation vs validation
                order.total_price = total
                order.save()

                # Clean session
                if is_direct_checkout:
                    request.session.pop("checkout_item")
                else:
                    request.session["cart"] = []
                
                request.session.pop("customer", None)
                request.session.pop("razorpay_order_id", None)
                
                logger.info(f"Order {order.order_id} successfully saved.")

                # If N+1 was possible in views, we'd use select_related here, but we just pass order.
                # Example usage of prefetch_related if needed elsewhere:
                # order_with_items = Order.objects.prefetch_related('items').get(id=order.id)

                return render(request, "payment_success.html", {"order": order})

        except (IntegrityError, DatabaseError) as db_err:
            logger.critical(f"Database error saving order after payment: {db_err}", exc_info=True)
            messages.error(request, "Payment was successful but order creation failed. Refund will be processed.")
            return redirect("order")
        except OrderProcessingError as e:
            logger.error(f"Order Processing Error: {e}")
            messages.error(request, str(e))
            return redirect("order")
        except Exception as e:
            logger.critical(f"Unexpected error in payment success: {e}", exc_info=True)
            messages.error(request, "An unexpected error occurred. Please contact support.")
            return redirect("order")


@method_decorator(csrf_exempt, name='dispatch')
class RazorpaySuccessWebhookView(View):
    def post(self, request):
        # We can implement signature validation here using Razorpay SDK Utility
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            # e.g. client.utility.verify_webhook_signature(...)
            logger.info("Webhook hit.")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Webhook signature mismatch: {e}")
            return HttpResponse(status=400)

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('index')

    return render(request, 'register.html')
@login_required
def order(request):
    return render(request, 'order.html')
@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'profile.html', {'orders': orders})
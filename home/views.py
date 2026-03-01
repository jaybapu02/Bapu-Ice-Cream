from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from django.utils.crypto import get_random_string
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Contact, CateringEnquiry, Order, OrderItem


# ------------------ BASIC PAGES ------------------

def index(request):
    return render(request, "index.html")
def about(request):
    return render(request, "about.html")
def services(request):
    return render(request, "services.html")
def products(request):
    return render(request, "products.html")


# ------------------ CONTACT ------------------

def contact(request):
    if request.method == "POST":
        Contact.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            message=request.POST.get("desc"),
        )
        messages.success(request, "Your message has been sent successfully!")
    return render(request, "contact.html")


# ------------------ CATERING ------------------

def catering(request):
    if request.method == "POST":
        CateringEnquiry.objects.create(
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            event_type=request.POST.get("event_type"),
            event_date=request.POST.get("event_date") or None,
            guests=request.POST.get("guests") or None,
            message=request.POST.get("message"),
        )
        messages.success(request, "🎉 Thank you! We will contact you shortly.")
        return redirect("catering")

    return render(request, "catering.html")


# ------------------ ORDER PAGE ------------------

def order_now(request):
    # GET → open order page with preselected values
    if request.method == "GET":
        return render(request, "order.html", {
            "selected_flavour": request.GET.get("flavour", ""),
            "selected_type": request.GET.get("type", "")
        })

    # POST → store customer info ONLY (no DB save)
    if request.method == "POST":
        request.session["customer"] = {
            "name": request.POST.get("name"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "delivery_type": request.POST.get("delivery_type"),
            "payment_mode": request.POST.get("payment_mode"),
        }

        messages.info(request, "Proceed to payment to complete your order.")
        return redirect("payment")


# ------------------ CART ------------------

def add_to_cart(request):
    if request.method == "POST":
        cart = request.session.get("cart", [])

        cart.append({
            "type": request.POST.get("ice_cream_type"),
            "flavour": request.POST.get("flavour"),
            "size": request.POST.get("size"),
            "toppings": request.POST.get("toppings"),
            "quantity": int(request.POST.get("quantity")),
            "total": int(request.POST.get("total_price")),
        })

        request.session["cart"] = cart
        messages.success(request, "🍦 Added to cart successfully!")

    return redirect("cart")


def cart_view(request):
    cart = request.session.get("cart", [])
    return render(request, "cart.html", {
        "cart": cart,
        "grand_total": sum(item["total"] for item in cart)
    })


def remove_from_cart(request, index):
    cart = request.session.get("cart", [])
    if index < len(cart):
        cart.pop(index)
        request.session["cart"] = cart
    return redirect("cart")


# ------------------ DIRECT CHECKOUT (BUY NOW) ------------------

def direct_checkout(request):
    if request.method == "POST":

        # ✅ store customer info
        request.session["customer"] = {
            "name": request.POST.get("name"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "delivery_type": request.POST.get("delivery_type"),
            "payment_mode": request.POST.get("payment_mode"),
        }

        # ✅ store checkout item
        request.session["checkout_item"] = {
            "type": request.POST.get("ice_cream_type"),
            "flavour": request.POST.get("flavour"),
            "size": request.POST.get("size"),
            "toppings": request.POST.get("toppings"),
            "quantity": int(request.POST.get("quantity")),
            "total": int(request.POST.get("total_price")),
        }

        return redirect("payment")

# ------------------ PAYMENT ------------------

def payment_page(request):
    customer = request.session.get("customer")
    checkout_item = request.session.get("checkout_item")
    cart = request.session.get("cart", [])

    if checkout_item:
        amount = checkout_item["total"]
        items = [checkout_item]
    elif cart:
        amount = sum(item["total"] for item in cart)
        items = cart
    else:
        return redirect("order")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create({
        "amount": amount * 100,  # paise
        "currency": "INR",
        "payment_capture": 1
    })

    request.session["razorpay_order_id"] = razorpay_order["id"]

    return render(request, "payment.html", {
        "items": items,
        "grand_total": amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": razorpay_order["id"],
        "amount": amount * 100,
        "customer": customer
    })


# ------------------ PAYMENT SUCCESS (SAVE TO DB) ------------------

def payment_success(request):
    customer = request.session.get("customer")

    if not customer:
        return redirect("order")

    order = Order.objects.create(
        order_id="ICE" + get_random_string(6).upper(),
        name=customer["name"],
        phone=customer["phone"],
        address=customer["address"],
        delivery_type=customer["delivery_type"],
        payment_mode=customer["payment_mode"],
        total_price=0,
        status="PAID"
    )

    total = 0

    # Direct checkout
    if "checkout_item" in request.session:
        item = request.session["checkout_item"]

        OrderItem.objects.create(
            order=order,
            ice_cream_type=item["type"],
            flavour=item["flavour"],
            size=item["size"],
            toppings=item["toppings"],
            quantity=item["quantity"],
            price=item["total"],
        )

        total = item["total"]
        request.session.pop("checkout_item")

    # Cart checkout
    else:
        cart = request.session.get("cart", [])
        for item in cart:
            OrderItem.objects.create(
                order=order,
                ice_cream_type=item["type"],
                flavour=item["flavour"],
                size=item["size"],
                toppings=item["toppings"],
                quantity=item["quantity"],
                price=item["total"],
            )
            total += item["total"]

        request.session["cart"] = []

    order.total_price = total
    order.save()

    request.session.pop("customer")

    return render(request, "payment_success.html")

@csrf_exempt
def razorpay_success(request):
    if request.method == "POST":
        # OPTIONAL: Signature verification (advanced)
        return HttpResponse(status=200)
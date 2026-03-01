from django.contrib import admin
from django.urls import path
from home import views
urlpatterns = [
    path("",views.index,name="home"),
    path("about/",views.about,name="about"),
    path("services",views.services,name="services"),
    path("contact",views.contact,name="contact"),
    path("catering",views.catering,name="catering"),
    path("order/", views.order_now, name="order"),
    path("cart/", views.cart_view, name="cart"),
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("remove/<int:index>/", views.remove_from_cart, name="remove_from_cart"),
    path("products/", views.products, name="products"),
    path("payment/", views.payment_page, name="payment"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("direct-checkout/", views.direct_checkout, name="direct_checkout"),
    path("razorpay-success/", views.razorpay_success, name="razorpay_success"),
]
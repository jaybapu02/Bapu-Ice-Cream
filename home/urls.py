from django.urls import path
from home import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("services/", views.ServicesView.as_view(), name="services"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("catering/", views.CateringView.as_view(), name="catering"),
    path("order/", views.OrderView.as_view(), name="order"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/add/", views.AddToCartView.as_view(), name="add_to_cart"),
    path("cart/remove/<int:index>/", views.RemoveFromCartView.as_view(), name="remove_from_cart"),
    path("products/", views.ProductsView.as_view(), name="products"),
    path("checkout/direct/", views.DirectCheckoutView.as_view(), name="direct_checkout"),
    path("payment/", views.PaymentPageView.as_view(), name="payment"),
    path("payment/success/", views.PaymentSuccessView.as_view(), name="payment_success"),
    path("payment/webhook/", views.RazorpaySuccessWebhookView.as_view(), name="razorpay_success"),
]
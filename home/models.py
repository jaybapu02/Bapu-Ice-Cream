from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.conf import settings
from decimal import Decimal

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    image = models.ImageField(upload_to='products/', blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3, decimal_places=1, default=Decimal('0.0'),
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('5.0'))]
    )
    ingredients = models.TextField(blank=True, help_text="List of ingredients")
    flavours = models.JSONField(default=list, blank=True, help_text="Available flavours as JSON array")
    sizes = models.JSONField(default=list, blank=True, help_text="Available sizes as JSON array")
    toppings = models.JSONField(default=list, blank=True, help_text="Available toppings as JSON array")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
            models.Index(fields=['is_available']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_best_seller']),
            models.Index(fields=['is_new_arrival']),
        ]

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(validators=[phone_regex], max_length=17)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        indexes = [models.Index(fields=['-created_at'])]

    def __str__(self):
        return f"{self.name} - {self.email}"


class CateringEnquiry(models.Model):
    PACKAGE_CHOICES = [
        ("basic", "Basic — Ice Cream Tub Service"),
        ("standard", "Standard — Ice Cream + Toppings Bar"),
        ("premium", "Premium — Full Dessert Catering"),
        ("custom", "Custom — Tailored Package"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(blank=True, help_text="We'll send a confirmation to this email")
    event_type = models.CharField(max_length=50, choices=[
        ("birthday", "Birthday Party"),
        ("wedding", "Wedding / Reception"),
        ("corporate", "Corporate Event"),
        ("college", "College Fest"),
        ("family", "Family Gathering"),
        ("other", "Other"),
    ], default="other")
    event_date = models.DateField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True, help_text="Where will the event be held?")
    guests = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )
    catering_package = models.CharField(
        max_length=20, choices=PACKAGE_CHOICES, default="basic"
    )
    budget = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Approximate budget in INR"
    )
    special_requirements = models.TextField(blank=True, help_text="Dietary restrictions, allergies, preferred flavours, etc.")
    message = models.TextField(blank=True)
    reference_image = models.ImageField(
        upload_to="catering_references/", blank=True,
        help_text="Optional: upload a reference image or mood board"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catering Enquiry"
        verbose_name_plural = "Catering Enquiries"
        indexes = [
            models.Index(fields=["event_date"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_event_type_display()} on {self.event_date}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("PREPARING", "Preparing"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="orders"
    )
    order_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, help_text="Confirmation will be sent here")
    phone = models.CharField(validators=[phone_regex], max_length=17)
    address = models.TextField()
    delivery_type = models.CharField(max_length=20)
    payment_mode = models.CharField(max_length=20)
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    tax = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    delivery_charge = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    special_instructions = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return f"Order {self.order_id} — {self.name} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="order_items"
    )
    ice_cream_type = models.CharField(max_length=50)
    flavour = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    toppings = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["flavour"]),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.flavour} ({self.ice_cream_type}) — {self.order.order_id}"


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.product.name} ({self.rating}★)"


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wishlist'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

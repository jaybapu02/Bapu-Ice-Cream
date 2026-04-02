from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from decimal import Decimal

phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

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
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.email}"

class CateringEnquiry(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(validators=[phone_regex], max_length=17)
    event_type = models.CharField(max_length=50)
    event_date = models.DateField(null=True, blank=True)
    guests = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catering Enquiry"
        verbose_name_plural = "Catering Enquiries"
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.event_type} on {self.event_date}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    order_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(validators=[phone_regex], max_length=17)
    address = models.TextField()
    delivery_type = models.CharField(max_length=20)
    payment_mode = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['phone']),
        ]

    def get_order_total(self):
        # Calculate sum of related order items
        total = sum(item.price for item in self.items.all())
        return total

    def __str__(self):
        return f"Order {self.order_id} - {self.name} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    ice_cream_type = models.CharField(max_length=50)
    flavour = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    toppings = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['flavour']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.flavour} ({self.ice_cream_type}) for {self.order.order_id}"

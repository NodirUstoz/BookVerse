"""
Order models: Order, OrderItem.
Complete order lifecycle management.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from shortuuid import ShortUUID


def generate_order_number():
    """Generate a unique order number like BV-A3X9K2M1."""
    su = ShortUUID(alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f"BV-{su.random(length=8)}"


class Order(models.Model):
    """Customer order."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(
        max_length=20,
        unique=True,
        default=generate_order_number,
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="stripe"
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_code = models.CharField(max_length=50, blank=True)

    # Shipping address
    shipping_first_name = models.CharField(max_length=150)
    shipping_last_name = models.CharField(max_length=150)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20, blank=True)
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default="US")

    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_carrier = models.CharField(max_length=50, blank=True)
    estimated_delivery = models.DateField(blank=True, null=True)

    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def calculate_totals(self):
        """Recalculate order totals from items."""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.tax_amount = self.subtotal * Decimal("0.08")  # 8% tax
        self.total = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        self.save(update_fields=["subtotal", "tax_amount", "total"])

    def confirm(self):
        self.status = "confirmed"
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_at"])

    def ship(self, tracking_number="", carrier=""):
        self.status = "shipped"
        self.tracking_number = tracking_number
        self.tracking_carrier = carrier
        self.shipped_at = timezone.now()
        self.save(
            update_fields=["status", "tracking_number", "tracking_carrier", "shipped_at"]
        )

    def deliver(self):
        self.status = "delivered"
        self.delivered_at = timezone.now()
        self.save(update_fields=["status", "delivered_at"])

    def cancel(self):
        self.status = "cancelled"
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at"])
        # Restore stock
        for item in self.items.all():
            item.book.stock_quantity += item.quantity
            item.book.save(update_fields=["stock_quantity"])

    @property
    def item_count(self):
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    @property
    def shipping_full_name(self):
        return f"{self.shipping_first_name} {self.shipping_last_name}".strip()


class OrderItem(models.Model):
    """Individual item in an order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
    )

    # Snapshot of book data at time of purchase
    book_title = models.CharField(max_length=500)
    book_isbn = models.CharField(max_length=13)
    book_cover_url = models.URLField(blank=True)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.book_title}"

    @property
    def effective_price(self):
        if self.discount_price and self.discount_price < self.unit_price:
            return self.discount_price
        return self.unit_price

    @property
    def line_total(self):
        return self.effective_price * self.quantity

    def save(self, *args, **kwargs):
        # Snapshot book data when creating
        if not self.book_title and self.book:
            self.book_title = self.book.title
            self.book_isbn = self.book.isbn_13
            if self.book.cover_image:
                self.book_cover_url = self.book.cover_image.url
            self.unit_price = self.book.price
            if self.book.sale_price:
                self.discount_price = self.book.sale_price
        super().save(*args, **kwargs)

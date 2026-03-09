"""
Wishlist models.
"""

import uuid

from django.conf import settings
from django.db import models


class Wishlist(models.Model):
    """User's wishlist of books they want to purchase."""

    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
        ("shared", "Shared via Link"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )
    name = models.CharField(max_length=255, default="My Wishlist")
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="private"
    )
    share_token = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        help_text="Token for sharing the wishlist via link.",
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wishlists"
        ordering = ["-is_default", "-created_at"]
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return f"{self.user.full_name}'s {self.name}"

    @property
    def item_count(self):
        return self.items.count()

    @property
    def total_value(self):
        return sum(
            item.book.effective_price for item in self.items.select_related("book")
        )

    def save(self, *args, **kwargs):
        if self.visibility == "shared" and not self.share_token:
            import secrets

            self.share_token = secrets.token_urlsafe(24)
        super().save(*args, **kwargs)


class WishlistItem(models.Model):
    """Item in a wishlist."""

    PRIORITY_CHOICES = [
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
        (4, "Must Have"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES, default=2
    )
    notes = models.TextField(blank=True, max_length=500)
    price_at_addition = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    is_price_drop_alert = models.BooleanField(
        default=False,
        help_text="Notify when the book price drops.",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wishlist_items"
        ordering = ["-priority", "-added_at"]
        unique_together = ["wishlist", "book"]
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.book.title} in {self.wishlist.name}"

    def save(self, *args, **kwargs):
        if not self.price_at_addition and self.book:
            self.price_at_addition = self.book.effective_price
        super().save(*args, **kwargs)

    @property
    def has_price_dropped(self):
        """Check if the book's price has dropped since it was added."""
        if self.price_at_addition and self.book:
            return self.book.effective_price < self.price_at_addition
        return False

    @property
    def price_change(self):
        """Calculate the price difference since addition."""
        if self.price_at_addition and self.book:
            return self.book.effective_price - self.price_at_addition
        return 0

"""
Review models: Review, Rating.
User reviews and ratings for books.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """User review for a book."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars.",
    )
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(
        max_length=5000,
        help_text="Review text (max 5000 characters).",
    )
    contains_spoilers = models.BooleanField(default=False)

    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, blank=True)

    # Helpfulness voting
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)

    # Verified purchase
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text="Whether the reviewer purchased the book through BookVerse.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        unique_together = ["user", "book"]
        indexes = [
            models.Index(fields=["book", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["-helpful_count"]),
        ]

    def __str__(self):
        return f"{self.user.full_name}'s review of {self.book.title}"

    def save(self, *args, **kwargs):
        # Check if user has purchased this book
        if not self.is_verified_purchase:
            from apps.orders.models import OrderItem

            self.is_verified_purchase = OrderItem.objects.filter(
                order__user=self.user,
                book=self.book,
                order__status__in=["confirmed", "processing", "shipped", "delivered"],
            ).exists()

        super().save(*args, **kwargs)
        # Update book rating stats
        self.book.update_rating_stats()

    def delete(self, *args, **kwargs):
        book = self.book
        super().delete(*args, **kwargs)
        book.update_rating_stats()

    @property
    def helpfulness_score(self):
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return round(self.helpful_count / total * 100)


class ReviewVote(models.Model):
    """Track user votes on review helpfulness."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_votes",
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "review_votes"
        unique_together = ["user", "review"]
        verbose_name = "Review Vote"
        verbose_name_plural = "Review Votes"

    def __str__(self):
        vote_type = "helpful" if self.is_helpful else "not helpful"
        return f"{self.user.email} voted {vote_type} on review {self.review.id}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_vote = None

        if not is_new:
            try:
                old_vote = ReviewVote.objects.get(pk=self.pk)
            except ReviewVote.DoesNotExist:
                is_new = True

        super().save(*args, **kwargs)

        review = self.review
        if is_new:
            if self.is_helpful:
                review.helpful_count += 1
            else:
                review.not_helpful_count += 1
        elif old_vote and old_vote.is_helpful != self.is_helpful:
            if self.is_helpful:
                review.helpful_count += 1
                review.not_helpful_count = max(0, review.not_helpful_count - 1)
            else:
                review.not_helpful_count += 1
                review.helpful_count = max(0, review.helpful_count - 1)

        review.save(update_fields=["helpful_count", "not_helpful_count"])

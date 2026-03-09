"""
Account models for BookVerse.
Custom User model with email authentication and ReaderProfile for reading preferences.
"""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager for User model with email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email for authentication instead of username."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # Address fields
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default="US")

    # Status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email

    @property
    def full_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(part for part in parts if part)


class ReaderProfile(models.Model):
    """Extended profile for reading preferences and statistics."""

    READING_GOAL_FREQUENCY = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reader_profile",
    )
    bio = models.TextField(max_length=1000, blank=True)
    favorite_genres = models.ManyToManyField(
        "books.Genre",
        blank=True,
        related_name="fans",
    )
    favorite_authors = models.ManyToManyField(
        "books.Author",
        blank=True,
        related_name="fans",
    )
    reading_goal_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of books the reader aims to read.",
    )
    reading_goal_frequency = models.CharField(
        max_length=10,
        choices=READING_GOAL_FREQUENCY,
        default="yearly",
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Whether the reading profile is publicly visible.",
    )
    goodreads_url = models.URLField(blank=True)
    website = models.URLField(blank=True)

    # Calculated statistics (updated periodically)
    total_books_read = models.PositiveIntegerField(default=0)
    total_pages_read = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating_given = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reader_profiles"
        verbose_name = "Reader Profile"
        verbose_name_plural = "Reader Profiles"

    def __str__(self):
        return f"Profile: {self.user.full_name}"

    def update_statistics(self):
        """Recalculate reading statistics from related models."""
        from apps.reading.models import ReadingProgress
        from apps.reviews.models import Review

        finished = ReadingProgress.objects.filter(
            user=self.user, status="finished"
        )
        reviews = Review.objects.filter(user=self.user, is_approved=True)

        self.total_books_read = finished.count()
        self.total_pages_read = sum(
            rp.book.page_count or 0 for rp in finished.select_related("book")
        )
        self.total_reviews = reviews.count()

        avg = reviews.aggregate(avg=models.Avg("rating"))["avg"]
        self.average_rating_given = avg or 0.00
        self.save(
            update_fields=[
                "total_books_read",
                "total_pages_read",
                "total_reviews",
                "average_rating_given",
            ]
        )

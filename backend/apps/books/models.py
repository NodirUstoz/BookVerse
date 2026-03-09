"""
Book-related models: Book, Author, Genre, Publisher, BookImage.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    """Book genre / category."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "genres"
        ordering = ["display_order", "name"]
        verbose_name = "Genre"
        verbose_name_plural = "Genres"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def book_count(self):
        return self.books.filter(is_active=True).count()


class Author(models.Model):
    """Book author."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="authors/%Y/%m/", blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    death_date = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "authors"
        ordering = ["name"]
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Author.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def book_count(self):
        return self.books.filter(is_active=True).count()

    @property
    def average_rating(self):
        from django.db.models import Avg

        result = self.books.filter(is_active=True).aggregate(
            avg=Avg("reviews__rating")
        )
        return round(result["avg"] or 0, 2)


class Publisher(models.Model):
    """Book publisher."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="publishers/", blank=True, null=True)
    website = models.URLField(blank=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    headquarters = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "publishers"
        ordering = ["name"]
        verbose_name = "Publisher"
        verbose_name_plural = "Publishers"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    """Core book model."""

    FORMAT_CHOICES = [
        ("hardcover", "Hardcover"),
        ("paperback", "Paperback"),
        ("ebook", "E-Book"),
        ("audiobook", "Audiobook"),
    ]

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
        ("de", "German"),
        ("it", "Italian"),
        ("pt", "Portuguese"),
        ("ja", "Japanese"),
        ("zh", "Chinese"),
        ("ko", "Korean"),
        ("ar", "Arabic"),
        ("hi", "Hindi"),
        ("ru", "Russian"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500, db_index=True)
    slug = models.SlugField(max_length=550, unique=True, blank=True)
    isbn_10 = models.CharField(max_length=10, blank=True, db_index=True)
    isbn_13 = models.CharField(max_length=13, unique=True, db_index=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)

    # Relationships
    authors = models.ManyToManyField(Author, related_name="books")
    genres = models.ManyToManyField(Genre, related_name="books")
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )

    # Book details
    publication_date = models.DateField(blank=True, null=True)
    page_count = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default="en")
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="paperback")
    edition = models.CharField(max_length=100, blank=True)
    series_name = models.CharField(max_length=255, blank=True)
    series_number = models.PositiveIntegerField(blank=True, null=True)

    # Cover image
    cover_image = models.ImageField(
        upload_to="books/covers/%Y/%m/", blank=True, null=True
    )
    thumbnail = models.ImageField(
        upload_to="books/thumbnails/%Y/%m/", blank=True, null=True
    )

    # Pricing & inventory
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    # Ratings (denormalized for performance)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )
    rating_count = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)

    # Metadata
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    weight_grams = models.PositiveIntegerField(blank=True, null=True)
    dimensions = models.CharField(
        max_length=50, blank=True, help_text="Format: LxWxH in cm"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "books"
        ordering = ["-created_at"]
        verbose_name = "Book"
        verbose_name_plural = "Books"
        indexes = [
            models.Index(fields=["isbn_13"]),
            models.Index(fields=["title"]),
            models.Index(fields=["-average_rating"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_active", "is_available"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Book.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        """Return sale price if available, otherwise regular price."""
        if self.sale_price and self.sale_price < self.price:
            return self.sale_price
        return self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage if on sale."""
        if self.sale_price and self.sale_price < self.price and self.price > 0:
            return round((1 - self.sale_price / self.price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock_quantity > 0 and self.is_available

    @property
    def primary_author(self):
        return self.authors.first()

    def update_rating_stats(self):
        """Recalculate denormalized rating statistics."""
        from django.db.models import Avg, Count

        stats = self.reviews.filter(is_approved=True).aggregate(
            avg_rating=Avg("rating"),
            num_reviews=Count("id"),
        )
        self.average_rating = stats["avg_rating"] or 0.00
        self.review_count = stats["num_reviews"]
        self.rating_count = self.reviews.filter(
            is_approved=True, rating__isnull=False
        ).count()
        self.save(update_fields=["average_rating", "review_count", "rating_count"])


class BookImage(models.Model):
    """Additional images for a book (preview pages, back cover, etc.)."""

    IMAGE_TYPE_CHOICES = [
        ("cover_front", "Front Cover"),
        ("cover_back", "Back Cover"),
        ("preview", "Preview Page"),
        ("author_signed", "Author Signed"),
        ("other", "Other"),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="books/images/%Y/%m/")
    image_type = models.CharField(
        max_length=20, choices=IMAGE_TYPE_CHOICES, default="other"
    )
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "book_images"
        ordering = ["display_order"]
        verbose_name = "Book Image"
        verbose_name_plural = "Book Images"

    def __str__(self):
        return f"{self.book.title} - {self.get_image_type_display()}"

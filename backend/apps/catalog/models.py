"""
Catalog models: BookCatalog, FeaturedBook, BestSeller.
Manages curated collections and promotional book listings.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class BookCatalog(models.Model):
    """Curated collection of books (e.g., 'Summer Reads', 'Staff Picks')."""

    CATALOG_TYPE_CHOICES = [
        ("collection", "Collection"),
        ("staff_picks", "Staff Picks"),
        ("seasonal", "Seasonal"),
        ("themed", "Themed"),
        ("award_winners", "Award Winners"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField(blank=True)
    catalog_type = models.CharField(
        max_length=20, choices=CATALOG_TYPE_CHOICES, default="collection"
    )
    cover_image = models.ImageField(
        upload_to="catalogs/%Y/%m/", blank=True, null=True
    )
    books = models.ManyToManyField(
        "books.Book",
        related_name="catalogs",
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_catalogs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "book_catalogs"
        ordering = ["display_order", "-created_at"]
        verbose_name = "Book Catalog"
        verbose_name_plural = "Book Catalogs"

    def __str__(self):
        return self.name

    @property
    def is_current(self):
        """Check if the catalog is within its active date range."""
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return self.is_active

    @property
    def book_count(self):
        return self.books.filter(is_active=True).count()


class FeaturedBook(models.Model):
    """Featured book placement on the homepage or special sections."""

    PLACEMENT_CHOICES = [
        ("hero", "Hero Banner"),
        ("homepage", "Homepage Section"),
        ("sidebar", "Sidebar"),
        ("category", "Category Page"),
        ("newsletter", "Newsletter"),
    ]

    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="featured_placements",
    )
    placement = models.CharField(
        max_length=20, choices=PLACEMENT_CHOICES, default="homepage"
    )
    headline = models.CharField(max_length=255, blank=True)
    subtitle = models.CharField(max_length=500, blank=True)
    custom_image = models.ImageField(
        upload_to="featured/%Y/%m/",
        blank=True,
        null=True,
        help_text="Custom promotional image (uses book cover if empty).",
    )
    link_url = models.URLField(
        blank=True,
        help_text="Custom link URL (defaults to book detail page).",
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "featured_books"
        ordering = ["display_order", "-created_at"]
        verbose_name = "Featured Book"
        verbose_name_plural = "Featured Books"

    def __str__(self):
        return f"Featured: {self.book.title} ({self.get_placement_display()})"

    @property
    def is_current(self):
        now = timezone.now()
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return self.is_active


class BestSeller(models.Model):
    """Bestseller list entry, tracked weekly."""

    CATEGORY_CHOICES = [
        ("overall", "Overall"),
        ("fiction", "Fiction"),
        ("nonfiction", "Non-Fiction"),
        ("children", "Children"),
        ("ya", "Young Adult"),
    ]

    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="bestseller_entries",
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="overall"
    )
    rank = models.PositiveIntegerField()
    previous_rank = models.PositiveIntegerField(blank=True, null=True)
    weeks_on_list = models.PositiveIntegerField(default=1)
    week_date = models.DateField(
        help_text="The Monday of the bestseller week.",
    )
    units_sold = models.PositiveIntegerField(default=0)
    is_new_entry = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bestsellers"
        ordering = ["category", "rank"]
        verbose_name = "Bestseller"
        verbose_name_plural = "Bestsellers"
        unique_together = ["book", "category", "week_date"]

    def __str__(self):
        return f"#{self.rank} {self.book.title} ({self.get_category_display()})"

    @property
    def rank_change(self):
        """Positive means moved up, negative means dropped."""
        if self.previous_rank is None:
            return None
        return self.previous_rank - self.rank

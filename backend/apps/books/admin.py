"""
Admin configuration for books app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Author, Book, BookImage, Genre, Publisher


class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 1
    fields = ("image", "image_type", "alt_text", "display_order")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "isbn_13",
        "display_authors",
        "price",
        "sale_price",
        "stock_quantity",
        "average_rating",
        "is_active",
        "is_featured",
        "cover_preview",
    )
    list_filter = (
        "is_active",
        "is_featured",
        "is_available",
        "format",
        "language",
        "genres",
    )
    search_fields = ("title", "isbn_13", "isbn_10", "authors__name")
    filter_horizontal = ("authors", "genres")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [BookImageInline]
    readonly_fields = ("average_rating", "rating_count", "review_count")
    list_per_page = 25
    list_editable = ("is_active", "is_featured", "stock_quantity")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "isbn_10",
                    "isbn_13",
                    "description",
                    "short_description",
                )
            },
        ),
        (
            "Relationships",
            {"fields": ("authors", "genres", "publisher")},
        ),
        (
            "Book Details",
            {
                "fields": (
                    "publication_date",
                    "page_count",
                    "language",
                    "format",
                    "edition",
                    "series_name",
                    "series_number",
                )
            },
        ),
        (
            "Media",
            {"fields": ("cover_image", "thumbnail")},
        ),
        (
            "Pricing & Inventory",
            {
                "fields": (
                    "price",
                    "sale_price",
                    "stock_quantity",
                    "is_available",
                )
            },
        ),
        (
            "Ratings",
            {
                "fields": (
                    "average_rating",
                    "rating_count",
                    "review_count",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "is_active",
                    "is_featured",
                    "tags",
                    "weight_grams",
                    "dimensions",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def display_authors(self, obj):
        return ", ".join(a.name for a in obj.authors.all()[:3])

    display_authors.short_description = "Authors"

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />', obj.cover_image.url
            )
        return "-"

    cover_preview.short_description = "Cover"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "nationality", "birth_date", "book_count", "is_active")
    list_filter = ("is_active", "nationality")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "book_count", "display_order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("display_order", "is_active")


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name", "headquarters", "founded_year", "website", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

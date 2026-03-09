"""
Serializers for catalog app.
"""

from rest_framework import serializers

from apps.books.serializers import BookListSerializer

from .models import BestSeller, BookCatalog, FeaturedBook


class BookCatalogSerializer(serializers.ModelSerializer):
    books = BookListSerializer(many=True, read_only=True)
    book_count = serializers.ReadOnlyField()
    is_current = serializers.ReadOnlyField()

    class Meta:
        model = BookCatalog
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "catalog_type",
            "cover_image",
            "books",
            "book_count",
            "is_current",
            "display_order",
            "start_date",
            "end_date",
            "created_at",
        ]


class BookCatalogListSerializer(serializers.ModelSerializer):
    """Compact catalog serializer for list views."""

    book_count = serializers.ReadOnlyField()
    is_current = serializers.ReadOnlyField()
    preview_books = serializers.SerializerMethodField()

    class Meta:
        model = BookCatalog
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "catalog_type",
            "cover_image",
            "book_count",
            "is_current",
            "preview_books",
        ]

    def get_preview_books(self, obj):
        """Return first 4 books as a preview."""
        books = obj.books.filter(is_active=True)[:4]
        return BookListSerializer(books, many=True, context=self.context).data


class FeaturedBookSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    is_current = serializers.ReadOnlyField()

    class Meta:
        model = FeaturedBook
        fields = [
            "id",
            "book",
            "placement",
            "headline",
            "subtitle",
            "custom_image",
            "link_url",
            "display_order",
            "is_current",
            "start_date",
            "end_date",
        ]


class BestSellerSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    rank_change = serializers.ReadOnlyField()
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = BestSeller
        fields = [
            "id",
            "book",
            "category",
            "category_display",
            "rank",
            "previous_rank",
            "rank_change",
            "weeks_on_list",
            "week_date",
            "is_new_entry",
        ]

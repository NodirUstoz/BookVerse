"""
Filters for books app.
"""

from django_filters import rest_framework as filters

from .models import Author, Book


class BookFilter(filters.FilterSet):
    """Advanced filtering for book listings."""

    title = filters.CharFilter(lookup_expr="icontains")
    author = filters.CharFilter(
        field_name="authors__name", lookup_expr="icontains"
    )
    author_id = filters.UUIDFilter(field_name="authors__id")
    genre = filters.CharFilter(field_name="genres__slug")
    genre_id = filters.NumberFilter(field_name="genres__id")
    publisher = filters.CharFilter(
        field_name="publisher__name", lookup_expr="icontains"
    )
    isbn = filters.CharFilter(field_name="isbn_13", lookup_expr="exact")
    language = filters.ChoiceFilter(choices=Book.LANGUAGE_CHOICES)
    format = filters.ChoiceFilter(choices=Book.FORMAT_CHOICES)

    # Price range
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")

    # Rating range
    min_rating = filters.NumberFilter(field_name="average_rating", lookup_expr="gte")

    # Date range
    published_after = filters.DateFilter(
        field_name="publication_date", lookup_expr="gte"
    )
    published_before = filters.DateFilter(
        field_name="publication_date", lookup_expr="lte"
    )

    # Boolean filters
    in_stock = filters.BooleanFilter(method="filter_in_stock")
    on_sale = filters.BooleanFilter(method="filter_on_sale")
    is_featured = filters.BooleanFilter()

    # Series
    series = filters.CharFilter(
        field_name="series_name", lookup_expr="icontains"
    )

    # Page count range
    min_pages = filters.NumberFilter(field_name="page_count", lookup_expr="gte")
    max_pages = filters.NumberFilter(field_name="page_count", lookup_expr="lte")

    # Ordering
    ordering = filters.OrderingFilter(
        fields=(
            ("title", "title"),
            ("price", "price"),
            ("average_rating", "rating"),
            ("publication_date", "published"),
            ("created_at", "newest"),
            ("review_count", "popularity"),
        ),
        field_labels={
            "title": "Title",
            "price": "Price",
            "average_rating": "Rating",
            "publication_date": "Publication Date",
            "created_at": "Date Added",
            "review_count": "Popularity",
        },
    )

    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "author_id",
            "genre",
            "genre_id",
            "publisher",
            "isbn",
            "language",
            "format",
            "is_featured",
        ]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0, is_available=True)
        return queryset.filter(
            models.Q(stock_quantity=0) | models.Q(is_available=False)
        )

    def filter_on_sale(self, queryset, name, value):
        if value:
            return queryset.filter(
                sale_price__isnull=False,
                sale_price__lt=models.F("price"),
            )
        return queryset.filter(sale_price__isnull=True)


class AuthorFilter(filters.FilterSet):
    """Filters for author listings."""

    name = filters.CharFilter(lookup_expr="icontains")
    nationality = filters.CharFilter(lookup_expr="icontains")
    has_photo = filters.BooleanFilter(method="filter_has_photo")

    ordering = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("created_at", "newest"),
        ),
    )

    class Meta:
        model = Author
        fields = ["name", "nationality"]

    def filter_has_photo(self, queryset, name, value):
        if value:
            return queryset.exclude(photo="")
        return queryset.filter(photo="")

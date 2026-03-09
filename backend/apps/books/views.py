"""
Views for books app.
"""

from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import AuthorFilter, BookFilter
from .models import Author, Book, BookImage, Genre, Publisher
from .serializers import (
    AuthorDetailSerializer,
    AuthorListSerializer,
    BookCreateUpdateSerializer,
    BookDetailSerializer,
    BookListSerializer,
    GenreSerializer,
    PublisherSerializer,
)


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for books.
    - list: Browse all active books with filtering
    - retrieve: Get detailed book info by slug or ISBN
    - create/update/destroy: Admin only
    """

    lookup_field = "slug"
    filterset_class = BookFilter
    search_fields = ["title", "description", "authors__name", "isbn_13", "tags"]
    ordering_fields = ["title", "price", "average_rating", "publication_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Book.objects.filter(is_active=True).select_related(
            "publisher"
        ).prefetch_related("authors", "genres", "images")

        if self.action == "list":
            return queryset
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return BookListSerializer
        if self.action in ("create", "update", "partial_update"):
            return BookCreateUpdateSerializer
        return BookDetailSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="by-isbn/(?P<isbn>[0-9]{13})")
    def by_isbn(self, request, isbn=None):
        """Look up a book by ISBN-13."""
        try:
            book = Book.objects.get(isbn_13=isbn, is_active=True)
            serializer = BookDetailSerializer(book, context={"request": request})
            return Response(serializer.data)
        except Book.DoesNotExist:
            return Response(
                {"detail": "Book not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Full-text search across books."""
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response(
                {"detail": "Search query is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        books = Book.objects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(authors__name__icontains=query)
            | Q(isbn_13__icontains=query)
            | Q(tags__icontains=query),
            is_active=True,
        ).distinct().order_by("-average_rating")[:50]

        serializer = BookListSerializer(
            books, many=True, context={"request": request}
        )
        return Response(
            {"count": len(serializer.data), "results": serializer.data}
        )

    @action(detail=False, methods=["get"])
    def new_arrivals(self, request):
        """Get recently added books."""
        books = self.get_queryset().order_by("-created_at")[:20]
        serializer = BookListSerializer(
            books, many=True, context={"request": request}
        )
        return Response(serializer.data)


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing authors."""

    queryset = Author.objects.filter(is_active=True)
    lookup_field = "slug"
    filterset_class = AuthorFilter
    search_fields = ["name", "nationality"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return AuthorListSerializer
        return AuthorDetailSerializer

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing genres."""

    queryset = Genre.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = GenreSerializer
    lookup_field = "slug"

    @method_decorator(cache_page(60 * 60))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def books(self, request, slug=None):
        """Get all books in a specific genre."""
        genre = self.get_object()
        # Include books from child genres
        genre_ids = [genre.id] + list(
            genre.children.values_list("id", flat=True)
        )
        books = Book.objects.filter(
            genres__id__in=genre_ids, is_active=True
        ).distinct().order_by("-average_rating")

        page = self.paginate_queryset(books)
        if page is not None:
            serializer = BookListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = BookListSerializer(
            books, many=True, context={"request": request}
        )
        return Response(serializer.data)


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing publishers."""

    queryset = Publisher.objects.filter(is_active=True)
    serializer_class = PublisherSerializer
    lookup_field = "slug"
    search_fields = ["name"]
    ordering = ["name"]

"""
Views for catalog app.
"""

from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BestSeller, BookCatalog, FeaturedBook
from .serializers import (
    BestSellerSerializer,
    BookCatalogListSerializer,
    BookCatalogSerializer,
    FeaturedBookSerializer,
)


class BookCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for curated book catalogs."""

    lookup_field = "slug"
    search_fields = ["name", "description"]
    ordering = ["display_order", "-created_at"]

    def get_queryset(self):
        now = timezone.now()
        return BookCatalog.objects.filter(
            is_active=True,
            is_public=True,
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now),
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now),
        ).prefetch_related("books__authors", "books__genres")

    def get_serializer_class(self):
        if self.action == "list":
            return BookCatalogListSerializer
        return BookCatalogSerializer

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return BookCatalog.objects.filter(
            is_active=True, is_public=True
        ).prefetch_related("books__authors", "books__genres")


class FeaturedBookListView(generics.ListAPIView):
    """List currently featured books."""

    serializer_class = FeaturedBookSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        now = timezone.now()
        queryset = FeaturedBook.objects.filter(
            is_active=True,
            start_date__lte=now,
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        ).select_related(
            "book__publisher"
        ).prefetch_related("book__authors", "book__genres")

        placement = self.request.query_params.get("placement")
        if placement:
            queryset = queryset.filter(placement=placement)

        return queryset.order_by("display_order")

    def get_queryset(self):
        now = timezone.now()
        queryset = FeaturedBook.objects.filter(
            is_active=True,
            start_date__lte=now,
        ).select_related(
            "book__publisher"
        ).prefetch_related("book__authors", "book__genres")

        placement = self.request.query_params.get("placement")
        if placement:
            queryset = queryset.filter(placement=placement)

        return queryset.order_by("display_order")

    @method_decorator(cache_page(60 * 10))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class BestSellerListView(generics.ListAPIView):
    """List current bestsellers by category."""

    serializer_class = BestSellerSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = BestSeller.objects.select_related(
            "book__publisher"
        ).prefetch_related("book__authors", "book__genres")

        category = self.request.query_params.get("category", "overall")
        queryset = queryset.filter(category=category)

        # Get the most recent week
        latest_week = queryset.order_by("-week_date").values_list(
            "week_date", flat=True
        ).first()

        if latest_week:
            queryset = queryset.filter(week_date=latest_week)

        return queryset.order_by("rank")

    @method_decorator(cache_page(60 * 30))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


# Need to import models for Q objects
from django.db import models  # noqa: E402

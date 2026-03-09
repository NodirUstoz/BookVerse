"""
URL patterns for catalog app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "catalog"

router = DefaultRouter()
router.register("collections", views.BookCatalogViewSet, basename="catalog")

urlpatterns = [
    path("", include(router.urls)),
    path("featured/", views.FeaturedBookListView.as_view(), name="featured"),
    path("bestsellers/", views.BestSellerListView.as_view(), name="bestsellers"),
]

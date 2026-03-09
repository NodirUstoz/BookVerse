"""
URL patterns for wishlist app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "wishlist"

router = DefaultRouter()
router.register("", views.WishlistViewSet, basename="wishlist")

urlpatterns = [
    path("quick-add/", views.QuickAddToDefaultWishlistView.as_view(), name="quick-add"),
    path(
        "shared/<str:share_token>/",
        views.SharedWishlistView.as_view(),
        name="shared-wishlist",
    ),
    path("", include(router.urls)),
]

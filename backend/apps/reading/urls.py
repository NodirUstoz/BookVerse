"""
URL patterns for reading app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "reading"

router = DefaultRouter()
router.register("lists", views.ReadingListViewSet, basename="reading-list")
router.register("clubs", views.BookClubViewSet, basename="book-club")

urlpatterns = [
    path("", include(router.urls)),
    path("progress/", views.ReadingProgressListView.as_view(), name="progress-list"),
    path(
        "progress/update/",
        views.ReadingProgressCreateUpdateView.as_view(),
        name="progress-update",
    ),
]

"""
URL patterns for books app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "books"

router = DefaultRouter()
router.register("", views.BookViewSet, basename="book")
router.register("authors", views.AuthorViewSet, basename="author")
router.register("genres", views.GenreViewSet, basename="genre")
router.register("publishers", views.PublisherViewSet, basename="publisher")

urlpatterns = [
    path("", include(router.urls)),
]

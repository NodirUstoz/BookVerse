"""
URL patterns for recommendations app.
"""

from django.urls import path

from . import views

app_name = "recommendations"

urlpatterns = [
    path("", views.UserRecommendationListView.as_view(), name="recommendation-list"),
    path(
        "<uuid:pk>/dismiss/",
        views.DismissRecommendationView.as_view(),
        name="dismiss-recommendation",
    ),
    path(
        "refresh/",
        views.RefreshRecommendationsView.as_view(),
        name="refresh-recommendations",
    ),
    path(
        "similar/<uuid:book_id>/",
        views.SimilarBooksView.as_view(),
        name="similar-books",
    ),
]

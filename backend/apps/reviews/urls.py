"""
URL patterns for reviews app.
"""

from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("", views.ReviewListCreateView.as_view(), name="review-list-create"),
    path("<uuid:pk>/", views.ReviewDetailView.as_view(), name="review-detail"),
    path("<uuid:pk>/vote/", views.ReviewVoteView.as_view(), name="review-vote"),
    path("book/<uuid:book_id>/stats/", views.BookReviewStatsView.as_view(), name="book-review-stats"),
    path("mine/", views.UserReviewsView.as_view(), name="user-reviews"),
]

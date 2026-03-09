"""
URL patterns for accounts app.
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/<uuid:id>/", views.PublicProfileView.as_view(), name="public-profile"),
    path("reader-profile/", views.ReaderProfileView.as_view(), name="reader-profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("reading-stats/", views.ReadingStatsView.as_view(), name="reading-stats"),
    path("delete-account/", views.delete_account, name="delete-account"),
]

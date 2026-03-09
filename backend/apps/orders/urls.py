"""
URL patterns for orders app.
"""

from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("create/", views.OrderCreateView.as_view(), name="order-create"),
    path("<str:order_number>/", views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "<str:order_number>/cancel/",
        views.OrderCancelView.as_view(),
        name="order-cancel",
    ),
    path("webhook/stripe/", views.stripe_webhook, name="stripe-webhook"),
]

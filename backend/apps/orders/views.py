"""
Views for orders app.
"""

import logging

import stripe
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderListSerializer,
    OrderSerializer,
)
from .tasks import send_order_confirmation_email

logger = logging.getLogger(__name__)


class OrderListView(generics.ListAPIView):
    """List the authenticated user's orders."""

    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items__book")


class OrderDetailView(generics.RetrieveAPIView):
    """Retrieve order details by order number."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items__book")


class OrderCreateView(APIView):
    """Create a new order and initiate payment."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Create Stripe PaymentIntent
        payment_intent = None
        if order.payment_method == "stripe" and settings.STRIPE_SECRET_KEY:
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(order.total * 100),  # cents
                    currency="usd",
                    metadata={
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                    },
                )
                order.stripe_payment_intent_id = payment_intent.id
                order.save(update_fields=["stripe_payment_intent_id"])
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error for order {order.order_number}: {e}")

        response_data = OrderSerializer(order).data
        if payment_intent:
            response_data["client_secret"] = payment_intent.client_secret

        return Response(response_data, status=status.HTTP_201_CREATED)


class OrderCancelView(APIView):
    """Cancel an order (only if still pending or confirmed)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_number):
        try:
            order = Order.objects.get(
                order_number=order_number, user=request.user
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if order.status not in ("pending", "confirmed"):
            return Response(
                {"detail": "This order cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.cancel()

        # Refund via Stripe if payment was captured
        if (
            order.stripe_payment_intent_id
            and order.payment_status == "captured"
            and settings.STRIPE_SECRET_KEY
        ):
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe.Refund.create(
                    payment_intent=order.stripe_payment_intent_id
                )
                order.payment_status = "refunded"
                order.status = "refunded"
                order.save(update_fields=["payment_status", "status"])
            except stripe.error.StripeError as e:
                logger.error(f"Stripe refund error for {order.order_number}: {e}")

        return Response(
            {"message": "Order cancelled successfully."},
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    if not settings.STRIPE_WEBHOOK_SECRET:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        try:
            order = Order.objects.get(
                stripe_payment_intent_id=payment_intent["id"]
            )
            order.payment_status = "captured"
            order.save(update_fields=["payment_status"])
            order.confirm()
            send_order_confirmation_email.delay(str(order.id))
        except Order.DoesNotExist:
            logger.warning(
                f"Order not found for PaymentIntent {payment_intent['id']}"
            )

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        try:
            order = Order.objects.get(
                stripe_payment_intent_id=payment_intent["id"]
            )
            order.payment_status = "failed"
            order.save(update_fields=["payment_status"])
        except Order.DoesNotExist:
            pass

    return Response(status=status.HTTP_200_OK)

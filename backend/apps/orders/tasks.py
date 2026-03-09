"""
Celery tasks for orders app.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id):
    """Send order confirmation email to the customer."""
    from .models import Order

    try:
        order = Order.objects.prefetch_related("items__book").get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for confirmation email.")
        return

    subject = f"BookVerse - Order Confirmation #{order.order_number}"
    items_text = "\n".join(
        f"  - {item.book_title} (x{item.quantity}): ${item.line_total:.2f}"
        for item in order.items.all()
    )

    message = (
        f"Hello {order.shipping_first_name},\n\n"
        f"Thank you for your order!\n\n"
        f"Order Number: {order.order_number}\n"
        f"Items:\n{items_text}\n\n"
        f"Subtotal: ${order.subtotal:.2f}\n"
        f"Tax: ${order.tax_amount:.2f}\n"
        f"Shipping: ${order.shipping_cost:.2f}\n"
        f"Total: ${order.total:.2f}\n\n"
        f"Shipping to:\n"
        f"  {order.shipping_full_name}\n"
        f"  {order.shipping_address_line1}\n"
        f"  {order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}\n"
        f"  {order.shipping_country}\n\n"
        f"We'll notify you when your order ships.\n\n"
        f"Thank you for shopping with BookVerse!"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.shipping_email],
            fail_silently=False,
        )
        logger.info(f"Confirmation email sent for order {order.order_number}")
    except Exception as exc:
        logger.error(f"Failed to send confirmation email for order {order.order_number}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_shipping_notification_email(self, order_id):
    """Send shipping notification email to the customer."""
    from .models import Order

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for shipping notification.")
        return

    subject = f"BookVerse - Your Order #{order.order_number} Has Shipped!"

    message = (
        f"Hello {order.shipping_first_name},\n\n"
        f"Great news! Your order #{order.order_number} has been shipped.\n\n"
    )

    if order.tracking_number:
        message += (
            f"Tracking Number: {order.tracking_number}\n"
            f"Carrier: {order.tracking_carrier}\n\n"
        )

    if order.estimated_delivery:
        message += f"Estimated Delivery: {order.estimated_delivery.strftime('%B %d, %Y')}\n\n"

    message += "Thank you for shopping with BookVerse!"

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.shipping_email],
            fail_silently=False,
        )
        logger.info(f"Shipping notification sent for order {order.order_number}")
    except Exception as exc:
        logger.error(f"Failed to send shipping notification for order {order.order_number}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def cleanup_abandoned_orders():
    """Cancel orders that have been pending for more than 24 hours."""
    from .models import Order

    cutoff = timezone.now() - timedelta(hours=24)
    abandoned = Order.objects.filter(
        status="pending",
        payment_status="pending",
        created_at__lt=cutoff,
    )

    count = 0
    for order in abandoned:
        order.cancel()
        count += 1

    if count:
        logger.info(f"Cancelled {count} abandoned orders.")
    return count


@shared_task
def generate_daily_sales_report():
    """Generate a daily sales summary report."""
    from django.db.models import Count, Sum

    from .models import Order

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    orders = Order.objects.filter(
        created_at__date=yesterday,
        status__in=["confirmed", "processing", "shipped", "delivered"],
    )

    stats = orders.aggregate(
        total_orders=Count("id"),
        total_revenue=Sum("total"),
    )

    logger.info(
        f"Daily sales report for {yesterday}: "
        f"{stats['total_orders'] or 0} orders, "
        f"${stats['total_revenue'] or 0:.2f} revenue"
    )
    return stats

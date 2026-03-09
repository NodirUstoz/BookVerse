"""
Admin configuration for orders app.
"""

from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "book",
        "book_title",
        "book_isbn",
        "quantity",
        "unit_price",
        "discount_price",
        "line_total",
    )

    def line_total(self, obj):
        return obj.line_total

    line_total.short_description = "Line Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "payment_status",
        "total",
        "item_count",
        "created_at",
    )
    list_filter = ("status", "payment_status", "payment_method", "created_at")
    search_fields = (
        "order_number",
        "user__email",
        "shipping_email",
        "shipping_last_name",
    )
    readonly_fields = (
        "order_number",
        "stripe_payment_intent_id",
        "subtotal",
        "tax_amount",
        "total",
        "created_at",
        "updated_at",
        "confirmed_at",
        "shipped_at",
        "delivered_at",
        "cancelled_at",
    )
    inlines = [OrderItemInline]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Order Info",
            {
                "fields": (
                    "order_number",
                    "user",
                    "status",
                    "payment_status",
                    "payment_method",
                    "stripe_payment_intent_id",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "subtotal",
                    "tax_amount",
                    "shipping_cost",
                    "discount_amount",
                    "discount_code",
                    "total",
                )
            },
        ),
        (
            "Shipping Address",
            {
                "fields": (
                    "shipping_first_name",
                    "shipping_last_name",
                    "shipping_email",
                    "shipping_phone",
                    "shipping_address_line1",
                    "shipping_address_line2",
                    "shipping_city",
                    "shipping_state",
                    "shipping_postal_code",
                    "shipping_country",
                )
            },
        ),
        (
            "Tracking",
            {
                "fields": (
                    "tracking_number",
                    "tracking_carrier",
                    "estimated_delivery",
                )
            },
        ),
        (
            "Notes",
            {"fields": ("customer_notes", "admin_notes")},
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "confirmed_at",
                    "shipped_at",
                    "delivered_at",
                    "cancelled_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_shipped", "mark_as_delivered"]

    def mark_as_shipped(self, request, queryset):
        for order in queryset.filter(status="confirmed"):
            order.ship()
        self.message_user(request, f"Marked {queryset.count()} orders as shipped.")

    mark_as_shipped.short_description = "Mark selected orders as shipped"

    def mark_as_delivered(self, request, queryset):
        for order in queryset.filter(status="shipped"):
            order.deliver()
        self.message_user(request, f"Marked {queryset.count()} orders as delivered.")

    mark_as_delivered.short_description = "Mark selected orders as delivered"

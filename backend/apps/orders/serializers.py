"""
Serializers for orders app.
"""

from rest_framework import serializers

from apps.books.models import Book

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    effective_price = serializers.ReadOnlyField()
    line_total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "book",
            "book_title",
            "book_isbn",
            "book_cover_url",
            "quantity",
            "unit_price",
            "discount_price",
            "effective_price",
            "line_total",
        ]
        read_only_fields = [
            "book_title",
            "book_isbn",
            "book_cover_url",
            "unit_price",
            "discount_price",
        ]


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items within an order."""

    book_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=99)

    def validate_book_id(self, value):
        try:
            book = Book.objects.get(id=value, is_active=True)
            if not book.in_stock:
                raise serializers.ValidationError("This book is currently out of stock.")
            return value
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book not found.")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    shipping_full_name = serializers.ReadOnlyField()
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "status_display",
            "payment_status",
            "payment_status_display",
            "payment_method",
            "subtotal",
            "tax_amount",
            "shipping_cost",
            "discount_amount",
            "total",
            "discount_code",
            "shipping_full_name",
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
            "tracking_number",
            "tracking_carrier",
            "estimated_delivery",
            "customer_notes",
            "items",
            "item_count",
            "created_at",
            "confirmed_at",
            "shipped_at",
            "delivered_at",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "status",
            "payment_status",
            "subtotal",
            "tax_amount",
            "total",
            "tracking_number",
            "tracking_carrier",
            "estimated_delivery",
            "created_at",
            "confirmed_at",
            "shipped_at",
            "delivered_at",
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating a new order."""

    items = OrderItemCreateSerializer(many=True, min_length=1)
    payment_method = serializers.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES, default="stripe"
    )
    shipping_first_name = serializers.CharField(max_length=150)
    shipping_last_name = serializers.CharField(max_length=150)
    shipping_email = serializers.EmailField()
    shipping_phone = serializers.CharField(max_length=20, required=False, default="")
    shipping_address_line1 = serializers.CharField(max_length=255)
    shipping_address_line2 = serializers.CharField(
        max_length=255, required=False, default=""
    )
    shipping_city = serializers.CharField(max_length=100)
    shipping_state = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20)
    shipping_country = serializers.CharField(max_length=100, default="US")
    customer_notes = serializers.CharField(required=False, default="")
    discount_code = serializers.CharField(required=False, default="")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")

        # Check stock availability for all items
        for item_data in value:
            book = Book.objects.get(id=item_data["book_id"])
            if book.stock_quantity < item_data["quantity"]:
                raise serializers.ValidationError(
                    f'Only {book.stock_quantity} copies of "{book.title}" available.'
                )
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].user

        order = Order.objects.create(user=user, **validated_data)

        for item_data in items_data:
            book = Book.objects.get(id=item_data["book_id"])
            OrderItem.objects.create(
                order=order,
                book=book,
                quantity=item_data["quantity"],
            )
            # Deduct stock
            book.stock_quantity -= item_data["quantity"]
            book.save(update_fields=["stock_quantity"])

        order.calculate_totals()
        return order


class OrderListSerializer(serializers.ModelSerializer):
    """Compact order serializer for list views."""

    item_count = serializers.ReadOnlyField()
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "status_display",
            "total",
            "item_count",
            "created_at",
        ]

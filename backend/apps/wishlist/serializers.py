"""
Serializers for wishlist app.
"""

from rest_framework import serializers

from apps.books.serializers import BookListSerializer

from .models import Wishlist, WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    has_price_dropped = serializers.ReadOnlyField()
    price_change = serializers.ReadOnlyField()
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = WishlistItem
        fields = [
            "id",
            "book",
            "priority",
            "priority_display",
            "notes",
            "price_at_addition",
            "is_price_drop_alert",
            "has_price_dropped",
            "price_change",
            "added_at",
        ]
        read_only_fields = ["id", "price_at_addition", "added_at"]


class WishlistItemCreateSerializer(serializers.Serializer):
    book_id = serializers.UUIDField()
    priority = serializers.IntegerField(min_value=1, max_value=4, default=2)
    notes = serializers.CharField(required=False, default="")
    is_price_drop_alert = serializers.BooleanField(default=False)

    def validate_book_id(self, value):
        from apps.books.models import Book

        if not Book.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Book not found.")
        return value


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    total_value = serializers.ReadOnlyField()

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "name",
            "description",
            "visibility",
            "share_token",
            "is_default",
            "item_count",
            "total_value",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "share_token", "is_default", "created_at", "updated_at"]


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ["name", "description", "visibility"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class WishlistListSerializer(serializers.ModelSerializer):
    """Compact wishlist serializer for list views."""

    item_count = serializers.ReadOnlyField()

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "name",
            "visibility",
            "is_default",
            "item_count",
            "created_at",
        ]

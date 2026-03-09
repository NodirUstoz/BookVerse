"""
Views for wishlist app.
"""

from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.books.models import Book

from .models import Wishlist, WishlistItem
from .serializers import (
    WishlistCreateSerializer,
    WishlistItemCreateSerializer,
    WishlistItemSerializer,
    WishlistListSerializer,
    WishlistSerializer,
)


class WishlistViewSet(viewsets.ModelViewSet):
    """Manage wishlists."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return WishlistListSerializer
        if self.action == "create":
            return WishlistCreateSerializer
        return WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "items__book__authors", "items__book__genres"
        )

    def perform_create(self, serializer):
        # Ensure user has a default wishlist
        if not Wishlist.objects.filter(
            user=self.request.user, is_default=True
        ).exists():
            serializer.save(is_default=True)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if instance.is_default:
            return Response(
                {"detail": "Default wishlist cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        """Add a book to the wishlist."""
        wishlist = self.get_object()
        serializer = WishlistItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = Book.objects.get(id=serializer.validated_data["book_id"])

        if WishlistItem.objects.filter(wishlist=wishlist, book=book).exists():
            return Response(
                {"detail": "This book is already in the wishlist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = WishlistItem.objects.create(
            wishlist=wishlist,
            book=book,
            priority=serializer.validated_data.get("priority", 2),
            notes=serializer.validated_data.get("notes", ""),
            is_price_drop_alert=serializer.validated_data.get(
                "is_price_drop_alert", False
            ),
        )

        return Response(
            WishlistItemSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path="remove-item/(?P<item_id>[^/.]+)",
    )
    def remove_item(self, request, pk=None, item_id=None):
        """Remove an item from the wishlist."""
        wishlist = self.get_object()
        try:
            item = WishlistItem.objects.get(id=item_id, wishlist=wishlist)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WishlistItem.DoesNotExist:
            return Response(
                {"detail": "Item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        """Generate or return a sharing link for the wishlist."""
        wishlist = self.get_object()
        wishlist.visibility = "shared"
        wishlist.save()

        share_url = request.build_absolute_uri(
            f"/api/v1/wishlist/shared/{wishlist.share_token}/"
        )
        return Response(
            {
                "share_url": share_url,
                "share_token": wishlist.share_token,
            }
        )

    @action(detail=True, methods=["post"], url_path="move-to-cart")
    def move_to_cart(self, request, pk=None):
        """Return all books in the wishlist as a cart-ready list."""
        wishlist = self.get_object()
        items = wishlist.items.select_related("book").filter(
            book__is_active=True, book__is_available=True
        )

        cart_items = []
        for item in items:
            if item.book.in_stock:
                cart_items.append(
                    {
                        "book_id": str(item.book.id),
                        "title": item.book.title,
                        "price": str(item.book.effective_price),
                        "quantity": 1,
                    }
                )

        return Response(
            {
                "cart_items": cart_items,
                "total_items": len(cart_items),
            }
        )


class SharedWishlistView(generics.RetrieveAPIView):
    """View a wishlist shared via token (no authentication required)."""

    serializer_class = WishlistSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "share_token"

    def get_queryset(self):
        return Wishlist.objects.filter(
            visibility="shared"
        ).prefetch_related(
            "items__book__authors", "items__book__genres"
        )


class QuickAddToDefaultWishlistView(APIView):
    """Quick add a book to the user's default wishlist."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        book_id = request.data.get("book_id")
        if not book_id:
            return Response(
                {"detail": "book_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            book = Book.objects.get(id=book_id, is_active=True)
        except Book.DoesNotExist:
            return Response(
                {"detail": "Book not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get or create default wishlist
        wishlist, _ = Wishlist.objects.get_or_create(
            user=request.user,
            is_default=True,
            defaults={"name": "My Wishlist"},
        )

        item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist, book=book
        )

        if not created:
            return Response(
                {"detail": "Book is already in your wishlist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": f"'{book.title}' added to your wishlist."},
            status=status.HTTP_201_CREATED,
        )

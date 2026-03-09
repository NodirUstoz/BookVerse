"""
Views for reviews app.
"""

from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.books.models import Book

from .models import Review, ReviewVote
from .serializers import (
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
    ReviewVoteSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ReviewListCreateView(generics.ListCreateAPIView):
    """List reviews for a book or create a new review."""

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = Review.objects.filter(
            is_approved=True
        ).select_related("user")

        book_id = self.request.query_params.get("book")
        if book_id:
            queryset = queryset.filter(book_id=book_id)

        # Ordering
        ordering = self.request.query_params.get("ordering", "-created_at")
        valid_orderings = {
            "-created_at": "-created_at",
            "created_at": "created_at",
            "-rating": "-rating",
            "rating": "rating",
            "-helpful": "-helpful_count",
            "helpful": "helpful_count",
        }
        if ordering in valid_orderings:
            queryset = queryset.order_by(valid_orderings[ordering])

        # Filter by rating
        rating = self.request.query_params.get("rating")
        if rating:
            queryset = queryset.filter(rating=int(rating))

        # Filter verified purchases
        verified = self.request.query_params.get("verified")
        if verified == "true":
            queryset = queryset.filter(is_verified_purchase=True)

        return queryset


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a review."""

    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ReviewUpdateSerializer
        return ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(is_approved=True).select_related("user")


class ReviewVoteView(APIView):
    """Vote on a review's helpfulness."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            review = Review.objects.get(pk=pk, is_approved=True)
        except Review.DoesNotExist:
            return Response(
                {"detail": "Review not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if review.user == request.user:
            return Response(
                {"detail": "You cannot vote on your own review."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewVoteSerializer(
            data=request.data,
            context={"request": request, "review": review},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Vote recorded.",
                "helpful_count": review.helpful_count,
                "not_helpful_count": review.not_helpful_count,
            }
        )

    def delete(self, request, pk):
        """Remove a vote from a review."""
        try:
            vote = ReviewVote.objects.get(
                user=request.user, review_id=pk
            )
        except ReviewVote.DoesNotExist:
            return Response(
                {"detail": "Vote not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        review = vote.review
        if vote.is_helpful:
            review.helpful_count = max(0, review.helpful_count - 1)
        else:
            review.not_helpful_count = max(0, review.not_helpful_count - 1)
        review.save(update_fields=["helpful_count", "not_helpful_count"])

        vote.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookReviewStatsView(APIView):
    """Get aggregated review statistics for a book."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id, is_active=True)
        except Book.DoesNotExist:
            return Response(
                {"detail": "Book not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        reviews = Review.objects.filter(book=book, is_approved=True)

        stats = reviews.aggregate(
            average_rating=Avg("rating"),
            total_reviews=Count("id"),
            verified_purchase_count=Count("id", filter=Q(is_verified_purchase=True)),
        )

        # Rating distribution (1-5 stars)
        distribution = {}
        for i in range(1, 6):
            count = reviews.filter(rating=i).count()
            distribution[str(i)] = count

        stats["rating_distribution"] = distribution
        stats["average_rating"] = round(stats["average_rating"] or 0, 2)

        return Response(stats)


class UserReviewsView(generics.ListAPIView):
    """List all reviews by the authenticated user."""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(
            user=self.request.user
        ).select_related("user").order_by("-created_at")

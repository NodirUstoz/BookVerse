"""
Views for recommendations app.
"""

from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.books.serializers import BookListSerializer

from .models import SimilarBook, UserRecommendation
from .services import compute_similar_books, generate_recommendations_for_user


class UserRecommendationListView(generics.ListAPIView):
    """Get personalized book recommendations for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            UserRecommendation.objects.filter(
                user=self.request.user,
                is_dismissed=False,
            )
            .select_related("book__publisher")
            .prefetch_related("book__authors", "book__genres")
            .order_by("-score")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Generate recommendations if none exist or expired
        if not queryset.exists() or queryset.filter(
            expires_at__lt=timezone.now()
        ).exists():
            generate_recommendations_for_user(request.user)
            queryset = self.get_queryset()

        results = []
        for rec in queryset[:30]:
            book_data = BookListSerializer(
                rec.book, context={"request": request}
            ).data
            results.append(
                {
                    "id": str(rec.id),
                    "book": book_data,
                    "score": round(rec.score, 3),
                    "reason": rec.get_reason_display(),
                    "reason_detail": rec.reason_detail,
                }
            )

        return Response(
            {"count": len(results), "results": results}
        )


class DismissRecommendationView(APIView):
    """Dismiss a recommendation so it won't appear again."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            rec = UserRecommendation.objects.get(
                pk=pk, user=request.user
            )
            rec.is_dismissed = True
            rec.save(update_fields=["is_dismissed"])
            return Response(
                {"message": "Recommendation dismissed."},
                status=status.HTTP_200_OK,
            )
        except UserRecommendation.DoesNotExist:
            return Response(
                {"detail": "Recommendation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class RefreshRecommendationsView(APIView):
    """Force refresh recommendations for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        recommendations = generate_recommendations_for_user(request.user)
        return Response(
            {
                "message": f"Generated {len(recommendations)} recommendations.",
                "count": len(recommendations),
            },
            status=status.HTTP_200_OK,
        )


class SimilarBooksView(APIView):
    """Get books similar to a given book."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, book_id):
        from apps.books.models import Book

        try:
            book = Book.objects.get(id=book_id, is_active=True)
        except Book.DoesNotExist:
            return Response(
                {"detail": "Book not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get cached similar books
        similar = SimilarBook.objects.filter(
            book=book
        ).select_related(
            "similar_book__publisher"
        ).prefetch_related(
            "similar_book__authors", "similar_book__genres"
        )

        # Recompute if none cached
        if not similar.exists():
            compute_similar_books(book)
            similar = SimilarBook.objects.filter(book=book).select_related(
                "similar_book__publisher"
            ).prefetch_related(
                "similar_book__authors", "similar_book__genres"
            )

        results = []
        for sb in similar[:10]:
            book_data = BookListSerializer(
                sb.similar_book, context={"request": request}
            ).data
            results.append(
                {
                    "book": book_data,
                    "similarity_score": round(sb.similarity_score, 3),
                }
            )

        return Response({"count": len(results), "results": results})

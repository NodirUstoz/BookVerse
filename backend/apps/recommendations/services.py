"""
Recommendation engine for BookVerse.

Implements multiple recommendation strategies:
1. Content-based filtering (genre, author similarity)
2. Collaborative filtering (users with similar tastes)
3. Popularity-based (trending and highly rated)
4. Hybrid approach combining all signals
"""

import logging
from collections import Counter, defaultdict
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, Q
from django.utils import timezone

from apps.books.models import Book, Genre
from apps.reading.models import ReadingProgress
from apps.reviews.models import Review

from .models import SimilarBook, UserRecommendation

User = get_user_model()
logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Core recommendation engine that combines multiple strategies
    to produce personalized book recommendations.
    """

    # Weight for each recommendation strategy
    WEIGHTS = {
        "genre_match": 0.25,
        "author_match": 0.20,
        "similar_readers": 0.25,
        "reading_history": 0.15,
        "trending": 0.10,
        "high_rated": 0.05,
    }

    def __init__(self, user):
        self.user = user
        self._user_books = None
        self._user_genres = None
        self._user_authors = None

    @property
    def user_book_ids(self) -> set:
        """Get set of book IDs the user has interacted with."""
        if self._user_books is None:
            read_ids = set(
                ReadingProgress.objects.filter(user=self.user)
                .values_list("book_id", flat=True)
            )
            reviewed_ids = set(
                Review.objects.filter(user=self.user)
                .values_list("book_id", flat=True)
            )
            self._user_books = read_ids | reviewed_ids
        return self._user_books

    @property
    def user_genre_ids(self) -> set:
        """Get genres the user has shown preference for."""
        if self._user_genres is None:
            genre_ids = set()

            # From reader profile favorites
            try:
                profile = self.user.reader_profile
                genre_ids.update(
                    profile.favorite_genres.values_list("id", flat=True)
                )
            except Exception:
                pass

            # From reading history (genres of books they read and rated highly)
            high_rated_books = Review.objects.filter(
                user=self.user, rating__gte=4
            ).values_list("book_id", flat=True)

            genre_ids.update(
                Genre.objects.filter(
                    books__id__in=high_rated_books
                ).values_list("id", flat=True)
            )

            # From currently reading
            reading_books = ReadingProgress.objects.filter(
                user=self.user, status="reading"
            ).values_list("book_id", flat=True)

            genre_ids.update(
                Genre.objects.filter(
                    books__id__in=reading_books
                ).values_list("id", flat=True)
            )

            self._user_genres = genre_ids
        return self._user_genres

    @property
    def user_author_ids(self) -> set:
        """Get authors the user has shown preference for."""
        if self._user_authors is None:
            author_ids = set()

            try:
                profile = self.user.reader_profile
                author_ids.update(
                    profile.favorite_authors.values_list("id", flat=True)
                )
            except Exception:
                pass

            # Authors of highly rated books
            high_rated_books = Review.objects.filter(
                user=self.user, rating__gte=4
            ).values_list("book_id", flat=True)

            from apps.books.models import Author

            author_ids.update(
                Author.objects.filter(
                    books__id__in=high_rated_books
                ).values_list("id", flat=True)
            )

            self._user_authors = author_ids
        return self._user_authors

    def get_genre_based_recommendations(self, limit: int = 20) -> List[Tuple[Book, float, str]]:
        """Recommend books based on the user's preferred genres."""
        if not self.user_genre_ids:
            return []

        # Count how many of the user's preferred genres each book matches
        books = (
            Book.objects.filter(
                genres__id__in=self.user_genre_ids,
                is_active=True,
            )
            .exclude(id__in=self.user_book_ids)
            .annotate(genre_overlap=Count("genres", filter=Q(genres__id__in=self.user_genre_ids)))
            .order_by("-genre_overlap", "-average_rating")
            .distinct()[:limit]
        )

        results = []
        max_genres = len(self.user_genre_ids) or 1
        for book in books:
            score = min(book.genre_overlap / max_genres, 1.0)
            matched = ", ".join(
                book.genres.filter(id__in=self.user_genre_ids)
                .values_list("name", flat=True)[:3]
            )
            detail = f"Matches your interest in {matched}"
            results.append((book, score, detail))

        return results

    def get_author_based_recommendations(self, limit: int = 15) -> List[Tuple[Book, float, str]]:
        """Recommend books by authors the user enjoys."""
        if not self.user_author_ids:
            return []

        books = (
            Book.objects.filter(
                authors__id__in=self.user_author_ids,
                is_active=True,
            )
            .exclude(id__in=self.user_book_ids)
            .select_related("publisher")
            .prefetch_related("authors")
            .order_by("-average_rating")
            .distinct()[:limit]
        )

        results = []
        for book in books:
            matching_authors = book.authors.filter(id__in=self.user_author_ids)
            author_names = ", ".join(a.name for a in matching_authors[:2])
            score = 0.9 if matching_authors.count() > 1 else 0.7
            detail = f"By {author_names}, an author you enjoy"
            results.append((book, score, detail))

        return results

    def get_collaborative_recommendations(self, limit: int = 20) -> List[Tuple[Book, float, str]]:
        """
        Collaborative filtering: find users with similar taste
        and recommend books they liked that the current user hasn't read.
        """
        if not self.user_book_ids:
            return []

        # Find users who have read the same books and rated them similarly
        user_reviews = dict(
            Review.objects.filter(user=self.user)
            .values_list("book_id", "rating")
        )

        if not user_reviews:
            return []

        # Find similar users (users who rated the same books similarly)
        similar_users = (
            Review.objects.filter(
                book_id__in=user_reviews.keys(),
                rating__gte=3,
            )
            .exclude(user=self.user)
            .values("user")
            .annotate(
                overlap=Count("id"),
                avg_rating=Avg("rating"),
            )
            .filter(overlap__gte=2)
            .order_by("-overlap")[:50]
        )

        similar_user_ids = [su["user"] for su in similar_users]

        if not similar_user_ids:
            return []

        # Get highly rated books from similar users
        candidate_reviews = (
            Review.objects.filter(
                user_id__in=similar_user_ids,
                rating__gte=4,
                is_approved=True,
            )
            .exclude(book_id__in=self.user_book_ids)
            .values("book_id")
            .annotate(
                recommender_count=Count("user", distinct=True),
                avg_score=Avg("rating"),
            )
            .order_by("-recommender_count", "-avg_score")[:limit]
        )

        book_ids = [cr["book_id"] for cr in candidate_reviews]
        books = Book.objects.filter(id__in=book_ids, is_active=True).in_bulk()
        score_map = {cr["book_id"]: cr for cr in candidate_reviews}

        results = []
        for book_id in book_ids:
            if book_id in books:
                book = books[book_id]
                cr = score_map[book_id]
                score = min(cr["recommender_count"] / 10.0, 1.0)
                detail = (
                    f"Enjoyed by {cr['recommender_count']} readers with similar taste"
                )
                results.append((book, score, detail))

        return results

    def get_trending_recommendations(self, limit: int = 10) -> List[Tuple[Book, float, str]]:
        """Recommend currently trending books."""
        recent_cutoff = timezone.now() - timedelta(days=30)

        trending = (
            Book.objects.filter(
                is_active=True,
                reviews__created_at__gte=recent_cutoff,
            )
            .exclude(id__in=self.user_book_ids)
            .annotate(
                recent_reviews=Count(
                    "reviews",
                    filter=Q(reviews__created_at__gte=recent_cutoff),
                ),
            )
            .filter(recent_reviews__gte=3)
            .order_by("-recent_reviews", "-average_rating")
            .distinct()[:limit]
        )

        results = []
        for book in trending:
            score = min(book.recent_reviews / 20.0, 1.0)
            detail = f"Trending with {book.recent_reviews} recent reviews"
            results.append((book, score, detail))

        return results

    def get_highly_rated_recommendations(self, limit: int = 10) -> List[Tuple[Book, float, str]]:
        """Recommend highly rated books in the user's preferred genres."""
        genre_filter = Q(genres__id__in=self.user_genre_ids) if self.user_genre_ids else Q()

        books = (
            Book.objects.filter(
                genre_filter,
                is_active=True,
                average_rating__gte=4.0,
                rating_count__gte=10,
            )
            .exclude(id__in=self.user_book_ids)
            .order_by("-average_rating", "-rating_count")
            .distinct()[:limit]
        )

        results = []
        for book in books:
            score = float(book.average_rating) / 5.0
            detail = f"Rated {book.average_rating}/5 by {book.rating_count} readers"
            results.append((book, score, detail))

        return results

    def generate_recommendations(self, max_results: int = 30) -> List[UserRecommendation]:
        """
        Generate personalized recommendations by combining all strategies.
        Returns a list of UserRecommendation objects.
        """
        logger.info(f"Generating recommendations for user {self.user.email}")

        # Gather candidates from all strategies
        strategy_results = {
            "genre_match": self.get_genre_based_recommendations(),
            "author_match": self.get_author_based_recommendations(),
            "similar_readers": self.get_collaborative_recommendations(),
            "trending": self.get_trending_recommendations(),
            "high_rated": self.get_highly_rated_recommendations(),
        }

        # Combine scores using weighted approach
        book_scores: Dict[str, Dict] = {}

        for strategy, results in strategy_results.items():
            weight = self.WEIGHTS.get(strategy, 0.1)
            for book, raw_score, detail in results:
                book_id = str(book.id)
                if book_id not in book_scores:
                    book_scores[book_id] = {
                        "book": book,
                        "total_score": 0.0,
                        "reasons": [],
                        "best_reason": strategy,
                        "best_detail": detail,
                        "best_score": 0.0,
                    }

                weighted_score = raw_score * weight
                book_scores[book_id]["total_score"] += weighted_score

                if weighted_score > book_scores[book_id]["best_score"]:
                    book_scores[book_id]["best_score"] = weighted_score
                    book_scores[book_id]["best_reason"] = strategy
                    book_scores[book_id]["best_detail"] = detail

        # Sort by total score and take top results
        sorted_books = sorted(
            book_scores.values(),
            key=lambda x: x["total_score"],
            reverse=True,
        )[:max_results]

        # Clear old recommendations
        UserRecommendation.objects.filter(user=self.user).delete()

        # Create new recommendations
        recommendations = []
        expires_at = timezone.now() + timedelta(days=7)

        for entry in sorted_books:
            rec = UserRecommendation(
                user=self.user,
                book=entry["book"],
                score=min(entry["total_score"], 1.0),
                reason=entry["best_reason"],
                reason_detail=entry["best_detail"],
                expires_at=expires_at,
            )
            recommendations.append(rec)

        UserRecommendation.objects.bulk_create(recommendations)

        logger.info(
            f"Generated {len(recommendations)} recommendations for {self.user.email}"
        )
        return recommendations


def compute_similar_books(book: Book, limit: int = 10):
    """
    Compute and cache similar books based on genre overlap,
    author overlap, and rating patterns.
    """
    # Genre overlap
    book_genre_ids = set(book.genres.values_list("id", flat=True))
    book_author_ids = set(book.authors.values_list("id", flat=True))

    candidates = (
        Book.objects.filter(is_active=True)
        .exclude(id=book.id)
        .annotate(
            genre_overlap=Count(
                "genres", filter=Q(genres__id__in=book_genre_ids)
            ),
            author_overlap=Count(
                "authors", filter=Q(authors__id__in=book_author_ids)
            ),
        )
        .filter(Q(genre_overlap__gte=1) | Q(author_overlap__gte=1))
        .order_by("-author_overlap", "-genre_overlap", "-average_rating")
        .distinct()[:limit * 2]
    )

    total_genres = len(book_genre_ids) or 1
    total_authors = len(book_author_ids) or 1

    scored = []
    for candidate in candidates:
        genre_sim = candidate.genre_overlap / total_genres * 0.6
        author_sim = candidate.author_overlap / total_authors * 0.4
        score = min(genre_sim + author_sim, 1.0)
        scored.append((candidate, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:limit]

    # Persist
    SimilarBook.objects.filter(book=book).delete()
    similar_objects = [
        SimilarBook(
            book=book,
            similar_book=candidate,
            similarity_score=score,
        )
        for candidate, score in scored
    ]
    SimilarBook.objects.bulk_create(similar_objects)

    return similar_objects


def generate_recommendations_for_user(user) -> List[UserRecommendation]:
    """Convenience function to generate recommendations for a single user."""
    engine = RecommendationEngine(user)
    return engine.generate_recommendations()

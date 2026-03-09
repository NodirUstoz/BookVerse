"""
Serializers for reviews app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserPublicSerializer

from .models import Review, ReviewVote

User = get_user_model()


class ReviewSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    helpfulness_score = serializers.ReadOnlyField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "book",
            "rating",
            "title",
            "content",
            "contains_spoilers",
            "is_verified_purchase",
            "helpful_count",
            "not_helpful_count",
            "helpfulness_score",
            "user_vote",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "is_verified_purchase",
            "helpful_count",
            "not_helpful_count",
            "created_at",
            "updated_at",
        ]

    def get_user_vote(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                vote = ReviewVote.objects.get(user=request.user, review=obj)
                return "helpful" if vote.is_helpful else "not_helpful"
            except ReviewVote.DoesNotExist:
                pass
        return None


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "book",
            "rating",
            "title",
            "content",
            "contains_spoilers",
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        book = attrs.get("book")
        if Review.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError(
                {"book": "You have already reviewed this book."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "rating",
            "title",
            "content",
            "contains_spoilers",
        ]


class ReviewVoteSerializer(serializers.Serializer):
    is_helpful = serializers.BooleanField()

    def create(self, validated_data):
        user = self.context["request"].user
        review = self.context["review"]

        vote, created = ReviewVote.objects.update_or_create(
            user=user,
            review=review,
            defaults={"is_helpful": validated_data["is_helpful"]},
        )
        return vote


class ReviewStatsSerializer(serializers.Serializer):
    """Aggregated review statistics for a book."""

    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    rating_distribution = serializers.DictField()
    verified_purchase_count = serializers.IntegerField()

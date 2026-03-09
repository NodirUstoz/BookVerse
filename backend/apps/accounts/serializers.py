"""
Serializers for accounts app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ReaderProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer for profile views."""

    full_name = serializers.ReadOnlyField()
    reader_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "date_of_birth",
            "phone_number",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_verified",
            "date_joined",
            "reader_profile",
        ]
        read_only_fields = ["id", "email", "is_verified", "date_joined"]

    def get_reader_profile(self, obj):
        try:
            profile = obj.reader_profile
            return ReaderProfileSerializer(profile).data
        except ReaderProfile.DoesNotExist:
            return None


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        ReaderProfile.objects.create(user=user)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "avatar",
            "date_of_birth",
            "phone_number",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
        ]


class UserPublicSerializer(serializers.ModelSerializer):
    """Minimal user serializer for public display (reviews, clubs, etc.)."""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ["id", "full_name", "avatar", "date_joined"]


class ReaderProfileSerializer(serializers.ModelSerializer):
    """Serializer for reader profile."""

    favorite_genres = serializers.StringRelatedField(many=True, read_only=True)
    favorite_authors = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = ReaderProfile
        fields = [
            "bio",
            "favorite_genres",
            "favorite_authors",
            "reading_goal_count",
            "reading_goal_frequency",
            "is_public",
            "goodreads_url",
            "website",
            "total_books_read",
            "total_pages_read",
            "total_reviews",
            "average_rating_given",
        ]
        read_only_fields = [
            "total_books_read",
            "total_pages_read",
            "total_reviews",
            "average_rating_given",
        ]


class ReaderProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating reader profile details."""

    favorite_genre_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    favorite_author_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = ReaderProfile
        fields = [
            "bio",
            "reading_goal_count",
            "reading_goal_frequency",
            "is_public",
            "goodreads_url",
            "website",
            "favorite_genre_ids",
            "favorite_author_ids",
        ]

    def update(self, instance, validated_data):
        genre_ids = validated_data.pop("favorite_genre_ids", None)
        author_ids = validated_data.pop("favorite_author_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if genre_ids is not None:
            from apps.books.models import Genre

            instance.favorite_genres.set(
                Genre.objects.filter(id__in=genre_ids)
            )

        if author_ids is not None:
            from apps.books.models import Author

            instance.favorite_authors.set(
                Author.objects.filter(id__in=author_ids)
            )

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

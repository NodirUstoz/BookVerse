"""
Serializers for reading app.
"""

from rest_framework import serializers

from apps.accounts.serializers import UserPublicSerializer
from apps.books.serializers import BookListSerializer

from .models import (
    BookClub,
    BookClubMember,
    ReadingList,
    ReadingListEntry,
    ReadingProgress,
)


class ReadingListEntrySerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)

    class Meta:
        model = ReadingListEntry
        fields = ["id", "book", "notes", "display_order", "added_at"]


class ReadingListSerializer(serializers.ModelSerializer):
    entries = ReadingListEntrySerializer(many=True, read_only=True)
    book_count = serializers.ReadOnlyField()

    class Meta:
        model = ReadingList
        fields = [
            "id",
            "name",
            "description",
            "list_type",
            "visibility",
            "is_default",
            "book_count",
            "entries",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_default", "created_at", "updated_at"]


class ReadingListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingList
        fields = ["name", "description", "list_type", "visibility"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class AddBookToListSerializer(serializers.Serializer):
    book_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, default="")

    def validate_book_id(self, value):
        from apps.books.models import Book

        if not Book.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Book not found.")
        return value


class ReadingProgressSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = ReadingProgress
        fields = [
            "id",
            "book",
            "status",
            "status_display",
            "current_page",
            "percentage",
            "started_at",
            "finished_at",
            "last_read_at",
            "notes",
            "rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "started_at",
            "finished_at",
            "last_read_at",
            "created_at",
            "updated_at",
        ]


class ReadingProgressCreateSerializer(serializers.Serializer):
    book_id = serializers.UUIDField()
    current_page = serializers.IntegerField(min_value=0, required=False)
    percentage = serializers.FloatField(min_value=0, max_value=100, required=False)
    notes = serializers.CharField(required=False, default="")

    def validate_book_id(self, value):
        from apps.books.models import Book

        if not Book.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Book not found.")
        return value

    def validate(self, attrs):
        if "current_page" not in attrs and "percentage" not in attrs:
            raise serializers.ValidationError(
                "Either current_page or percentage must be provided."
            )
        return attrs


class ReadingProgressUpdateSerializer(serializers.Serializer):
    current_page = serializers.IntegerField(min_value=0, required=False)
    percentage = serializers.FloatField(min_value=0, max_value=100, required=False)
    status = serializers.ChoiceField(
        choices=ReadingProgress.STATUS_CHOICES, required=False
    )
    notes = serializers.CharField(required=False)
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)


class BookClubMemberSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    role_display = serializers.CharField(
        source="get_role_display", read_only=True
    )

    class Meta:
        model = BookClubMember
        fields = ["id", "user", "role", "role_display", "is_active", "joined_at"]


class BookClubSerializer(serializers.ModelSerializer):
    member_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    current_book = BookListSerializer(read_only=True)
    created_by = UserPublicSerializer(read_only=True)
    user_membership = serializers.SerializerMethodField()

    class Meta:
        model = BookClub
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "cover_image",
            "privacy",
            "max_members",
            "current_book",
            "reading_deadline",
            "member_count",
            "is_full",
            "created_by",
            "is_active",
            "user_membership",
            "created_at",
        ]

    def get_user_membership(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                membership = BookClubMember.objects.get(
                    club=obj, user=request.user, is_active=True
                )
                return BookClubMemberSerializer(membership).data
            except BookClubMember.DoesNotExist:
                pass
        return None


class BookClubDetailSerializer(BookClubSerializer):
    members = serializers.SerializerMethodField()
    past_books = BookListSerializer(many=True, read_only=True)

    class Meta(BookClubSerializer.Meta):
        fields = BookClubSerializer.Meta.fields + ["members", "past_books"]

    def get_members(self, obj):
        memberships = obj.memberships.filter(is_active=True).select_related("user")
        return BookClubMemberSerializer(memberships, many=True).data


class BookClubCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookClub
        fields = [
            "name",
            "slug",
            "description",
            "cover_image",
            "privacy",
            "max_members",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user
        club = super().create(validated_data)
        BookClubMember.objects.create(club=club, user=user, role="owner")
        return club

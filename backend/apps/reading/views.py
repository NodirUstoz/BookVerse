"""
Views for reading app.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.books.models import Book

from .models import (
    BookClub,
    BookClubMember,
    ReadingList,
    ReadingListEntry,
    ReadingProgress,
)
from .serializers import (
    AddBookToListSerializer,
    BookClubCreateSerializer,
    BookClubDetailSerializer,
    BookClubSerializer,
    ReadingListCreateSerializer,
    ReadingListSerializer,
    ReadingProgressCreateSerializer,
    ReadingProgressSerializer,
    ReadingProgressUpdateSerializer,
)


class ReadingListViewSet(viewsets.ModelViewSet):
    """Manage reading lists."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ReadingListCreateSerializer
        return ReadingListSerializer

    def get_queryset(self):
        return ReadingList.objects.filter(
            user=self.request.user
        ).prefetch_related("entries__book__authors", "entries__book__genres")

    def perform_destroy(self, instance):
        if instance.is_default:
            return Response(
                {"detail": "Default lists cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()

    @action(detail=True, methods=["post"])
    def add_book(self, request, pk=None):
        """Add a book to a reading list."""
        reading_list = self.get_object()
        serializer = AddBookToListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = Book.objects.get(id=serializer.validated_data["book_id"])

        entry, created = ReadingListEntry.objects.get_or_create(
            reading_list=reading_list,
            book=book,
            defaults={"notes": serializer.validated_data.get("notes", "")},
        )

        if not created:
            return Response(
                {"detail": "Book is already in this list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": f"'{book.title}' added to '{reading_list.name}'."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path="remove-book/(?P<book_id>[^/.]+)")
    def remove_book(self, request, pk=None, book_id=None):
        """Remove a book from a reading list."""
        reading_list = self.get_object()
        try:
            entry = ReadingListEntry.objects.get(
                reading_list=reading_list, book_id=book_id
            )
            entry.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ReadingListEntry.DoesNotExist:
            return Response(
                {"detail": "Book not found in this list."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ReadingProgressListView(generics.ListAPIView):
    """List reading progress for the authenticated user."""

    serializer_class = ReadingProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ReadingProgress.objects.filter(
            user=self.request.user
        ).select_related("book").prefetch_related("book__authors")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class ReadingProgressCreateUpdateView(APIView):
    """Create or update reading progress for a book."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ReadingProgressCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = Book.objects.get(id=serializer.validated_data["book_id"])

        progress, created = ReadingProgress.objects.get_or_create(
            user=request.user,
            book=book,
        )

        current_page = serializer.validated_data.get("current_page")
        percentage = serializer.validated_data.get("percentage")
        notes = serializer.validated_data.get("notes", "")

        if notes:
            progress.notes = notes

        progress.update_progress(current_page=current_page, percentage=percentage)

        result_serializer = ReadingProgressSerializer(
            progress, context={"request": request}
        )
        return Response(
            result_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def patch(self, request):
        """Update existing progress."""
        book_id = request.data.get("book_id")
        if not book_id:
            return Response(
                {"detail": "book_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            progress = ReadingProgress.objects.get(
                user=request.user, book_id=book_id
            )
        except ReadingProgress.DoesNotExist:
            return Response(
                {"detail": "No reading progress found for this book."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ReadingProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if "status" in data:
            progress.status = data["status"]
        if "notes" in data:
            progress.notes = data["notes"]
        if "rating" in data:
            progress.rating = data["rating"]

        current_page = data.get("current_page")
        percentage = data.get("percentage")

        if current_page is not None or percentage is not None:
            progress.update_progress(current_page=current_page, percentage=percentage)
        else:
            progress.save()

        result_serializer = ReadingProgressSerializer(
            progress, context={"request": request}
        )
        return Response(result_serializer.data)


class BookClubViewSet(viewsets.ModelViewSet):
    """Manage book clubs."""

    lookup_field = "slug"
    search_fields = ["name", "description"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return BookClubCreateSerializer
        if self.action == "retrieve":
            return BookClubDetailSerializer
        return BookClubSerializer

    def get_queryset(self):
        queryset = BookClub.objects.filter(is_active=True).select_related(
            "current_book", "created_by"
        )

        if self.action == "list":
            # Show public clubs and clubs the user is a member of
            if self.request.user.is_authenticated:
                from django.db.models import Q

                queryset = queryset.filter(
                    Q(privacy="public")
                    | Q(memberships__user=self.request.user, memberships__is_active=True)
                ).distinct()
            else:
                queryset = queryset.filter(privacy="public")

        return queryset

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        club = self.get_object()
        membership = BookClubMember.objects.filter(
            club=club, user=self.request.user, role__in=["owner", "admin"]
        )
        if not membership.exists() and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only club owners and admins can edit the club.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def join(self, request, slug=None):
        """Join a book club."""
        club = self.get_object()

        if club.is_full:
            return Response(
                {"detail": "This book club is full."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if club.privacy == "private":
            return Response(
                {"detail": "This is a private club."},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership, created = BookClubMember.objects.get_or_create(
            club=club,
            user=request.user,
            defaults={"role": "member"},
        )

        if not created:
            if membership.is_active:
                return Response(
                    {"detail": "You are already a member of this club."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            membership.is_active = True
            membership.save(update_fields=["is_active"])

        return Response(
            {"message": f"You have joined '{club.name}'."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def leave(self, request, slug=None):
        """Leave a book club."""
        club = self.get_object()
        try:
            membership = BookClubMember.objects.get(
                club=club, user=request.user, is_active=True
            )
        except BookClubMember.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this club."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if membership.role == "owner":
            return Response(
                {"detail": "Owners cannot leave. Transfer ownership first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.is_active = False
        membership.save(update_fields=["is_active"])

        return Response(
            {"message": f"You have left '{club.name}'."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="set-book")
    def set_current_book(self, request, slug=None):
        """Set the club's current book (owner/admin only)."""
        club = self.get_object()

        if not BookClubMember.objects.filter(
            club=club, user=request.user, role__in=["owner", "admin"], is_active=True
        ).exists():
            return Response(
                {"detail": "Only owners and admins can set the current book."},
                status=status.HTTP_403_FORBIDDEN,
            )

        book_id = request.data.get("book_id")
        deadline = request.data.get("deadline")

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

        # Archive current book
        if club.current_book:
            club.past_books.add(club.current_book)

        club.current_book = book
        if deadline:
            club.reading_deadline = deadline
        club.save()

        return Response(
            {"message": f"Current book set to '{book.title}'."},
            status=status.HTTP_200_OK,
        )

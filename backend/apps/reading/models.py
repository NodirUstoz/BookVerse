"""
Reading models: ReadingList, ReadingProgress, BookClub, BookClubMember.
Tracks reading activity and manages book clubs.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class ReadingList(models.Model):
    """Custom reading list created by a user."""

    LIST_TYPE_CHOICES = [
        ("want_to_read", "Want to Read"),
        ("currently_reading", "Currently Reading"),
        ("finished", "Finished"),
        ("did_not_finish", "Did Not Finish"),
        ("custom", "Custom"),
    ]

    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("friends", "Friends Only"),
        ("private", "Private"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_lists",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    list_type = models.CharField(
        max_length=20, choices=LIST_TYPE_CHOICES, default="custom"
    )
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="public"
    )
    books = models.ManyToManyField(
        "books.Book",
        through="ReadingListEntry",
        related_name="reading_lists",
        blank=True,
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default system lists (Want to Read, etc.) cannot be deleted.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reading_lists"
        ordering = ["list_type", "name"]
        verbose_name = "Reading List"
        verbose_name_plural = "Reading Lists"

    def __str__(self):
        return f"{self.user.full_name}: {self.name}"

    @property
    def book_count(self):
        return self.entries.count()


class ReadingListEntry(models.Model):
    """An entry linking a book to a reading list with metadata."""

    reading_list = models.ForeignKey(
        ReadingList, on_delete=models.CASCADE, related_name="entries"
    )
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="reading_list_entries"
    )
    notes = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reading_list_entries"
        ordering = ["display_order", "-added_at"]
        unique_together = ["reading_list", "book"]
        verbose_name = "Reading List Entry"
        verbose_name_plural = "Reading List Entries"

    def __str__(self):
        return f"{self.book.title} in {self.reading_list.name}"


class ReadingProgress(models.Model):
    """Track reading progress for a specific book."""

    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("reading", "Currently Reading"),
        ("on_hold", "On Hold"),
        ("finished", "Finished"),
        ("dnf", "Did Not Finish"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_progress",
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="reader_progress",
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="not_started"
    )
    current_page = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    last_read_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Quick rating upon finishing.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reading_progress"
        ordering = ["-updated_at"]
        verbose_name = "Reading Progress"
        verbose_name_plural = "Reading Progress"
        unique_together = ["user", "book"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "-last_read_at"]),
        ]

    def __str__(self):
        return f"{self.user.full_name} reading {self.book.title}: {self.percentage:.0f}%"

    def update_progress(self, current_page=None, percentage=None):
        """Update reading progress, auto-calculating percentage from pages."""
        if current_page is not None:
            self.current_page = current_page
            if self.book.page_count and self.book.page_count > 0:
                self.percentage = min(
                    (current_page / self.book.page_count) * 100, 100.0
                )
        elif percentage is not None:
            self.percentage = min(percentage, 100.0)
            if self.book.page_count:
                self.current_page = int(
                    self.book.page_count * (percentage / 100)
                )

        self.last_read_at = timezone.now()

        if self.status == "not_started" and self.percentage > 0:
            self.status = "reading"
            if not self.started_at:
                self.started_at = timezone.now()

        if self.percentage >= 100:
            self.status = "finished"
            self.percentage = 100.0
            if not self.finished_at:
                self.finished_at = timezone.now()

        self.save()


class BookClub(models.Model):
    """Book club for group reading and discussions."""

    PRIVACY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
        ("invite_only", "Invite Only"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to="clubs/%Y/%m/", blank=True, null=True
    )
    privacy = models.CharField(
        max_length=15, choices=PRIVACY_CHOICES, default="public"
    )
    max_members = models.PositiveIntegerField(default=50)

    # Current reading
    current_book = models.ForeignKey(
        "books.Book",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_clubs",
    )
    reading_deadline = models.DateField(blank=True, null=True)

    # Previously read books
    past_books = models.ManyToManyField(
        "books.Book",
        blank=True,
        related_name="past_clubs",
    )

    # Management
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_clubs",
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "book_clubs"
        ordering = ["-created_at"]
        verbose_name = "Book Club"
        verbose_name_plural = "Book Clubs"

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()

    @property
    def is_full(self):
        return self.member_count >= self.max_members


class BookClubMember(models.Model):
    """Membership in a book club."""

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("moderator", "Moderator"),
        ("member", "Member"),
    ]

    club = models.ForeignKey(
        BookClub, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="club_memberships",
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "book_club_members"
        unique_together = ["club", "user"]
        verbose_name = "Book Club Member"
        verbose_name_plural = "Book Club Members"

    def __str__(self):
        return f"{self.user.full_name} in {self.club.name} ({self.get_role_display()})"

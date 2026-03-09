"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ReaderProfile

User = get_user_model()


class ReaderProfileInline(admin.StackedInline):
    model = ReaderProfile
    can_delete = False
    verbose_name_plural = "Reader Profile"
    fk_name = "user"
    fields = (
        "bio",
        "reading_goal_count",
        "reading_goal_frequency",
        "is_public",
        "total_books_read",
        "total_pages_read",
        "total_reviews",
        "average_rating_given",
    )
    readonly_fields = (
        "total_books_read",
        "total_pages_read",
        "total_reviews",
        "average_rating_given",
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_verified",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_verified", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    inlines = [ReaderProfileInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "avatar",
                    "date_of_birth",
                    "phone_number",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(ReaderProfile)
class ReaderProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_books_read",
        "total_reviews",
        "reading_goal_count",
        "is_public",
    )
    list_filter = ("is_public", "reading_goal_frequency")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = (
        "total_books_read",
        "total_pages_read",
        "total_reviews",
        "average_rating_given",
    )

"""
Views for accounts app.
"""

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReaderProfile
from .serializers import (
    ChangePasswordSerializer,
    ReaderProfileSerializer,
    ReaderProfileUpdateSerializer,
    UserCreateSerializer,
    UserPublicSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""

    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Account created successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class PublicProfileView(generics.RetrieveAPIView):
    """Retrieve a public user profile by ID."""

    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.filter(is_active=True)
    lookup_field = "id"


class ReaderProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's reader profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ReaderProfileUpdateSerializer
        return ReaderProfileSerializer

    def get_object(self):
        profile, _ = ReaderProfile.objects.get_or_create(user=self.request.user)
        return profile


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class ReadingStatsView(APIView):
    """Get the authenticated user's reading statistics."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = ReaderProfile.objects.get_or_create(user=request.user)
        profile.update_statistics()
        return Response(
            {
                "total_books_read": profile.total_books_read,
                "total_pages_read": profile.total_pages_read,
                "total_reviews": profile.total_reviews,
                "average_rating_given": float(profile.average_rating_given),
                "reading_goal_count": profile.reading_goal_count,
                "reading_goal_frequency": profile.reading_goal_frequency,
            }
        )


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_account(request):
    """Soft-delete the authenticated user's account."""
    user = request.user
    user.is_active = False
    user.save()
    return Response(
        {"message": "Account deactivated successfully."},
        status=status.HTTP_200_OK,
    )

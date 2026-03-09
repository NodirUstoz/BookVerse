from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework import permissions, status
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """Standard pagination with configurable page size."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })


class LargePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ServiceException(APIException):
    """Base exception for service layer errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A service error occurred.'
    default_code = 'service_error'


class NotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested resource was not found.'
    default_code = 'not_found'


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A conflict occurred with the current state.'
    default_code = 'conflict'


class ForbiddenException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'forbidden'


class IsOwner(permissions.BasePermission):
    """Only allow owners of an object to access it."""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow full access to admin, read-only for others."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow access to the owner or admin users."""
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


def validate_file_size(file, max_size_mb=10):
    """Validate uploaded file size."""
    max_bytes = max_size_mb * 1024 * 1024
    if file.size > max_bytes:
        raise DjangoValidationError(f'File size must be under {max_size_mb}MB. Got {file.size / (1024*1024):.1f}MB.')


def validate_file_extension(file, allowed_extensions=None):
    """Validate uploaded file extension."""
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'csv']
    ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
    if ext not in allowed_extensions:
        raise DjangoValidationError(f'File type .{ext} is not allowed. Allowed: {", ".join(allowed_extensions)}')


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def success_response(data=None, message='Success', status_code=status.HTTP_200_OK):
    """Standard success response."""
    response = {'status': 'success', 'message': message}
    if data is not None:
        response['data'] = data
    return Response(response, status=status_code)


def error_response(message='An error occurred', errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """Standard error response."""
    response = {'status': 'error', 'message': message}
    if errors:
        response['errors'] = errors
    return Response(response, status=status_code)

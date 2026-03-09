"""
Production settings for BookVerse.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug
# =============================================================================

DEBUG = False

# =============================================================================
# Security
# =============================================================================

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

X_FRAME_OPTIONS = "DENY"

# =============================================================================
# Static Files (WhiteNoise + S3)
# =============================================================================

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Uncomment below for S3 media storage
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")  # noqa: F405
# AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")  # noqa: F405
# AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")  # noqa: F405
# AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")  # noqa: F405
# AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
# AWS_DEFAULT_ACL = None
# AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
# AWS_QUERYSTRING_AUTH = False

# =============================================================================
# Email (Real SMTP in production)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# =============================================================================
# CORS (Strict in production)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS is set from .env via base settings

# =============================================================================
# Caching (Redis with longer timeouts)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,  # noqa: F405
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        },
        "KEY_PREFIX": "bookverse_prod",
        "TIMEOUT": 60 * 60,  # 1 hour
    }
}

# =============================================================================
# Logging (Production-grade)
# =============================================================================

LOGGING["handlers"]["file"]["level"] = "WARNING"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "WARNING"  # noqa: F405

# =============================================================================
# Sentry (Error Tracking)
# =============================================================================

SENTRY_DSN = config("SENTRY_DSN", default="")  # noqa: F405

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production",
    )

# =============================================================================
# Elasticsearch
# =============================================================================

ELASTICSEARCH_DSL_AUTOSYNC = True

# =============================================================================
# REST Framework (Tighter throttling, no browsable API)
# =============================================================================

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
)

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "50/hour",
    "user": "500/hour",
}

# =============================================================================
# Admin
# =============================================================================

ADMIN_URL = config("DJANGO_ADMIN_URL", default="admin/")  # noqa: F405

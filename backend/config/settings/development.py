"""
Development settings for BookVerse.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug
# =============================================================================

DEBUG = True

# =============================================================================
# Installed Apps (Development extras)
# =============================================================================

INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

# =============================================================================
# Middleware (Development extras)
# =============================================================================

MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.common.CommonMiddleware"),  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

# =============================================================================
# Debug Toolbar
# =============================================================================

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
]

# Docker-compatible internal IPs
import socket

try:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]
except socket.gaierror:
    pass

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# =============================================================================
# Email (Console backend for development)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# CORS (Allow all in development)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# Caching (Local memory for development)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,  # noqa: F405
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "bookverse_dev",
        "TIMEOUT": 60 * 5,
    }
}

# =============================================================================
# Logging (More verbose in development)
# =============================================================================

LOGGING["loggers"]["django.db.backends"] = {  # noqa: F405
    "handlers": ["console"],
    "level": "WARNING",
    "propagate": False,
}

# =============================================================================
# Static files (simplified for dev)
# =============================================================================

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# =============================================================================
# Throttling (Relaxed for development)
# =============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/hour",
    "user": "10000/hour",
}

# =============================================================================
# Elasticsearch (optional in development)
# =============================================================================

ELASTICSEARCH_DSL_AUTOSYNC = False

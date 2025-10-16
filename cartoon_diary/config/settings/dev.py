"""Development settings."""

from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Enable django-extensions only if installed to avoid import errors
try:  # pragma: no cover - convenience for local dev
    import django_extensions  # type: ignore
except Exception:
    django_extensions = None

if django_extensions:  # type: ignore[truthy-bool]
    INSTALLED_APPS += ["django_extensions"]  # type: ignore[name-defined]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

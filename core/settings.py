"""
Django settings for the Deadline Tracker project.

This configuration is intentionally concise and selfâ€‘documenting to make it
easy to understand and adapt.  For production, override sensitive values such
as the secret key and email credentials via environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path
from celery.schedules import crontab

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

###############################################################################
# General settings
###############################################################################

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "replaceâ€‘meâ€‘withâ€‘aâ€‘randomâ€‘string")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in {"true", "1", "yes"}

ALLOWED_HOSTS: list[str] = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "*").split(",") if host.strip()]

###############################################################################
# Application definition
###############################################################################

INSTALLED_APPS = [
    'deadlines.apps.DeadlinesConfig',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "deadlines.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "deadlines.wsgi.application"

###############################################################################
# Database configuration
###############################################################################

DATABASES: dict[str, dict[str, str]] = {
    "default": {
        "ENGINE": os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DJANGO_DB_NAME", str(BASE_DIR / "db.sqlite3")),
        # Additional database settings (USER, PASSWORD, HOST, PORT) can be
        # configured via environment variables for PostgreSQL deployments.
    }
}

###############################################################################
# Internationalisation
###############################################################################

LANGUAGE_CODE = "en-us"

# Use Africa/Windhoek as the default timezone for both display and Celery
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Africa/Windhoek")

USE_I18N = True
USE_L10N = True
USE_TZ = True

###############################################################################
# Static and media files
###############################################################################

# URL to use when referring to static files located in STATIC_ROOT
STATIC_URL = "/static/"

# The directory from which static files should be served in production
STATIC_ROOT = os.environ.get("STATIC_ROOT", str(BASE_DIR / "staticfiles"))

# Media files (used for attachments)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))

###############################################################################
# Email configuration
###############################################################################

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "deadlines@example.com")
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False").lower() in {"true", "1", "yes"}
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() in {"true", "1", "yes"}

###############################################################################
# Celery configuration
###############################################################################

# Broker and backend for Celery.  When deploying to production you should
# set REDIS_URL to something like ``redis://:password@hostname:6379/0``.
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TIMEZONE = TIME_ZONE

# Schedule periodic tasks using Celery Beat.  The send_due_reminders task
# runs every minute to check for reminders that should be dispatched.
CELERY_BEAT_SCHEDULE = {
    "send-due-reminders-every-minute": {
        "task": "core.tasks.send_due_reminders",
        "schedule": crontab(minute="*"),
    },
    # Daily digest summarising today and the next three days (disabled by default
    # until digest emails are implemented in views or tasks).  Uncomment and set
    # an appropriate time of day to enable.
    # "send-daily-digest": {
    #     "task": "core.tasks.send_daily_digest",
    #     "schedule": crontab(hour=3, minute=5),
    # },
}

###############################################################################
# Logging configuration
###############################################################################

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}

"""
WSGI config for the Deadline Tracker project.

This module contains the WSGI application used by Django's deployment
utilities and by WSGI servers such as Gunicorn.  It exposes a module‑level
variable called ``application`` that is used to serve your Django application.
"""
from __future__ import annotations

import os
from django.core.wsgi import get_wsgi_application


# Set the default settings module for the 'deadlines' project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deadlines.settings")

application = get_wsgi_application()
"""
URL configuration for the Deadline Tracker project.

This module defines the URL patterns for the application.  By default it
includes the Django admin interface.  You can extend this file with
additional routes as you build out custom views or APIs.
"""
from __future__ import annotations

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    # Include additional URL patterns from applications here.  For example:
    # path("api/", include("api.urls")),
]

if settings.DEBUG:
    # In development serve media files through Django.  In production you
    # should configure your web server (e.g. Nginx) to handle this.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
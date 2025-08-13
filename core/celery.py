"""
Celery configuration module for the Deadline Tracker project.

This file creates the Celery application and configures it from Django's
settings module.  Celery workers use this application to discover and
execute tasks defined within the project.  It should be imported in the
``__init__.py`` of the ``deadlines`` package so that tasks are registered
when Django starts.
"""
from __future__ import annotations

import os
from celery import Celery

# Set default Django settings module so that Celery can read configuration
os.environ.setdefault("DJANGO_SETTINGS_MODULE","core.settings")

app = Celery("deadlines")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self, *args, **kwargs) -> None:
    """A simple debug task that prints its request.  Use for testing only."""
    print(f"Request: {self.request!r}")

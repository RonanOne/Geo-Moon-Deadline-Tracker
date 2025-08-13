"""
The deadlines package initialises Celery and exposes the Celery application for
autodiscovery of tasks.  Importing this module ensures that shared tasks
within the project are registered when Django starts up.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
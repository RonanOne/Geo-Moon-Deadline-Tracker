#!/usr/bin/env python
"""
This script functions as the commandâ€‘line entry point for the Django application.

It sets the default settings module to `deadlines.settings` and then delegates
execution to Djangoâ€™s management command system.  You can use it to run
migrations, start the development server or invoke custom commands such as the
CSV import.
"""
import os
import sys


def main() -> None:
    """Entrypoint for Django management commands."""
    # Set the default settings module for Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deadlines.settings")
    try:
        from django.core.management import execute_from_command_line  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your "
            "PYTHONPATH environment variable? Did you forget to activate a virtual "
            "environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

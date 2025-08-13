"""
Management command to import deadlines from a CSV file.

The CSV is expected to have the following columns:

```
title,description,due_at,reminders_minutes_before,labels
```

* ``title`` – Required.  A short name for the event.
* ``description`` – Optional.  A longer description of the event.
* ``due_at`` – Required.  The due date and time in ``YYYY-MM-DD HH:MM`` format.
* ``reminders_minutes_before`` – Optional.  A comma-separated list of integers
  specifying how many minutes before the due date each reminder should be sent
  (e.g. ``1440,120,30`` for reminders at 24 hours, 2 hours and 30 minutes before).
* ``labels`` – Optional.  A semicolon-separated list of labels (e.g.
  ``Vacancy;Work``).  Any labels that do not already exist for the user will
  be created automatically.

Usage:

```
python manage.py import_deadlines user_email /path/to/file.csv
```

The command performs a dry run and reports any errors before creating records.
"""
from __future__ import annotations

import csv
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from dateutil import parser
from typing import Iterable, List
from core.models import Event, Reminder, Label


class Command(BaseCommand):
    help = (
        "Import deadlines from a CSV file.  Columns: title, description, "
        "due_at (YYYY-MM-DD HH:MM), reminders_minutes_before (e.g. '1440,60'), "
        "labels (e.g. 'Vacancy;Work')."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "user_email",
            help="Email address of the user who will own the imported events",
        )
        parser.add_argument(
            "csv_path",
            help="Path to the CSV file containing the events to import",
        )

    def handle(self, *args, **opts) -> None:
        User = get_user_model()
        try:
            user = User.objects.get(email=opts["user_email"])
        except User.DoesNotExist:
            raise CommandError(f"No user found with email {opts['user_email']}")
        csv_path: str = opts["csv_path"]
        created = 0
        errors: List[str] = []
        events_to_create: List[tuple] = []  # Hold parsed data before commit
        # Read and parse the CSV
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):  # start=2 for header row
                title = (row.get("title") or "").strip()
                if not title:
                    errors.append(f"Row {idx}: missing title")
                    continue
                description = (row.get("description") or "").strip()
                due_raw = (row.get("due_at") or "").strip()
                try:
                    due_dt = parser.parse(due_raw)
                    due = timezone.make_aware(due_dt) if timezone.is_naive(due_dt) else due_dt
                except Exception as exc:
                    errors.append(f"Row {idx}: invalid due_at '{due_raw}' ({exc})")
                    continue
                # Parse reminder offsets
                offsets_raw = (row.get("reminders_minutes_before") or "").strip()
                offsets: List[int] = []
                if offsets_raw:
                    try:
                        offsets = [int(val.strip()) for val in offsets_raw.split(",") if val.strip()]
                    except ValueError as exc:
                        errors.append(f"Row {idx}: invalid reminders_minutes_before '{offsets_raw}' ({exc})")
                        continue
                # Parse labels and ensure they exist
                labels_raw = (row.get("labels") or "").strip()
                label_names: List[str] = []
                if labels_raw:
                    label_names = [name.strip() for name in labels_raw.split(";") if name.strip()]
                events_to_create.append((title, description, due, offsets, label_names))
        # Report errors if any
        if errors:
            for err in errors:
                self.stderr.write(self.style.ERROR(err))
            raise CommandError("Aborting import due to errors.")
        # Create events and associated objects
        for title, description, due, offsets, label_names in events_to_create:
            event = Event.objects.create(
                user=user,
                title=title,
                description=description,
                due_at=due,
            )
            # Ensure labels exist and assign them
            for name in label_names:
                label, _ = Label.objects.get_or_create(user=user, name=name)
                event.labels.add(label)
            # Create reminders
            for minutes in offsets:
                Reminder.objects.create(
                    event=event,
                    channel=Reminder.CHANNEL_EMAIL,
                    send_at=due - timedelta(minutes=minutes),
                )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {created} events"))
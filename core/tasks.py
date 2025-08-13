"""
Celery tasks for the Deadline Tracker.

This module defines asynchronous tasks used to process and deliver reminders,
and to send daily digest emails.  The ``send_due_reminders`` task polls the
database for reminders that are ready to be sent and dispatches them via
email.  To avoid duplicate sends, each reminder has an ``is_sent`` flag that
is set once delivery has completed.
"""
from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Reminder


@shared_task
def send_due_reminders() -> int:
    """Send all unsent reminders whose send time has passed.

    Returns the number of reminders that were sent.  Reminders are fetched in
    small batches to prevent huge bursts of email in case of a backlog.  Each
    reminder is marked as sent after the email has been dispatched to ensure
    idempotence.
    """
    now = timezone.now()
    # Select a batch of pending reminders that should be sent now
    reminders = (
        Reminder.objects
        .select_related("event", "event__user")
        .filter(is_sent=False, send_at__lte=now)
        .order_by("send_at")[:200]
    )
    sent_count = 0
    for reminder in reminders:
        user = reminder.event.user
        # Skip if user has no email address
        if not user.email:
            continue
        subject = (
            f"Reminder: {reminder.event.title} "
            f"(due {reminder.event.due_at.astimezone(timezone.get_current_timezone()):%Y-%m-%d %H:%M})"
        )
        # Compose the body including description and labels
        labels = ", ".join(label.name for label in reminder.event.labels.all())
        body_lines = [reminder.event.description or "No description."]
        if labels:
            body_lines.append(f"Labels: {labels}")
        body_lines.append(
            f"Due: {reminder.event.due_at.astimezone(timezone.get_current_timezone()).isoformat()}"
        )
        body_lines.append(f"Event owner: {user.get_username()}")
        body = "\n\n".join(body_lines)
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        reminder.is_sent = True
        reminder.sent_at = now
        reminder.save(update_fields=["is_sent", "sent_at"])
        sent_count += 1
    return sent_count


@shared_task
def send_daily_digest() -> int:
    """Placeholder task for sending a daily digest of upcoming events.

    The implementation of this task is left as an exercise.  It should iterate
    over users and send them a summary of events due today and in the next
    three days, grouped by label.  Return the number of users who received
    digest emails.
    """
    # To be implemented: summarise events per user and send via email
    return 0
"""
Database models for the Deadline Tracker.

These models capture events with due dates, user‑defined labels, attachments
(images or text files) and reminders for notification delivery.  They are
designed to be flexible and extensible, supporting multiple labels per event
via a many‑to‑many relationship and allowing future addition of new reminder
channels or attachment types.
"""
from __future__ import annotations

from datetime import datetime
from django.conf import settings
from django.db import models


class Event(models.Model):
    """Represents a deadline or event with a due date.

    Each event belongs to a single user and can have an arbitrary number of
    associated reminders, labels and attachments.  The ``status`` field is
    used to hide completed or archived events from the default list view.
    """

    STATUS_OPEN = "open"
    STATUS_DONE = "done"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_DONE, "Done"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Many‑to‑many relationship to labels (through table defined below)
    labels = models.ManyToManyField(
        "Label",
        through="EventLabel",
        related_name="events",
    )

    def __str__(self) -> str:  # pragma: no cover
        return self.title

    class Meta:
        ordering = ["due_at"]


class Label(models.Model):
    """A user‑defined label that can be attached to events.

    Labels allow events to be categorised and filtered.  Each label belongs to
    a user and can only be used by that user.  The optional colour field can
    be used in the UI to highlight events with different colours.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    colour = models.CharField(max_length=7, blank=True, help_text="Hexadecimal colour code (e.g. #ff0000)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "name")]
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class EventLabel(models.Model):
    """Through model linking events and labels (many‑to‑many).

    Using an explicit through model makes it easy to extend the relationship
    later, for example by adding a field recording when the label was added.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("event", "label")]
        ordering = ["added_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.label.name} -> {self.event.title}"


def attachment_upload_to(instance: "Attachment", filename: str) -> str:
    """Return the upload path for an attachment based on event and filename."""
    return f"attachments/{instance.event_id}/{filename}"


class Attachment(models.Model):
    """File attached to an event.

    Supports images and text files.  Files are stored under the ``media`` directory
    in a subdirectory named after the event's ID.  The ``mime_type`` field
    records the type of the file for client‑side rendering.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_to)
    mime_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs) -> None:
        """Populate the size and mime type when saving the attachment."""
        if self.file and not self.mime_type:
            # Determine mime type based on the file name if not provided
            import mimetypes

            mime, _ = mimetypes.guess_type(self.file.name)
            self.mime_type = mime or "application/octet-stream"
        if self.file and not self.size:
            self.size = self.file.size  # type: ignore
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.file.name


class Reminder(models.Model):
    """A scheduled reminder for an event.

    Reminders store an absolute ``send_at`` timestamp which is calculated when
    the reminder is created.  If ``is_sent`` is False and the current time
    reaches or exceeds ``send_at``, the ``send_due_reminders`` task will send
    the notification using the specified channel.  Currently only email is
    supported, but the channel field is defined to allow future expansion.
    """

    CHANNEL_EMAIL = "email"
    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reminders")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default=CHANNEL_EMAIL)
    send_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_sent", "send_at"]),
        ]
        ordering = ["send_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Reminder for {self.event.title} at {self.send_at}"
"""
Administrative configuration for the Deadline Tracker.

This module customises how events, labels, attachments and reminders appear in
the Django admin.  It makes it easier to navigate events by showing key
fields, enabling search and filtering and inlining related objects.
"""
from __future__ import annotations

from django.contrib import admin
from .models import Event, Label, EventLabel, Attachment, Reminder


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "colour", "created_at")
    search_fields = ("name", "user__username", "user__email")
    list_filter = ("user",)


class EventLabelInline(admin.TabularInline):
    model = EventLabel
    extra = 0


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


class ReminderInline(admin.TabularInline):
    model = Reminder
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "due_at", "status", "created_at")
    search_fields = ("title", "description", "user__username", "user__email")
    list_filter = ("status", "due_at", "labels__name")
    inlines = [EventLabelInline, AttachmentInline, ReminderInline]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file", "event", "mime_type", "size", "created_at")
    search_fields = ("file", "event__title", "event__user__username")
    list_filter = ("mime_type",)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("event", "channel", "send_at", "is_sent", "sent_at")
    search_fields = ("event__title", "event__user__username", "event__user__email")
    list_filter = ("channel", "is_sent")
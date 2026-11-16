"""Notification fan-out.

`notify()` swallows duplicate-insert races so a caller never has to care: a
re-triggered achievement or an edited comment must not spam the inbox.
"""

import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.notifications.models import Notification

logger = logging.getLogger("apps.notifications")


def notify(recipient, kind, title, body="", link="", actor=None, dedupe_key=""):
    """Create one inbox row. Returns the Notification, or None when it was a duplicate."""
    if recipient is None or (actor is not None and actor.pk == recipient.pk):
        # Never notify a person about their own action.
        return None

    if dedupe_key:
        # Cheap pre-check so a known duplicate does not spend a transaction; the
        # uniq_notification_dedupe_ref index is the actual guarantee under concurrency.
        exists = Notification.objects.filter(
            recipient=recipient, kind=kind, dedupe_key=dedupe_key
        ).exists()
        if exists:
            return None

    try:
        with transaction.atomic():
            return Notification.objects.create(
                recipient=recipient,
                kind=kind,
                title=title[:200],
                body=body[:500],
                link=link[:300],
                actor=actor,
                dedupe_key=dedupe_key[:120],
            )
    except IntegrityError:
        logger.debug("Suppressed duplicate notification %s", dedupe_key)
        return None


def notify_many(recipients, kind, title, body="", link="", actor=None, dedupe_prefix=""):
    """Bulk notify used by announcements; returns the number actually created."""
    created = 0
    for recipient in recipients:
        key = f"{dedupe_prefix}:{recipient.pk}" if dedupe_prefix else ""
        if notify(recipient, kind, title, body, link, actor=actor, dedupe_key=key):
            created += 1
    return created


def mark_read(notification, user):
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at", "updated_at"])
    return notification


def mark_all_read(user):
    return Notification.objects.filter(recipient=user, read_at__isnull=True).update(
        read_at=timezone.now(), updated_at=timezone.now()
    )


def unread_count(user):
    return Notification.objects.filter(recipient=user, read_at__isnull=True, archived_at__isnull=True).count()

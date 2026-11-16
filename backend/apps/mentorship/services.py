"""Mentorship request lifecycle.

Learners create requests, mentors answer them, and only the mentor on a pair can
attach a meeting link — enforced here as well as in the permission classes.
"""

import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.achievements.services import award_xp, evaluate_achievements
from apps.mentorship.models import MentorProfile, MentorshipRequest, MentorshipSession

logger = logging.getLogger("apps.mentorship")

LIVE_STATUSES = [MentorshipRequest.STATUS_PENDING, MentorshipRequest.STATUS_ACCEPTED]


class MentorshipConflict(Exception):
    """Raised when a live request already exists or the mentor has no capacity."""


def active_request_count(mentor_user):
    return MentorshipRequest.objects.filter(mentor=mentor_user, status=MentorshipRequest.STATUS_ACCEPTED).count()


def create_request(learner, mentor_user, goal, message, preferred_slots=None):
    if learner.pk == mentor_user.pk:
        raise MentorshipConflict("Choose a mentor other than yourself.")

    profile = MentorProfile.objects.filter(user=mentor_user, is_approved=True).first()
    if profile is None:
        raise MentorshipConflict("That mentor is not available on CodeHer yet.")
    if not profile.is_accepting:
        raise MentorshipConflict("That mentor is not accepting new mentees right now.")
    if not profile.has_capacity:
        raise MentorshipConflict("That mentor has reached their active mentee capacity.")

    live = MentorshipRequest.objects.filter(
        learner=learner, mentor=mentor_user, status__in=LIVE_STATUSES
    ).first()
    if live is not None:
        raise MentorshipConflict("You already have an open request with this mentor.")

    try:
        with transaction.atomic():
            request = MentorshipRequest.objects.create(
                learner=learner,
                mentor=mentor_user,
                goal=goal,
                message=message,
                preferred_slots=preferred_slots or [],
            )
    except IntegrityError as error:
        # Two tabs raced past the check above; uniq_live_mentorship_request picks a winner.
        raise MentorshipConflict("You already have an open request with this mentor.") from error

    from apps.notifications.services import notify

    notify(
        mentor_user,
        kind="mentorship_update",
        title=f"New mentorship request from {learner.display_name}",
        body=goal,
        link="/mentorship/incoming",
        actor=learner,
        dedupe_key=f"mentor-request:{request.pk}",
    )
    return request


def accept_request(request, mentor_user, note=""):
    _assert_owner_mentor(request, mentor_user)
    if request.status != MentorshipRequest.STATUS_PENDING:
        raise MentorshipConflict(f"This request is already {request.status}.")

    with transaction.atomic():
        request.status = MentorshipRequest.STATUS_ACCEPTED
        request.mentor_note = note
        request.responded_at = timezone.now()
        request.save(update_fields=["status", "mentor_note", "responded_at", "updated_at"])

        MentorProfile.objects.filter(user=mentor_user).update(matched_count=_matched_count(mentor_user))

    award_xp(
        mentor_user,
        settings.XP_RULES["mentor_match"],
        reason="mentor_match",
        source_type="mentorship",
        source_id=request.pk,
        note=f"Accepted {request.learner.display_name}",
    )
    evaluate_achievements(mentor_user)

    from apps.notifications.services import notify

    notify(
        request.learner,
        kind="mentorship_update",
        title=f"{mentor_user.display_name} accepted your mentorship request",
        body=note,
        link=f"/mentorship/requests/{request.pk}",
        actor=mentor_user,
        dedupe_key=f"mentor-accept:{request.pk}",
    )
    return request


def decline_request(request, mentor_user, reason=""):
    _assert_owner_mentor(request, mentor_user)
    if request.status != MentorshipRequest.STATUS_PENDING:
        raise MentorshipConflict(f"This request is already {request.status}.")

    request.status = MentorshipRequest.STATUS_DECLINED
    request.declined_reason = reason
    request.responded_at = timezone.now()
    request.save(update_fields=["status", "declined_reason", "responded_at", "updated_at"])

    from apps.notifications.services import notify

    notify(
        request.learner,
        kind="mentorship_update",
        title=f"{mentor_user.display_name} declined your mentorship request",
        body=reason,
        link=f"/mentorship/requests/{request.pk}",
        actor=mentor_user,
        dedupe_key=f"mentor-decline:{request.pk}",
    )
    return request


def cancel_request(request, learner_user):
    if request.learner_id != learner_user.pk:
        raise PermissionError("You can cancel only your own requests.")
    if request.status not in {MentorshipRequest.STATUS_PENDING, MentorshipRequest.STATUS_ACCEPTED}:
        raise MentorshipConflict(f"This request is already {request.status}.")

    was_accepted = request.status == MentorshipRequest.STATUS_ACCEPTED
    request.status = MentorshipRequest.STATUS_CANCELLED
    request.responded_at = timezone.now()
    request.save(update_fields=["status", "responded_at", "updated_at"])

    if was_accepted:
        MentorProfile.objects.filter(user=request.mentor).update(matched_count=_matched_count(request.mentor))

    from apps.notifications.services import notify

    notify(
        request.mentor,
        kind="mentorship_update",
        title=f"{learner_user.display_name} cancelled their mentorship request",
        body=request.goal,
        link="/mentorship/incoming",
        actor=learner_user,
        dedupe_key=f"mentor-cancel:{request.pk}",
    )
    return request


def complete_request(request, mentor_user):
    _assert_owner_mentor(request, mentor_user)
    if request.status != MentorshipRequest.STATUS_ACCEPTED:
        raise MentorshipConflict("Only an accepted mentorship can be completed.")
    request.status = MentorshipRequest.STATUS_COMPLETED
    request.save(update_fields=["status", "updated_at"])
    MentorProfile.objects.filter(user=mentor_user).update(matched_count=_matched_count(mentor_user))
    return request


def schedule_session(request, mentor_user, starts_at, duration_minutes=45, agenda="", meeting_url=""):
    _assert_owner_mentor(request, mentor_user)
    if request.status != MentorshipRequest.STATUS_ACCEPTED:
        raise MentorshipConflict("Accept the request before scheduling a session.")
    if starts_at <= timezone.now():
        raise ValueError("Schedule sessions in the future.")

    session = MentorshipSession.objects.create(
        request=request,
        mentor=request.mentor,
        learner=request.learner,
        starts_at=starts_at,
        duration_minutes=duration_minutes,
        agenda=agenda,
        meeting_url=meeting_url,
    )
    _sync_session_count(request)

    from apps.notifications.services import notify

    notify(
        request.learner,
        kind="session_reminder",
        title=f"Session scheduled with {mentor_user.display_name}",
        body=starts_at.strftime("%A %d %B %Y at %H:%M"),
        link="/mentorship/sessions",
        actor=mentor_user,
        dedupe_key=f"session:{session.pk}",
    )
    return session


def update_session(session, user, **fields):
    """Mentor-only edits: agenda, meeting link, notes, status, attendance."""
    if session.mentor_id != user.pk and not user.is_admin:
        raise PermissionError("Only the mentor on a session can change its details.")

    allowed = {"agenda", "meeting_url", "notes", "status", "learner_attended", "starts_at", "duration_minutes"}
    changed = [key for key, value in fields.items() if key in allowed and getattr(session, key) != value]
    for key in changed:
        setattr(session, key, fields[key])
    if changed:
        session.save(update_fields=changed + ["updated_at"])

    if "status" in changed and session.status == "completed":
        from apps.notifications.services import notify

        notify(
            session.learner,
            kind="session_reminder",
            title="Your mentorship session was marked complete",
            body=session.notes[:200],
            link="/mentorship/sessions",
            actor=user,
            dedupe_key=f"session-done:{session.pk}",
        )
    return session


def pending_reminders(minutes=60):
    """Sessions starting within `minutes` that have not been reminded yet."""
    now = timezone.now()
    horizon = now + timezone.timedelta(minutes=minutes)
    return MentorshipSession.objects.filter(
        status="scheduled", starts_at__gt=now, starts_at__lte=horizon, reminder_sent_at__isnull=True
    ).select_related("mentor", "learner")


def send_reminders(minutes=60):
    from apps.notifications.services import notify

    sent = 0
    for session in pending_reminders(minutes):
        created = notify(
            session.learner,
            kind="session_reminder",
            title=f"Your session with {session.mentor.display_name} starts soon",
            body=session.starts_at.strftime("%H:%M today"),
            link="/mentorship/sessions",
            actor=session.mentor,
            dedupe_key=f"session-reminder:{session.pk}",
        )
        if created:
            session.reminder_sent_at = timezone.now()
            session.save(update_fields=["reminder_sent_at", "updated_at"])
            sent += 1
    return sent


def _matched_count(mentor_user):
    from django.db.models import Count

    return MentorshipRequest.objects.filter(
        mentor=mentor_user, status=MentorshipRequest.STATUS_ACCEPTED
    ).aggregate(total=Count("id"))["total"]


def _sync_session_count(request):
    from django.db.models import Count

    request.session_count = request.sessions.aggregate(total=Count("id"))["total"]
    request.save(update_fields=["session_count", "updated_at"])


def _assert_owner_mentor(request, mentor_user):
    if request.mentor_id != mentor_user.pk and not mentor_user.is_admin:
        raise PermissionError("Only the assigned mentor can act on this request.")

"""Community write paths: engagement toggles, counters, trending and moderation.

Counters are denormalised for read speed but always recomputed from Engagement
rows, so a toggle race cannot leave the displayed numbers drifting.
"""

import logging
import math

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.achievements.services import award_xp, evaluate_achievements
from apps.community.models import Comment, Engagement, Post, Project, Report

logger = logging.getLogger("apps.community")


def target_link(obj):
    if isinstance(obj, Post):
        return f"/community/{obj.pk}"
    if isinstance(obj, Project):
        return f"/projects/{obj.pk}"
    if isinstance(obj, Comment):
        return f"/community/{obj.post_id}"
    return ""


def toggle_engagement(user, target, kind):
    """Like/bookmark on/off for a Post, Project or Comment. Returns {"active": bool}."""
    if isinstance(target, Post):
        field = "post"
    elif isinstance(target, Project):
        field = "project"
    else:
        field = "comment"

    filters = {"user": user, "kind": kind, field: target}
    existing = Engagement.objects.filter(**filters).first()

    if existing:
        existing.delete()
        active = False
    else:
        try:
            with transaction.atomic():
                Engagement.objects.create(kind=kind, user=user, **{field: target})
        except IntegrityError:
            # A concurrent duplicate click; treat the toggle as an off-switch.
            Engagement.objects.filter(**filters).delete()
            active = False
        else:
            active = True

    refresh_counters(target)
    return {"active": active}


def refresh_counters(target):
    if isinstance(target, Post):
        _refresh_post(target)
    elif isinstance(target, Comment):
        _refresh_comment(target)
    else:
        _refresh_project(target)


def _refresh_post(post):
    post.likes_count = Engagement.objects.filter(post=post, kind="like").count()
    post.comments_count = post.comments.filter(status="published").count()
    post.bookmarks_count = Engagement.objects.filter(post=post, kind="bookmark").count()
    post.save(update_fields=["likes_count", "comments_count", "bookmarks_count", "updated_at"])


def _refresh_comment(comment):
    comment.likes_count = Engagement.objects.filter(comment=comment, kind="like").count()
    comment.save(update_fields=["likes_count", "updated_at"])
    post = comment.post
    post.comments_count = post.comments.filter(status="published").count()
    post.last_activity_at = timezone.now()
    post.save(update_fields=["comments_count", "last_activity_at", "updated_at"])


def _refresh_project(project):
    project.likes_count = Engagement.objects.filter(project=project, kind="like").count()
    project.bookmarks_count = Engagement.objects.filter(project=project, kind="bookmark").count()
    project.last_activity_at = timezone.now()
    project.save(update_fields=["likes_count", "bookmarks_count", "last_activity_at", "updated_at"])
    recompute_trending(project)


def add_comment(user, post, body, parent=None):
    comment = Comment.objects.create(post=post, user=user, body=body, parent=parent)
    _refresh_comment(comment)
    _notify_comment(user, post, comment, parent)
    evaluate_achievements(user)
    return comment


def _notify_comment(user, post, comment, parent):
    from apps.notifications.services import notify

    dedupe = f"comment:{comment.pk}"
    if parent is not None:
        recipient = parent.user
        kind = "reply" if recipient.pk != post.user_id else "comment"
        title = f"{user.display_name} replied to you"
    else:
        recipient = post.user
        kind = "comment"
        title = f"{user.display_name} commented on your post"

    notify(
        recipient,
        kind=kind,
        title=title,
        body=comment.body[:200],
        link=f"/community/{post.pk}",
        actor=user,
        dedupe_key=dedupe,
    )


def publish_project(user, project):
    """Publishing awards XP once — the PointEvent constraint blocks a repeat."""
    first_publish = project.status != "published"
    project.status = "published"
    project.last_activity_at = timezone.now()
    project.save(update_fields=["status", "last_activity_at", "updated_at"])
    recompute_trending(project)

    if first_publish:
        award_xp(
            user,
            settings.XP_RULES["project_publish"],
            reason="project_publish",
            source_type="project",
            source_id=project.pk,
            note=project.title,
        )
        evaluate_achievements(user)
    return project


def recompute_trending(project):
    """Engagement weighted by recency; refreshed on write rather than guessed."""
    age_days = max((timezone.now() - project.created_at).total_seconds() / 86400, 0.01)
    score = (
        project.likes_count * 3 + project.views_count * 0.4 + project.bookmarks_count * 2
    ) / math.pow(age_days + 2, 0.8)
    project.trending_score = round(score, 4)
    project.save(update_fields=["trending_score", "updated_at"])
    return project


def refresh_all_trending():
    projects = Project.objects.filter(status="published")
    for project in projects:
        recompute_trending(project)
    return projects.count()


def mark_helpful(post, comment, user):
    if comment.post_id != post.pk:
        raise ValueError("That comment does not belong to this post.")
    post.helpful_comment = comment
    post.save(update_fields=["helpful_comment", "updated_at"])

    from apps.notifications.services import notify

    notify(
        comment.user,
        kind="comment",
        title=f"Your answer was marked helpful on “{post.title[:60]}”",
        body="",
        link=f"/community/{post.pk}",
        actor=user,
        dedupe_key=f"helpful:{post.pk}:{comment.pk}",
    )
    evaluate_achievements(comment.user)
    return post


def create_report(user, target, reason, details=""):
    if isinstance(target, Post):
        field = "post"
    elif isinstance(target, Comment):
        field = "comment"
    else:
        field = "project"

    report = Report(created_by=user, target_type=field, reason=reason, details=details)
    setattr(report, field, target)
    try:
        with transaction.atomic():
            report.save()
    except IntegrityError:
        return Report.objects.filter(created_by=user, **{field: target}).first()
    return report


def resolve_report(report, admin_user, action, note=""):
    """action is "hide" (content removed) or "dismiss" (report closed)."""
    report.status = "resolved" if action == "hide" else "dismissed"
    report.resolved_by = admin_user
    report.resolved_at = timezone.now()
    report.resolution_note = note
    report.action_taken = action
    target = report.target

    with transaction.atomic():
        report.save()
        if action == "hide" and target is not None:
            target.status = "hidden"
            target.save(update_fields=["status", "updated_at"])

    if action == "hide" and target is not None:
        from apps.notifications.services import notify

        notify(
            target.user,
            kind="moderation",
            title="Your content was hidden by a moderator",
            body=note or report.reason,
            link="/community",
            actor=admin_user,
            dedupe_key=f"report:{report.pk}",
        )
    return report


def toggle_follow(follower, target):
    from apps.users.models import Follow

    if follower.pk == target.pk:
        raise ValueError("You cannot follow yourself.")

    existing = Follow.objects.filter(follower=follower, following=target).first()
    if existing:
        existing.delete()
        return {"following": False}

    try:
        with transaction.atomic():
            Follow.objects.create(follower=follower, following=target)
    except IntegrityError:
        # uniq_follow_pair lost the race against a double click: the switch is off.
        return {"following": False}

    from apps.notifications.services import notify

    notify(
        target,
        kind="follow",
        title=f"{follower.display_name} started following you",
        body="",
        link=f"/members/{follower.pk}",
        actor=follower,
        dedupe_key=f"follow:{follower.pk}:{target.pk}",
    )
    return {"following": True}

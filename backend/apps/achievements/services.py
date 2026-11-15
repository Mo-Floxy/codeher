"""XP, levels, streaks and achievement evaluation.

Every reward in CodeHer funnels through award_xp(), whose unique constraint makes
duplicate awards impossible at the database level rather than by application hope.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.achievements.models import Achievement, PointEvent, UserAchievement

logger = logging.getLogger("apps.achievements")


def level_for_xp(total_xp):
    """Highest level whose threshold the learner has crossed."""
    level = 1
    for index, threshold in enumerate(settings.LEVEL_THRESHOLDS):
        if total_xp >= threshold:
            level = index + 1
    return level


def next_level_xp(current_level):
    index = current_level
    if index < len(settings.LEVEL_THRESHOLDS):
        return settings.LEVEL_THRESHOLDS[index]
    # Past the published table each level costs one more threshold than the last.
    last = settings.LEVEL_THRESHOLDS[-1]
    previous = settings.LEVEL_THRESHOLDS[-2]
    return last + (last - previous)


def level_progress(total_xp, level):
    floor = settings.LEVEL_THRESHOLDS[level - 1] if level - 1 < len(settings.LEVEL_THRESHOLDS) else 0
    ceiling = next_level_xp(level)
    if ceiling <= floor:
        return 100
    return max(0, min(100, round(100 * (total_xp - floor) / (ceiling - floor))))


def award_xp(user, amount, reason, source_type, source_id, note=""):
    """Idempotent XP award. Returns (awarded_bool, PointEvent_or_None)."""
    amount = int(amount)
    if amount <= 0:
        return False, None

    try:
        with transaction.atomic():
            event = PointEvent.objects.create(
                user=user,
                amount=amount,
                reason=reason,
                source_type=source_type,
                source_id=str(source_id),
                note=note[:300],
            )
    except IntegrityError:
        # Already awarded for this exact action.
        return False, None

    profile = user.profile
    profile.total_xp = (profile.total_xp or 0) + amount
    profile.level = level_for_xp(profile.total_xp)
    profile.save(update_fields=["total_xp", "level", "updated_at"])

    evaluate_achievements(user)
    return True, event


def xp_total(user):
    return PointEvent.objects.filter(user=user).aggregate(total=Sum("amount"))["total"] or 0


def touch_activity(user, minutes=0, lessons=0, quizzes=0, challenges=0, xp=0, day=None):
    """Record learning activity for today (or `day`) and re-derive the streak."""
    day = day or timezone.localdate()
    from apps.progress.models import ActivityLog

    log, _created = ActivityLog.objects.get_or_create(user=user, day=day)
    log.minutes = min(24 * 60, (log.minutes or 0) + max(0, int(minutes)))
    log.lessons_completed = (log.lessons_completed or 0) + max(0, int(lessons))
    log.quizzes_passed = (log.quizzes_passed or 0) + max(0, int(quizzes))
    log.challenges_solved = (log.challenges_solved or 0) + max(0, int(challenges))
    log.xp_earned = (log.xp_earned or 0) + max(0, int(xp))
    log.save(
        update_fields=["minutes", "lessons_completed", "quizzes_passed", "challenges_solved", "xp_earned"]
    )
    recalculate_streak(user)
    return log


def recalculate_streak(user):
    """Streak = consecutive active days ending today, or yesterday if today is still clean."""
    from apps.progress.models import ActivityLog

    days = set(
        ActivityLog.objects.filter(user=user)
        .filter(Q(minutes__gt=0) | Q(lessons_completed__gt=0))
        .values_list("day", flat=True)
    )

    current = 0
    if days:
        today = timezone.localdate()
        cursor = today if today in days else today - timedelta(days=1)
        while cursor in days:
            current += 1
            cursor -= timedelta(days=1)

    profile = user.profile
    profile.current_streak = current
    profile.longest_streak = max(profile.longest_streak or 0, longest_streak_from(days))
    profile.last_activity_date = max(days) if days else None
    profile.save(update_fields=["current_streak", "longest_streak", "last_activity_date", "updated_at"])
    return current


def longest_streak_from(days):
    if not days:
        return 0
    ordered = sorted(days)
    best = run = 1
    for previous, current in zip(ordered, ordered[1:]):
        run = run + 1 if (current - previous).days == 1 else 1
        best = max(best, run)
    return best


def weekly_activity(user, days=7):
    """Minutes + lesson counts per day, zero-filled so charts stay aligned."""
    from apps.progress.models import ActivityLog

    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    rows = ActivityLog.objects.filter(user=user, day__gte=start, day__lte=today).values("day", "minutes", "lessons_completed")
    by_day = {row["day"]: row for row in rows}
    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = by_day.get(day)
        series.append(
            {
                "date": day.isoformat(),
                "minutes": int(row["minutes"]) if row else 0,
                "lessons_completed": int(row["lessons_completed"]) if row else 0,
            }
        )
    return series


def weekly_minutes(user, days=7):
    start = timezone.localdate() - timedelta(days=days - 1)
    from apps.progress.models import ActivityLog

    return ActivityLog.objects.filter(user=user, day__gte=start).aggregate(total=Sum("minutes"))["total"] or 0


# --------------------------------------------------------------------- metrics
def compute_metrics(user):
    """Real counters the badge catalogue is evaluated against."""
    from apps.challenges.models import Submission
    from apps.community.models import Comment, Post, Project
    from apps.courses.models import Course
    from apps.mentorship.models import MentorshipSession
    from apps.progress.models import Enrollment, LessonCompletion, QuizAttempt

    completed_lessons = LessonCompletion.objects.filter(user=user).values("lesson").distinct().count()
    courses_completed = Enrollment.objects.filter(user=user, is_completed=True).count()
    challenges_solved = Submission.objects.filter(user=user, passed=True).values("challenge").distinct().count()
    quizzes_passed = QuizAttempt.objects.filter(user=user, passed=True).values("quiz").distinct().count()
    projects_published = Project.objects.filter(user=user, status="published").count()
    posts_created = Post.objects.filter(user=user, status="published").count()
    comments_created = Comment.objects.filter(user=user, status="published").count()
    mentor_sessions = MentorshipSession.objects.filter(learner=user, status="completed").count()

    profile = user.profile
    return {
        "lessons_completed": completed_lessons,
        "courses_completed": courses_completed,
        "challenges_solved": challenges_solved,
        "quizzes_passed": quizzes_passed,
        "projects_published": projects_published,
        "posts_created": posts_created,
        "comments_created": comments_created,
        "mentor_sessions": mentor_sessions,
        "streak_days": profile.current_streak or 0,
        "total_xp": profile.total_xp or 0,
    }


def evaluate_achievements(user):
    """Award every unearned badge whose metric now meets the requirement."""
    metrics = compute_metrics(user)
    earned_codes = set(UserAchievement.objects.filter(user=user).values_list("achievement__code", flat=True))
    candidates = Achievement.objects.filter(is_active=True).exclude(code__in=earned_codes)

    unlocked = []
    for achievement in candidates:
        value = metrics.get(achievement.metric, 0)
        if value >= achievement.requirement_value:
            created = UserAchievement.objects.filter(user=user, achievement=achievement).exists()
            if not created:
                UserAchievement.objects.create(user=user, achievement=achievement)
                unlocked.append(achievement)
                if achievement.xp_reward:
                    award_xp(
                        user,
                        achievement.xp_reward,
                        reason=f"badge:{achievement.code}",
                        source_type="achievement",
                        source_id=achievement.code,
                        note=achievement.title,
                    )
                from apps.notifications.services import notify

                notify(
                    user,
                    kind="achievement",
                    title=f"Achievement unlocked: {achievement.title}",
                    body=achievement.description,
                    link="/achievements",
                    dedupe_key=f"achievement:{achievement.code}",
                )
    return unlocked


def leaderboard(scope="xp", period="alltime", limit=50):
    """Ranking built only from stored rows; weekly ranks ignore older awards.

    Returns [{rank, user, value}] — the view serialises `user` so avatars are
    rendered with the request the service never sees.
    """
    from apps.users.models import Profile

    profiles = Profile.objects.filter(user__is_active=True).select_related("user")

    if period == "weekly":
        if scope == "streak":
            # A weekly streak ranking is just the live streak, capped at 7 active days.
            since = timezone.localdate() - timedelta(days=6)
            from apps.progress.models import ActivityLog

            active_days = (
                ActivityLog.objects.filter(day__gte=since)
                .values("user")
                .annotate(value=Count("id"))
                .order_by("-value")[:limit]
            )
            by_user = {row["user"]: row["value"] for row in active_days}
            profiles = [profile for profile in profiles if profile.user_id in by_user]
            profiles.sort(key=lambda profile: -by_user[profile.user_id])
            return [
                {"rank": index + 1, "user": profile.user, "value": by_user[profile.user_id]}
                for index, profile in enumerate(profiles)
            ]

        since = timezone.now() - timedelta(days=7)
        totals = (
            PointEvent.objects.filter(created_at__gte=since)
            .values("user")
            .annotate(value=Sum("amount"))
            .order_by("-value")[:limit]
        )
        by_user = {row["user"]: row["value"] for row in totals}
        profiles = list(Profile.objects.filter(user_id__in=by_user.keys(), user__is_active=True).select_related("user"))
        profiles.sort(key=lambda profile: -by_user[profile.user_id])
        return [
            {"rank": index + 1, "user": profile.user, "value": by_user[profile.user_id]}
            for index, profile in enumerate(profiles)
        ]

    order_by = "-current_streak" if scope == "streak" else "-total_xp"
    profiles = profiles.order_by(order_by, "-total_xp")[:limit]
    value_attr = "current_streak" if scope == "streak" else "total_xp"
    return [
        {"rank": index + 1, "user": profile.user, "value": getattr(profile, value_attr) or 0}
        for index, profile in enumerate(profiles)
    ]

"""Learner dashboard aggregation.

Every number here is a query against stored rows — nothing is a placeholder, and a
new account honestly sees zeros and empty states.
"""

import logging
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.achievements.services import (
    level_for_xp,
    level_progress,
    next_level_xp,
    weekly_activity,
    weekly_minutes,
)
from apps.core.models import Event
from apps.courses.models import Course, Lesson
from apps.community.models import Post
from apps.progress.models import Enrollment, LessonBookmark, LessonCompletion

logger = logging.getLogger("apps.progress")


def _greeting(now):
    if now.hour < 12:
        return "Good morning"
    if now.hour < 18:
        return "Good afternoon"
    return "Good evening"


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = user.profile
        now = timezone.now()

        enrollments = list(
            Enrollment.objects.filter(user=user)
            .select_related("course", "course__learning_path", "course__instructor")
            .order_by("-updated_at")
        )
        from apps.courses.serializers import CourseCardSerializer

        context = {"request": request}

        in_progress = [row for row in enrollments if not row.is_completed]
        completed_lessons = LessonCompletion.objects.filter(user=user).count()
        completed_courses = sum(1 for row in enrollments if row.is_completed)
        total_lessons_taken = sum(row.total_lesson_count for row in enrollments)
        completion_rate = (
            round(100 * sum(row.completed_lesson_count for row in enrollments) / total_lessons_taken)
            if total_lessons_taken
            else 0
        )

        continue_learning = []
        for enrollment in in_progress[:4]:
            next_lesson = _next_lesson(user, enrollment.course)
            continue_learning.append(
                {
                    "course": CourseCardSerializer(enrollment.course, context=context).data,
                    "lesson": next_lesson,
                    "progress_percent": enrollment.progress_percent,
                    "next_position": next_lesson["position"] if next_lesson else None,
                }
            )

        from apps.progress.models import ActivityLog

        recent_days = list(
            ActivityLog.objects.filter(user=user, day__gte=now.date() - timedelta(days=27)).values_list(
                "day", flat=True
            )
        )

        streak = {
            "current": profile.current_streak,
            "longest": profile.longest_streak,
            "last_activity_date": profile.last_activity_date.isoformat() if profile.last_activity_date else None,
            "activity_dates": [day.isoformat() for day in sorted(recent_days)],
        }

        actual_minutes = weekly_minutes(user)
        weekly_goal = {
            "target_minutes": profile.weekly_goal_minutes,
            "actual_minutes": actual_minutes,
            "achieved": actual_minutes >= profile.weekly_goal_minutes,
            "progress_percent": (
                min(100, round(100 * actual_minutes / profile.weekly_goal_minutes))
                if profile.weekly_goal_minutes
                else 0
            ),
        }

        events = Event.objects.filter(is_published=True, starts_at__gte=now).order_by("starts_at")[:5]
        recommended = _recommended_courses(user, context)
        community = _community_activity(request)

        from apps.achievements.models import UserAchievement

        earned = UserAchievement.objects.filter(user=user).select_related("achievement").order_by("-earned_at")[:6]

        return Response(
            {
                "greeting": f"{_greeting(now)}, {user.display_name}",
                "xp": profile.total_xp,
                "level": profile.level,
                "level_progress_percent": level_progress(profile.total_xp, profile.level),
                "next_level_xp": next_level_xp(profile.level),
                "xp_to_next_level": max(0, next_level_xp(profile.level) - profile.total_xp),
                "enrolled_courses": len(enrollments),
                "completed_courses": completed_courses,
                "completed_lessons": completed_lessons,
                "completion_rate_percent": completion_rate,
                "continue_learning": continue_learning,
                "streak": streak,
                "weekly_activity": weekly_activity(user),
                "weekly_goal": weekly_goal,
                "upcoming_events": [
                    {"id": event.pk, "kind": event.kind, "title": event.title, "starts_at": event.starts_at, "url": event.url}
                    for event in events
                ],
                "recommended_courses": recommended,
                "community_activity": community,
                "achievements": [
                    {
                        "badge": award.achievement.code,
                        "title": award.achievement.title,
                        "description": award.achievement.description,
                        "icon": award.achievement.icon,
                        "color": award.achievement.color,
                        "earned_at": award.earned_at,
                    }
                    for award in earned
                ],
                "quick_links": {"projects": "/projects", "mentors": "/mentorship", "challenges": "/challenges"},
            }
        )


def _next_lesson(user, course):
    done = set(
        LessonCompletion.objects.filter(user=user, lesson__course=course).values_list("lesson_id", flat=True)
    )
    for lesson in course.lessons.filter(is_published=True).order_by("position", "id"):
        if lesson.pk not in done:
            return {"id": lesson.pk, "title": lesson.title, "position": lesson.position, "kind": lesson.kind}
    return None


def _recommended_courses(user, context):
    """Unenrolled published courses matching the learner's declared skill level."""
    from apps.courses.serializers import CourseCardSerializer

    enrolled_ids = list(Enrollment.objects.filter(user=user).values_list("course_id", flat=True))
    queryset = (
        Course.objects.filter(is_published=True)
        .exclude(pk__in=enrolled_ids)
        .select_related("learning_path", "instructor")
    )
    preferred = queryset.filter(level=user.profile.skill_level)
    rows = list(preferred[:4])
    if len(rows) < 4:
        rows += list(queryset.exclude(pk__in=[row.pk for row in rows]).order_by("-enrolled_count")[: 4 - len(rows)])
    return CourseCardSerializer(rows, many=True, context=context).data


def _community_activity(request):
    """Recent published discussion rows, flattened here so the dashboard has no
    dependency on the community serializer naming."""
    from apps.users.serializers import avatar_url, safe_profile

    posts = (
        Post.objects.filter(status="published")
        .select_related("user", "course")
        .order_by("-last_activity_at")[:6]
    )
    return [
        {
            "id": post.pk,
            "type": post.type,
            "title": post.title,
            "excerpt": post.body[:180],
            "tags": post.tags or [],
            "likes_count": post.likes_count,
            "comments_count": post.comments_count,
            "is_solved": post.is_solved,
            "created_at": post.created_at,
            "last_activity_at": post.last_activity_at,
            "course": {"id": post.course_id, "title": post.course.title} if post.course_id else None,
            "author": {
                "id": post.user_id,
                "display_name": post.user.display_name,
                "username": post.user.username,
                "avatar": avatar_url(safe_profile(post.user), request),
            },
        }
        for post in posts
    ]


class MyActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.progress.models import ActivityLog

        days = int(request.query_params.get("days", 30))
        days = max(1, min(days, 180))
        start = timezone.localdate() - timedelta(days=days - 1)
        rows = ActivityLog.objects.filter(user=request.user, day__gte=start).order_by("day")
        return Response(
            {
                "range_days": days,
                "series": [
                    {
                        "date": row.day.isoformat(),
                        "minutes": row.minutes,
                        "lessons_completed": row.lessons_completed,
                        "quizzes_passed": row.quizzes_passed,
                        "challenges_solved": row.challenges_solved,
                        "xp_earned": row.xp_earned,
                    }
                    for row in rows
                ],
                "totals": {
                    "minutes": sum(row.minutes for row in rows),
                    "lessons": sum(row.lessons_completed for row in rows),
                    "xp": sum(row.xp_earned for row in rows),
                },
            }
        )


class MyBookmarksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.courses.serializers import LessonSummarySerializer

        lessons = (
            Lesson.objects.filter(bookmarks__user=request.user, is_published=True)
            .select_related("course", "module")
            .distinct()[:50]
        )
        data = LessonSummarySerializer(lessons, many=True, context={"request": request}).data
        return Response({"count": len(data), "results": data})


class ProgressSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        stats = (
            Enrollment.objects.filter(user=user)
            .aggregate(
                courses=Count("id"),
                completed=Count("id", filter=Q(is_completed=True)),
                lessons_done=Sum("completed_lesson_count"),
            )
        )
        return Response(
            {
                "enrolled_courses": stats["courses"] or 0,
                "completed_courses": stats["completed"] or 0,
                "lessons_completed": LessonCompletion.objects.filter(user=user).count(),
                "bookmarked_lessons": LessonBookmark.objects.filter(user=user).count(),
                "level": user.profile.level,
                "xp": user.profile.total_xp,
                "level_progress_percent": level_progress(user.profile.total_xp, user.profile.level),
                "level_for_current_xp": level_for_xp(user.profile.total_xp),
            }
        )


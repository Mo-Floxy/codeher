"""Public site data, uploads and the administrative console."""

import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.challenges.models import Challenge, Submission
from apps.community.models import Comment, Engagement, Post, Project, Report
from apps.core import admin_serializers as admin_s
from apps.core.models import Announcement, Event, Testimonial
from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsAdmin
from apps.courses.models import Course, CourseModule, LearningPath, Lesson, Quiz
from apps.mentorship.models import MentorProfile, MentorshipRequest, MentorshipSession
from apps.progress.models import Certificate, Enrollment, LessonCompletion, QuizAttempt
from apps.users.models import Profile

User = get_user_model()
logger = logging.getLogger("apps.core")

IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}
MAX_UPLOAD_BYTES = 4 * 1024 * 1024


# ------------------------------------------------------------------- public site
class SiteStatsView(APIView):
    """Landing-page impact numbers, counted from real rows only."""

    permission_classes = [AllowAny]

    def get(self, request):
        learners = User.objects.filter(is_active=True, role="learner").count()
        members = User.objects.filter(is_active=True).count()
        courses = Course.objects.filter(is_published=True).count()
        lessons = Lesson.objects.filter(is_published=True).count()
        projects = Project.objects.filter(status="published").count()
        matches = MentorshipRequest.objects.filter(status=MentorshipRequest.STATUS_ACCEPTED).count()
        solves = Submission.objects.filter(passed=True).count()
        countries = (
            Profile.objects.exclude(country="")
            .values_list("country", flat=True)
            .distinct()
            .count()
        )
        completions = Enrollment.objects.filter(is_completed=True).count()
        return Response(
            {
                "learners": members,
                "learner_accounts": learners,
                "courses": courses,
                "lessons": lessons,
                "projects": projects,
                "mentor_matches": matches,
                "challenge_solves": solves,
                "countries": countries,
                "course_completions": completions,
                "generated_at": timezone.now(),
            }
        )


class TestimonialListView(APIView):
    """Only admin-published quotes. An empty list is a real answer, not a fallback."""

    permission_classes = [AllowAny]

    def get(self, request):
        rows = Testimonial.objects.filter(is_published=True).select_related("user", "course")[:12]
        data = admin_s.TestimonialSerializer(rows, many=True).data
        return Response({"count": len(data), "results": data, "is_sample": len(data) == 0})


class EventListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        rows = Event.objects.filter(is_published=True, starts_at__gte=timezone.now()).order_by("starts_at")[:12]
        data = admin_s.EventSerializer(rows, many=True).data
        return Response({"count": len(data), "results": data})


# ----------------------------------------------------------------------- uploads
class UploadView(APIView):
    """Avatar and screenshot uploads. Restricted to images, size-capped, random names."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"file": "No file was provided."}, status=status.HTTP_400_BAD_REQUEST)
        if upload.size > MAX_UPLOAD_BYTES:
            return Response(
                {"file": f"Images must be {MAX_UPLOAD_BYTES // (1024 * 1024)} MB or smaller."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        extension = IMAGE_TYPES.get(getattr(upload, "content_type", ""))
        if extension is None:
            return Response(
                {"file": "Only PNG, JPEG, WebP or GIF images are accepted."},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        folder = request.data.get("folder", "uploads")
        if folder not in {"avatars", "project-screenshots", "course-thumbnails", "uploads"}:
            folder = "uploads"
        name = f"{folder}/{uuid.uuid4().hex}.{extension}"
        path = default_storage.save(name, upload)
        url = default_storage.url(path)
        absolute = request.build_absolute_uri(url)
        logger.info("user=%s uploaded %s", request.user.pk, path)
        return Response({"url": absolute, "path": url, "size": upload.size}, status=status.HTTP_201_CREATED)


# -------------------------------------------------------------------- api root
class ApiRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "name": "CodeHer API",
                "version": "1.0",
                "authenticated": bool(request.user.is_authenticated),
                "endpoints": {
                    "auth": "/api/auth/",
                    "users": "/api/users/",
                    "learning": "/api/learning/",
                    "progress": "/api/progress/",
                    "dashboard": "/api/dashboard/",
                    "challenges": "/api/challenges/",
                    "community": "/api/community/",
                    "mentorship": "/api/mentorship/",
                    "achievements": "/api/achievements/",
                    "notifications": "/api/notifications/",
                    "site": "/api/site/",
                    "uploads": "/api/uploads/",
                    "admin": "/api/admin/",
                    "django_admin": "/django-admin/",
                },
                "runner": {
                    "base_url": settings.RUNNER_BASE_URL,
                    "configured": True,
                    "note": "Code never executes inside Django; it is proxied to the isolated runner service.",
                },
            }
        )


# ------------------------------------------------------------------------ admin
class AdminOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        now = timezone.now()
        week = now - timedelta(days=7)
        enrollments = Enrollment.objects.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(is_completed=True)),
            average_progress=Avg("progress_percent"),
        )
        submissions = Submission.objects.aggregate(
            total=Count("id"), passed=Count("id", filter=Q(passed=True))
        )
        return Response(
            {
                "users": {
                    "total": User.objects.count(),
                    "active": User.objects.filter(is_active=True).count(),
                    "learners": User.objects.filter(role="learner", is_active=True).count(),
                    "mentors": User.objects.filter(role="mentor", is_active=True).count(),
                    "admins": User.objects.filter(role="admin").count(),
                    "new_this_week": User.objects.filter(date_joined__gte=week).count(),
                    "active_this_week": Profile.objects.filter(
                        user__is_active=True, last_activity_date__gte=week.date()
                    ).count(),
                },
                "learning": {
                    "paths": LearningPath.objects.count(),
                    "courses": Course.objects.count(),
                    "published_courses": Course.objects.filter(is_published=True).count(),
                    "modules": CourseModule.objects.count(),
                    "lessons": Lesson.objects.count(),
                    "quizzes": Quiz.objects.count(),
                    "enrollments": enrollments["total"] or 0,
                    "course_completions": enrollments["completed"] or 0,
                    "average_progress_percent": round(enrollments["average_progress"] or 0, 1),
                    "lesson_completions": LessonCompletion.objects.count(),
                    "certificates": Certificate.objects.count(),
                    "quiz_attempts": QuizAttempt.objects.count(),
                    "quiz_pass_rate_percent": _quiz_pass_rate(),
                },
                "challenges": {
                    "total": Challenge.objects.count(),
                    "published": Challenge.objects.filter(is_published=True).count(),
                    "submissions": submissions["total"] or 0,
                    "accepted": submissions["passed"] or 0,
                    "acceptance_rate_percent": _acceptance_rate(submissions),
                    "unique_solvers": Submission.objects.filter(passed=True).values("user").distinct().count(),
                },
                "community": {
                    "posts": Post.objects.count(),
                    "published_posts": Post.objects.filter(status="published").count(),
                    "questions_unanswered": _unanswered_questions(),
                    "comments": Comment.objects.count(),
                    "projects": Project.objects.count(),
                    "published_projects": Project.objects.filter(status="published").count(),
                    "likes": Engagement.objects.filter(kind="like").count(),
                    "bookmarks": Engagement.objects.filter(kind="bookmark").count(),
                },
                "mentorship": {
                    "mentors": MentorProfile.objects.count(),
                    "approved_mentors": MentorProfile.objects.filter(is_approved=True).count(),
                    "pending_requests": MentorshipRequest.objects.filter(status="pending").count(),
                    "accepted_requests": MentorshipRequest.objects.filter(status="accepted").count(),
                    "sessions": MentorshipSession.objects.count(),
                    "upcoming_sessions": MentorshipSession.objects.filter(
                        status="scheduled", starts_at__gt=now
                    ).count(),
                },
                "moderation": {
                    "reports_total": Report.objects.count(),
                    "reports_pending": Report.objects.filter(status="pending").count(),
                    "reports_resolved": Report.objects.filter(status="resolved").count(),
                    "hidden_content": Post.objects.filter(status="hidden").count()
                    + Project.objects.filter(status="hidden").count(),
                },
                "generated_at": now,
            }
        )


def _quiz_pass_rate():
    total = QuizAttempt.objects.count()
    if not total:
        return 0.0
    passed = QuizAttempt.objects.filter(passed=True).count()
    return round(100 * passed / total, 1)


def _acceptance_rate(submissions):
    total = submissions["total"] or 0
    if not total:
        return 0.0
    return round(100 * (submissions["passed"] or 0) / total, 1)


def _unanswered_questions():
    return (
        Post.objects.filter(type="question", status="published", helpful_comment__isnull=True)
        .annotate(reply_count=Count("comments"))
        .filter(reply_count=0)
        .count()
    )


METRICS = {
    "signups": ("user", User, "date_joined"),
    "enrollments": ("enrollment", Enrollment, "created_at"),
    "submissions": ("submission", Submission, "created_at"),
    "activity": ("activity", None, None),
    "xp": ("xp", None, None),
}


class AdminAnalyticsView(APIView):
    """Daily buckets straight from the tables — no synthetic chart data."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        metric = request.query_params.get("metric", "signups")
        if metric not in METRICS:
            return Response({"metric": list(METRICS)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        days = max(1, min(days, 365))
        start = timezone.now() - timedelta(days=days)

        if metric == "activity":
            rows = (
                Enrollment.objects.filter(updated_at__gte=start)
                .annotate(day=TruncDate("updated_at"))
                .values("day")
                .annotate(value=Count("id"))
                .order_by("day")
            )
        elif metric == "xp":
            from apps.achievements.models import PointEvent

            rows = (
                PointEvent.objects.filter(created_at__gte=start)
                .annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(value=Count("id"))
                .order_by("day")
            )
        else:
            _, model, field = METRICS[metric]
            rows = (
                model.objects.filter(**{f"{field}__gte": start})
                .annotate(day=TruncDate(field))
                .values("day")
                .annotate(value=Count("id"))
                .order_by("day")
            )

        by_day = {row["day"]: row["value"] for row in rows if row["day"]}
        today = timezone.localdate()
        labels = [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]
        series = [by_day.get(label, 0) for label in labels]
        return Response(
            {
                "metric": metric,
                "days": days,
                "labels": [label.isoformat() for label in labels],
                "series": series,
                "total": sum(series),
            }
        )


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = User.objects.select_related("profile").annotate(
            enrollments=Count("enrollments", distinct=True),
            posts=Count("posts", distinct=True),
            submissions=Count("submissions", distinct=True),
        )
        term = request.query_params.get("search", "").strip()
        if term:
            queryset = queryset.filter(
                Q(email__icontains=term) | Q(display_name__icontains=term) | Q(username__icontains=term)
            )
        role = request.query_params.get("role")
        if role in dict(User.ROLE_CHOICES):
            queryset = queryset.filter(role=role)
        is_active = request.query_params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active == "true")

        ordering = request.query_params.get("ordering", "-date_joined")
        allowed = {"-date_joined", "date_joined", "-profile__total_xp", "profile__total_xp", "display_name"}
        queryset = queryset.order_by(ordering if ordering in allowed else "-date_joined")

        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        data = admin_s.AdminUserSerializer(rows, many=True).data
        return page.get_paginated_response(data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(User.objects.select_related("profile"), pk=pk)

    def get(self, request, pk):
        user = self.get_object(pk)
        return Response(admin_s.AdminUserSerializer(user).data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        serializer = admin_s.AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("admin=%s updated user=%s", request.user.pk, user.pk)
        return Response(admin_s.AdminUserSerializer(user).data)


class AdminCourseListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Course.objects.select_related("learning_path", "instructor").order_by("title")
        term = request.query_params.get("search", "").strip()
        if term:
            queryset = queryset.filter(title__icontains=term)
        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        return page.get_paginated_response(admin_s.CourseWriteSerializer(rows, many=True).data)

    def post(self, request):
        serializer = admin_s.CourseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminCourseDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Course, pk=pk)

    def get(self, request, pk):
        return Response(admin_s.CourseWriteSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        course = self.get_object(pk)
        serializer = admin_s.CourseWriteSerializer(course, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminLessonListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Lesson.objects.select_related("course", "module").order_by("course__title", "position")
        course = request.query_params.get("course")
        if course and course.isdigit():
            queryset = queryset.filter(course_id=int(course))
        term = request.query_params.get("search", "").strip()
        if term:
            queryset = queryset.filter(title__icontains=term)
        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        return page.get_paginated_response(admin_s.LessonWriteSerializer(rows, many=True).data)

    def post(self, request):
        serializer = admin_s.LessonWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminLessonDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Lesson, pk=pk)

    def get(self, request, pk):
        return Response(admin_s.LessonWriteSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        lesson = self.get_object(pk)
        serializer = admin_s.LessonWriteSerializer(lesson, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminPathListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        rows = LearningPath.objects.annotate(course_count=Count("courses")).order_by("position", "title")
        return Response({"count": rows.count(), "results": admin_s.LearningPathWriteSerializer(rows, many=True).data})

    def post(self, request):
        serializer = admin_s.LearningPathWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminPathDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(LearningPath, pk=pk)

    def get(self, request, pk):
        return Response(admin_s.LearningPathWriteSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        path = self.get_object(pk)
        serializer = admin_s.LearningPathWriteSerializer(path, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminModuleListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = CourseModule.objects.select_related("course").order_by("course__title", "position")
        course = request.query_params.get("course")
        if course and course.isdigit():
            queryset = queryset.filter(course_id=int(course))
        return Response(
            {"count": queryset.count(), "results": admin_s.CourseModuleWriteSerializer(queryset, many=True).data}
        )

    def post(self, request):
        serializer = admin_s.CourseModuleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminQuizDetailView(APIView):
    """Admin editing of a quiz and its answer key (hidden from learners)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Quiz, pk=pk)

    def get(self, request, pk):
        return Response(admin_s.QuizWriteSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        quiz = self.get_object(pk)
        serializer = admin_s.QuizWriteSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def post(self, request, pk=None):
        serializer = admin_s.QuizWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminChallengeListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Challenge.objects.order_by("difficulty", "position", "title")
        term = request.query_params.get("search", "").strip()
        if term:
            queryset = queryset.filter(title__icontains=term)
        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        return page.get_paginated_response(admin_s.ChallengeWriteSerializer(rows, many=True).data)

    def post(self, request):
        serializer = admin_s.ChallengeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminChallengeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Challenge, pk=pk)

    def get(self, request, pk):
        return Response(admin_s.ChallengeWriteSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        challenge = self.get_object(pk)
        serializer = admin_s.ChallengeWriteSerializer(challenge, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMentorListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = MentorProfile.objects.select_related("user").order_by("-is_approved", "user__display_name")
        status_filter = request.query_params.get("is_approved")
        if status_filter in {"true", "false"}:
            queryset = queryset.filter(is_approved=status_filter == "true")
        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        return page.get_paginated_response(admin_s.MentorProfileSerializer(rows, many=True).data)


class AdminMentorDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(MentorProfile.objects.select_related("user"), pk=pk)

    def get(self, request, pk):
        return Response(admin_s.MentorProfileSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        profile = self.get_object(pk)
        serializer = admin_s.MentorProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        was_approved = profile.is_approved
        serializer.save()
        if not was_approved and profile.is_approved:
            profile.approved_by = request.user
            profile.save(update_fields=["approved_by", "updated_at"])
        return Response(admin_s.MentorProfileSerializer(profile).data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminReportListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Report.objects.select_related("created_by", "post", "comment", "project").order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter in {"pending", "resolved", "dismissed"}:
            queryset = queryset.filter(status=status_filter)
        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        return page.get_paginated_response(admin_s.ReportSerializer(rows, many=True).data)


class AdminReportResolveView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404

        from apps.community.services import resolve_report

        report = get_object_or_404(
            Report.objects.select_related("post", "comment", "project"), pk=pk
        )
        action = request.data.get("action", "dismiss")
        if action not in {"hide", "dismiss", "remove_content"}:
            return Response(
                {"action": "Choose dismiss, hide or remove_content."}, status=status.HTTP_400_BAD_REQUEST
            )
        # The frontend token for "take the content down" is remove_content.
        action = "hide" if action in {"hide", "remove_content"} else "dismiss"
        report = resolve_report(report, request.user, action, note=request.data.get("note", ""))
        return Response(admin_s.ReportSerializer(report).data)


class AdminAnnouncementListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        rows = Announcement.objects.select_related("course", "learning_path", "created_by").order_by("-created_at")
        page = StandardResultsSetPagination()
        items = page.paginate_queryset(rows, request, view=self)
        return page.get_paginated_response(admin_s.AnnouncementSerializer(items, many=True).data)

    def post(self, request):
        serializer = admin_s.AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save(created_by=request.user)

        from apps.notifications.services import notify_many

        sent_at = timezone.now()
        created = notify_many(
            _audience(announcement),
            kind="course_announcement",
            title=announcement.title,
            body=announcement.body[:500],
            link=f"/learning/{announcement.course.slug}" if announcement.course_id else "/learning",
            actor=request.user,
            dedupe_prefix=f"announcement:{announcement.pk}",
        )

        announcement.recipient_count = created
        announcement.save(update_fields=["sent_at", "recipient_count", "updated_at"])
        logger.info("admin=%s sent announcement=%s to %s", request.user.pk, announcement.pk, created)
        return Response(admin_s.AnnouncementSerializer(announcement).data, status=status.HTTP_201_CREATED)


class AdminAnnouncementDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Announcement, pk=pk)

    def get(self, request, pk):
        return Response(admin_s.AnnouncementSerializer(self.get_object(pk)).data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _audience(announcement):
    if announcement.audience == "all_members":
        return list(User.objects.filter(is_active=True))
    if announcement.audience == "course_enrolled" and announcement.course_id:
        return list(User.objects.filter(enrollments__course_id=announcement.course_id, is_active=True).distinct())
    if announcement.audience == "path_enrolled" and announcement.learning_path_id:
        return list(
            User.objects.filter(
                enrollments__course__learning_path_id=announcement.learning_path_id, is_active=True
            ).distinct()
        )
    return []


class AdminTestimonialListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        rows = Testimonial.objects.select_related("user", "course").order_by("-created_at")
        return Response({"count": rows.count(), "results": admin_s.TestimonialSerializer(rows, many=True).data})

    def post(self, request):
        serializer = admin_s.TestimonialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminTestimonialDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Testimonial, pk=pk)

    def patch(self, request, pk):
        testimonial = self.get_object(pk)
        serializer = admin_s.TestimonialSerializer(testimonial, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

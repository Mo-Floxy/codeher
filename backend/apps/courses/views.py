"""Learning catalogue API — paths, courses, curriculum, lessons, quizzes."""

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsAdmin
from apps.courses import serializers as s
from apps.courses.filters import CourseFilter
from apps.courses.models import Course, LearningPath, Lesson, Quiz
from apps.progress import services as progress
from apps.progress.models import Certificate, Enrollment

logger = logging.getLogger("apps.courses")


def get_course(lookup):
    """Courses are addressable by primary key or slug."""
    if lookup.isdigit():
        return get_object_or_404(Course, pk=int(lookup))
    return get_object_or_404(Course, slug=lookup)


class PathListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        paths = LearningPath.objects.filter(is_published=True).prefetch_related("courses")
        data = s.PathSerializer(paths, many=True, context={"request": request}).data
        return Response({"count": len(data), "results": data})


ORDERABLE = {"created_at", "-created_at", "title", "-title", "enrolled_count", "-enrolled_count",
             "duration_hours", "-duration_hours", "-updated_at"}


class CourseListView(APIView):
    """Public catalog; administrators may create courses here too."""

    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method in {"POST", "PUT", "PATCH"}:
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

    def get(self, request):
        queryset = (
            Course.objects.filter(is_published=True)
            .select_related("learning_path", "instructor")
        )
        queryset = CourseFilter(request.query_params, queryset=queryset).qs
        ordering = request.query_params.get("ordering", "")
        if ordering in ORDERABLE:
            if ordering == "created_at":
                ordering = "-created_at"
            queryset = queryset.order_by(ordering, "id")
        else:
            queryset = queryset.order_by("learning_path", "position", "title")

        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        data = s.CourseCardSerializer(rows, many=True, context={"request": request}).data
        return page.get_paginated_response(data)

    def post(self, request):
        serializer = s.CourseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save(instructor=serializer.validated_data.get("instructor") or request.user)
        return Response(
            s.CourseSerializer(course, context={"request": request}).data, status=status.HTTP_201_CREATED
        )


class CourseDetailView(APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

    def get(self, request, lookup):
        course = get_course(lookup)
        if not course.is_published and not getattr(request.user, "is_admin", False):
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(s.CourseSerializer(course, context={"request": request}).data)

    def patch(self, request, lookup):
        course = get_course(lookup)
        serializer = s.CourseWriteSerializer(course, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(s.CourseSerializer(course, context={"request": request}).data)

    def delete(self, request, lookup):
        course = get_course(lookup)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseEnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lookup):
        course = get_course(lookup)
        enrollment, created = progress.enroll(request.user, course)
        if created:
            logger.info("user=%s enrolled course=%s", request.user.pk, course.pk)
        return Response(
            {
                "enrolled": True,
                "created": created,
                "enrollment": s.EnrollmentSerializer(enrollment, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, lookup):
        course = get_course(lookup)
        Enrollment.objects.filter(user=request.user, course=course).delete()
        Course.objects.filter(pk=course.pk).update(
            enrolled_count=Enrollment.objects.filter(course=course).count()
        )
        return Response({"enrolled": False})


class CourseCurriculumView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, lookup):
        course = get_course(lookup)
        modules = course.modules.filter(lessons__is_published=True).prefetch_related(
            "lessons"
        ).distinct()
        data = s.CurriculumModuleSerializer(modules, many=True, context={"request": request}).data
        enrollment = None
        if request.user.is_authenticated:
            enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        return Response(
            {
                "course": s.CourseCardSerializer(course, context={"request": request}).data,
                "modules": data,
                "enrolled": enrollment is not None,
                "progress_percent": enrollment.progress_percent if enrollment else 0,
            }
        )


class LessonDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        if not lesson.is_published and not getattr(request.user, "is_admin", False):
            return Response({"detail": "Lesson not found."}, status=status.HTTP_404_NOT_FOUND)
        if lesson.requires_enrollment:
            enrolled = request.user.is_authenticated and Enrollment.objects.filter(
                user=request.user, course=lesson.course
            ).exists()
            if not enrolled and not getattr(request.user, "is_admin", False):
                return Response(
                    {
                        "locked": True,
                        "lesson": {
                            "id": lesson.pk,
                            "title": lesson.title,
                            "course": lesson.course_id,
                            "course_slug": lesson.course.slug,
                            "kind": lesson.kind,
                            "summary": lesson.summary,
                        },
                        "detail": "Enroll in this course to open the lesson.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        return Response(s.LessonSerializer(lesson, context={"request": request}).data)


class LessonCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        seconds = request.data.get("time_spent_seconds", 0)
        try:
            result = progress.complete_lesson(request.user, lesson, seconds)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        enrollment = result["enrollment"]
        nxt = progress.lesson_next(request.user, lesson)
        return Response(
            {
                "completed": True,
                "duplicate": not result["created"],
                "xp_awarded": result["xp_awarded"],
                "progress_percent": enrollment.progress_percent,
                "completed_lesson_count": enrollment.completed_lesson_count,
                "total_lesson_count": enrollment.total_lesson_count,
                "course_completed": enrollment.is_completed,
                "next_lesson": {"id": nxt.pk, "title": nxt.title} if nxt else None,
            },
            status=status.HTTP_200_OK if not result["created"] else status.HTTP_201_CREATED,
        )


class LessonBookmarkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        bookmarked = progress.toggle_bookmark(request.user, lesson)
        return Response({"bookmarked": bookmarked})


class QuizSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        raw_answers = request.data.get("answers", request.data)
        answers = _answer_map(raw_answers)
        if not answers:
            return Response({"answers": "No answers were supplied."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            attempt = progress.grade_quiz(request.user, quiz, answers)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                "attempt_id": attempt.pk,
                "score_percent": attempt.score_percent,
                "passed": attempt.passed,
                "correct": attempt.correct_count,
                "total": attempt.total_count,
                "passing_percent": quiz.passing_percent,
                "results": attempt.detail,
                "xp_awarded": getattr(attempt, "xp_awarded", 0),
            }
        )


def _answer_map(raw):
    """Accept [{question_id, choice_index}] or {question_id: choice_index}."""
    if isinstance(raw, dict):
        return {int(key): value for key, value in raw.items() if str(key).isdigit()}
    mapping = {}
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            key = item.get("question_id", item.get("question"))
            value = item.get("choice_index", item.get("choice", item.get("answer")))
            if key is None:
                continue
            try:
                mapping[int(key)] = value
            except (TypeError, ValueError):
                continue
    return mapping


class MyEnrollmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            Enrollment.objects.filter(user=request.user)
            .select_related("course", "course__learning_path", "course__instructor")
            .order_by("-updated_at")
        )
        if request.query_params.get("completed") == "true":
            queryset = queryset.filter(is_completed=True)
        page = StandardResultsSetPagination()
        rows = page.paginate_queryset(queryset, request, view=self)
        data = s.EnrollmentSerializer(rows, many=True, context={"request": request}).data
        return page.get_paginated_response(data)


class MyCertificatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = Certificate.objects.filter(user=request.user).select_related(
            "course", "course__instructor"
        )
        data = s.CertificateSerializer(rows, many=True, context={"request": request}).data
        return Response({"count": len(data), "results": data})


class CertificateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        certificate = get_object_or_404(Certificate, pk=pk, user=request.user)
        return Response(s.CertificateSerializer(certificate, context={"request": request}).data)

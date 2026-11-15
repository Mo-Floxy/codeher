"""Mentorship API views.

The whole lifecycle lives in `apps.mentorship.services` — capacity, the one-live-
request-per-pair rule, accept/decline/cancel/complete transitions, session
scheduling, mentor-only edits, XP and notifications. These views only resolve the
actor, validate the payload, call a service function and translate its exceptions:

* `services.MentorshipConflict` -> 409 Conflict (the payload may be valid; the
  server state refuses it — duplicate live request, capacity, wrong status),
* builtin `PermissionError`     -> 403,
* builtin `ValueError`          -> 400,
* a user who must not even see a row -> 404, matching the contract's "missing".

Every error body keeps the `{detail: "..."}` shape: DRF wraps a string `detail` for
us and `apps.core.exceptions.api_exception_handler` adds the status.
"""

from contextlib import contextmanager
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ValidationFailed
from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsMentor
from apps.mentorship import filters, services
from apps.mentorship.models import MentorProfile, MentorshipRequest, MentorshipSession
from apps.mentorship.serializers import (
    AttendanceSerializer,
    DeclineSerializer,
    MentorCardSerializer,
    MentorDetailSerializer,
    MentorResponseSerializer,
    MentorshipRequestCreateSerializer,
    MentorshipRequestSerializer,
    MentorshipSessionSerializer,
    MyMentorProfileSerializer,
    SessionScheduleSerializer,
    SessionUpdateSerializer,
)


class MentorshipConflictError(APIException):
    """`services.MentorshipConflict` as 409 — see the module docstring for the rule."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "That mentorship action conflicts with the current state."
    default_code = "mentorship_conflict"


@contextmanager
def service_errors():
    """Translate service exceptions into contract-shaped HTTP errors (409/403/400)."""
    try:
        yield
    except services.MentorshipConflict as exc:
        raise MentorshipConflictError(str(exc)) from exc
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc
    except ValueError as exc:
        raise ValidationFailed(str(exc)) from exc


def _is_admin(user):
    return bool(user is not None and getattr(user, "is_admin", False))


def _sees_row(obj, user):
    """True when `user` is one of the two people on this row (or an admin)."""
    return obj.learner_id == user.pk or obj.mentor_id == user.pk or _is_admin(user)


def _request_rows():
    """Requests always ship both participants, so the joins are declared once."""
    return MentorshipRequest.objects.select_related(
        "learner", "mentor", "learner__profile", "mentor__profile"
    )


def _session_rows():
    return MentorshipSession.objects.select_related(
        "request", "request__learner", "request__mentor", "mentor", "learner", "mentor__profile", "learner__profile"
    )


class MentorDirectoryView(ListAPIView):
    """`GET /mentorship/mentors/` — approved mentors only, public.

    Query string: `?expertise=` (case-insensitive match on the JSON expertise list),
    `?search=` (display name, bio, expertise), `?accepting=true|false`.
    """

    permission_classes = (AllowAny,)
    serializer_class = MentorCardSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.MentorFilterSet

    def get_queryset(self):
        # Ordering is restated explicitly: annotating an aggregate drops the model's
        # Meta.ordering, and an unordered page is a pagination bug waiting to happen.
        return filters.with_mentor_counts(
            MentorProfile.objects.filter(is_approved=True).select_related("user")
        ).order_by("-matched_count", "user__display_name")


class MentorDetailView(RetrieveAPIView):
    """`GET /mentorship/mentors/{user_id}/`.

    URL pattern name `mentor-detail-by-user`: the lookup is the mentor's **user id**,
    the same value the directory returns as `id` and that `POST /mentorship/requests/`
    expects in its `mentor` field. Profiles an admin has not approved 404 for
    everyone but admins.
    """

    permission_classes = (AllowAny,)
    serializer_class = MentorDetailSerializer
    pagination_class = None

    def get_object(self):
        queryset = filters.with_mentor_counts(MentorProfile.objects.select_related("user"))
        if not _is_admin(self.request.user):
            queryset = queryset.filter(is_approved=True)
        try:
            lookup = int(self.kwargs["user_id"])
        except (TypeError, ValueError):
            raise NotFound("That mentor is not listed.") from None
        profile = queryset.filter(user_id=lookup).first()
        if profile is None:
            raise NotFound("That mentor is not listed.")
        return profile


class MyMentorProfileView(RetrieveUpdateAPIView):
    """`GET/PATCH /mentorship/mentors/me/` for role `mentor` (admins included).

    The record is created on demand and starts unapproved. `is_approved`,
    `matched_count`, `approved_by` and `rating_average` are read-only here, so a
    mentor (or anyone spoofing the payload) cannot promote themselves (§9); a
    submitted value for them is ignored rather than half-applied.
    """

    permission_classes = (IsAuthenticated, IsMentor)
    serializer_class = MyMentorProfileSerializer
    pagination_class = None

    def get_object(self):
        profile, _created = MentorProfile.objects.get_or_create(user=self.request.user)
        return profile


class MentorshipRequestListView(ListCreateAPIView):
    """`GET /mentorship/requests/?status=` (my requests) + `POST` to ask a mentor."""

    permission_classes = (IsAuthenticated,)
    serializer_class = MentorshipRequestSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.MentorshipRequestFilterSet

    def get_queryset(self):
        return _request_rows().filter(learner=self.request.user)

    def create(self, request, *args, **kwargs):
        """`POST /mentorship/requests/` -> `services.create_request` (201)."""
        payload = MentorshipRequestCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        with service_errors():
            created = services.create_request(
                learner=request.user,
                mentor_user=data["mentor"],
                goal=data["goal"],
                message=data["message"],
                preferred_slots=data.get("preferred_slots"),
            )
        output = MentorshipRequestSerializer(created, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class IncomingRequestListView(ListAPIView):
    """`GET /mentorship/requests/incoming/` — the mentor's inbox; role `learner` gets 403."""

    permission_classes = (IsAuthenticated, IsMentor)
    serializer_class = MentorshipRequestSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.MentorshipRequestFilterSet

    def get_queryset(self):
        return _request_rows().filter(mentor=self.request.user)


class MentorshipRequestDetailView(RetrieveAPIView):
    """`GET /mentorship/requests/{id}/` — the pair or an admin; anyone else gets 404."""

    permission_classes = (IsAuthenticated,)
    serializer_class = MentorshipRequestSerializer
    pagination_class = None

    def get_object(self):
        obj = _request_rows().filter(pk=self.kwargs["pk"]).first()
        if obj is None or not _sees_row(obj, self.request.user):
            raise NotFound("That mentorship request does not exist.")
        return obj


class MentorshipRequestActionView(APIView):
    """`POST /mentorship/requests/{id}/{action}/` for accept, decline, cancel, complete.

    Ownership is decided inside the service (`accept/decline/complete` require the
    assigned mentor, `cancel` requires the learner), so the wrong actor gets 403 and
    a stale status gets 409 — never a silent write. Only a request that does not
    exist at all answers 404 here; `GET /requests/{id}/` keeps the row invisible to
    outsiders.
    """

    permission_classes = (IsAuthenticated,)

    ACTIONS = ("accept", "decline", "cancel", "complete")

    def post(self, request, pk, action):
        if action not in self.ACTIONS:
            raise NotFound("Unknown mentorship action.")

        obj = _request_rows().filter(pk=pk).first()
        if obj is None:
            raise NotFound("That mentorship request does not exist.")

        body = request.data if isinstance(request.data, dict) else {}
        with service_errors():
            if action == "accept":
                note = MentorResponseSerializer(data=body)
                note.is_valid(raise_exception=True)
                obj = services.accept_request(obj, request.user, note=note.validated_data.get("note", ""))
            elif action == "decline":
                reason = DeclineSerializer(data=body)
                reason.is_valid(raise_exception=True)
                obj = services.decline_request(obj, request.user, reason=reason.validated_data.get("reason", ""))
            elif action == "cancel":
                obj = services.cancel_request(obj, request.user)
            else:
                obj = services.complete_request(obj, request.user)

        return Response(MentorshipRequestSerializer(obj, context={"request": request}).data)


class SessionListView(ListCreateAPIView):
    """`GET /mentorship/sessions/?scope=upcoming|past` + `POST /mentorship/sessions/`."""

    permission_classes = (IsAuthenticated,)
    serializer_class = MentorshipSessionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.MentorshipSessionFilterSet

    def get_queryset(self):
        user = self.request.user
        return _session_rows().filter(Q(mentor=user) | Q(learner=user))

    def get_permissions(self):
        if self.request.method == "POST":
            # Scheduling is a mentor action; the service also pins it to the pair.
            return [IsAuthenticated(), IsMentor()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """`services.schedule_session` owns the mentor-on-this-pair check."""
        payload = SessionScheduleSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        with service_errors():
            session = services.schedule_session(
                data["request"],
                request.user,
                starts_at=data["starts_at"],
                duration_minutes=data.get("duration_minutes", 45),
                agenda=data.get("agenda", ""),
                meeting_url=data.get("meeting_url", ""),
            )
        output = MentorshipSessionSerializer(session, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class SessionDetailView(RetrieveUpdateDestroyAPIView):
    """`GET/PATCH/DELETE /mentorship/sessions/{id}/` — every write is `services.update_session`."""

    permission_classes = (IsAuthenticated,)
    serializer_class = MentorshipSessionSerializer
    pagination_class = None

    def get_object(self):
        session = _session_rows().filter(pk=self.kwargs["pk"]).first()
        if session is None or not _sees_row(session, self.request.user):
            raise NotFound("That session does not exist.")
        return session

    def update(self, request, *args, **kwargs):
        """Mentor-only fields; `update_session` raises PermissionError for the learner."""
        session = self.get_object()
        payload = SessionUpdateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        with service_errors():
            session = services.update_session(session, request.user, **payload.validated_data)
        return Response(MentorshipSessionSerializer(session, context={"request": request}).data)

    def destroy(self, request, *args, **kwargs):
        """Cancel is a status transition, so the history of the pair survives."""
        session = self.get_object()
        with service_errors():
            services.update_session(session, request.user, status="cancelled")
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionAttendanceView(APIView):
    """`POST /mentorship/sessions/{id}/attendance/` with `{attended: true|false}`.

    The mentor (or an admin) records attendance through `services.update_session`.
    A learner confirming their *own* attendance is a one-field write on their own
    row, which the mentor-only service guard deliberately does not cover, so it
    happens here instead of loosening that guard.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        session = _session_rows().filter(pk=pk).first()
        if session is None or not _sees_row(session, request.user):
            raise NotFound("That session does not exist.")

        payload = AttendanceSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        attended = payload.validated_data["attended"]

        with service_errors():
            if session.mentor_id == request.user.pk or _is_admin(request.user):
                session = services.update_session(session, request.user, learner_attended=attended)
            else:
                if session.starts_at > timezone.now():
                    raise MentorshipConflictError("Attendance can be confirmed once the session has started.")
                session.learner_attended = attended
                session.save(update_fields=["learner_attended", "updated_at"])

        return Response(MentorshipSessionSerializer(session, context={"request": request}).data)

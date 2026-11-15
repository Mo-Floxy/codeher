"""Mentorship API serializers.

Self-contained on purpose: the small "user brief" below is re-declared here rather
than imported from `apps.users.serializers` / `apps.community.serializers`, so this
app never depends on a workstream that is still being written. Only model imports
are used from other apps.

Visibility rules encoded here:
* a mentor directory row is only ever built from an approved `MentorProfile`;
* `has_capacity` / `active_mentees` come from live request rows, never a constant;
* `meeting_url` is mentor-authored and shown only to the two people on a session.
"""

from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.mentorship.models import MentorProfile, MentorshipRequest, MentorshipSession
from apps.users.models import User


def _profile_of(user):
    """A user without a Profile row must not turn the API into a 500."""
    try:
        return user.profile
    except (ObjectDoesNotExist, AttributeError):
        return None


def avatar_url(user, request):
    """Absolute media URL when an avatar file exists, otherwise None."""
    profile = _profile_of(user)
    if profile is None or not profile.avatar:
        return None
    url = profile.avatar.url
    return request.build_absolute_uri(url) if request is not None else url


def viewing_user(serializer):
    """The authenticated user behind the current request, or None (anonymous/unbound)."""
    request = serializer.context.get("request")
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    return user


def session_ends_at(session):
    """Derived from the stored start + duration so both sides see one window."""
    return session.starts_at + timedelta(minutes=session.duration_minutes or 0)


class SlotListField(serializers.Field):
    """`preferred_slots` is a JSON array of either strings or {weekday, time} objects."""

    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError("Provide a list of preferred slots.")
        if len(data) > 12:
            raise serializers.ValidationError("Send at most 12 preferred slots.")
        return data

    def to_representation(self, value):
        return value if isinstance(value, list) else []


class UserBriefSerializer(serializers.Serializer):
    """The public minimum of a member: enough to show a face and a name."""

    id = serializers.IntegerField(source="pk")
    display_name = serializers.CharField()
    username = serializers.CharField()
    avatar = serializers.SerializerMethodField()
    headline = serializers.SerializerMethodField()

    def get_avatar(self, user):
        return avatar_url(user, self.context.get("request"))

    def get_headline(self, user):
        profile = _profile_of(user)
        return profile.headline if profile else ""


class _MentorCountFields(serializers.Serializer):
    """Shared read-only capacity fields for every mentor shape."""

    active_mentees = serializers.SerializerMethodField()
    has_capacity = serializers.SerializerMethodField()
    rating_average = serializers.FloatField(read_only=True, allow_null=True)

    def get_active_mentees(self, mentor):
        """Live accepted-request count (annotated on list views, counted otherwise)."""
        value = getattr(mentor, "active_mentees", None)
        if value is not None:
            return int(value)
        from apps.mentorship.services import active_request_count

        return active_request_count(mentor.user)

    def get_has_capacity(self, mentor):
        """Real accepted count vs the mentor's declared capacity — never a literal True."""
        value = getattr(mentor, "active_mentees", None)
        if value is not None:
            return int(value) < mentor.capacity
        return mentor.has_capacity


class MentorCardSerializer(_MentorCountFields, serializers.ModelSerializer):
    """Directory row.

    `id` is the mentor's **user id** (see the `mentor-detail-by-user` URL pattern),
    which is exactly what `POST /mentorship/requests/` expects in its `mentor` field.
    """

    id = serializers.IntegerField(source="user_id", read_only=True)
    user = UserBriefSerializer(read_only=True)
    expertise = serializers.ListField(child=serializers.CharField(max_length=120), read_only=True)
    languages = serializers.ListField(child=serializers.CharField(max_length=60), read_only=True)

    class Meta:
        model = MentorProfile
        fields = [
            "id",
            "user",
            "expertise",
            "current_role",
            "company",
            "years_experience",
            "bio",
            "availability_note",
            "languages",
            "capacity",
            "active_mentees",
            "has_capacity",
            "is_accepting",
            "matched_count",
            "rating_average",
        ]
        read_only_fields = fields


class MentorDetailSerializer(MentorCardSerializer):
    """Mentor profile page: the card fields plus the mentor's stated availability.

    `availability` mirrors `preferred_slots` because the contract describes this
    endpoint as "mentor detail + availability" and the web page renders that key.
    """

    preferred_slots = serializers.JSONField(read_only=True)
    availability = serializers.SerializerMethodField()
    linkedin_url = serializers.URLField(read_only=True)

    class Meta(MentorCardSerializer.Meta):
        fields = MentorCardSerializer.Meta.fields + ["preferred_slots", "availability", "linkedin_url"]
        read_only_fields = fields

    def get_availability(self, mentor):
        slots = mentor.preferred_slots
        return slots if isinstance(slots, list) else []


class MyMentorProfileSerializer(_MentorCountFields, serializers.ModelSerializer):
    """`GET/PATCH /mentorship/mentors/me/`.

    Writable surface is the mentor's own content. `is_approved`, `matched_count`,
    `approved_by` and `rating_average` are read-only here: approval is an admin act,
    so a mentor (or a learner spoofing the payload) cannot promote themselves (§9).
    """

    # Declared fields ignore Meta.read_only_fields, so anything that must not be
    # written here is marked read_only explicitly: `id` (the owner of the record)
    # included, otherwise a PATCH could re-point a mentor profile at another user.
    id = serializers.IntegerField(source="user_id", read_only=True)
    user = UserBriefSerializer(read_only=True)
    expertise = serializers.ListField(child=serializers.CharField(max_length=120), required=False)
    languages = serializers.ListField(child=serializers.CharField(max_length=60), required=False)
    preferred_slots = SlotListField(required=False)
    bio = serializers.CharField(max_length=3000, required=False, allow_blank=True)
    availability_note = serializers.CharField(max_length=300, required=False, allow_blank=True)
    current_role = serializers.CharField(max_length=200, required=False, allow_blank=True)
    company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    linkedin_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    capacity = serializers.IntegerField(min_value=1, max_value=20, required=False)
    years_experience = serializers.IntegerField(min_value=0, max_value=70, required=False)
    is_accepting = serializers.BooleanField(required=False)

    class Meta:
        model = MentorProfile
        fields = [
            "id",
            "user",
            "expertise",
            "bio",
            "availability_note",
            "preferred_slots",
            "capacity",
            "years_experience",
            "current_role",
            "company",
            "linkedin_url",
            "languages",
            "is_accepting",
            "is_approved",
            "matched_count",
            "active_mentees",
            "has_capacity",
            "rating_average",
        ]
        # Admin-controlled model fields: ignored when submitted, never half-applied.
        read_only_fields = ["is_approved", "matched_count"]


class MentorshipRequestSerializer(serializers.ModelSerializer):
    """One mentorship request, used for both the learner's list and the mentor's inbox."""

    learner = UserBriefSerializer(read_only=True)
    mentor = UserBriefSerializer(read_only=True)
    preferred_slots = serializers.JSONField(read_only=True)

    class Meta:
        model = MentorshipRequest
        fields = [
            "id",
            "learner",
            "mentor",
            "goal",
            "message",
            "preferred_slots",
            "status",
            "mentor_note",
            "declined_reason",
            "responded_at",
            "session_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MentorshipRequestCreateSerializer(serializers.Serializer):
    """Validated input for `POST /mentorship/requests/`; the service does the rest."""

    mentor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        error_messages={"does_not_exist": "We could not find that mentor."},
    )
    goal = serializers.CharField(max_length=300)
    message = serializers.CharField(max_length=4000)
    preferred_slots = SlotListField(required=False)

    def validate_goal(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Tell your mentor what you want to achieve.")
        return cleaned

    def validate_message(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Introduce yourself and why this mentor fits.")
        return cleaned


class MentorResponseSerializer(serializers.Serializer):
    """Body of `accept/` — an optional note that travels to the learner."""

    note = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")


class DeclineSerializer(serializers.Serializer):
    """Body of `decline/` — the reason the learner sees back."""

    reason = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")


class AttendanceSerializer(serializers.Serializer):
    attended = serializers.BooleanField()


class MentorshipRequestBriefSerializer(serializers.ModelSerializer):
    """The request as embedded in a session row, so both sides see who it is with."""

    learner = UserBriefSerializer(read_only=True)
    mentor = UserBriefSerializer(read_only=True)

    class Meta:
        model = MentorshipRequest
        fields = ["id", "status", "goal", "learner", "mentor"]
        read_only_fields = fields


class MentorshipSessionSerializer(serializers.ModelSerializer):
    """A session between one mentor and one learner.

    `meeting_url` is null for anyone who is not on that session; `notes` stays with
    the mentor. `attended` is the learner-facing alias of `learner_attended`.
    """

    request = MentorshipRequestBriefSerializer(read_only=True)
    request_id = serializers.IntegerField(read_only=True)
    mentor = UserBriefSerializer(read_only=True)
    learner = UserBriefSerializer(read_only=True)
    meeting_url = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    attended = serializers.SerializerMethodField()
    ends_at = serializers.SerializerMethodField()
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = MentorshipSession
        fields = [
            "id",
            "request",
            "request_id",
            "mentor",
            "learner",
            "starts_at",
            "ends_at",
            "duration_minutes",
            "agenda",
            "status",
            "meeting_url",
            "notes",
            "learner_attended",
            "attended",
            "is_upcoming",
            "created_at",
        ]
        read_only_fields = fields

    def get_meeting_url(self, session):
        """Mentor-authored; revealed only to the mentor and the learner on this session."""
        viewer = viewing_user(self)
        if viewer is None:
            return None
        if session.mentor_id != viewer.pk and session.learner_id != viewer.pk:
            return None
        return session.meeting_url or None

    def get_notes(self, session):
        viewer = viewing_user(self)
        if viewer is None:
            return None
        if session.mentor_id == viewer.pk or getattr(viewer, "is_admin", False):
            return session.notes or None
        return None

    def get_attended(self, session):
        return bool(session.learner_attended) if session.learner_attended is not None else None

    def get_ends_at(self, session):
        return serializers.DateTimeField().to_representation(session_ends_at(session))


class SessionScheduleSerializer(serializers.Serializer):
    """Body of `POST /mentorship/sessions/` — always the mentor on an accepted request."""

    request = serializers.PrimaryKeyRelatedField(
        queryset=MentorshipRequest.objects.all(),
        error_messages={"does_not_exist": "That mentorship request no longer exists."},
    )
    starts_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(min_value=5, max_value=240, required=False, default=45)
    agenda = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
    meeting_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")


class SessionUpdateSerializer(serializers.Serializer):
    """Body of `PATCH /mentorship/sessions/{id}/` — the mentor's own editable fields."""

    starts_at = serializers.DateTimeField(required=False)
    duration_minutes = serializers.IntegerField(min_value=5, max_value=240, required=False)
    agenda = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    meeting_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["scheduled", "completed", "cancelled"], required=False)

"""Query-string filters for the mentorship endpoints.

`expertise` is a JSON array and JSON containment lookups are not available on every
backend (SQLite has none), so directory matching runs against the JSON column cast
to text. That works identically on the MySQL production database and the SQLite test
database, and it keeps filtering in the database instead of in Python.
"""

import django_filters
from django.db.models import Count, Q, TextField
from django.db.models.functions import Cast
from django.utils import timezone

from apps.mentorship.models import MentorProfile, MentorshipRequest, MentorshipSession

TRUTHY = {"1", "true", "yes", "on"}
FALSEY = {"0", "false", "no", "off"}


def with_expertise_text(queryset):
    """Expose the expertise JSON array as searchable text exactly once per queryset."""
    if "expertise_text" in getattr(queryset.query, "annotations", {}):
        return queryset
    return queryset.annotate(expertise_text=Cast("expertise", TextField()))


def with_mentor_counts(queryset):
    """Annotate the live accepted-mentee count in one grouped query, not N count queries.

    It is the same number the model property `MentorProfile.has_capacity` compares
    against `capacity`, so the directory row and the property can never disagree.
    """
    if "active_mentees" in getattr(queryset.query, "annotations", {}):
        return queryset
    return queryset.annotate(
        active_mentees=Count(
            "user__incoming_requests",
            filter=Q(user__incoming_requests__status=MentorshipRequest.STATUS_ACCEPTED),
        )
    )


def _bool_option(value):
    """`?accepting=true` / `false`; anything else leaves the queryset untouched."""
    text = str(value or "").strip().lower()
    if text in TRUTHY:
        return True
    if text in FALSEY:
        return False
    return None


class MentorFilterSet(django_filters.FilterSet):
    """Directory filters: `?expertise=`, `?search=`, `?accepting=`."""

    expertise = django_filters.CharFilter(method="filter_expertise")
    search = django_filters.CharFilter(method="filter_search")
    accepting = django_filters.CharFilter(method="filter_accepting")

    class Meta:
        model = MentorProfile
        fields = ("expertise", "search", "accepting")

    def filter_expertise(self, queryset, name, value):
        term = (value or "").strip()
        if not term:
            return queryset
        return with_expertise_text(queryset).filter(expertise_text__icontains=term)

    def filter_search(self, queryset, name, value):
        term = (value or "").strip()
        if not term:
            return queryset
        return with_expertise_text(queryset).filter(
            Q(user__display_name__icontains=term) | Q(bio__icontains=term) | Q(expertise_text__icontains=term)
        ).distinct()

    def filter_accepting(self, queryset, name, value):
        flag = _bool_option(value)
        if flag is None:
            return queryset
        return queryset.filter(is_accepting=flag)


class MentorshipRequestFilterSet(django_filters.FilterSet):
    """`?status=pending|accepted|declined|cancelled|completed` on both request lists."""

    status = django_filters.ChoiceFilter(choices=MentorshipRequest.STATUS_CHOICES)
    mentor = django_filters.NumberFilter(field_name="mentor_id")

    class Meta:
        model = MentorshipRequest
        fields = ("status", "mentor")


class MentorshipSessionFilterSet(django_filters.FilterSet):
    """`?scope=upcoming|past` plus the plain `?status=`/`?request=` narrowers."""

    scope = django_filters.CharFilter(method="filter_scope")
    status = django_filters.ChoiceFilter(choices=MentorshipSession._meta.get_field("status").choices)
    request = django_filters.NumberFilter(field_name="request_id")

    class Meta:
        model = MentorshipSession
        fields = ("scope", "status", "request")

    def filter_scope(self, queryset, name, value):
        """`upcoming` has not started yet, `past` already did — the same cut the web
        app makes with `isPastIso(starts_at)`. Anything else returns the full range."""
        option = str(value or "").strip().lower()
        now = timezone.now()
        if option == "upcoming":
            return queryset.filter(starts_at__gte=now)
        if option == "past":
            return queryset.filter(starts_at__lt=now)
        return queryset

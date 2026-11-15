"""Query-parameter handling for the challenge catalogue."""

import django_filters
from django.db.models import Case, IntegerField as DjangoIntegerField, Value, When
from rest_framework.filters import OrderingFilter

from apps.challenges.models import Challenge

# Difficulty is stored as text but must order beginner -> advanced.
DIFFICULTY_ANNOTATION = Case(
    When(difficulty="beginner", then=Value(1)),
    When(difficulty="intermediate", then=Value(2)),
    When(difficulty="advanced", then=Value(3)),
    default=Value(0),
    output_field=DjangoIntegerField(),
)

REAL_ORDERING_FIELDS = (
    "id",
    "title",
    "points",
    "created_at",
    "updated_at",
    "position",
    "submission_count",
    "accepted_count",
)

# Aliases the frontend may send, mapped onto real columns by the filter below.
ORDERING_ALIASES = {
    "points": "-points",
    "difficulty": "difficulty_rank",
    "hardest": "-difficulty_rank",
    "recent": "-created_at",
    "oldest": "created_at",
    "newest_solved": "-accepted_count",
    "most_solved": "-accepted_count",
    "attempts": "-submission_count",
    "pass_rate": "-accepted_count",
    "solved": "-accepted_count",
}


def _alias_map(choices):
    """value -> value plus every human label (and a dashed variant) -> value."""
    mapping = {}
    for value, label in choices:
        mapping[value] = value
        mapping[label] = value
        lowered = label.lower()
        mapping[lowered] = value
        mapping[lowered.replace(" ", "-")] = value
        mapping[lowered.replace(" ", "")] = value
    return mapping


CATEGORY_ALIASES = _alias_map(Challenge.CATEGORY_CHOICES)
DIFFICULTY_ALIASES = _alias_map(Challenge.DIFFICULTY_CHOICES)


def _normalise(choices, raw):
    """Accept the stored value or its label (case/space insensitive)."""
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    return choices.get(value, choices.get(value.lower(), value))


class ChallengeFilter(django_filters.FilterSet):
    difficulty = django_filters.CharFilter(method="filter_difficulty")
    category = django_filters.CharFilter(method="filter_category")

    class Meta:
        model = Challenge
        fields = ("difficulty", "category", "is_published")

    def filter_difficulty(self, queryset, name, value):
        return queryset.filter(difficulty=_normalise(DIFFICULTY_ALIASES, value) or "__no_match__")

    def filter_category(self, queryset, name, value):
        return queryset.filter(category=_normalise(CATEGORY_ALIASES, value) or "__no_match__")


class ChallengeOrderingFilter(OrderingFilter):
    """`?ordering=points|recent|newest_solved|difficulty` plus real columns."""

    ALIASES = ORDERING_ALIASES

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        resolved = []
        for clause in ordering or []:
            descending = clause.startswith("-")
            name = clause.lstrip("-")
            mapped = self.ALIASES.get(name)
            if mapped is None:
                resolved.append(clause)
            elif mapped.startswith("-"):
                resolved.append(mapped)
            else:
                resolved.append("-{}".format(mapped) if descending else mapped)
        return resolved

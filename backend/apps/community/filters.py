"""Query-string filters for the community feed and project gallery."""

import django_filters
from django.db.models import TextField
from django.db.models.functions import Cast

from apps.community.models import Post, Project


def _json_list_contains(queryset, field, value):
    """Membership test inside a JSON list.

    ``<field>__contains`` is unsupported on SQLite, so cast the JSON column to
    text and match the quoted token — portable across SQLite and MySQL.
    """
    return (
        queryset.annotate(**{f"{field}_text": Cast(field, TextField())})
        .filter(**{f"{field}_text__icontains": f'"{value}"'})
    )


class PostFilterSet(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(choices=Post.TYPE_CHOICES)
    tag = django_filters.CharFilter(method="filter_tag", label="Tag")

    class Meta:
        model = Post
        fields = ("type",)

    def filter_tag(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return _json_list_contains(queryset, "tags", value)


class ProjectFilterSet(django_filters.FilterSet):
    technology = django_filters.CharFilter(method="filter_technology", label="Technology")

    class Meta:
        model = Project
        fields = ("technology",)

    def filter_technology(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return _json_list_contains(queryset, "technologies", value)

"""Query filters for the course catalog."""

import django_filters as filters

from apps.courses.models import Course


class CourseFilter(filters.FilterSet):
    search = filters.CharFilter(method="search_matches", label="Title or description")
    level = filters.CharFilter(field_name="level")
    category = filters.CharFilter(field_name="category")
    path = filters.NumberFilter(field_name="learning_path_id")
    path_slug = filters.CharFilter(field_name="learning_path__slug", lookup_expr="iexact")

    class Meta:
        model = Course
        fields = ["level", "category", "is_published"]

    def search_matches(self, queryset, _name, value):
        term = value.strip()
        if not term:
            return queryset
        return queryset.filter(title__icontains=term) | queryset.filter(description__icontains=term)

"""Notification inbox API.

Every route is filtered by `recipient=request.user`, so a row belonging to another
member resolves to a 404 rather than leaking (or revealing) someone else's inbox.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import StandardResultsSetPagination
from apps.notifications import services
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer

TRUE_VALUES = {"1", "true", "yes", "on"}


def is_truthy(value):
    return str(value or "").strip().lower() in TRUE_VALUES


class NotificationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """`/api/notifications/` — the signed-in member's own inbox."""

    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination
    serializer_class = NotificationSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = {"kind": ["exact"]}
    ordering_fields = ("created_at", "read_at", "id")
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = (
            Notification.objects.filter(recipient=self.request.user, archived_at__isnull=True)
            .select_related("actor")
            .order_by("-created_at", "-id")
        )
        if self.action == "list" and is_truthy(self.request.query_params.get("unread_only")):
            queryset = queryset.filter(read_at__isnull=True)
        return queryset

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request, *args, **kwargs):
        return Response({"count": services.unread_count(request.user)})

    @action(detail=True, methods=["post"], url_path="read")
    def read(self, request, pk=None):
        notification = self.get_object()
        services.mark_read(notification, request.user)
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request, *args, **kwargs):
        updated = services.mark_all_read(request.user)
        return Response({"updated": updated, "count": services.unread_count(request.user)})

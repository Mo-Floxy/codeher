"""Community API views.

All stateful mutations (engagement toggles, comments, helpful answers,
reports, publishing, trending) are delegated to apps.community.services —
the views only shape requests and responses.
"""

from django.core.exceptions import ValidationError as CoreValidationError
from django.db.models import BooleanField, Exists, OuterRef, Prefetch, Q, Value
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsAuthenticatedOrReadOnly, IsOwnerOrAdmin
from apps.community import filters as community_filters
from apps.community import serializers as community_serializers
from apps.community import services
from apps.community.models import Comment, Engagement, Post, Project, Report

# Contract ordering for /community/projects/. Anything unknown falls back to trending.
PROJECT_ORDERING = {
    "trending": ("-trending_score", "-last_activity_at"),
    "-trending": ("trending_score", "last_activity_at"),
    "recent": ("-created_at",),
    "-recent": ("created_at",),
    "most_liked": ("-likes_count", "-last_activity_at"),
    "-most_liked": ("likes_count",),
    "most_viewed": ("-views_count", "-last_activity_at"),
}
PROJECT_ORDERING_FIELDS = {"last_activity_at", "created_at", "likes_count", "views_count", "bookmarks_count"}


def _visibility(qs, user):
    """SQL mirror of Post.visible_to()/Project status rules: staff see everything,
    authors see their own rows, everyone else sees published content only."""
    if user and user.is_authenticated:
        if user.is_staff:
            return qs
        return qs.filter(Q(status="published") | Q(user=user))
    return qs.filter(status="published")


def _engagement_flags(qs, user, model):
    """Annotate per-request liked/bookmarked state without extra queries."""
    if user and user.is_authenticated:
        return qs.annotate(
            liked=Exists(Engagement.objects.filter(kind="like", user=user, **{model: OuterRef("pk")})),
            bookmarked=Exists(
                Engagement.objects.filter(kind="bookmark", user=user, **{model: OuterRef("pk")})
            ),
        )
    return qs.annotate(
        liked=Value(False, output_field=BooleanField()),
        bookmarked=Value(False, output_field=BooleanField()),
    )


def _get_object_or_none(model, pk):
    """``Comment.objects.filter(pk="abc")`` raises; the API should answer 400 instead."""
    try:
        return model.objects.filter(pk=pk).first()
    except (ValueError, TypeError, CoreValidationError):
        return None


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = community_serializers.PostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = community_filters.PostFilterSet
    search_fields = ("title", "body")
    ordering_fields = ("last_activity_at", "created_at", "likes_count", "comments_count", "bookmarks_count")
    ordering = ("-last_activity_at",)

    def get_queryset(self):
        qs = Post.objects.select_related("user__profile", "course", "helpful_comment")
        qs = _visibility(qs, self.request.user)
        return _engagement_flags(qs, self.request.user, "post")

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        result = services.toggle_engagement(request.user, post, "like")
        post.refresh_from_db(fields=["likes_count"])
        return Response({"liked": result["active"], "likes_count": post.likes_count})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        post = self.get_object()
        result = services.toggle_engagement(request.user, post, "bookmark")
        post.refresh_from_db(fields=["bookmarks_count"])
        return Response({"bookmarked": result["active"], "bookmarks_count": post.bookmarks_count})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def helpful(self, request, pk=None):
        """Mark an answer helpful — post author or admin only."""
        post = self.get_object()
        if not isinstance(request.data, dict) or "comment_id" not in request.data:
            raise ValidationError({"comment_id": ["This field is required."]})
        comment = _get_object_or_none(Comment, request.data["comment_id"])
        if comment is None:
            raise ValidationError({"comment_id": ["Unknown comment."]})
        try:
            post = services.mark_helpful(post, comment, request.user)
        except ValueError as exc:
            raise ValidationError({"comment_id": [str(exc)]})
        return Response(self.get_serializer(post).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        post = self.get_object()
        serializer = community_serializers.ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        duplicate = Report.objects.filter(created_by=request.user, post=post).exists()
        report = services.create_report(request.user, post, **serializer.validated_data)
        body = community_serializers.ReportSerializer(report).data
        return Response(body, status=status.HTTP_200_OK if duplicate else status.HTTP_201_CREATED)


class PostCommentsView(APIView):
    """Nested comment thread for one post: top-level rows carry one level of replies."""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def _post(self, request, post_id):
        post = _get_object_or_none(Post, post_id)
        if post is None or not post.visible_to(request.user):
            raise NotFound("Post not found.")
        return post

    def _visible_comments(self, post, user):
        qs = post.comments.select_related("user__profile")
        if user and user.is_authenticated:
            if not user.is_staff:
                return qs.filter(Q(status="published") | Q(user=user))
            return qs
        return qs.filter(status="published")

    def get(self, request, post_id):
        post = self._post(request, post_id)
        replies = self._visible_comments(post, request.user).exclude(parent__isnull=True)
        thread = (
            self._visible_comments(post, request.user)
            .filter(parent__isnull=True)
            .prefetch_related(Prefetch("replies", queryset=replies.order_by("created_at")))
            .order_by("created_at")
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(thread, request, view=self)
        serializer = community_serializers.CommentSerializer(
            page, many=True, context={"request": request, "post": post}
        )
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, post_id):
        post = self._post(request, post_id)
        serializer = community_serializers.CommentSerializer(
            data=request.data, context={"request": request, "post": post}
        )
        serializer.is_valid(raise_exception=True)
        parent = serializer.validated_data.get("parent")
        if parent is not None:
            if parent.post_id != post.pk:
                raise ValidationError({"parent": ["That comment belongs to a different post."]})
            # One level of nesting: replies-to-replies join the root thread.
            if parent.parent_id is not None:
                parent = parent.parent
        comment = services.add_comment(request.user, post, serializer.validated_data["body"], parent=parent)
        return Response(
            community_serializers.CommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CommentDetailView(viewsets.GenericViewSet):
    """DELETE /community/comments/{id}/ — author or admin."""

    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    queryset = Comment.objects.select_related("user", "post")

    def destroy(self, request, *args, pk=None, **kwargs):
        comment = self.get_object()
        post = comment.post
        comment.delete()
        services.refresh_counters(post)  # keeps comments_count in step with live rows
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = community_serializers.ProjectSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = community_filters.ProjectFilterSet
    search_fields = ("title", "description")

    def get_queryset(self):
        qs = Project.objects.select_related("user__profile", "course")
        qs = _visibility(qs, self.request.user)
        qs = _engagement_flags(qs, self.request.user, "project")
        ordering_param = (self.request.query_params.get("ordering") or "trending").strip()
        if ordering_param in PROJECT_ORDERING:
            qs = qs.order_by(*PROJECT_ORDERING[ordering_param])
        else:
            key = ordering_param.lstrip("-")
            if key in PROJECT_ORDERING_FIELDS:
                qs = qs.order_by(ordering_param)
            else:
                qs = qs.order_by("-trending_score", "-last_activity_at")
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        if self.action in ("like", "bookmark", "report"):
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = self.request.user
        # An omitted status defaults to published (the model default), so route it
        # through the service too — created as draft first, XP awarded exactly once.
        wants_publish = serializer.validated_data.get("status", "published") == "published"
        if wants_publish:
            serializer.validated_data["status"] = "draft"
        instance = serializer.save(user=user)
        if wants_publish:
            services.publish_project(user, instance)
            instance.refresh_from_db()

    def perform_update(self, serializer):
        was_published = serializer.instance.status == "published"
        wants_publish = serializer.validated_data.get("status") == "published"
        if wants_publish and not was_published:
            serializer.validated_data.pop("status")
            instance = serializer.save()
            services.publish_project(instance.user, instance)
            instance.refresh_from_db()
        else:
            serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        project = self.get_object()
        result = services.toggle_engagement(request.user, project, "like")
        project.refresh_from_db(fields=["likes_count", "trending_score"])
        return Response({"liked": result["active"], "likes_count": project.likes_count})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        project = self.get_object()
        result = services.toggle_engagement(request.user, project, "bookmark")
        project.refresh_from_db(fields=["bookmarks_count", "trending_score"])
        return Response({"bookmarked": result["active"], "bookmarks_count": project.bookmarks_count})

    @action(detail=True, methods=["post"], url_path="view", permission_classes=[AllowAny])
    def record_view(self, request, pk=None):
        """Counts real gallery traffic; trending is recomputed from it by the service."""
        project = self.get_object()
        project.add_view()
        project.refresh_from_db()
        services.recompute_trending(project)
        return Response({"views_count": project.views_count, "trending_score": project.trending_score})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        project = self.get_object()
        serializer = community_serializers.ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        duplicate = Report.objects.filter(created_by=request.user, project=project).exists()
        report = services.create_report(request.user, project, **serializer.validated_data)
        body = community_serializers.ReportSerializer(report).data
        return Response(body, status=status.HTTP_200_OK if duplicate else status.HTTP_201_CREATED)


class MyBookmarksView(APIView):
    """GET /community/me/bookmarks/ -> {posts: [...], projects: [...]}."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = (
            _engagement_flags(
                _visibility(Post.objects.select_related("user__profile", "course"), request.user),
                request.user,
                "post",
            )
            .filter(engagements__user=request.user, engagements__kind="bookmark")
            .distinct()
        )
        projects = (
            _engagement_flags(
                _visibility(Project.objects.select_related("user__profile", "course"), request.user),
                request.user,
                "project",
            )
            .filter(engagements__user=request.user, engagements__kind="bookmark")
            .distinct()
        )
        context = {"request": request}
        return Response(
            {
                "posts": community_serializers.PostSerializer(posts, many=True, context=context).data,
                "projects": community_serializers.ProjectSerializer(projects, many=True, context=context).data,
            }
        )

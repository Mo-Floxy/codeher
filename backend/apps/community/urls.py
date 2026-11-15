"""URLs for the community app, mounted by config/urls.py at api/community/."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.community import views

router = DefaultRouter()
router.register("posts", views.PostViewSet, basename="post")
router.register("projects", views.ProjectViewSet, basename="project")

urlpatterns = [
    path("posts/<int:post_id>/comments/", views.PostCommentsView.as_view(), name="post-comments"),
    path("comments/<int:pk>/", views.CommentDetailView.as_view({"delete": "destroy"}), name="comment-detail"),
    path("me/bookmarks/", views.MyBookmarksView.as_view(), name="my-bookmarks"),
] + router.urls

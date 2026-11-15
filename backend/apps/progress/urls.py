from django.urls import path

from apps.progress import views

urlpatterns = [
    path("summary/", views.ProgressSummaryView.as_view(), name="progress-summary"),
    path("activity/", views.MyActivityView.as_view(), name="my-activity"),
    path("bookmarks/", views.MyBookmarksView.as_view(), name="my-bookmarks"),
]

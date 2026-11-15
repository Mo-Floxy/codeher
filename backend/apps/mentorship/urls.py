"""Mentorship routes, mounted by `config.urls` at `api/mentorship/`.

`mentor-detail-by-user` is the lookup contract: `/mentors/{id}/` takes the mentor's
**user id**, which is the `id` every directory row carries and the value a request
POST sends as `mentor`.
"""

from django.urls import path

from apps.mentorship import views

app_name = "mentorship"

urlpatterns = [
    # Directory.
    path("mentors/", views.MentorDirectoryView.as_view(), name="mentor-list"),
    path("mentors/me/", views.MyMentorProfileView.as_view(), name="mentor-me"),
    path("mentors/<int:user_id>/", views.MentorDetailView.as_view(), name="mentor-detail-by-user"),
    # Requests — the static `incoming/` route is declared before the id routes.
    path("requests/", views.MentorshipRequestListView.as_view(), name="request-list"),
    path("requests/incoming/", views.IncomingRequestListView.as_view(), name="request-incoming"),
    path("requests/<int:pk>/", views.MentorshipRequestDetailView.as_view(), name="request-detail"),
    path(
        "requests/<int:pk>/<str:action>/",
        views.MentorshipRequestActionView.as_view(),
        name="request-action",
    ),
    # Sessions.
    path("sessions/", views.SessionListView.as_view(), name="session-list"),
    path("sessions/<int:pk>/", views.SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<int:pk>/attendance/", views.SessionAttendanceView.as_view(), name="session-attendance"),
]

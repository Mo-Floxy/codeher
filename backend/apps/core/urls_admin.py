from django.urls import path

from apps.core import views

urlpatterns = [
    path("overview/", views.AdminOverviewView.as_view(), name="admin-overview"),
    path("analytics/", views.AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("users/", views.AdminUserListView.as_view(), name="admin-users"),
    path("users/<int:pk>/", views.AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("paths/", views.AdminPathListView.as_view(), name="admin-paths"),
    path("paths/<int:pk>/", views.AdminPathDetailView.as_view(), name="admin-path-detail"),
    path("courses/", views.AdminCourseListView.as_view(), name="admin-courses"),
    path("courses/<int:pk>/", views.AdminCourseDetailView.as_view(), name="admin-course-detail"),
    path("modules/", views.AdminModuleListView.as_view(), name="admin-modules"),
    path("lessons/", views.AdminLessonListView.as_view(), name="admin-lessons"),
    path("lessons/<int:pk>/", views.AdminLessonDetailView.as_view(), name="admin-lesson-detail"),
    path("quizzes/<int:pk>/", views.AdminQuizDetailView.as_view(), name="admin-quiz-detail"),
    path("challenges/", views.AdminChallengeListView.as_view(), name="admin-challenges"),
    path("challenges/<int:pk>/", views.AdminChallengeDetailView.as_view(), name="admin-challenge-detail"),
    path("mentors/", views.AdminMentorListView.as_view(), name="admin-mentors"),
    path("mentors/<int:pk>/", views.AdminMentorDetailView.as_view(), name="admin-mentor-detail"),
    path("reports/", views.AdminReportListView.as_view(), name="admin-reports"),
    path("reports/<int:pk>/resolve/", views.AdminReportResolveView.as_view(), name="admin-report-resolve"),
    path("announcements/", views.AdminAnnouncementListView.as_view(), name="admin-announcements"),
    path("announcements/<int:pk>/", views.AdminAnnouncementDetailView.as_view(), name="admin-announcement-detail"),
    path("testimonials/", views.AdminTestimonialListView.as_view(), name="admin-testimonials"),
    path("testimonials/<int:pk>/", views.AdminTestimonialDetailView.as_view(), name="admin-testimonial-detail"),
]

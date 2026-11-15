from django.urls import path

from apps.courses import views

urlpatterns = [
    path("paths/", views.PathListView.as_view(), name="path-list"),
    path("courses/", views.CourseListView.as_view(), name="course-list"),
    path("courses/<str:lookup>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("courses/<str:lookup>/enroll/", views.CourseEnrollView.as_view(), name="course-enroll"),
    path("courses/<str:lookup>/curriculum/", views.CourseCurriculumView.as_view(), name="course-curriculum"),
    path("lessons/<int:pk>/", views.LessonDetailView.as_view(), name="lesson-detail"),
    path("lessons/<int:pk>/complete/", views.LessonCompleteView.as_view(), name="lesson-complete"),
    path("lessons/<int:pk>/bookmark/", views.LessonBookmarkView.as_view(), name="lesson-bookmark"),
    path("quizzes/<int:pk>/submit/", views.QuizSubmitView.as_view(), name="quiz-submit"),
    path("me/enrollments/", views.MyEnrollmentsView.as_view(), name="my-enrollments"),
    path("me/certificates/", views.MyCertificatesView.as_view(), name="my-certificates"),
    path("me/certificates/<int:pk>/", views.CertificateDetailView.as_view(), name="certificate-detail"),
]

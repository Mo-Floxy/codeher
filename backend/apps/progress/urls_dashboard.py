from django.urls import path

from apps.progress import views

urlpatterns = [path("", views.DashboardView.as_view(), name="dashboard")]

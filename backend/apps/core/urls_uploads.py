from django.urls import path

from apps.core import views

urlpatterns = [path("", views.UploadView.as_view(), name="upload")]

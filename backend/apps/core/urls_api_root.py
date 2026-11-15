from django.urls import path

from apps.core import views

urlpatterns = [path("", views.ApiRootView.as_view(), name="api-root")]

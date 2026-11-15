from django.urls import path

from apps.core import views

urlpatterns = [
    path("stats/", views.SiteStatsView.as_view(), name="site-stats"),
    path("testimonials/", views.TestimonialListView.as_view(), name="site-testimonials"),
    path("events/", views.EventListView.as_view(), name="site-events"),
]

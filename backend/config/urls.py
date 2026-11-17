from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from apps.core.health import health

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # Liveness for the deployment platform; deliberately outside the versioned API.
    path("api/health/", health),
    path("api/auth/", include("apps.users.urls_auth")),
    path("api/users/", include("apps.users.urls")),
    path("api/learning/", include("apps.courses.urls")),
    path("api/progress/", include("apps.progress.urls")),
    path("api/dashboard/", include("apps.progress.urls_dashboard")),
    path("api/challenges/", include("apps.challenges.urls")),
    path("api/community/", include("apps.community.urls")),
    path("api/mentorship/", include("apps.mentorship.urls")),
    path("api/achievements/", include("apps.achievements.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/admin/", include("apps.core.urls_admin")),
    path("api/site/", include("apps.core.urls_site")),
    path("api/uploads/", include("apps.core.urls_uploads")),
    # Drf-style browsable root helps manual API testing during development.
    path("api/", include("apps.core.urls_api_root")),
]

if settings.DEBUG or settings.SERVE_MEDIA_IN_PRODUCTION:
    # django.views.static.serve is not a file server. It keeps uploads reachable in
    # development and on a single-host deployment with a disk; the note next to
    # SERVE_MEDIA_IN_PRODUCTION in settings explains when that is acceptable.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "CodeHer administration"
admin.site.site_title = "CodeHer admin"
admin.site.index_title = "Curriculum, community and platform data"

"""URLs for `/api/achievements/`."""

from rest_framework.routers import SimpleRouter

from apps.achievements.views import AchievementViewSet

router = SimpleRouter()
router.register("", AchievementViewSet, basename="achievement")

urlpatterns = list(router.urls)

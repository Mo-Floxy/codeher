"""URLs for `/api/challenges/`.

A plain router keeps the list-route actions (`leaderboard`, `submissions/me`)
ahead of the `{id-or-slug}/` detail pattern, so those literals never get parsed
as a challenge lookup.
"""

from rest_framework.routers import SimpleRouter

from apps.challenges.views import ChallengeViewSet

router = SimpleRouter()
router.register("", ChallengeViewSet, basename="challenge")

urlpatterns = list(router.urls)

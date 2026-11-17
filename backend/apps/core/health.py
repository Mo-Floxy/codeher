"""Deployment health endpoint.

A platform such as Render polls this to decide whether to keep a service in rotation, so
it answers fast and says only what is true: the database gets a real round trip, and no
credentials, versions or tracebacks appear in the body.
"""

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database = "ok"
    except Exception:
        # A health endpoint that raises cannot report anything; 503 with a reason is the
        # useful answer, and the exception details stay in the server logs.
        database = "unreachable"

    return JsonResponse(
        {
            "status": "ok" if database == "ok" else "degraded",
            "database": database,
            "debug": settings.DEBUG,
        },
        status=200 if database == "ok" else 503,
    )

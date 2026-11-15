import logging
import time
import uuid

logger = logging.getLogger("apps.core.requests")


class RequestLogMiddleware:
    """Tags every request with an id and logs slow API calls for local debugging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        request.request_id = uuid.uuid4().hex[:12]
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response["X-Request-ID"] = request.request_id

        if request.path.startswith("/api/") and (elapsed_ms > 1000 or response.status_code >= 500):
            logger.warning(
                "%s %s -> %s in %.0fms (rid=%s)",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
                request.request_id,
            )
        return response

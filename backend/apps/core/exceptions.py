import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("apps.core.exceptions")


class RunnerUnavailable(APIException):
    """The sandbox could not be reached — reported as 503, never as a fake pass."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "The code runner is unavailable. Try again once the runner service is started."
    default_code = "runner_unavailable"


class ValidationFailed(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The submitted data is not valid."
    default_code = "invalid"


def api_exception_handler(exc, context):
    """Normalises errors so the frontend can rely on one shape."""

    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict):
            payload = response.data
        elif isinstance(response.data, list):
            payload = {"detail": "; ".join(str(item) for item in response.data)}
        else:
            payload = {"detail": str(response.data)}
        payload.setdefault("status", response.status_code)
        response.data = payload
        return response

    logger.exception("Unhandled API error", exc_info=exc)
    return Response(
        {"detail": "An unexpected server error occurred.", "status": 500},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

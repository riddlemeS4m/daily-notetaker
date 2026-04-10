import logging
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from apps.core.exceptions import ApplicationError

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """
    Centralised error handling for the request/response cycle.
    Maps ApplicationError subclasses to the appropriate HTTP status code and
    logs unexpected exceptions with request context.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception,
    ) -> HttpResponse:
        if isinstance(exception, ApplicationError):
            logger.warning(
                "%s on %s %s: %s",
                type(exception).__name__,
                request.method,
                request.path,
                exception,
            )
            return exception.to_response()

        logger.exception(
            "Unhandled exception on %s %s",
            request.method,
            request.path,
        )
        return HttpResponse(status=500)

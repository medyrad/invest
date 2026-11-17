import logging
from uuid import UUID, uuid4

from django.core.exceptions import DisallowedHost
from django.utils.deprecation import MiddlewareMixin

from config.api import error_response

logger = logging.getLogger("invest")


class RequestContextMiddleware(MiddlewareMixin):
    def process_request(self, request):
        incoming = request.headers.get("X-Request-ID", "")
        try:
            if len(incoming) != 36:
                raise ValueError
            request.request_id = str(UUID(incoming))
        except ValueError:
            request.request_id = str(uuid4())
        try:
            request.get_host()
        except DisallowedHost:
            return error_response(request, 400, "invalid_host")

    def process_response(self, request, response):
        response["X-Request-ID"] = request.request_id
        response["Cache-Control"] = "no-store"
        return response

    def process_exception(self, request, exception):
        logger.error(
            "unhandled_error request_id=%s type=%s", request.request_id, type(exception).__name__
        )
        return error_response(request, 500)

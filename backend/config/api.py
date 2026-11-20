import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("invest")
ERRORS = {
    400: ("invalid_request", "درخواست معتبر نیست."),
    403: ("permission_denied", "دسترسی مجاز نیست."),
    404: ("not_found", "مسیر موردنظر پیدا نشد."),
    405: ("method_not_allowed", "این روش درخواست مجاز نیست."),
    415: ("unsupported_media_type", "نوع محتوای درخواست مجاز نیست."),
    429: ("rate_limited", "تعداد درخواست‌ها بیش از حد مجاز است."),
    500: ("internal_error", "خطایی رخ داده است؛ دوباره تلاش کنید."),
}
CODE_MESSAGES = {
    "csrf_failed": (
        "اعتبار امنیتی درخواست پذیرفته نشد؛ صفحه را از نشانی رسمی همین محیط باز کنید، "
        "سپس تازه‌سازی و دوباره تلاش کنید."
    ),
}


def error_data(request, status, code=None):
    default_code, message = ERRORS.get(status, ERRORS[500])
    return {
        "error": {
            "code": code or default_code,
            "message": CODE_MESSAGES.get(code, message),
            "fields": {},
            "request_id": request.request_id,
        }
    }


def error_response(request, status, code=None):
    logger.info(
        "request_failed status=%s code=%s request_id=%s",
        status,
        code or ERRORS.get(status, ERRORS[500])[0],
        request.request_id,
    )
    return JsonResponse(error_data(request, status, code), status=status)


def csrf_failure(request, reason=""):
    return error_response(request, 403, "csrf_failed")


def exception_handler(exc, context):
    request = context["request"]
    if isinstance(exc, APIException):
        status = exc.status_code
        code = exc.get_codes()
        if isinstance(code, list) and len(code) == 1:
            code = code[0]
        code = (
            code
            if isinstance(code, str) and code in ("invalid_version", "invalid_idempotency_key")
            else None
        )
        return Response(error_data(request, status, code), status=status)
    logger.error("unhandled_error request_id=%s type=%s", request.request_id, type(exc).__name__)
    return Response(error_data(request, 500), status=500)


@method_decorator(csrf_protect, name="dispatch")
class CsrfProtectedAPIView(APIView):
    """Explicitly protect anonymous unsafe requests as well as session-authenticated ones."""


def bad_request(request, exception=None):
    return error_response(request, 400)


def permission_denied(request, exception=None):
    return error_response(request, 403)


def not_found(request, exception=None):
    return error_response(request, 404)


def server_error(request):
    return error_response(request, 500)

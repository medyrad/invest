from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.api import CsrfProtectedAPIView
from config.protocol import parse_version, validate_idempotency_key
from config.urls import urlpatterns as base_patterns


class Probe(CsrfProtectedAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        parse_version(request.headers.get("If-Match"))
        validate_idempotency_key(request.headers.get("Idempotency-Key"))
        response = Response(
            {
                "method": request.method,
                "body": request.data,
                "query": request.query_params.get("q"),
                "cookie": request.COOKIES.get("probe"),
            }
        )
        response.set_cookie("probe_reply", "received", httponly=True, samesite="Lax")
        return response


def crash(request):
    raise RuntimeError("PRIVATE-SENTINEL secret=never-show")


urlpatterns = [
    *base_patterns,
    path("api/v1/_test/probe", Probe.as_view()),
    path("api/v1/_test/crash", crash),
]

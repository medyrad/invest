import json

from django.conf import settings
from django.db import DatabaseError, connection
from django.middleware.csrf import get_token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.api import CsrfProtectedAPIView


class PublicBase(CsrfProtectedAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []


class Live(PublicBase):
    def get(self, request):
        return Response({"status": "ok"})


class Ready(PublicBase):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    raise DatabaseError
        except DatabaseError:
            connection.close()
            return Response({"status": "unavailable"}, status=503)
        return Response({"status": "ok"})


class Csrf(PublicBase):
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class Schema(PublicBase):
    def get(self, request):
        return Response(
            json.loads((settings.BASE_DIR.parent / "contracts/openapi.yaml").read_text())
        )

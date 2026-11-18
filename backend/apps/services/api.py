from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response

from apps.identity.sessions import current_session
from apps.workspace.schema import Fault, check_keys
from config.views import PublicBase

from . import advisories, schemas, service
from .evaluation import evaluate


class ServicesAPI(PublicBase):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store, private"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    def handle(self, request, path):
        try:
            parts = path.strip("/").split("/")
            if request.method == "POST":
                check_keys(
                    request.data, list(request.data) if isinstance(request.data, dict) else []
                )
            if request.method == "GET" and parts == ["advisories"]:
                return Response(
                    {
                        "version": 1,
                        "configs": [
                            {k: c[k] for k in ["id", "group", "name", "context"]}
                            for c in advisories.CONFIGS.values()
                        ],
                    }
                )
            if request.method == "POST" and len(parts) == 2 and parts[0] == "advisories":
                check_keys(request.data, ["answers", "funding", "role"])
                return Response(advisories.evaluate(parts[1], **request.data))
            if len(parts) == 2 and parts[0] in ["schema", "evaluate"]:
                kind = parts[1]
                if kind not in schemas.KINDS:
                    raise Fault("نوع خدمت معتبر نیست.", field="kind")
                if request.method == "GET" and parts[0] == "schema":
                    return Response(schemas.definition(kind))
                if request.method == "POST" and parts[0] == "evaluate":
                    check_keys(request.data, ["raw", "schema_version"])
                    if (
                        type(request.data["schema_version"]) is not int
                        or request.data["schema_version"] != 1
                    ):
                        raise Fault("نسخه قرارداد معتبر نیست.", field="schema_version")
                    return Response(evaluate(kind, request.data["raw"]))
            session = current_session(request.COOKIES.get("invest_session"), timezone.now())
            if not session:
                raise Fault("برای ذخیره یا ارسال وارد شوید؛ ورودی شما هنوز ذخیره نشده است.", 403)
            if len(parts) == 3 and parts[0] == "drafts" and request.method == "POST":
                handler = {"report": service.create_report, "submit": service.submit}.get(parts[2])
                if handler:
                    return Response(handler(session, parts[1], request.data))
            if (
                len(parts) == 3
                and parts[0] == "reports"
                and parts[2] in ["download", "package"]
                and request.method == "GET"
            ):
                if parts[2] == "package":
                    response = HttpResponse(
                        service.render_report(session.user, parts[1], package=True),
                        content_type="application/zip",
                    )
                    response["Content-Disposition"] = 'attachment; filename="invest-service.zip"'
                    return response
                response = HttpResponse(
                    service.render_report(session.user, parts[1]),
                    content_type="text/html; charset=utf-8",
                )
                response["Content-Disposition"] = 'attachment; filename="invest-service.html"'
                response["Content-Security-Policy"] = (
                    "default-src 'none'; style-src 'unsafe-inline'; font-src data:; sandbox"
                )
                return response
            raise Fault("مسیر یا روش درخواست پیدا نشد.", 404)
        except Fault as e:
            return Response(
                {
                    "error": {
                        "code": "conflict" if e.status == 409 else "service_error",
                        "message": e.message,
                        "fields": {e.field: e.message},
                        "request_id": request.request_id,
                    },
                    **({"current": e.current} if e.current is not None else {}),
                },
                status=e.status,
            )

    def get(self, request, path):
        return self.handle(request, path)

    def post(self, request, path):
        return self.handle(request, path)

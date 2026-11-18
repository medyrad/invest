from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response

from apps.identity.sessions import current_session
from config.views import PublicBase

from . import service
from .schema import Fault


class WorkspaceAPI(PublicBase):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store, private"
        response["Pragma"] = "no-cache"
        return response

    def execute(self, request, action, id=None, verb="GET"):
        from . import files

        try:
            session = current_session(request.COOKIES.get("invest_session"), timezone.now())
            if not session:
                raise Fault(
                    "نشست معتبر نیست؛ دوباره وارد شوید. ورودی شما هنوز ذخیره نشده است.",
                    403,
                )
            user = session.user
            if verb == "GET":
                if action == "schema":
                    from .other_schema import definition

                    kind = request.query_params.get("kind", "project")
                    from apps.services.schemas import KINDS

                    if kind not in ["project", "fund", "sale", *KINDS]:
                        raise Fault("نوع فرصت معتبر نیست.")
                    result = definition(kind)
                elif action == "owners":
                    result = service.owners(user)
                elif action == "drafts":
                    result = {
                        "drafts": service.list_drafts(
                            user, request.query_params.get("trash") == "1"
                        )
                    }
                elif action == "draft":
                    result = service.get_draft(user, id)
                elif action == "download":
                    data, mime = files.download(user, id)
                    response = HttpResponse(data, content_type=mime)
                    response["Content-Disposition"] = (
                        'attachment; filename="private-file'
                        + (".pdf" if mime == "application/pdf" else ".jpg")
                        + '"'
                    )
                    response["X-Content-Type-Options"] = "nosniff"
                    return response
                else:
                    raise Fault("مسیر پیدا نشد.", 404)
            elif verb == "PUT" and action == "content":
                result = files.receive(user, id, request)
            elif verb == "POST":
                data = request.data
                if action == "drafts":
                    result = service.create_draft(user, data)
                elif action == "draft":
                    result = service.save_draft(user, id, data)
                elif action in ["delete", "restore"]:
                    result = service.draft_action(user, id, action, data)
                elif action == "organizations":
                    result = service.organization(user, data, id)
                elif action == "reserve":
                    result = files.reserve(user, data)
                elif action in ["file-delete", "file-restore", "retry"]:
                    result = files.action(user, id, action, data)
                else:
                    raise Fault("مسیر پیدا نشد.", 404)
            else:
                raise Fault("روش درخواست مجاز نیست.", 405)
            return Response(result)
        except Fault as e:
            body = {
                "error": {
                    "code": "conflict" if e.status == 409 else "workspace_error",
                    "message": e.message,
                    "fields": {e.field: e.message},
                    "request_id": request.request_id,
                }
            }
            if e.current is not None:
                body["current"] = e.current
            return Response(body, status=e.status)

    def get(self, request, action, id=None):
        return self.execute(request, action, id)

    def post(self, request, action, id=None):
        return self.execute(request, action, id, "POST")

    def put(self, request, action, id=None):
        return self.execute(request, action, id, "PUT")

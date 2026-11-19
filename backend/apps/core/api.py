import json

from django.conf import settings
from django.db.models import F as models_F
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response

from apps.identity.models import User
from apps.identity.sessions import current_session, mint_session
from apps.services.models import ServiceSubmission
from apps.workspace.downloads import download_transaction
from apps.workspace.models import Draft, Organization, PrivateFile, RepresentationRequest
from apps.workspace.schema import Fault, check_keys
from apps.workspace.service import application_dto
from config.views import PublicBase

from . import cases, discovery, personal
from . import publication as pub
from .common import identifier, owner, role
from .models import Case, Consent, Event, Opportunity, Personal, Report, Submission


class CoreAPI(PublicBase):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store, private"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    def handle(self, request, path):
        try:
            path = path.strip("/")
            if request.method == "GET" and path == "version":
                return Response({"version": settings.CORE_VERSION})
            parts = path.split("/")
            at = timezone.now()
            if request.method == "POST":
                if not isinstance(request.data, dict):
                    raise Fault("بدنه درخواست باید شیء باشد.")
                check_keys(request.data, list(request.data))
            session = current_session(request.COOKIES.get("invest_session"), at)
            if request.method == "GET" and path == "opportunities":
                try:
                    c = json.loads(request.query_params.get("criteria", "{}"))
                except ValueError as e:
                    raise Fault("معیار معتبر نیست.") from e
                return Response(discovery.listing(c, request.query_params.get("cursor")))
            if request.method == "GET" and len(parts) == 2 and parts[0] == "opportunities":
                return Response(discovery.public_dto(pub.get_op(parts[1])))
            if request.method == "GET" and parts[0] == "public-image" and len(parts) == 2:
                fid = str(identifier(parts[1]))
                s = Submission.objects.filter(
                    review__decision="approved",
                    review__public_files__contains=[fid],
                    opportunity__public_revision_id=models_F("pk"),
                ).first()
                if (
                    not s
                    or s.opportunity.availability == "admin_suspended"
                    or (settings.INVEST_ENV == "public" and pub.is_synthetic(s.opportunity))
                ):
                    raise Fault("تصویر عمومی پیدا نشد.", 404)
                try:
                    f = PrivateFile.objects.get(
                        pk=fid, status="clean", derivative__isnull=False, purged_at__isnull=True
                    )
                except PrivateFile.DoesNotExist as e:
                    raise Fault("تصویر پیدا نشد.", 404) from e
                return HttpResponse(bytes(f.derivative), content_type=f.media_type)
            if request.method == "POST" and path == "compare":
                check_keys(request.data, ["ids"])
                return Response(discovery.compare(request.data["ids"]))
            if request.method == "POST" and len(parts) == 2 and parts[0] == "guide":
                op = pub.get_op(parts[1])
                if not op.public_revision_id:
                    raise Fault("فرصت عمومی نیست.", 404)
                snapshot = personal.report_snapshot(op, request.data, "پیش‌نمایش؛ هنوز ذخیره نشده")
                return Response(
                    {
                        "html": snapshot["rendered_html"],
                        "revision": snapshot["opportunity"]["revision"],
                    }
                )
            if path == "local-roles":
                if settings.INVEST_ENV not in ["development", "test"]:
                    raise Fault("مسیر پیدا نشد.", 404)
                profiles = Personal.objects.filter(
                    profile__local_role=True, user__is_active=True
                ).select_related("user")
                if request.method == "GET":
                    return Response(
                        {
                            "synthetic": True,
                            "roles": [
                                {
                                    "id": str(p.user_id),
                                    "name": p.profile.get("name"),
                                    "role": p.user.role,
                                }
                                for p in profiles
                            ],
                        }
                    )
                check_keys(request.data, ["id"])
                p = profiles.filter(user_id=identifier(request.data["id"])).first()
                if not p:
                    raise Fault("فقط حساب مصنوعی آماده‌شده مجاز است.", 403)
                if session:
                    session.revoked = True
                    session.save(update_fields=["revoked"])
                Event.objects.create(
                    actor=p.user, target=p.user_id, action="synthetic_local_role_entry"
                )
                _, token = mint_session(p.user, at, sensitive=p.user.role in ["admin", "expert"])
                response = Response(
                    {
                        "synthetic": True,
                        "path": "/admin"
                        if p.user.role == "admin"
                        else "/expert"
                        if p.user.role == "expert"
                        else "/workspace"
                        if p.user.role == "owner"
                        else "/opportunities",
                    }
                )
                response.set_cookie(
                    "invest_session",
                    token,
                    httponly=True,
                    samesite="Lax",
                    secure=settings.SESSION_COOKIE_SECURE,
                )
                return response
            if not session:
                raise Fault("برای این بخش وارد شوید.", 403)
            user = session.user
            if request.method == "GET":
                if path == "personal":
                    return Response(personal.state(user))
                if path == "dashboard":
                    admin = user.role == "admin"
                    if admin:
                        role(session, "admin")
                    if user.role == "expert":
                        role(session, "expert")
                    ops = [
                        o
                        for o in Opportunity.objects.select_related("draft", "public_revision")
                        if admin or owner(o) == user
                    ]
                    submissions = Submission.objects.filter(opportunity__in=ops).order_by(
                        "-created_at"
                    )
                    cs = [
                        c
                        for c in Case.objects.select_related(
                            "service_draft__organization",
                            "service_submission",
                            "opportunity__draft",
                            "submission",
                        ).order_by("-created_at")
                        if admin or c.expert_id == user.pk or cases.is_customer(user, c)
                    ]
                    return Response(
                        {
                            "opportunities": [
                                {
                                    "id": str(o.pk),
                                    "draft_id": str(o.draft_id),
                                    "title": o.draft.raw.get("title"),
                                    "availability": o.availability,
                                    "version": o.version,
                                    "public_revision": str(o.public_revision_id)
                                    if o.public_revision_id
                                    else None,
                                }
                                for o in ops
                            ],
                            "submissions": [pub.submission_dto(s) for s in submissions],
                            "applications": [
                                application_dto(a) for a in RepresentationRequest.objects.all()
                            ]
                            if admin
                            else [],
                            "experts": [
                                {
                                    "id": str(u.pk),
                                    "name": u.core_personal.profile.get("name", "کارشناس")
                                    if hasattr(u, "core_personal")
                                    else "کارشناس " + str(u.pk)[:6],
                                }
                                for u in User.objects.filter(role="expert", is_active=True)
                            ]
                            if admin
                            else [],
                            "cases": [cases.dto(c) for c in cs],
                            "contact_grants": [
                                {
                                    "case_id": str(g.case_id),
                                    "title": g.case.submission.snapshot.get("title"),
                                    "kind": g.kind,
                                }
                                for g in Consent.objects.filter(
                                    recipient=user, kind="owner", revoked_at__isnull=True
                                ).select_related("case__opportunity__draft", "case__submission")
                                if owner(g.case.opportunity) == user
                            ],
                            "events": [
                                {
                                    "target": str(e.target),
                                    "action": e.action,
                                    "data": e.data,
                                    "at": e.created_at.isoformat(),
                                }
                                for e in Event.objects.filter(
                                    target__in=[o.pk for o in ops]
                                ).order_by("id")
                            ],
                        }
                    )
                if parts[0] == "cases" and len(parts) == 2:
                    return Response(cases.dto(cases.get_case(session, parts[1])))
                if parts[0] == "contact" and len(parts) == 2:
                    return Response(cases.contact(session, parts[1]))
                if parts[0] == "reports" and len(parts) == 2:
                    r = Report.objects.filter(pk=identifier(parts[1])).first()
                    from apps.services.service import permitted_report

                    if not r or not permitted_report(user, r):
                        raise Fault("گزارش پیدا نشد.", 404)
                    if r.snapshot.get("subject_type") == "service":
                        from apps.services.service import render_report

                        body = render_report(user, r.pk, as_json=True)
                        content_type = "application/json; charset=utf-8"
                        filename = "invest-report.json"
                    else:
                        body = r.snapshot.get("rendered_html")
                        if not isinstance(body, str) or r.snapshot.get("template_version", 1) < 2:
                            body = personal._report_html(r.snapshot)
                        content_type = "text/html; charset=utf-8"
                        filename = "invest-guide.html"
                    response = HttpResponse(
                        body,
                        content_type=content_type,
                    )
                    response["Content-Disposition"] = f'attachment; filename="{filename}"'
                    if content_type.startswith("text/html"):
                        response["Content-Security-Policy"] = (
                            "default-src 'none'; style-src 'unsafe-inline'; sandbox"
                        )
                    return response
                if parts[0] == "private-file" and len(parts) == 2:
                    return self.private_file(session, parts[1])
            elif request.method == "POST":
                data = request.data
                if path == "personal":
                    return Response(personal.mutate(user, data, session=session))
                if path == "cases":
                    return Response(cases.create(session, data))
                if len(parts) == 2:
                    action, id = parts
                    handler = {
                        "submit": pub.submit,
                        "review": pub.review,
                        "organization": pub.organization_review,
                        "availability": pub.availability,
                        "cases": cases.action,
                    }.get(action)
                    if handler:
                        return Response(handler(session, id, data))
            raise Fault("مسیر یا روش درخواست پیدا نشد.", 404)
        except Fault as e:
            return Response(
                {
                    "error": {
                        "code": "conflict" if e.status == 409 else "core_error",
                        "message": e.message,
                        "fields": {e.field: e.message},
                        "request_id": request.request_id,
                    }
                },
                status=e.status,
            )

    def get(self, request, path):
        return self.handle(request, path)

    def post(self, request, path):
        return self.handle(request, path)

    @download_transaction
    def private_file(self, session, id):
        user = session.user
        try:
            f = PrivateFile.objects.get(pk=identifier(id), status="clean", purged_at__isnull=True)
        except PrivateFile.DoesNotExist as e:
            raise Fault("فایل پیدا نشد.", 404) from e
        parent = Draft if f.draft_id else RepresentationRequest
        organization_id = parent.objects.values_list("organization_id", flat=True).get(
            pk=f.draft_id or f.application_id
        )
        if organization_id:
            Organization.objects.select_for_update().get(pk=organization_id)
        f = PrivateFile.objects.select_for_update().get(pk=f.pk)
        if f.status != "clean" or f.purged_at:
            raise Fault("فایل اکنون قابل دریافت نیست.", 409, "files")
        allowed = False
        if user.role == "admin":
            role(session, "admin")
            allowed = bool(
                f.application_id
                or ServiceSubmission.objects.filter(files__contains=[str(f.pk)]).exists()
                or Submission.objects.filter(files__contains=[str(f.pk)]).exists()
            )
        if not allowed:
            for c in Case.objects.filter(
                Q(message__files__contains=[str(f.pk)])
                | Q(service_submission__files__contains=[str(f.pk)])
            ).distinct():
                if cases.is_customer(user, c) or user.pk == c.expert_id:
                    cases.get_case(session, c.pk)
                    allowed = True
                    break
        if not allowed:
            raise Fault("دسترسی به مدرک مجاز نیست.", 403)
        response = HttpResponse(
            bytes(f.derivative if f.derivative is not None else f.content),
            content_type=f.media_type,
        )
        response["Content-Disposition"] = 'attachment; filename="invest-private-file"'
        return response

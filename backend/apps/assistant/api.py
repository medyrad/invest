import hashlib
import json
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.response import Response

from apps.identity.sessions import current_session
from apps.workspace.schema import Fault
from config.views import PublicBase

from . import quota
from .models import QuotaPolicy
from .orchestrator import prepare_turn, product_tool_runner, provider_context
from .provider import ProviderError, get_provider, provider_status


def _payload(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _history(value):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 12:
        raise Fault("تاریخچه معتبر نیست.")
    output = []
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {"role", "text"}
            or item.get("role") not in {"user", "assistant"}
            or not isinstance(item.get("text"), str)
            or len(item["text"]) > 4000
        ):
            raise Fault("تاریخچه فقط پیام متنی محدود است.")
        output.append({"role": item["role"], "text": item["text"]})
    return output


class AssistantAPI(PublicBase):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store, private"
        response["Pragma"] = "no-cache"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    def _with_guest(self, response, p):
        response.set_cookie(
            quota.COOKIE,
            quota.signed_guest(p.guest_value),
            httponly=True,
            samesite="Lax",
            secure=settings.SESSION_COOKIE_SECURE,
            max_age=400 * 86400,
        )
        return response

    def get(self, request, path):
        p = quota.principal(request)
        if path.strip("/") == "status":
            return self._with_guest(Response(provider_status()), p)
        if path.strip("/") != "usage":
            return self._error(request, "not_found", "مسیر دستیار پیدا نشد.", 404, p)
        return self._with_guest(Response(quota.usage_view(p)), p)

    def post(self, request, path):
        p = quota.principal(request)
        if path.strip("/") == "turns/stream":
            return self._stream(request, p)
        try:
            if path.strip("/") != "turns" or not isinstance(request.data, dict):
                raise Fault("مسیر یا بدنه معتبر نیست.", 404)
            allowed = {"message", "criteria", "opportunity_ids", "history", "purpose"}
            if set(request.data) - allowed or "message" not in request.data:
                raise Fault("کلیدهای درخواست با قرارداد یکسان نیستند.")
            message = request.data.get("message")
            criteria = request.data.get("criteria")
            ids = request.data.get("opportunity_ids") or []
            purpose = request.data.get("purpose", "product")
            if purpose != "product" and settings.INVEST_ENV != "test":
                raise Fault("نوع اجرا مجاز نیست.", 403)
            if (
                not isinstance(ids, list)
                or len(ids) > 4
                or any(not isinstance(x, str) for x in ids)
            ):
                raise Fault("شناسه فرصت معتبر نیست.")
            history = _history(request.data.get("history"))
            prepared = prepare_turn(
                message=message, criteria=criteria, opportunity_ids=ids, history=history
            )
            normalized = prepared.normalized
            decision = prepared.decision
            model = decision.model
            clarification_only = prepared.server_result is None
            server_result = prepared.server_result or {"items": [], "total": 0}
            provider = get_provider()
            if not provider.available:
                response = Response(
                    {
                        "state": "failed",
                        "error": {
                            "code": "provider_unavailable",
                            "message": (
                                "دستیار متصل در دسترس نیست؛ نتایج سرور و مسیر دستی آماده است."
                            ),
                        },
                        "interpretation": normalized,
                        "server_result": server_result,
                        "quota": quota.usage_view(p),
                        "steps": [
                            {"id": "interpretation", "status": "completed"},
                            {"id": "public_data", "status": "completed"},
                            {"id": "explanation", "status": "failed"},
                        ],
                    },
                    status=503,
                )
                return self._with_guest(response, p)
            key = request.headers.get("Idempotency-Key", "")
            body_hash = _payload(
                {
                    "message": message,
                    "criteria": normalized["criteria"],
                    "ids": ids,
                    "route": decision.code,
                }
            )
            reservation, policy, replay = quota.reserve(
                p,
                key,
                body_hash,
                model,
                purpose,
                route_code=decision.code,
                route_reason=decision.reason,
                router_version=decision.version,
            )
            if replay:
                code = (
                    "in_progress"
                    if reservation.status == "reserved"
                    else "completed_reply_unavailable"
                    if reservation.status == "completed"
                    else reservation.failure_code or reservation.status
                )
                return self._with_guest(
                    Response(
                        {
                            "state": "failed",
                            "error": {
                                "code": code,
                                "message": (
                                    "متن پاسخ روی سرور نگهداری نمی‌شود؛ مسیر دستی یا "
                                    "نوبت صریح تازه را انتخاب کنید."
                                ),
                            },
                            "receipt": str(reservation.pk),
                            "quota": quota.usage_view(p),
                            "steps": [
                                {"id": "interpretation", "status": "completed"},
                                {"id": "public_data", "status": "completed"},
                                {"id": "explanation", "status": "failed"},
                            ],
                        },
                        status=409,
                    ),
                    p,
                )
            try:
                result = provider.complete(
                    provider_context(
                        prepared, lambda: quota.claim_provider_call(reservation)
                    ),
                    product_tool_runner(prepared),
                    policy,
                    reservation,
                )
            except ProviderError as exc:
                status = "held" if exc.unknown_cost else "failed"
                usage = {**exc.usage, "calls": exc.calls}
                quota.settle(
                    reservation,
                    status=status,
                    usage=usage,
                    request_id=exc.request_id,
                    failure_code=exc.code,
                )
                return self._with_guest(
                    Response(
                        {
                            "state": "failed",
                            "error": {
                                "code": exc.code,
                                "message": "پاسخ کامل نشد؛ ورودی شما برای ادامه دستی محفوظ است.",
                            },
                            "interpretation": normalized,
                            "server_result": server_result,
                            "receipt": str(reservation.pk),
                            "quota": quota.usage_view(p),
                            "steps": [
                                {"id": "interpretation", "status": "completed"},
                                {"id": "public_data", "status": "completed"},
                                {"id": "explanation", "status": "failed"},
                            ],
                        },
                        status=503,
                    ),
                    p,
                )
            quota.settle(
                reservation,
                status="completed",
                usage=result.usage,
                model_returned=result.model,
                request_id=result.request_id,
            )
            return self._with_guest(
                Response(
                    {
                        "state": "needs_clarification" if clarification_only else "completed",
                        "interpretation": normalized,
                        "server_result": server_result,
                        **result.output,
                        "receipt": str(reservation.pk),
                        "quota": quota.usage_view(p),
                        "versions": {
                            "model_requested": model,
                            "model_returned": result.model,
                            "route": decision.code,
                            "route_reason": decision.reason,
                            "router": decision.version,
                            "prompt": quota.PROMPT_VERSION,
                            "tool": quota.TOOL_VERSION,
                            "schema": quota.SCHEMA_VERSION,
                            "policy": policy.version,
                        },
                        "steps": [
                            {"id": "interpretation", "status": "completed"},
                            {
                                "id": "public_data",
                                "status": "not_run" if clarification_only else "completed",
                            },
                            {"id": "explanation", "status": "completed"},
                        ],
                    }
                ),
                p,
            )
        except quota.QuotaError as exc:
            fields = {"retry_after": exc.retry_after} if exc.retry_after else {}
            return self._with_guest(
                Response(
                    {
                        "error": {
                            "code": exc.code,
                            "message": exc.message,
                            "fields": fields,
                            "request_id": request.request_id,
                        },
                        "state": "failed",
                        "quota": quota.usage_view(p),
                    },
                    status=exc.status,
                ),
                p,
            )
        except Fault as exc:
            return self._error(request, "assistant_error", exc.message, exc.status, p)

    def _stream(self, request, p):
        def line(value):
            return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"

        def events():
            try:
                if not isinstance(request.data, dict):
                    raise Fault("بدنه معتبر نیست.")
                allowed = {"message", "criteria", "opportunity_ids", "history", "purpose"}
                if set(request.data) - allowed or "message" not in request.data:
                    raise Fault("کلیدهای درخواست با قرارداد یکسان نیستند.")
                message = request.data.get("message")
                criteria = request.data.get("criteria")
                ids = request.data.get("opportunity_ids") or []
                purpose = request.data.get("purpose", "product")
                if purpose != "product" and settings.INVEST_ENV != "test":
                    raise Fault("نوع اجرا مجاز نیست.", 403)
                if (
                    not isinstance(ids, list)
                    or len(ids) > 4
                    or any(not isinstance(value, str) for value in ids)
                ):
                    raise Fault("شناسه فرصت معتبر نیست.")
                history = _history(request.data.get("history"))
                yield line(
                    {
                        "event": "progress",
                        "stage": "interpretation",
                        "status": "active",
                        "detail": "متن و شرط‌های قابل مشاهده در حال اعتبارسنجی است.",
                    }
                )
                prepared = prepare_turn(
                    message=message, criteria=criteria, opportunity_ids=ids, history=history
                )
                normalized = prepared.normalized
                yield line(
                    {
                        "event": "progress",
                        "stage": "interpretation",
                        "status": "completed",
                        "detail": f"{len(normalized['criteria'])} شرط معتبر برداشت شد.",
                        "interpretation": normalized,
                    }
                )
                decision = prepared.decision
                clarification_only = prepared.server_result is None
                yield line(
                    {
                        "event": "progress",
                        "stage": "public_data",
                        "status": "active",
                        "detail": "نسخه‌های عمومی جاری در سرور بازخوانی می‌شوند.",
                    }
                )
                server_result = prepared.server_result or {"items": [], "total": 0}
                count = len(server_result.get("items") or server_result.get("rows") or [])
                yield line(
                    {
                        "event": "progress",
                        "stage": "public_data",
                        "status": "not_run" if clarification_only else "completed",
                        "detail": "تا رفع ابهام، جست‌وجوی عمومی اجرا نمی‌شود."
                        if clarification_only
                        else f"{count} مورد از داده عمومی جاری آماده شد.",
                        "server_result": server_result,
                    }
                )
                provider = get_provider()
                if not provider.available:
                    yield line(
                        {
                            "event": "failure",
                            "data": {
                                "state": "failed",
                                "error": {"code": "provider_unavailable", "message": "دستیار متصل در دسترس نیست؛ مسیر دستی آماده است."},
                                "interpretation": normalized,
                                "server_result": server_result,
                                "quota": quota.usage_view(p),
                            },
                        }
                    )
                    return
                yield line(
                    {
                        "event": "progress",
                        "stage": "explanation",
                        "status": "active",
                        "detail": "توضیح مستند در حال تولید و سپس اعتبارسنجی مستقل است.",
                    }
                )
                key = request.headers.get("Idempotency-Key", "")
                body_hash = _payload(
                    {
                        "message": message,
                        "criteria": normalized["criteria"],
                        "ids": ids,
                        "route": decision.code,
                    }
                )
                reservation, policy, replay = quota.reserve(
                    p,
                    key,
                    body_hash,
                    decision.model,
                    purpose,
                    route_code=decision.code,
                    route_reason=decision.reason,
                    router_version=decision.version,
                )
                if replay:
                    raise quota.QuotaError(
                        "completed_reply_unavailable" if reservation.status == "completed" else "in_progress",
                        "متن پاسخ روی سرور نگهداری نمی‌شود؛ وضعیت همان تلاش بازیابی شد.",
                        409,
                    )
                try:
                    result = provider.complete(
                        provider_context(
                            prepared, lambda: quota.claim_provider_call(reservation)
                        ),
                        product_tool_runner(prepared),
                        policy,
                        reservation,
                    )
                except ProviderError as exc:
                    quota.settle(
                        reservation,
                        status="held" if exc.unknown_cost else "failed",
                        usage={**exc.usage, "calls": exc.calls},
                        request_id=exc.request_id,
                        failure_code=exc.code,
                    )
                    yield line(
                        {
                            "event": "progress",
                            "stage": "explanation",
                            "status": "failed",
                            "detail": "پاسخ معتبر کامل نشد؛ متن شما محفوظ است.",
                        }
                    )
                    yield line(
                        {
                            "event": "failure",
                            "data": {
                                "state": "failed",
                                "error": {"code": exc.code, "message": "پاسخ کامل نشد؛ مسیر دستی آماده است."},
                                "interpretation": normalized,
                                "server_result": server_result,
                                "receipt": str(reservation.pk),
                                "quota": quota.usage_view(p),
                            },
                        }
                    )
                    return
                quota.settle(
                    reservation,
                    status="completed",
                    usage=result.usage,
                    model_returned=result.model,
                    request_id=result.request_id,
                )
                yield line(
                    {
                        "event": "progress",
                        "stage": "explanation",
                        "status": "completed",
                        "detail": "پاسخ ساختاریافته اعتبارسنجی شد.",
                    }
                )
                yield line(
                    {
                        "event": "result",
                        "data": {
                            "state": "needs_clarification" if clarification_only else "completed",
                            "interpretation": normalized,
                            "server_result": server_result,
                            **result.output,
                            "receipt": str(reservation.pk),
                            "quota": quota.usage_view(p),
                            "versions": {
                                "model_returned": result.model,
                                "route": decision.code,
                                "route_reason": decision.reason,
                                "router": decision.version,
                                "prompt": quota.PROMPT_VERSION,
                                "tool": quota.TOOL_VERSION,
                                "schema": quota.SCHEMA_VERSION,
                                "policy": policy.version,
                            },
                        },
                    }
                )
            except quota.QuotaError as exc:
                yield line({"event": "failure", "data": {"state": "failed", "error": {"code": exc.code, "message": exc.message}, "quota": quota.usage_view(p)}})
            except Fault as exc:
                yield line({"event": "failure", "data": {"state": "failed", "error": {"code": "assistant_error", "message": exc.message}}})
            except Exception:
                yield line({"event": "failure", "data": {"state": "failed", "error": {"code": "internal_error", "message": "پردازش کامل نشد؛ مسیر دستی آماده است."}}})

        response = StreamingHttpResponse(events(), content_type="application/x-ndjson; charset=utf-8")
        response["X-Accel-Buffering"] = "no"
        return self._with_guest(response, p)

    def put(self, request, path):
        p = quota.principal(request)
        try:
            if path.strip("/") != "policy" or not isinstance(request.data, dict):
                raise Fault("مسیر یا بدنه معتبر نیست.", 404)
            session = current_session(request.COOKIES.get("invest_session"), timezone.now())
            if not session or session.user.role != "admin":
                raise Fault("فقط مدیر مجاز است.", 403)
            if set(request.data) != {"expected_version", "values"} or not isinstance(
                request.data["values"], dict
            ):
                raise Fault("قرارداد سیاست معتبر نیست.")
            allowed = {
                "guest_daily",
                "account_daily",
                "concurrent_turns",
                "guest_hourly_starts",
                "account_hourly_starts",
                "monthly_usd",
                "principal_monthly_usd",
                "turn_reserve_usd",
                "smoke_usd",
                "eval_usd",
                "max_input_tokens",
                "max_output_tokens",
                "max_provider_calls",
                "deadline_seconds",
                "safe_retries",
            }
            if set(request.data["values"]) - allowed:
                raise Fault("فیلد سیاست مجاز نیست.")
            with transaction.atomic():
                current = (
                    QuotaPolicy.objects.select_for_update()
                    .filter(active=True)
                    .order_by("-version")
                    .first()
                )
                if not current:
                    current = QuotaPolicy.objects.create(version=1)
                if request.data["expected_version"] != current.version:
                    raise Fault("سیاست هم‌زمان تغییر کرده است.", 409)
                values = {name: getattr(current, name) for name in allowed}
                values.update(request.data["values"])
                if int(values["guest_daily"]) < 1 or int(values["account_daily"]) < int(
                    values["guest_daily"]
                ):
                    raise Fault("سهمیه حساب باید دست‌کم سهمیه مهمان باشد.")
                if int(values["guest_daily"]) > 3 or int(values["account_daily"]) > 20:
                    raise Fault("سهمیه روزانه از مصوبه بیشتر است.")
                if (
                    not 1 <= int(values["concurrent_turns"]) <= 2
                    or not 1 <= int(values["max_provider_calls"]) <= 4
                ):
                    raise Fault("حد هم‌زمانی یا فراخوانی معتبر نیست.")
                if int(values["guest_hourly_starts"]) < 1 or int(
                    values["account_hourly_starts"]
                ) < int(values["guest_hourly_starts"]):
                    raise Fault("حد ساعتی حساب باید دست‌کم حد مهمان باشد.")
                if (
                    int(values["guest_hourly_starts"]) > 10
                    or int(values["account_hourly_starts"]) > 60
                ):
                    raise Fault("حد ساعتی از مصوبه بیشتر است.")
                monthly = Decimal(str(values["monthly_usd"]))
                principal_monthly = Decimal(str(values["principal_monthly_usd"]))
                reserve = Decimal(str(values["turn_reserve_usd"]))
                smoke = Decimal(str(values["smoke_usd"]))
                evaluation = Decimal(str(values["eval_usd"]))
                if (
                    reserve <= 0
                    or smoke < reserve
                    or evaluation < reserve
                    or monthly < smoke + evaluation
                    or principal_monthly <= 0
                    or principal_monthly > Decimal("10")
                    or reserve > Decimal("0.10")
                    or smoke > Decimal("5")
                    or evaluation > Decimal("15")
                    or monthly > Decimal("100")
                ):
                    raise Fault("سقف‌های هزینه با یکدیگر سازگار نیستند.")
                if (
                    not 1 <= int(values["max_input_tokens"]) <= 8000
                    or not 1 <= int(values["max_output_tokens"]) <= 1000
                ):
                    raise Fault("سقف token از مصوبه بیشتر است.")
                if (
                    not 1 <= int(values["deadline_seconds"]) <= 45
                    or not 0 <= int(values["safe_retries"]) <= 1
                ):
                    raise Fault("مهلت یا retry از مصوبه بیشتر است.")
                current.active = False
                current.save(update_fields=["active"])
                created = QuotaPolicy.objects.create(version=current.version + 1, **values)
            return self._with_guest(Response({"version": created.version}), p)
        except Fault as exc:
            return self._error(request, "assistant_error", exc.message, exc.status, p)

    def _error(self, request, code, message, status, p):
        return self._with_guest(
            Response(
                {
                    "error": {
                        "code": code,
                        "message": message,
                        "fields": {},
                        "request_id": request.request_id,
                    }
                },
                status=status,
            ),
            p,
        )

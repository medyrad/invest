from datetime import timedelta

from django.conf import settings
from django.middleware.csrf import rotate_token
from rest_framework.response import Response

from config.views import PublicBase

from . import otp, sessions

COOKIE = "invest_session"
MESSAGES = {
    "invalid_mobile": "شماره موبایل ایران را با قالب درست وارد کنید.",
    "invalid_code": "کد صحیح نیست؛ دوباره بررسی کنید.",
    "challenge_expired": "اعتبار کد تمام شده است؛ کد تازه بگیرید.",
    "challenge_exhausted": "تعداد تلاش این کد تمام شد؛ کد تازه بگیرید.",
    "challenge_replaced": "این کد جایگزین شده است؛ آخرین کد را وارد کنید.",
    "challenge_cancelled": "این کد لغو شده است؛ کد تازه بگیرید.",
    "challenge_revoked": "اعتبار این ورود باطل شده است.",
    "rate_limited": "کمی صبر کنید و دوباره تلاش کنید.",
    "recovery_required": "کد مصرف شده است؛ وضعیت ورود را بررسی کنید یا ورود تازه آغاز کنید.",
    "flow_expired": "زمان این جریان ورود تمام شد؛ پنجره را دوباره باز کنید.",
    "delivery_unavailable": "ارسال پیامک پیکربندی نشده است.",
}


class AuthAPI(PublicBase):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["Cache-Control"] = "no-store, private"
        response["Pragma"] = "no-cache"
        return response

    def fields(self, request, expected):
        if not isinstance(request.data, dict) or set(request.data) != set(expected):
            raise otp.Fault("invalid_request")

    def get(self, request, action, owner=None):
        try:
            if action == "me":
                return Response(sessions.me(request.COOKIES.get(COOKIE)))
            if action == "private":
                return Response(sessions.operate(request.COOKIES.get(COOKIE), action, owner)[0])
            return Response(status=405)
        except otp.Fault as exc:
            return self.failure(request, exc)

    def post(self, request, action, owner=None):
        token = request.headers.get("X-Login-Flow", "")
        cookie = request.COOKIES.get(COOKIE)
        secret = None
        try:
            expected = {
                "issue": ("mobile", "key"),
                "verify": ("challenge_id", "code"),
                "reauth": ("challenge_id", "code"),
                "intent": ("destination", "snapshot"),
            }.get(action, ())
            self.fields(request, expected)
            if action == "flows":
                result = otp.new_flow()
            elif action == "issue":
                result = otp.issue(
                    token,
                    request.data["mobile"],
                    request.data["key"],
                    request.META.get("REMOTE_ADDR", ""),
                )
            elif action == "edit":
                result = otp.edit(token)
            elif action in ("verify", "reauth"):
                result, secret = otp.verify(
                    token,
                    request.data["challenge_id"],
                    request.data["code"],
                    cookie,
                    action == "reauth",
                )
                rotate_token(request)
            elif action in ("intent", "intent/cancel", "intent/consume"):
                result = otp.intent(
                    token,
                    {"intent": "set", "intent/cancel": "cancel", "intent/consume": "consume"}[
                        action
                    ],
                    request.data,
                    cookie,
                )
            else:
                result, secret = sessions.operate(cookie, action, owner)
            response = Response(result)
            if result.get("delivery") == "failed":
                response = self.failure(request, otp.Fault("delivery_unavailable", 503))
                response.data["receipt"] = result
            if secret:
                # Rotation and reauth never extend absolute expiry.
                with sessions.identity_transaction():
                    session = sessions.AuthSession.objects.get(digest=otp.digest(secret))
                    absolute = timedelta(hours=12) if session.sensitive else timedelta(days=7)
                    age = max(0, int((session.created_at + absolute - otp.now()).total_seconds()))
                response.set_cookie(
                    COOKIE,
                    secret,
                    max_age=age,
                    httponly=True,
                    secure=settings.SESSION_COOKIE_SECURE,
                    samesite="Lax",
                    path="/",
                )
            if action in ("logout", "revoke-all"):
                response.delete_cookie(COOKIE, path="/", samesite="Lax")
            return response
        except otp.Fault as exc:
            return self.failure(request, exc)

    def failure(self, request, exc):
        body = {
            "error": {
                "code": exc.code,
                "message": MESSAGES.get(exc.code, "درخواست مجاز یا معتبر نیست."),
                "fields": {},
                "request_id": request.request_id,
            }
        }
        response = Response(body, status=exc.status)
        if exc.retry_after is not None:
            body["retry_after"] = exc.retry_after
            response["Retry-After"] = str(exc.retry_after)
        return response

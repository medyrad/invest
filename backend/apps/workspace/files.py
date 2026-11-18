import hashlib
import re
import socket
import struct
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from . import service
from .models import Draft, PrivateFile, ReceiveAttempt, RepresentationRequest
from .schema import Fault, check_keys

MIB = 1048576


def file_target(user, f, trash=False, lock=False):
    return service.target(
        user,
        "draft" if f.draft_id else "request",
        f.draft_id or f.application_id,
        trash=trash,
        lock=lock,
    )


def get_file(user, id, trash=False):
    try:
        f = PrivateFile.objects.get(pk=id)
    except (ValueError, PrivateFile.DoesNotExist) as e:
        raise Fault("فایل پیدا نشد.", 404) from e
    file_target(user, f, trash=trash, lock=True)
    f = PrivateFile.objects.select_for_update().get(pk=id)
    if f.purged_at:
        raise Fault("فایل پاک‌سازی شده است.", 404)
    return f


def reserve(user, data):
    check_keys(
        data, ["key", "target_type", "target_id", "kind", "name", "size", "sha256", "replaces"]
    )
    if (
        data["target_type"] not in ["draft", "request"]
        or data["kind"] not in ["image", "document"]
        or data["target_type"] == "request"
        and data["kind"] != "document"
    ):
        raise Fault("نوع فایل یا مقصد مجاز نیست.")
    size = data["size"]
    kind = data["kind"]
    name = data["name"]
    if type(size) is not int or size <= 0 or size > (10 if kind == "image" else 20) * MIB:
        raise Fault("حجم تصویر تا۱۰ و مدرک تا۲۰ مگابایت مجاز است.", field="file")
    if (
        not isinstance(name, str)
        or len(name) > 200
        or "/" in name
        or "\\" in name
        or name.rsplit(".", 1)[-1].lower()
        not in (
            ["jpg", "jpeg", "png", "webp"] if kind == "image" else ["pdf", "jpg", "jpeg", "png"]
        )
    ):
        raise Fault("پسوند فایل در فهرست مجاز نیست.", field="file")
    if not isinstance(data["sha256"], str) or not re.fullmatch("[a-f0-9]{64}", data["sha256"]):
        raise Fault("اثر انگشت فایل معتبر نیست.")

    def run():
        t = service.target(user, data["target_type"], data["target_id"], lock=True)
        qs = PrivateFile.objects.filter(purged_at__isnull=True)
        account = qs.filter(uploader=user)
        if (account.aggregate(n=Sum("size"))["n"] or 0) + size > settings.WORKSPACE_ACCOUNT_BYTES:
            raise Fault("سقف کل دریافت حساب پر است؛ حذف و پاک‌سازی را بررسی کنید.", 429, "file")
        if (
            account.filter(created_at__gt=timezone.now() - timedelta(hours=1)).count()
            >= settings.WORKSPACE_HOURLY_UPLOADS
        ):
            raise Fault("سقف دریافت ساعتی حساب پر است؛ بعداً تلاش کنید.", 429, "file")
        same = qs.filter(
            **{"draft" if data["target_type"] == "draft" else "application": t}, kind=kind
        )
        limit_count, limit_bytes = (10, 50 * MIB) if kind == "image" else (20, 100 * MIB)
        if (
            same.count() >= limit_count
            or (same.aggregate(n=Sum("size"))["n"] or 0) + size > limit_bytes
        ):
            raise Fault("سقف تعداد یا حجم فایل‌های این بخش پر است.", 429, "file")
        replaces = None
        if data["replaces"] is not None:
            replaces = get_file(user, data["replaces"])
            if (
                replaces.kind != kind
                or replaces.draft_id != (t.pk if isinstance(t, Draft) else None)
                or replaces.application_id
                != (t.pk if isinstance(t, RepresentationRequest) else None)
                or not replaces.attached
                or replaces.deleted_at
            ):
                raise Fault("فایل جایگزین باید از همین بخش و متصل باشد.")
        f = PrivateFile.objects.create(
            uploader=user,
            kind=kind,
            name=name,
            size=size,
            sha256=data["sha256"],
            replaces=replaces,
            **{"draft" if isinstance(t, Draft) else "application": t},
        )
        return service.file_dto(f), data["target_type"], t.pk

    return service.operation(user, data, "reserve", run)


def receive(user, id, stream):
    # Commit admission separately: failed/checksum-mismatched retries consume the rate budget.
    with transaction.atomic():
        service.User.objects.select_for_update().get(pk=user.pk)
        get_file(user, id)
        recent = ReceiveAttempt.objects.filter(
            user=user, created_at__gt=timezone.now() - timedelta(hours=1)
        )
        if recent.count() >= settings.WORKSPACE_HOURLY_RECEIVES:
            raise Fault("سقف تلاش دریافت ساعتی حساب پر است.", 429, "file")
        ReceiveAttempt.objects.create(user=user)
    with transaction.atomic():
        f = get_file(user, id)
        if (
            f.deleted_at
            or f.replaced_at
            or timezone.now() >= f.created_at + timedelta(hours=24)
            and not f.received_at
        ):
            raise Fault("رزرو دریافت منقضی یا حذف شده است.")
        # DRF Request.read delegates to the underlying bounded stream; never parse multipart.
        content = bytearray()
        digest = hashlib.sha256()
        while True:
            chunk = stream.read(min(65536, f.size + 1 - len(content)))
            if not chunk:
                break
            content.extend(chunk)
            digest.update(chunk)
            if len(content) > f.size:
                raise Fault("حجم فایل با رزرو یکسان نیست.", field="file")
        if len(content) != f.size or digest.hexdigest() != f.sha256:
            raise Fault("فایل ناقص یا متفاوت است؛ همان فایل را دوباره ارسال کنید.", field="file")
        if f.received_at:
            return service.file_dto(f)
        f.content = bytes(content)
        f.received_at = timezone.now()
        f.next_check = timezone.now()
        f.save()
        return service.file_dto(f)


def scan(data):
    with socket.create_connection((settings.CLAMAV_HOST, settings.CLAMAV_PORT), timeout=30) as s:
        s.settimeout(30)
        s.sendall(b"zINSTREAM\0")
        for start in range(0, len(data), 65536):
            chunk = data[start : start + 65536]
            s.sendall(struct.pack("!I", len(chunk)) + chunk)
        s.sendall(struct.pack("!I", 0))
        result = bytearray()
        while len(result) < 4096:
            chunk = s.recv(1024)
            if not chunk:
                break
            result.extend(chunk)
            if b"\0" in chunk:
                break
    response = bytes(result).rstrip(b"\0\n")
    if response == b"stream: OK":
        return "clean"
    if response.endswith(b" FOUND"):
        return "quarantined"
    raise OSError("scanner_unavailable")


def inspect(data, name, kind):
    parser = Path(__file__).with_name("inspect_file.py")
    try:
        result = subprocess.run(
            [sys.executable, str(parser), name.rsplit(".", 1)[-1].lower(), kind],
            input=data,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode or len(result.stdout) > 10 * MIB + 200:
            raise ValueError()
        import json

        header, _, body = result.stdout.partition(b"\n")
        mime = json.loads(header)["mime"]
        if mime not in ["application/pdf", "image/jpeg"]:
            raise ValueError()
        return mime, body or None
    except (ValueError, KeyError, subprocess.TimeoutExpired) as e:
        raise Fault("نوع/محتوای فایل پذیرفته نیست یا از سقف پردازش بیشتر است.", field="file") from e


def parent_lock(f):
    model = Draft if f.draft_id else RepresentationRequest
    return model.objects.select_for_update().get(pk=f.draft_id or f.application_id)


def check_one(at=None):
    at = at or timezone.now()
    eligible = dict(
        status="pending_check",
        received_at__isnull=False,
        purged_at__isnull=True,
        deleted_at__isnull=True,
        next_check__lte=at,
    )
    with transaction.atomic():
        candidate = PrivateFile.objects.filter(**eligible).order_by("created_at").first()
        if not candidate:
            return False
        t = parent_lock(candidate)
        f = (
            PrivateFile.objects.select_for_update(skip_locked=True)
            .filter(pk=candidate.pk, **eligible)
            .first()
        )
        if not f or isinstance(t, Draft) and t.deleted_at:
            return False
        f.attempts += 1
        # A bounded lease survives worker death. No parent lock spans scanner/parser I/O.
        f.next_check = at + timedelta(seconds=120)
        f.save(update_fields=["attempts", "next_check"])
        attempt = f.attempts
        data, name, kind = bytes(f.content), f.name, f.kind
    state, reason, mime, derivative = "pending_check", "", "", None
    try:
        state = scan(data)
        if state == "clean":
            try:
                mime, derivative = inspect(data, name, kind)
            except Fault as exc:
                state, reason = "rejected", exc.message
        else:
            reason = "فایل مشکوک است و دریافت آن مجاز نیست؛ فایل دیگری بفرستید."
    except OSError:
        reason = "سرویس بررسی در دسترس نیست؛ تلاش دوباره زمان‌بندی شد."
    with transaction.atomic():
        t = parent_lock(candidate)
        f = PrivateFile.objects.select_for_update().get(pk=candidate.pk)
        if (
            f.purged_at
            or f.deleted_at
            or f.status != "pending_check"
            or f.attempts != attempt
            or isinstance(t, Draft)
            and t.deleted_at
        ):
            return True
        f.status, f.reason = state, reason
        if state == "pending_check":
            f.next_check = at + timedelta(seconds=min(900, 30 * 2 ** min(f.attempts, 5)))
        else:
            f.checked_at = at
        if state == "clean":
            f.media_type, f.derivative = mime, derivative
            if f.replaces_id:
                old = PrivateFile.objects.select_for_update().get(pk=f.replaces_id)
                if not old.attached or old.deleted_at or old.purged_at:
                    f.status, f.reason = (
                        "rejected",
                        "فایل قبلی تغییر کرده است؛ جایگزینی تازه انجام دهید.",
                    )
                else:
                    old.attached, old.replaced_at = False, at
                    old.save()
                    f.attached = True
            else:
                f.attached = True
        f.save()
    return True


def download(user, id):
    with transaction.atomic():
        f = get_file(user, id)
        if f.status != "clean" or not f.attached or f.deleted_at or f.replaced_at:
            raise Fault("فایل هنوز قابل دریافت نیست.", 403)
        return bytes(f.derivative if f.derivative is not None else f.content), f.media_type


def action(user, id, action, data):
    check_keys(data, [])
    with transaction.atomic():
        f = get_file(user, id, trash=True)
        t = file_target(user, f, trash=True, lock=True)
        at = timezone.now()
        if isinstance(t, Draft) and t.deleted_at:
            raise Fault("ابتدا پیش‌نویس را بازیابی کنید.")
        if action == "file-delete":
            f.deleted_at = f.deleted_at or at
        elif action == "file-restore":
            if not f.deleted_at or at >= f.deleted_at + timedelta(days=30) or f.replaced_at:
                raise Fault("مهلت یا شرایط بازیابی فایل برقرار نیست.")
            f.deleted_at = None
        elif action == "retry":
            if f.status != "pending_check" or not f.received_at or f.deleted_at:
                raise Fault("این فایل قابل تلاش دوباره نیست.")
            if at < f.next_check:
                raise Fault("تلاش دوباره زمان‌بندی شده؛ کمی صبر کنید.", 429)
            f.next_check = at
        f.save()
        return service.file_dto(f)


def purge(at=None):
    at = at or timezone.now()
    count = 0
    with transaction.atomic():
        for candidate in PrivateFile.objects.filter(purged_at__isnull=True):
            # Submitted/review evidence is retained until a real-data policy is approved.
            from apps.core.models import Message, Submission

            if (
                (
                    candidate.draft_id
                    and Submission.objects.filter(opportunity__draft_id=candidate.draft_id).exists()
                )
                or (candidate.application_id and candidate.application.status == "approved")
                or Message.objects.filter(files__contains=[str(candidate.pk)]).exists()
            ):
                continue
            if candidate.draft_id:
                Draft.objects.select_for_update().get(pk=candidate.draft_id)
            else:
                RepresentationRequest.objects.select_for_update().get(pk=candidate.application_id)
            f = (
                PrivateFile.objects.select_for_update(skip_locked=True)
                .filter(pk=candidate.pk, purged_at__isnull=True)
                .first()
            )
            if not f:
                continue
            t = Draft.objects.select_for_update().get(pk=f.draft_id) if f.draft_id else None
            held = bool(
                f.incident_reason.strip()
                and f.incident_owner.strip()
                and f.incident_review_at
                and f.incident_review_at > at
            )
            if held:
                continue
            deleted_dates = [d for d in [f.deleted_at, t.deleted_at if t else None] if d]
            deleted = min(deleted_dates) if deleted_dates else None
            due = (
                (deleted and at >= deleted + timedelta(days=30))
                or (f.replaced_at and not f.attached and at >= f.replaced_at + timedelta(days=30))
                or (
                    f.status in ["rejected", "quarantined"]
                    and f.checked_at
                    and at >= f.checked_at + timedelta(days=7)
                )
                or (
                    not f.attached
                    and not f.replaced_at
                    and f.status == "pending_check"
                    and at >= f.created_at + timedelta(hours=24)
                )
            )
            if due:
                f.content = None
                f.derivative = None
                f.attached = False
                f.purged_at = at
                f.save()
                count += 1
    return count

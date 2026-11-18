from datetime import date, datetime, time

from django.conf import settings
from django.utils import timezone

from apps.workspace import other_schema
from apps.workspace import service as ws
from apps.workspace.models import (
    Organization,
    PrivateFile,
    Representation,
    RepresentationRequest,
)
from apps.workspace.schema import Fault, check_keys

from .common import event, identifier, notify, owned, owner, role, run, text
from .models import Opportunity, Review, ReviewEvidence, Submission


def get_op(id, lock=False):
    qs = Opportunity.objects.select_for_update(of=("self",)) if lock else Opportunity.objects
    try:
        op = qs.select_related("draft", "public_revision").get(pk=identifier(id))
        if lock and op.draft.organization_id:
            Organization.objects.select_for_update().get(pk=op.draft.organization_id)
        return op
    except Opportunity.DoesNotExist as e:
        raise Fault("فرصت پیدا نشد.", 404) from e


def status(s):
    last = s.review_set.order_by("-id").first()
    return last.decision if last else "submitted"


def is_synthetic(op):
    profile = getattr(op.draft.creator, "core_personal", None)
    return bool(op.synthetic or (profile and profile.profile.get("local_role") is True))


def active(op, at=None):
    return bool(
        not (settings.INVEST_ENV == "public" and is_synthetic(op))
        and op.public_revision_id
        and op.availability == "active"
        and (not op.expires_at or op.expires_at > (at or timezone.now()))
        and owner(op)
    )


def submission_dto(s):
    previous = s.opportunity.public_revision
    before = previous.snapshot if previous else {}
    return {
        "id": str(s.pk),
        "opportunity_id": str(s.opportunity_id),
        "kind": s.kind,
        "draft_version": s.draft_version,
        "snapshot": s.snapshot,
        "files": s.files,
        "status": status(s),
        "created_at": s.created_at.isoformat(),
        "diff": {
            k: {"before": before.get(k), "after": s.snapshot.get(k)}
            for k in before.keys() | s.snapshot.keys()
            if before.get(k) != s.snapshot.get(k)
        },
        "reviews": [
            {"decision": r.decision, "reason": r.reason, "at": r.created_at.isoformat()}
            for r in s.review_set.order_by("id")
        ],
    }


def submit(session, id, data):
    check_keys(data, ["key", "version"])
    user = session.user

    def auth():
        d = ws.target(user, "draft", id, lock=True)
        if d.organization_id and not ws.grant(user, d.organization_id):
            raise Fault("ارسال سازمانی به اختیار نمایندگی فعال نیاز دارد.", 403)

    def work():
        d = ws.target(user, "draft", id, lock=True)
        if type(data["version"]) is not int or data["version"] != d.version:
            raise Fault("نسخه تغییر کرده؛ نسخه تازه را بازبینی کنید.", 409, field="version")
        effective, missing = other_schema.effective(d.kind, d.raw, d.routes, d.heritage_enabled)
        if missing or not d.routes or effective.get("title") in [None, "unknown", "not_applicable"]:
            raise Fault(
                "اطلاعات لازم را تکمیل کنید: " + "، ".join(missing or ["عنوان و مسیر"]),
                field="missing",
            )
        op, _ = Opportunity.objects.get_or_create(
            draft=d, defaults={"synthetic": settings.INVEST_ENV in ["development", "test"]}
        )
        op = get_op(op.pk, True)
        if Submission.objects.filter(opportunity=op, draft_version=d.version).exists():
            raise Fault("این نسخه قبلاً ارسال شده است.", 409)
        prior = op.submission_set.order_by("-created_at").first()
        if prior and status(prior) in ["submitted", "in_review"]:
            raise Fault("بررسی نسخه جاری هنوز پایان نیافته است.", 409)
        files = list(
            d.privatefile_set.filter(
                status="clean",
                attached=True,
                deleted_at__isnull=True,
                replaced_at__isnull=True,
                purged_at__isnull=True,
            ).values_list("pk", flat=True)
        )
        s = Submission.objects.create(
            opportunity=op,
            draft_version=d.version,
            kind=d.kind,
            routes=d.routes,
            snapshot=effective,
            files=[str(f) for f in files],
            submitted_by=user,
        )
        event(user, op.pk, "submitted", submission=str(s.pk))
        notify(user, "نسخه فرصت برای بررسی ارسال شد.", "/workspace")
        return submission_dto(s)

    return run(user, data, "submit", identifier(id), auth, work)


def review(session, id, data):
    check_keys(
        data,
        ["key", "decision", "reason", "public_files"]
        + (["verification"] if "verification" in data else []),
    )
    role(session, "admin")
    user = session.user

    def auth():
        role(session, "admin")

    def work():
        try:
            s = Submission.objects.get(pk=identifier(id))
        except Submission.DoesNotExist as e:
            raise Fault("نسخه پیدا نشد.", 404) from e
        op = get_op(s.opportunity_id, True)
        if s.submitted_by_id == user.pk or owner(op) == user:
            raise Fault("تأیید درخواست خود مجاز نیست.", 403)
        decision = data["decision"]
        reason = text(data["reason"], "reason")
        if decision not in ["in_review", "changes_requested", "rejected", "approved"] or status(
            s
        ) not in ["submitted", "in_review"]:
            raise Fault("انتقال وضعیت بررسی مجاز نیست.", 409)
        if not isinstance(data["public_files"], list) or len(set(data["public_files"])) != len(
            data["public_files"]
        ):
            raise Fault("فهرست مشتق‌های عمومی معتبر نیست.")
        if decision != "approved" and data["public_files"]:
            raise Fault("مشتق عمومی تنها هنگام تأیید انتخاب می‌شود.")
        if decision == "approved":
            if not owner(op):
                raise Fault("اختیار سازمان فعال نیست.", 403)
            for fid in data["public_files"]:
                if (
                    fid not in s.files
                    or not PrivateFile.objects.filter(
                        pk=identifier(fid),
                        status="clean",
                        kind="image",
                        derivative__isnull=False,
                        purged_at__isnull=True,
                    ).exists()
                ):
                    raise Fault("فقط مشتق تصویر پاک همین نسخه قابل انتشار است.")
            op.public_revision = s
            op.version += 1
            op.save()
        reviewed = Review.objects.create(
            submission=s,
            actor=user,
            decision=decision,
            reason=reason,
            public_files=data["public_files"],
        )
        verification = data.get("verification")
        if verification is not None:
            if decision != "approved" or s.kind != "fund" or s.snapshot.get("bank_exists") != "yes":
                raise Fault("احراز تضمین تنها برای ادعای فعال صندوق هنگام تأیید است.")
            check_keys(verification, ["source", "result", "files"])
            source = text(verification["source"], "verification.source")
            result = text(verification["result"], "verification.result")
            refs = verification["files"]
            if not isinstance(refs, list) or not refs or len(refs) > 10:
                raise Fault("مدرک ادعای تضمین را مشخص کنید.")
            for fid in refs:
                if (
                    fid not in s.files
                    or not PrivateFile.objects.filter(
                        pk=identifier(fid), kind="document", status="clean", purged_at__isnull=True
                    ).exists()
                ):
                    raise Fault("مدرک تضمین باید از مدارک پاک همین نسخه باشد.")
            ReviewEvidence.objects.create(review=reviewed, source=source, result=result, files=refs)
        event(user, op.pk, decision, reason=reason, submission=str(s.pk))
        recipient = owner(op)
        if recipient:
            notify(recipient, "نتیجه بررسی فرصت: " + decision, "/workspace")
        return submission_dto(s)

    return run(user, data, "review", identifier(id), auth, work)


def availability(session, id, data):
    check_keys(data, ["key", "version", "action", "reason", "expires_at"])
    user = session.user

    def auth():
        op = get_op(id, True)
        if data["action"] == "owner_paused":
            owned(user, op)
        else:
            role(session, "admin")

    def work():
        op = get_op(id, True)
        if data["version"] != op.version:
            raise Fault("نسخه فرصت تغییر کرده است.", 409)
        action = data["action"]
        reason = text(data["reason"], "reason")
        if action not in ["owner_paused", "active", "admin_suspended", "expired", "archived"]:
            raise Fault("وضعیت معتبر نیست.")
        if action == "active" and (not owner(op) or not op.public_revision_id):
            raise Fault("شرایط جاری انتشار برقرار نیست.")
        expires = None
        if data["expires_at"]:
            try:
                expires = datetime.fromisoformat(data["expires_at"])
                if timezone.is_naive(expires) or expires <= timezone.now():
                    raise ValueError()
            except (ValueError, TypeError) as e:
                raise Fault("زمان پایان معتبر آینده لازم است.") from e
        if action == "owner_paused" and op.availability in [
            "admin_suspended",
            "archived",
            "expired",
        ]:
            raise Fault("توقف مالک وضعیت تعلیق یا بایگانی ادمین را تغییر نمی‌دهد.", 409)
        op.availability = action
        op.expires_at = expires
        op.version += 1
        op.save()
        event(user, op.pk, action, reason=reason)
        return {"id": str(op.pk), "version": op.version, "availability": op.availability}

    return run(user, data, "availability", identifier(id), auth, work)


def organization_review(session, id, data):
    check_keys(data, ["key", "version", "decision", "reason", "source", "result"])
    role(session, "admin")
    user = session.user

    def auth():
        role(session, "admin")

    def work():
        try:
            a = RepresentationRequest.objects.select_for_update().get(pk=identifier(id))
        except RepresentationRequest.DoesNotExist as e:
            raise Fault("درخواست پیدا نشد.", 404) from e
        Organization.objects.select_for_update().get(pk=a.organization_id)
        if a.applicant_id == user.pk:
            raise Fault("خودتأییدی مجاز نیست.", 403)
        if data["version"] != a.version:
            raise Fault("نسخه درخواست تغییر کرده است.", 409)
        decision = data["decision"]
        reason = text(data["reason"], "reason")
        if decision not in ["needs_info", "rejected", "approved", "hold", "revoked"]:
            raise Fault("تصمیم معتبر نیست.")
        if decision == "approved":
            source = text(data["source"], "source")
            result = text(data["result"], "result")
            if a.status not in ["pending", "needs_info", "rejected"]:
                raise Fault("این درخواست قابل تأیید نیست.", 409)
            if (
                a.privatefile_set.filter(
                    kind="document",
                    status="clean",
                    attached=True,
                    deleted_at__isnull=True,
                    replaced_at__isnull=True,
                    purged_at__isnull=True,
                ).count()
                < 3
            ):
                raise Fault("مدرک ثبت، اختیار امضا و معرفی‌نامه پاک لازم است.")
            d = a.details
            if date.fromisoformat(d["starts_on"]) > timezone.localdate() or (
                not d["no_expiry"] and date.fromisoformat(d["ends_on"]) < timezone.localdate()
            ):
                raise Fault("تاریخ اختیار جاری نیست.")
            from .models import Consent

            Consent.objects.filter(
                case__opportunity__draft__organization=a.organization,
                kind="owner",
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())
            Representation.objects.filter(organization=a.organization, status="active").update(
                status="revoked"
            )
            ends = (
                None
                if d["no_expiry"]
                else timezone.make_aware(
                    datetime.combine(date.fromisoformat(d["ends_on"]), time.max)
                )
            )
            Representation.objects.create(
                organization=a.organization, user=a.applicant, status="active", ends_at=ends
            )
            event(
                user,
                a.organization_id,
                "independent_review",
                source=source,
                result=result,
                application=str(a.pk),
                details=a.details,
                files=[str(f.pk) for f in a.privatefile_set.all()],
            )
        elif decision in ["hold", "revoked"]:
            from .models import Consent

            Consent.objects.filter(
                case__opportunity__draft__organization=a.organization,
                kind="owner",
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())
            Representation.objects.filter(organization=a.organization, status="active").update(
                status=decision
            )
        a.status = decision if decision in ["approved", "needs_info", "rejected"] else "needs_info"
        a.version += 1
        a.save()
        event(
            user,
            a.organization_id,
            "organization_" + decision,
            reason=reason,
            application=str(a.pk),
        )
        notify(a.applicant, "نتیجه بررسی نمایندگی: " + decision, "/workspace")
        return ws.application_dto(a)

    return run(user, data, "organization_review", identifier(id), auth, work)


def bank_verified(s):
    return bool(
        s.kind == "fund"
        and getattr(s, "pk", None)
        and ReviewEvidence.objects.filter(
            review__submission=s, review__decision="approved"
        ).exists()
    )

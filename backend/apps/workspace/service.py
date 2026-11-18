import hashlib
import json
import uuid
from datetime import date, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import MoneyValue, Quantity, ReturnMetric
from apps.identity.models import User
from apps.services import schemas as services

from . import other_schema as schema
from .models import (
    Draft,
    DraftRevision,
    DraftValue,
    Operation,
    Organization,
    Representation,
    RepresentationRequest,
)
from .schema import Fault, check_keys, validate_one


def grant(user, organization_id):
    return (
        Representation.objects.filter(organization_id=organization_id, user=user, status="active")
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()))
        .exists()
    )


def permitted(user, target):
    if isinstance(target, RepresentationRequest):
        return grant(user, target.organization_id) or (
            target.applicant_id == user.pk and target.status != "approved"
        )
    if target.organization_id is None:
        return target.creator_id == user.pk
    if grant(user, target.organization_id):
        return True
    return bool(
        target.application_id
        and target.creator_id == user.pk
        and target.application.applicant_id == user.pk
        and target.application.status in ["pending", "needs_info", "rejected"]
        and not Representation.objects.filter(
            user=user, organization_id=target.organization_id
        ).exists()
    )


def target(user, kind, id, trash=False, lock=False):
    model = Draft if kind == "draft" else RepresentationRequest
    try:
        uuid.UUID(str(id))
        qs = model.objects.select_for_update() if lock else model.objects
        item = qs.get(pk=id)
    except (ValueError, model.DoesNotExist) as e:
        raise Fault("مورد پیدا نشد.", 404) from e
    if lock and item.organization_id:
        Organization.objects.select_for_update().get(pk=item.organization_id)
    if not permitted(user, item):
        raise Fault("دسترسی جاری به این مورد ندارید.", 403)
    if isinstance(item, Draft) and item.deleted_at and not trash:
        raise Fault("پیش‌نویس در سطل حذف است.", 404)
    return item


def file_dto(f):
    return {
        "id": str(f.pk),
        "name": f.name,
        "kind": f.kind,
        "size": f.size,
        "status": f.status,
        "reason": f.reason,
        "received": bool(f.received_at),
        "deleted": bool(f.deleted_at),
        "replaced": bool(f.replaced_at),
        "attached": f.attached,
        "purged": bool(f.purged_at),
        "replaces": str(f.replaces_id) if f.replaces_id else None,
    }


def draft_dto(d):
    if d.kind in services.KINDS:
        result, missing, validation_errors = services.readable_state(d.kind, d.raw)
    else:
        result, missing = schema.effective(d.kind, d.raw, d.routes, d.heritage_enabled)
        validation_errors = {}
    return {
        "validation_errors": validation_errors,
        "id": str(d.pk),
        "version": d.version,
        "kind": d.kind,
        "schema_version": d.schema_version,
        "routes": d.routes,
        "heritage_enabled": d.heritage_enabled,
        "raw": d.raw,
        "effective": result,
        "inactive": sorted(set(d.raw) - schema.active(d.kind, d.routes, d.heritage_enabled, d.raw)),
        "missing": missing,
        "deleted": bool(d.deleted_at),
        "owner_label": (
            d.application.details.get("name", d.organization.name)
            if d.application_id
            else d.organization.name
        )
        if d.organization_id
        else "مالک فردی",
        "files": [
            file_dto(f)
            for f in d.privatefile_set.filter(purged_at__isnull=True).order_by("created_at")
        ],
    }


def get_draft(user, id):
    return draft_dto(target(user, "draft", id))


def list_drafts(user, trash=False):
    qs = (
        Draft.objects.filter(deleted_at__isnull=not trash)
        .select_related("organization", "application")
        .order_by("-updated_at")
    )
    return [draft_dto(d) for d in qs if permitted(user, d)]


def application_dto(a):
    return {
        "id": str(a.pk),
        "version": a.version,
        "organization_id": str(a.organization_id),
        "status": a.status,
        "details": a.details,
        "active": False,
        "files": [file_dto(f) for f in a.privatefile_set.filter(purged_at__isnull=True)],
    }


def owners(user):
    apps = [
        application_dto(a)
        for a in RepresentationRequest.objects.filter(applicant=user)
        if permitted(user, a)
    ]
    for g in Representation.objects.filter(user=user, status="active").select_related(
        "organization"
    ):
        if not grant(user, g.organization_id):
            continue
        own = next((a for a in apps if a["organization_id"] == str(g.organization_id)), None)
        if own:
            own["active"] = True
        else:
            # An approved request is a stable selection handle, never an authority grant.
            app = RepresentationRequest.objects.filter(
                organization=g.organization, status="approved"
            ).first()
            if app:
                row = application_dto(app)
                row["active"] = True
                apps.append(row)
    return {"personal": True, "applications": apps}


def operation(user, data, kind, run):
    try:
        key = uuid.UUID(str(data.get("key")))
    except (ValueError, AttributeError) as e:
        raise Fault("کلید عملیات UUID معتبر لازم است.", field="key") from e
    digest = hashlib.sha256(
        json.dumps(
            {"kind": kind, "data": data}, sort_keys=True, ensure_ascii=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    with transaction.atomic():
        User.objects.select_for_update().get(pk=user.pk)
        previous = Operation.objects.filter(user=user, key=key).first()
        if previous:
            if previous.fingerprint != digest:
                raise Fault("این کلید برای ورودی دیگری مصرف شده است.", 409, field="key")
            target(user, previous.target_type, previous.target_id, trash=True, lock=True)
            return previous.receipt
        result, target_kind, target_id = run()
        Operation.objects.create(
            user=user,
            key=key,
            fingerprint=digest,
            receipt=result,
            target_type=target_kind,
            target_id=target_id,
        )
        return result


def create_draft(user, data):
    check_keys(data, ["key", "kind", "schema_version", "owner"])
    if (
        data["kind"] not in ["project", "fund", "sale", *services.KINDS]
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
    ):
        raise Fault("نوع فرصت و نسخه قرارداد معتبر نیست.")
    owner = data["owner"]

    def run():
        if Draft.objects.filter(creator=user).count() >= settings.WORKSPACE_MAX_DRAFTS:
            raise Fault("سقف پیش‌نویس حساب پر است.", 429)
        org = app = None
        if owner == {"kind": "personal"}:
            pass
        elif (
            isinstance(owner, dict)
            and set(owner) == {"kind", "request_id"}
            and owner["kind"] == "organization"
        ):
            app = target(user, "request", owner["request_id"], lock=True)
            if app.applicant_id != user.pk and not grant(user, app.organization_id):
                raise Fault("انتخاب مالک مجاز نیست.", 403)
            if app.status == "approved" and not grant(user, app.organization_id):
                raise Fault("اختیار سازمان فعال نیست.", 403)
            if (
                not grant(user, app.organization_id)
                and Representation.objects.filter(
                    user=user, organization_id=app.organization_id
                ).exists()
            ):
                raise Fault("اختیار پیشین سازمان دسترسی تازه ایجاد نمی‌کند.", 403)
            org = app.organization
        else:
            raise Fault("مالک را از گزینه‌های مجاز انتخاب کنید.", field="owner")
        d = Draft.objects.create(creator=user, organization=org, application=app, kind=data["kind"])
        DraftRevision.objects.create(draft=d, version=1, raw={}, effective={})
        return draft_dto(d), "draft", d.pk

    return operation(user, data, "create", run)


def save_draft(user, id, data):
    check_keys(data, ["key", "version", "routes", "heritage_enabled", "values"])

    def run():
        d = target(user, "draft", id, lock=True)
        if type(data["version"]) is not int or d.version != data["version"]:
            raise Fault(
                "نسخه دیگری ذخیره شده است؛ ورودی شما حفظ شده، نسخه سرور را بازبینی کنید.",
                409,
                "version",
                draft_dto(d),
            )
        FIELDS = schema.fields(d.kind)
        SCHEMA = schema.definition(d.kind)
        routes = data["routes"]
        vals = data["values"]
        if (
            not isinstance(routes, list)
            or any(not isinstance(r, str) or r not in SCHEMA["routes"] for r in routes)
            or len(set(routes)) != len(routes)
            or type(data["heritage_enabled"]) is not bool
        ):
            raise Fault("مسیر یا شرط میراث معتبر نیست.", field="routes")
        if not isinstance(vals, dict) or set(vals) - set(FIELDS):
            raise Fault("فیلد ناشناخته یا سیستمی قابل ثبت نیست.", field="values")
        if d.kind in services.KINDS:
            if routes or data["heritage_enabled"]:
                raise Fault("پیش‌نویس خدمت مسیر فرصت یا شرط میراث ندارد.", field="routes")
            raw = services.merge(d.kind, d.raw, vals)
        else:
            raw = dict(d.raw)
            # Conditions depend on explicit route/heritage selection and returns; dormant input
            # cannot overwrite previously saved dormant values.
            if "heritage" in routes and data["heritage_enabled"] and "heritage_returns" in vals:
                if vals["heritage_returns"] is None:
                    raw.pop("heritage_returns", None)
                else:
                    validate_one("heritage_returns", vals["heritage_returns"])
                    raw["heritage_returns"] = vals["heritage_returns"]
            for control in ["category", "bank_exists", "price_mode", "forecast_type"]:
                if control in vals and control in FIELDS:
                    if vals[control] is None:
                        raw.pop(control, None)
                    else:
                        schema.validate(d.kind, control, vals[control])
                        raw[control] = vals[control]
            active = schema.active(d.kind, routes, data["heritage_enabled"], raw)
            for k, v in vals.items():
                if k not in active:
                    continue
                if v is None:
                    raw.pop(k, None)
                else:
                    schema.validate(d.kind, k, v)
                    raw[k] = v
        result, _ = schema.effective(d.kind, raw, routes, data["heritage_enabled"])
        d.raw = raw
        d.routes = routes
        d.heritage_enabled = data["heritage_enabled"]
        d.version += 1
        d.updated_at = timezone.now()
        d.save()
        rev = DraftRevision.objects.create(draft=d, version=d.version, raw=raw, effective=result)
        for k in result:
            if not FIELDS[k]["unit"]:
                continue
            kind = FIELDS[k]["kind"]
            model = {"money": MoneyValue, "quantity": Quantity, "return": ReturnMetric}[kind]
            obj = model.from_payload(raw[k])
            obj.save()
            DraftValue.objects.create(
                revision=rev, key=k, **{("return_metric" if kind == "return" else kind): obj}
            )
        return draft_dto(d), "draft", d.pk

    # Include target in fingerprint to prevent same operation being replayed across drafts.
    return operation(user, data, "save:" + str(id), run)


def draft_action(user, id, action, data):
    check_keys(data, ["key", "version"])

    def run():
        d = target(user, "draft", id, trash=True, lock=True)
        if data["version"] != d.version:
            raise Fault("نسخه تغییر کرده است.", 409, "version", draft_dto(d))
        at = timezone.now()
        if action == "delete":
            d.deleted_at = d.deleted_at or at
        elif action == "restore":
            if not d.deleted_at or at >= d.deleted_at + timedelta(days=30):
                raise Fault("مهلت بازیابی این پیش‌نویس پایان یافته است.", 400)
            d.deleted_at = None
        else:
            raise Fault()
        d.version += 1
        d.save()
        return draft_dto(d), "draft", d.pk

    return operation(user, data, action + ":" + str(id), run)


DETAIL_KEYS = [
    "name",
    "country",
    "organization_type",
    "registration",
    "signatory",
    "representative_name",
    "scope",
    "starts_on",
    "ends_on",
    "no_expiry",
]


def validate_details(details):
    check_keys(details, DETAIL_KEYS)
    for k in DETAIL_KEYS[:8]:
        if not isinstance(details[k], str) or not details[k].strip() or len(details[k]) > 2000:
            raise Fault("مشخصات و حدود اختیار را کامل وارد کنید.", field=k)
    try:
        start = date.fromisoformat(details["starts_on"])
        if type(details["no_expiry"]) is not bool:
            raise ValueError()
        if details["no_expiry"]:
            if details["ends_on"] is not None:
                raise ValueError()
        elif date.fromisoformat(details["ends_on"]) < start:
            raise ValueError()
    except (ValueError, TypeError) as e:
        raise Fault("تاریخ معتبر یا پایان درج‌نشده را صریح انتخاب کنید.", field="ends_on") from e
    if (
        len(details["name"]) > 200
        or len(details["country"]) > 100
        or len(details["registration"]) > 200
    ):
        raise Fault("مشخصات سازمان بیش از حد طولانی است.")


def organization(user, data, id=None):
    check_keys(data, ["key", "version", "details"] if id else ["key", "details"])
    validate_details(data["details"])

    def run():
        detail = data["details"]
        if id:
            a = target(user, "request", id, lock=True)
            if a.applicant_id != user.pk or a.status == "approved":
                raise Fault("این درخواست قابل ویرایش نیست.", 403)
            if data["version"] != a.version:
                raise Fault("نسخه درخواست تغییر کرده است.", 409)
            if any(detail[k] != a.details.get(k) for k in ["country", "registration"]):
                raise Fault("برای سازمان دیگر درخواست تازه بسازید.")
            a.details = detail
            a.version += 1
            a.status = "pending"
            a.save()
        else:
            org, _ = Organization.objects.get_or_create(
                country=detail["country"],
                registration=detail["registration"],
                defaults={"name": detail["name"]},
            )
            a = RepresentationRequest.objects.create(
                organization=org, applicant=user, details=detail
            )
        return application_dto(a), "request", a.pk

    return operation(user, data, "organization:" + str(id), run)

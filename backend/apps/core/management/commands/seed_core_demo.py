import hashlib
import io
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from pypdf import PdfWriter

from apps.catalog.models import City, County, Group, Province, Subtype
from apps.core import publication as pub
from apps.core.models import Opportunity, Personal
from apps.identity.models import User
from apps.identity.sessions import mint_session
from apps.workspace import files, other_schema
from apps.workspace import service as ws
from apps.workspace.models import Draft, RepresentationRequest


def key():
    return str(uuid.uuid4())


def number(kind, k, unit, value=None, basis=None):
    return {
        "field": {"namespace": "invest.opportunity." + kind, "key": k, "version": 1},
        "unit": {"code": unit, "version": 1},
        "status": "known" if value is not None else "unknown",
        "source_value": value,
        "basis": basis,
    }


class Command(BaseCommand):
    help = (
        "Non-destructive synthetic core journey seed, development/test only; prints no credentials."
    )

    def handle(self, *args, **kwargs):
        if settings.INVEST_ENV not in ["development", "test"]:
            raise CommandError("Synthetic seed is forbidden in public.")
        team = {}
        for index, (name, role) in enumerate(
            [
                ("مالک مصنوعی", "owner"),
                ("ادمین بررسی مستقل مصنوعی", "admin"),
                ("مشتری مصنوعی", "user"),
                ("کارشناس مصنوعی یک", "expert"),
                ("کارشناس مصنوعی دو", "expert"),
            ],
            1,
        ):
            mobile = "+12025559" + str(index).zfill(3)
            u = User.objects.filter(mobile=mobile).first()
            if u and not Personal.objects.filter(user=u, profile__local_role=True).exists():
                raise CommandError("Reserved synthetic account collision; no data modified.")
            if not u:
                u = User.objects.create_user(mobile=mobile, role=role)
            Personal.objects.get_or_create(
                user=u, defaults={"profile": {"name": name, "local_role": True}}
            )
            team[role + str(index)] = u
        owner = team["owner1"]
        admin = team["admin2"]
        owner_session = mint_session(owner, timezone.now())[0]
        admin_session = mint_session(admin, timezone.now(), sensitive=True)[0]
        org = RepresentationRequest.objects.filter(
            applicant=owner, details__registration="CORE-SYNTHETIC-001"
        ).first()
        if not org:
            details = {
                "name": "سازمان مصنوعی توسعه هسته",
                "country": "ایران",
                "organization_type": "نمونه مصنوعی",
                "registration": "CORE-SYNTHETIC-001",
                "signatory": "اختیار امضای مصنوعی",
                "representative_name": "نماینده مصنوعی",
                "scope": "ثبت و پیگیری فرصت‌های مصنوعی توسعه",
                "starts_on": "2026-01-01",
                "ends_on": None,
                "no_expiry": True,
            }
            a = ws.organization(owner, {"key": key(), "details": details})
            org = RepresentationRequest.objects.get(pk=a["id"])
        if org.status != "approved":
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            writer.add_metadata({"/Title": "SYNTHETIC DEVELOPMENT DOCUMENT"})
            stream = io.BytesIO()
            writer.write(stream)
            content = stream.getvalue()
            existing = org.privatefile_set.count()
            for i in range(existing, 3):
                f = files.reserve(
                    owner,
                    {
                        "key": key(),
                        "target_type": "request",
                        "target_id": str(org.pk),
                        "kind": "document",
                        "name": [
                            "synthetic-registration.pdf",
                            "synthetic-signatory.pdf",
                            "synthetic-introduction.pdf",
                        ][i],
                        "size": len(content),
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "replaces": None,
                    },
                )
                files.receive(owner, f["id"], io.BytesIO(content))
            while files.check_one():
                pass
            pub.organization_review(
                admin_session,
                org.pk,
                {
                    "key": key(),
                    "version": org.version,
                    "decision": "approved",
                    "reason": "آزمون جریان مستقل؛ فقط داده مصنوعی، احراز واقعی نیست",
                    "source": "دفتر مصنوعی توسعه، مستقل از نقش متقاضی",
                    "result": "سه مدرک مصنوعی برای آزمون جریان تطبیق داده شد.",
                },
            )
        province = Province.objects.filter(name="تهران").first() or Province.objects.first()
        county = County.objects.filter(province=province).first()
        city = City.objects.filter(county=county).first()
        group = Group.objects.first()
        subtype = Subtype.objects.filter(group=group).first()
        for kind in ["project", "fund", "sale"]:
            for i in range(1, 3):
                title = f"فرصت مصنوعی {kind} شماره {i}"
                if Opportunity.objects.filter(
                    synthetic=True, draft__raw__title=title, public_revision__isnull=False
                ).exists():
                    continue
                d = Draft.objects.filter(creator=owner, kind=kind, raw__title=title).first()
                if not d:
                    d0 = ws.create_draft(
                        owner,
                        {
                            "key": key(),
                            "kind": kind,
                            "schema_version": 1,
                            "owner": {"kind": "organization", "request_id": str(org.pk)}
                            if i == 2
                            else {"kind": "personal"},
                        },
                    )
                    vals = {
                        f["key"]: (
                            number(
                                kind,
                                f["key"],
                                f["unit"],
                                basis={"start_basis": "unspecified"}
                                if f["unit"] in ["MONTH", "YEAR"]
                                else None,
                            )
                            if f["unit"]
                            else "unknown"
                        )
                        for f in other_schema.definition(kind)["fields"]
                    }
                    vals.update(
                        {
                            "title": title,
                            "description": (
                                "این فرصت و مدارک و مبالغ آن مصنوعی و برای تجربه محلی است؛ "
                                "پیشنهاد سرمایه‌گذاری نیست."
                            ),
                            "stage": "نمونه توسعه",
                            "model": "نمونه بررسی قرارداد",
                            "finance": "تأمین مالی ادعایی نمونه؛ تأیید نشده",
                            "repay": "بازگشت طبق قرارداد پس از بررسی مستقل",
                            "ownership": "حقوق ادعایی مصنوعی",
                            "caution": (
                                "داده مصنوعی؛ هیچ تضمین سود یا مجوز جذب سرمایه تأیید نشده است."
                            ),
                            "steps": ["بررسی مدارک", "گفتگو در پرونده"],
                            "province": province.pk,
                            "county": county.pk if county else "unknown",
                            "city": city.pk if city else "unknown",
                            "group": group.pk,
                            "subtype": subtype.pk,
                            "model_id": "unknown",
                            "category": "land",
                            "usage": "residential",
                            "fund_kind": "fund",
                            "fund_type": "fixed",
                            "price_mode": "total",
                            "bank_exists": "no",
                        }
                    )
                    primary = {
                        "project": ("min_capital", "BILLION_TOMAN", "25" if i == 1 else "40"),
                        "fund": ("minimum_investment", "MILLION_TOMAN", "1500"),
                        "sale": ("price", "BILLION_TOMAN", "12"),
                    }
                    k, u, v = primary[kind]
                    vals[k] = number(kind, k, u, v)
                    vals = {k: v for k, v in vals.items() if k in other_schema.fields(kind)}
                    row = ws.save_draft(
                        owner,
                        d0["id"],
                        {
                            "key": key(),
                            "version": d0["version"],
                            "routes": [
                                "fund"
                                if kind == "fund"
                                else "buyer"
                                if kind == "sale"
                                else "investor"
                            ],
                            "heritage_enabled": False,
                            "values": vals,
                        },
                    )
                    d = Draft.objects.get(pk=row["id"])
                op, created = Opportunity.objects.get_or_create(
                    draft=d, defaults={"synthetic": True}
                )
                if not op.synthetic:
                    raise CommandError("Non-synthetic opportunity collision.")
                s = op.submission_set.order_by("-created_at").first()
                if not s:
                    s0 = pub.submit(owner_session, d.pk, {"key": key(), "version": d.version})
                    s = op.submission_set.get(pk=s0["id"])
                if pub.status(s) in ["submitted", "in_review"]:
                    pub.review(
                        admin_session,
                        s.pk,
                        {
                            "key": key(),
                            "decision": "approved",
                            "reason": "انتشار مصنوعی از مسیر واقعی بررسی مستقل",
                            "public_files": [],
                        },
                    )
        self.stdout.write(
            "Synthetic journey seed ready: 5 local roles, organization and 6 "
            "published opportunities. No credentials printed."
        )

import hashlib
import io
import uuid
from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
from PIL import Image
from pypdf import PdfWriter

from apps.workspace import files, service
from apps.workspace.models import (
    DraftValue,
    Organization,
    PrivateFile,
    Representation,
    RepresentationRequest,
)
from apps.workspace.schema import FIELDS
from tests.test_workspace import create, number, save
from tests.test_workspace_files import image_bytes, reserve

pytestmark = pytest.mark.django_db


def full_basis():
    return {
        "version": 1,
        "metric_type": "irr",
        "period": "annual",
        "horizon": {"value": "5", "unit": {"code": "YEAR", "version": 1}},
        "basis_date": "2026-11-17",
        "price_basis": "nominal",
        "scope": "project",
        "observation": "claimed",
        "source": "مدل مصنوعی آزمون؛ تأییدنشده",
    }


@pytest.mark.parametrize("key", list(FIELDS))
def test_every_project_widget_contract_roundtrip(accounts, key):
    f = FIELDS[key]
    a = accounts[0]
    d = create(a)
    values = {}
    routes = ["investor", "contractor", "buyer", "lessee", "heritage", "operator"]
    if f["unit"]:
        value = number(
            key,
            "0",
            f["unit"],
            basis=full_basis()
            if f["kind"] == "return"
            else {"start_basis": "تحویل"}
            if f["unit"] in ["MONTH", "YEAR"]
            else None,
        )
    elif f["kind"] in ["enum", "multi"]:
        choice = next(iter(f["options"]))
        value = [choice] if f["kind"] == "multi" else choice
    elif f["kind"] == "lines":
        value = ["متن مصنوعی"]
    elif f["kind"] == "reference":
        value = "unknown"
    else:
        value = "متن مصنوعی"
    if key == "metric_quantity":
        values["metric_label"] = "ظرفیت آزمون"
    values[key] = value
    d = save(a, d, values, routes, heritage_enabled=True)
    assert key in d["effective"]
    assert d["raw"][key] == value
    if f["unit"]:
        assert DraftValue.objects.filter(revision__draft_id=d["id"], key=key).exists()


def test_money_equivalence_and_payload_boundaries(accounts):
    a = accounts[0]
    d = create(a)
    one = save(a, d, {"budget": number("budget", "۱٫۵")})
    two = save(a, one, {"budget": number("budget", "۱۵۰۰", "MILLION_TOMAN")})
    assert (
        one["effective"]["budget"]["value"] == two["effective"]["budget"]["value"] == "1500000000"
    )
    for val in ["1,50", "1.0000000001", "1e6", "9" * 25]:
        with pytest.raises(service.Fault):
            save(a, two, {"budget": number("budget", val)})
    with pytest.raises(service.Fault):
        save(
            a, two, {"partner_share": number("partner_share", "101", "SHARE_PERCENT")}, ["investor"]
        )
    with pytest.raises(service.Fault):
        save(a, two, {"execution_months": number("execution_months", "3", "MONTH")}, ["contractor"])
    with pytest.raises(service.Fault):
        save(a, two, {"budget": number("budget", "1", "USD")})


def test_org_two_orgs_successor_pending_and_revoked_download(accounts, monkeypatch):
    a, b = accounts
    ds = []
    grants = []
    for n in range(2):
        org = Organization.objects.create(
            name=f"سازمان مصنوعی{n}", country="IR", registration=f"TEST{n}"
        )
        app = RepresentationRequest.objects.create(
            organization=org, applicant=a, details={"name": org.name}, status="approved"
        )
        grants.append(Representation.objects.create(organization=org, user=a, status="active"))
        ds.append(create(a, {"kind": "organization", "request_id": str(app.pk)}))
    with pytest.raises(IntegrityError), transaction.atomic():
        Representation.objects.create(organization=grants[0].organization, user=b, status="active")
    pending = RepresentationRequest.objects.create(
        organization=grants[0].organization, applicant=b, details={"name": "درخواست جانشین"}
    )
    own = create(b, {"kind": "organization", "request_id": str(pending.pk)})
    assert own["id"] != ds[0]["id"]
    with pytest.raises(service.Fault):
        service.get_draft(b, ds[0]["id"])
    blob = image_bytes()
    f = reserve(a, ds[0], blob)
    files.receive(a, f["id"], io.BytesIO(blob))
    monkeypatch.setattr(files, "scan", lambda _: "clean")
    files.check_one()
    grants[0].status = "hold"
    grants[0].save()
    with pytest.raises(service.Fault):
        files.download(a, f["id"])
    assert service.get_draft(a, ds[1]["id"])["id"] == ds[1]["id"]
    with pytest.raises(service.Fault):
        service.draft_action(a, ds[0]["id"], "delete", {"key": str(uuid.uuid4()), "version": 1})


@pytest.mark.parametrize("case", ["clean", "encrypted", "js", "embedded", "fake"])
def test_pdf_content_real_parser(case):
    w = PdfWriter()
    w.add_blank_page(width=100, height=100)
    if case == "encrypted":
        w.encrypt("synthetic")
    if case == "js":
        from pypdf.generic import DictionaryObject, NameObject, TextStringObject

        w._root_object[NameObject("/OpenAction")] = DictionaryObject(
            {
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject('app.alert("synthetic")'),
            }
        )
    if case == "embedded":
        w.add_attachment("synthetic.txt", b"clean")
    stream = io.BytesIO()
    w.write(stream)
    data = stream.getvalue() if case != "fake" else b"<html>not pdf</html>"
    if case == "clean":
        assert files.inspect(data, "synthetic.pdf", "document") == ("application/pdf", None)
    else:
        with pytest.raises(service.Fault):
            files.inspect(data, "synthetic.pdf", "document")


@pytest.mark.parametrize("case", ["mismatch", "animated", "pixels", "metadata"])
def test_image_bounds_and_safe_derivative(case):
    stream = io.BytesIO()
    image = Image.new("RGB", (5001, 5000) if case == "pixels" else (20, 20), "red")
    if case == "animated":
        image.save(
            stream,
            format="PNG",
            save_all=True,
            append_images=[Image.new("RGB", (20, 20), "blue")],
            duration=100,
            loop=0,
        )
    else:
        from PIL.PngImagePlugin import PngInfo

        info = PngInfo()
        info.add_text("private", "SYNTHETIC_PRIVATE_METADATA")
        image.save(stream, format="PNG", pnginfo=info)
    name = "fake.jpg" if case == "mismatch" else "safe.png"
    if case == "metadata":
        mime, derivative = files.inspect(stream.getvalue(), name, "image")
        assert mime == "image/jpeg"
        assert b"SYNTHETIC_PRIVATE_METADATA" not in derivative
    else:
        with pytest.raises(service.Fault):
            files.inspect(stream.getvalue(), name, "image")


def test_retention_boundaries_hold_and_references(accounts, monkeypatch):
    a = accounts[0]
    d = create(a)
    at = timezone.now()
    blob = image_bytes()
    temporary = reserve(a, d, blob)
    f = PrivateFile.objects.get(pk=temporary["id"])
    f.created_at = at
    f.save()
    assert files.purge(at + timedelta(hours=24) - timedelta(microseconds=1)) == 0
    assert files.purge(at + timedelta(hours=24)) == 1
    assert files.purge(at + timedelta(days=100)) == 0
    r = reserve(a, d, blob)
    files.receive(a, r["id"], io.BytesIO(blob))
    monkeypatch.setattr(files, "scan", lambda _: "clean")
    files.check_one()
    assert files.purge(at + timedelta(days=100)) == 0  # valid attached reference
    deleted = service.draft_action(a, d["id"], "delete", {"key": str(uuid.uuid4()), "version": 1})
    stamp = PrivateFile.objects.get(pk=r["id"])
    stamp.incident_reason = "رخداد مصنوعی"
    stamp.incident_owner = "مسئول آزمون"
    stamp.incident_review_at = at + timedelta(days=40)
    stamp.save()
    assert files.purge(at + timedelta(days=31)) == 0
    assert files.purge(at + timedelta(days=41)) == 1
    with pytest.raises(service.Fault):
        from unittest.mock import patch

        with patch("apps.workspace.service.timezone.now", return_value=at + timedelta(days=31)):
            service.draft_action(
                a, d["id"], "restore", {"key": str(uuid.uuid4()), "version": deleted["version"]}
            )


def test_receive_rate_failed_requests_count(accounts, settings):
    settings.WORKSPACE_HOURLY_RECEIVES = 1
    a = accounts[0]
    blob = image_bytes()
    r = reserve(a, create(a), blob)
    with pytest.raises(service.Fault):
        files.receive(a, r["id"], io.BytesIO(b"wrong"))
    with pytest.raises(service.Fault) as exc:
        files.receive(a, r["id"], io.BytesIO(blob))
    assert exc.value.status == 429


def test_reservation_retry_different_input_and_quota(accounts, settings):
    a = accounts[0]
    d = create(a)
    blob = image_bytes()
    settings.WORKSPACE_ACCOUNT_BYTES = len(blob)
    data = {
        "key": str(uuid.uuid4()),
        "target_type": "draft",
        "target_id": d["id"],
        "kind": "image",
        "name": "test.png",
        "size": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "replaces": None,
    }
    r = files.reserve(a, data)
    assert files.reserve(a, data)["id"] == r["id"]
    with pytest.raises(service.Fault) as exc:
        files.reserve(a, {**data, "name": "other.png"})
    assert exc.value.status == 409
    with pytest.raises(service.Fault) as exc:
        reserve(a, d, blob)
    assert exc.value.status == 429


@pytest.mark.parametrize("unit", list(FIELDS["metric_quantity"]["unit_options"]))
def test_all_reference_capacity_units_explicit_v2(accounts, unit):
    payload = number("metric_quantity", "3", unit)
    payload["field"]["version"] = 2
    d = save(
        accounts[0],
        create(accounts[0]),
        {"metric_label": "ظرفیت مصنوعی", "metric_quantity": payload},
    )
    assert d["effective"]["metric_quantity"]["base_unit"] == unit
    assert d["effective"]["metric_quantity"]["value"] == "3"


def test_capacity_units_are_not_guessed_equivalent(accounts):
    from apps.catalog.values import compare

    a = accounts[0]

    def capacity(unit):
        p = number("metric_quantity", "3", unit)
        p["field"]["version"] = 2
        return save(a, create(a), {"metric_label": "ظرفیت مصنوعی", "metric_quantity": p})[
            "effective"
        ]["metric_quantity"]

    assert compare(capacity("MEGAWATT"), capacity("MEGAVOLT_AMPERE"))["comparable"] is False
    assert compare(capacity("ROOM"), capacity("BED"))["relation"] is None


def test_revoked_representative_cannot_read_approved_request_files(accounts, monkeypatch):
    a = accounts[0]
    org = Organization.objects.create(
        name="سازمان مصنوعی", country="IR", registration="TEST-REVOKE-DOC"
    )
    app = RepresentationRequest.objects.create(
        organization=org, applicant=a, details={"name": org.name}, status="approved"
    )
    grant = Representation.objects.create(organization=org, user=a, status="active")
    blob = image_bytes()
    f = files.reserve(
        a,
        {
            "key": str(uuid.uuid4()),
            "target_type": "request",
            "target_id": str(app.pk),
            "kind": "document",
            "name": "synthetic.png",
            "size": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "replaces": None,
        },
    )
    files.receive(a, f["id"], io.BytesIO(blob))
    monkeypatch.setattr(files, "scan", lambda _: "clean")
    files.check_one()
    assert files.download(a, f["id"])[0]
    grant.status = "revoked"
    grant.save()
    assert service.owners(a)["applications"] == []
    with pytest.raises(service.Fault):
        files.download(a, f["id"])
    with pytest.raises(service.Fault):
        service.target(a, "request", str(app.pk))

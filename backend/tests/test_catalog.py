import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from apps.catalog.management.commands.import_reference import SOURCE
from apps.catalog.models import City, County, Group, Province, Subtype

pytestmark = pytest.mark.django_db(transaction=True)


def test_import_counts_exact_source_and_repeat_preserves_custom_data():
    Group.objects.create(id="user-custom", name="مصنوعی کاربر", source_version="custom")
    call_command("import_reference")
    counts = [m.objects.count() for m in (Group, Subtype, Province, County, City)]
    assert counts == [12, 78, 31, 478, 22]
    call_command("import_reference")
    assert [m.objects.count() for m in (Group, Subtype, Province, County, City)] == counts
    assert Group.objects.get(pk="user-custom").name == "مصنوعی کاربر"
    source = json.loads(SOURCE.read_text())
    for p in source["provinces"]:
        assert list(County.objects.filter(province_id=p["id"]).values_list("name", flat=True)) == [
            c["name"] for c in p["counties"]
        ]
    for g in source["groups"]:
        assert [x.metadata for x in Subtype.objects.filter(group_id=g["id"])] == g["subtypes"]


def test_identity_conflict_rolls_back_and_foreign_keys_unique():
    Group.objects.create(id="building", name="متعارض", source_version="custom")
    with pytest.raises(CommandError):
        call_command("import_reference")
    assert Province.objects.count() == 0
    Group.objects.all().delete()
    call_command("import_reference")
    county = County.objects.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        County.objects.create(
            id="duplicate", name=county.name, source_version="custom", province=county.province
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        County.objects.create(
            id="orphan", name="نامعتبر", source_version="custom", province_id="missing"
        )


def test_catalog_api_matches_fixture_and_preview_contract_is_retired(client):
    call_command("import_reference")
    from jsonschema import Draft202012Validator

    # Custom child rows survive imports but cannot silently enter the versioned reference DTO.
    Subtype.objects.create(
        id="custom-child",
        raw_id="custom",
        group_id="building",
        name="کاربر",
        source_version="custom",
    )
    County.objects.create(
        id="custom-county", province_id="province-00", name="کاربر", source_version="custom"
    )
    City.objects.create(
        id="custom-city", county=County.objects.first(), name="کاربر", source_version="custom"
    )
    contract = client.get("/api/v1/schema").json()
    for endpoint, name in [
        ("taxonomy", "CatalogTaxonomy"),
        ("geography", "CatalogGeography"),
    ]:
        schema = {"$ref": "#/components/schemas/" + name, "components": contract["components"]}
        Draft202012Validator(schema).validate(client.get("/api/v1/catalog/" + endpoint).json())
    source = json.loads(SOURCE.read_text())
    response = client.get("/api/v1/catalog/taxonomy")
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert response.json()["groups"] == source["groups"]
    geography = client.get("/api/v1/catalog/geography").json()
    assert len(geography["provinces"]) == 31
    assert sum(len(p["counties"]) for p in geography["provinces"]) == 478
    assert client.get("/api/v1/catalog/preview").status_code == 404
    assert client.post("/api/v1/catalog/taxonomy", {}).status_code in (403, 405)


def test_empty_catalog_is_not_fabricated(client):
    assert client.get("/api/v1/catalog/taxonomy").json()["groups"] == []
    assert client.get("/api/v1/catalog/geography").json()["provinces"] == []

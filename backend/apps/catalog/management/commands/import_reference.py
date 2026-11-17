import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.catalog.models import City, County, Group, Province, Subtype

SOURCE = Path(__file__).resolve().parents[2] / "fixtures/classification-v1.json"


class Command(BaseCommand):
    help = (
        "Import versioned advisor classification; never delete user data or import opportunities."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(73004001)")
        source = json.loads(SOURCE.read_text())
        version = source["version"]

        def put(model, id, name, position, **fields):
            old = model.objects.filter(pk=id).first()
            if old and (old.source_version != version or old.name != name):
                raise CommandError("Source identity conflict; explicit mapping review required")
            model.objects.update_or_create(
                id=id,
                defaults={"name": name, "position": position, "source_version": version, **fields},
            )

        for i, group in enumerate(source["groups"]):
            put(
                Group,
                group["id"],
                group["name"],
                i,
                metadata={k: v for k, v in group.items() if k != "subtypes"},
            )
            for j, subtype in enumerate(group["subtypes"]):
                put(
                    Subtype,
                    group["id"] + "." + subtype["id"],
                    subtype["name"],
                    j,
                    group_id=group["id"],
                    raw_id=subtype["id"],
                    metadata=subtype,
                )
        for i, province in enumerate(source["provinces"]):
            put(Province, province["id"], province["name"], i)
            for j, county in enumerate(province["counties"]):
                put(County, county["id"], county["name"], j, province_id=province["id"])
                for k, name in enumerate(county["cities"]):
                    put(City, county["id"] + f".city-{k}", name, k, county_id=county["id"])
        self.stdout.write(
            "Classification imported: 11 groups, 78 subtypes, 31 provinces, "
            "478 counties, 22 source city links; no opportunity records imported."
        )

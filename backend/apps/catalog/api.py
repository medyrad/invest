from rest_framework.response import Response

from config.views import PublicBase

from .models import Group, Province

VERSION = "advisor-classification-v1"


class Taxonomy(PublicBase):
    def get(self, request):
        groups = []
        for row in Group.objects.filter(source_version=VERSION).prefetch_related("subtypes"):
            groups.append(
                {
                    **row.metadata,
                    "subtypes": [
                        s.metadata for s in row.subtypes.all() if s.source_version == VERSION
                    ],
                }
            )
        return Response({"version": VERSION, "groups": groups})


class Geography(PublicBase):
    def get(self, request):
        provinces = []
        for row in Province.objects.filter(source_version=VERSION).prefetch_related(
            "counties__cities"
        ):
            provinces.append(
                {
                    "id": row.pk,
                    "name": row.name,
                    "counties": [
                        {
                            "id": c.pk,
                            "name": c.name,
                            "cities": [
                                {"id": city.pk, "name": city.name}
                                for city in c.cities.all()
                                if city.source_version == VERSION
                            ],
                        }
                        for c in row.counties.all()
                        if c.source_version == VERSION
                    ],
                }
            )
        return Response(
            {"version": VERSION, "city_coverage": "source-linked-only", "provinces": provinces}
        )


class ValueDefinitions(PublicBase):
    def get(self, request):
        from .models import FieldDefinition, UnitDefinition

        return Response(
            {
                "version": "invest-values-v1",
                "units": [u.as_dict() for u in UnitDefinition.objects.all()],
                "fields": [
                    f.as_dict() for f in FieldDefinition.objects.select_related("unit").all()
                ],
            }
        )


class NormalizeValue(PublicBase):
    def post(self, request):
        from .schemas import ValueInputSerializer
        from .values import ValueErrorDetail

        try:
            serializer = ValueInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data)
        except ValueErrorDetail as e:
            return Response(
                {
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "fields": {e.field: [e.message]},
                        "request_id": request.request_id,
                    }
                },
                status=400,
            )

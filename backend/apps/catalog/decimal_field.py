"""Exact PostgreSQL storage: CHECK scale instead of typmod rounding."""

from django.core.exceptions import ValidationError
from django.db import models


class Scale(models.Transform):
    lookup_name = "scale"
    function = "SCALE"
    output_field = models.IntegerField()


class ExactDecimalField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_digits", 33)
        kwargs.setdefault("decimal_places", 9)
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        if connection.vendor != "postgresql":
            raise RuntimeError("Exact values require PostgreSQL")
        return "numeric"

    def to_python(self, value):
        if isinstance(value, (float, bool)):
            raise ValidationError("مقدار اعشاری باید دقیق و بدون float باشد.")
        return super().to_python(value)


ExactDecimalField.register_lookup(Scale)

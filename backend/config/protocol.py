import re

from rest_framework.exceptions import ValidationError


def parse_version(value):
    if value is None:
        return None
    if not re.fullmatch(r'"[1-9][0-9]{0,17}"', value):
        raise ValidationError("نسخه معتبر نیست.", code="invalid_version")
    return int(value[1:-1])


def validate_idempotency_key(value):
    if value is not None and not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value):
        raise ValidationError("کلید تکرار درخواست معتبر نیست.", code="invalid_idempotency_key")
    return value

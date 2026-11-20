import logging
import re
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def load_private_value(*, file_path, fallback="", public=False):
    """Read a rotating secret file first; env fallback is development/test only."""
    if file_path:
        path = Path(file_path)
        if path.is_file():
            if public and path.stat().st_mode & 0o077:
                raise ImproperlyConfigured("Invalid private credential file permissions")
            value = path.read_text().strip()
            if value:
                return value
    if not public:
        return fallback.strip()
    return ""


class SecretRedactionFilter(logging.Filter):
    patterns = (
        re.compile(r"(?i)bearer\s+[a-z0-9._-]{8,}"),
        re.compile(r"\bsk-[a-zA-Z0-9_-]{8,}\b"),
    )

    def filter(self, record):
        message = str(record.msg)
        for pattern in self.patterns:
            message = pattern.sub("[REDACTED]", message)
        record.msg = message
        if record.args:
            if isinstance(record.args, dict):
                record.args = {key: "[REDACTED]" if self._sensitive(value) else value for key, value in record.args.items()}
            else:
                record.args = tuple("[REDACTED]" if self._sensitive(value) else value for value in record.args)
        return True

    def _sensitive(self, value):
        text = str(value)
        return any(pattern.search(text) for pattern in self.patterns)

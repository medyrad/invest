#!/usr/bin/env python3
"""Create local-only credentials once; never print or replace an existing env file."""

import os
from pathlib import Path
import secrets


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    password = secrets.token_urlsafe(32)
    content = (root / ".env.example").read_text()
    content = content.replace(
        "replace-with-a-random-secret-at-least-50-characters", secrets.token_urlsafe(64)
    ).replace("replace-with-a-random-database-password", password)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print("Existing .env preserved.")
        return
    with os.fdopen(descriptor, "w") as output:
        output.write(content)
    print("Created private local .env (values not printed).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Prepare and start the primary local development runtime without exposing secrets."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    str(ENV_FILE),
    "-f",
    str(ROOT / "deploy/compose.yaml"),
]


def _read_lines() -> list[str]:
    if not ENV_FILE.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/dev_env.py")], check=True, cwd=ROOT
        )
    return ENV_FILE.read_text().splitlines()


def _values(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in lines:
        if line and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def prepare() -> int:
    lines = _read_lines()
    values = _values(lines)
    if values.get("INVEST_ENV") != "development":
        raise SystemExit(
            "Primary runtime preparation is allowed only for INVEST_ENV=development."
        )
    raw_port = os.environ.get("WEB_PORT", values.get("WEB_PORT", "3108"))
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise SystemExit("WEB_PORT must be an integer.") from exc
    if not 1024 <= port <= 65535:
        raise SystemExit("WEB_PORT must be between 1024 and 65535.")
    exact = {
        "WEB_PORT": str(port),
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1,backend",
        "CSRF_TRUSTED_ORIGINS": f"http://localhost:{port},http://127.0.0.1:{port}",
    }
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in exact:
            if key not in seen:
                output.append(f"{key}={exact[key]}")
                seen.add(key)
        else:
            output.append(line)
    for key, value in exact.items():
        if key not in seen:
            output.append(f"{key}={value}")
    content = "\n".join(output) + "\n"
    if content != ENV_FILE.read_text():
        mode = ENV_FILE.stat().st_mode & 0o777
        temporary = ENV_FILE.with_suffix(".runtime.tmp")
        temporary.write_text(content)
        os.chmod(temporary, mode)
        temporary.replace(ENV_FILE)
    print(
        f"Primary development runtime prepared on loopback port {port}; no secrets printed."
    )
    return port


def source_fingerprint(prefix: str) -> str:
    paths = subprocess.run(
        ["git", "ls-files", prefix, "contracts", "deploy"],
        check=True, cwd=ROOT, capture_output=True, text=True,
    ).stdout.splitlines()
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = ROOT / relative
        if path.is_file():
            digest.update(relative.encode()); digest.update(b"\0"); digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def provenance_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "INVEST_SOURCE_COMMIT": subprocess.run(["git", "rev-parse", "HEAD"], check=True, cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "INVEST_SOURCE_TREE": subprocess.run(["git", "write-tree"], check=True, cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "INVEST_BACKEND_SOURCE_SHA256": source_fingerprint("backend"),
        "INVEST_FRONTEND_SOURCE_SHA256": source_fingerprint("frontend"),
    })
    return env


def run(command: list[str], *, env=None) -> None:
    subprocess.run(command, check=True, cwd=ROOT, env=env)


def ensure_scanner() -> None:
    image = subprocess.run(
        ["docker", "image", "inspect", "invest-scanner:1.5.4"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        cwd=ROOT,
    ).returncode == 0
    data = ROOT / ".tools/scanner/data"
    if not image or not all((data / name).is_file() for name in ("main.cvd", "daily.cvd")):
        run([str(ROOT / "deploy/prepare-scanner.sh")])


def start(build: bool) -> None:
    prepare()
    if build:
        run(COMPOSE + ["build", "backend", "web"], env=provenance_env())
    ensure_scanner()
    run(COMPOSE + ["up", "-d", "--wait", "db", "scanner"])
    run(
        COMPOSE
        + [
            "run",
            "--rm",
            "backend",
            "/app/.venv/bin/python",
            "manage.py",
            "migrate",
            "--noinput",
        ]
    )
    run(
        COMPOSE
        + [
            "run",
            "--rm",
            "backend",
            "/app/.venv/bin/python",
            "manage.py",
            "import_reference",
        ]
    )
    run(
        COMPOSE
        + [
            "run",
            "--rm",
            "backend",
            "/app/.venv/bin/python",
            "manage.py",
            "seed_core_demo",
        ]
    )
    run(COMPOSE + ["up", "-d", "backend", "web", "workspace-jobs"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "up"])
    parser.add_argument(
        "--build",
        action="store_true",
        help="build the affected runtime images before starting",
    )
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        start(args.build)


if __name__ == "__main__":
    main()

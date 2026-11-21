#!/usr/bin/env python3
"""Prepare and start the primary local development runtime without exposing secrets."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import socket
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


def run(command: list[str], *, env=None, cwd: Path = ROOT) -> None:
    subprocess.run(command, check=True, cwd=cwd, env=env)


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


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        # Same as Node and Docker: ignore TIME_WAIT leftovers, fail only on a live listener.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def published(service: str, container_port: int, compose: list[str] = COMPOSE) -> bool:
    """True when this project's own container already holds the host port."""
    result = subprocess.run(
        compose + ["port", service, str(container_port)],
        capture_output=True, text=True, check=False, cwd=ROOT,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def ensure_db_port() -> None:
    """Move POSTGRES_PORT to a free port when another program already uses it."""
    if published("db", 5432):
        return
    values = _values(_read_lines())
    current = int(values.get("POSTGRES_PORT", "55432"))
    if port_free(current):
        return
    replacement = next((p for p in range(current + 1, current + 100) if port_free(p)), None)
    if replacement is None:
        raise SystemExit(f"Database port {current} is in use and no free port was found nearby.")
    text = ENV_FILE.read_text()
    text = re.sub(r"(?m)^POSTGRES_PORT=\d+$", f"POSTGRES_PORT={replacement}", text)
    text = re.sub(
        r"(?m)^(DATABASE_URL=.*@127\.0\.0\.1:)\d+/", rf"\g<1>{replacement}/", text
    )
    ENV_FILE.write_text(text)
    print(f"Database port {current} is used by another program; using {replacement} instead.")


def require_node() -> None:
    wanted = (ROOT / ".nvmrc").read_text().strip()
    try:
        found = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip().lstrip("v")
    except (OSError, subprocess.CalledProcessError):
        found = ""
    if found != wanted:
        raise SystemExit(
            f"`make dev` needs Node {wanted} (found: {found or 'none'}). "
            f"Install it with nvm: `nvm install {wanted}` then `nvm use {wanted}`."
        )


def image_fingerprint(image: str, label: str) -> str:
    result = subprocess.run(
        ["docker", "image", "inspect", image, "--format", f'{{{{index .Config.Labels "{label}"}}}}'],
        capture_output=True, text=True, check=False, cwd=ROOT,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def backend_image_stale() -> bool:
    built = image_fingerprint("invest-backend", "invest.source.backend.sha256")
    return built != source_fingerprint("backend")


def ensure_frontend_packages() -> None:
    frontend = ROOT / "frontend"
    wanted = hashlib.sha256((frontend / "package-lock.json").read_bytes()).hexdigest()
    stamp = frontend / "node_modules/.invest-lock.sha256"
    if stamp.is_file() and stamp.read_text().strip() == wanted:
        return
    print("Installing frontend packages (package-lock.json changed or first run)...")
    run(["npm", "ci"], cwd=frontend)
    stamp.write_text(wanted + "\n")


def start(build: bool, frontend_dev: bool = False) -> None:
    port = prepare()
    if frontend_dev:
        require_node()
        # The built web container also binds the port; stop it before checking.
        run(COMPOSE + ["stop", "web"])
        if not port_free(port):
            raise SystemExit(
                f"Port {port} is already in use, so `next dev` cannot start. "
                "Another `make dev` or dev server is probably running: stop it "
                f"(Ctrl+C in its terminal, or find it with `ss -ltnp | grep {port}`) and retry."
            )
    ensure_db_port()
    if build:
        services = ["backend"] if frontend_dev else ["backend", "web"]
        run(COMPOSE + ["build", *services], env=provenance_env())
    elif frontend_dev and backend_image_stale():
        print("Backend code changed since the last image build; rebuilding the backend image...")
        run(COMPOSE + ["build", "backend"], env=provenance_env())
    ensure_scanner()
    run(COMPOSE + ["up", "-d", "--wait", "db", "scanner"])
    for command in (["migrate", "--noinput"], ["import_reference"], ["seed_core_demo"]):
        run(COMPOSE + ["run", "--rm", "backend", "/app/.venv/bin/python", "manage.py", *command])
    if not frontend_dev:
        run(COMPOSE + ["up", "-d", "backend", "web", "workspace-jobs"])
        return
    # `make dev`: publish the backend for `next dev` on the host and leave the web
    # port free instead of starting the built web container.
    backend_port = int(os.environ.get("BACKEND_DEV_PORT", "8018"))
    dev_compose = COMPOSE + ["-f", str(ROOT / "deploy/compose.dev.yaml")]
    if not published("backend", 8000, dev_compose) and not port_free(backend_port):
        raise SystemExit(
            f"Backend dev port {backend_port} is in use. Pick another one, for example "
            "`make dev BACKEND_DEV_PORT=8028`."
        )
    env = os.environ | {"BACKEND_DEV_PORT": str(backend_port)}
    run(dev_compose + ["up", "-d", "--wait", "backend", "workspace-jobs"], env=env)
    ensure_frontend_packages()
    frontend = ROOT / "frontend"
    next_bin = str(frontend / "node_modules/.bin/next")
    print(
        f"\nOpen http://127.0.0.1:{port} . Frontend edits reload instantly.\n"
        "Ctrl+C stops only the frontend; run `make stop` to stop the backend too.\n"
    )
    os.chdir(frontend)
    os.execve(
        next_bin,
        [next_bin, "dev", "--hostname", "127.0.0.1", "--port", str(port)],
        env | {"BACKEND_INTERNAL_ORIGIN": f"http://127.0.0.1:{backend_port}"},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "up"])
    parser.add_argument(
        "--build",
        action="store_true",
        help="build the affected runtime images before starting",
    )
    parser.add_argument(
        "--frontend-dev",
        action="store_true",
        help="run `next dev` with hot reload against the dockerized backend",
    )
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        start(args.build, args.frontend_dev)


if __name__ == "__main__":
    main()

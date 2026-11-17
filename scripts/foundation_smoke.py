"""Exercise only the invest Compose stack; synthetic accounts, no secret output."""
import json
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "--env-file", str(ROOT / ".env"),
           "-f", str(ROOT / "deploy/compose.yaml")]


def run(*args):
    result = subprocess.run([*COMPOSE, *args], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Compose operation failed: {args[0]}")
    return result.stdout.strip()


def request(path):
    start = time.monotonic()
    try:
        response = urllib.request.urlopen("http://127.0.0.1:3108/api/v1/" + path, timeout=8)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response), round(time.monotonic() - start, 3)


def wait_ready():
    deadline = time.monotonic() + 55
    while time.monotonic() < deadline:
        try:
            if request("health/ready")[:2] == (200, {"status": "ok"}):
                return
        except (OSError, ValueError):
            pass
        time.sleep(1)
    raise RuntimeError("Invest readiness did not recover within 55 seconds")


def other_containers():
    result = subprocess.check_output(["docker", "ps", "--format", "{{.ID}} {{.Names}}"], text=True)
    return sorted(line for line in result.splitlines() if not line.split()[1].startswith("invest-"))


def main():
    before = other_containers()
    wait_ready()
    ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    # Valid-format synthetic data, with no authentication or SMS send.
    phones = ["+1999" + str(uuid.uuid4().int % 10**10).zfill(10) for _ in ids]
    code = ("import json; from django.contrib.auth import get_user_model; "
            f"pairs={list(zip(ids, phones))!r}; "
            "[get_user_model().objects.create_user(id=i,mobile=m) for i,m in pairs]; "
            "print(json.dumps(sorted(i for i,m in pairs)))")
    created = json.loads(run("exec", "-T", "backend", "/app/.venv/bin/python", "manage.py",
                             "shell", "--verbosity", "0", "-c", code).splitlines()[-1])
    run("restart", "db", "backend")
    wait_ready()
    query = ("import json; from django.contrib.auth import get_user_model; "
             f"print(json.dumps(sorted(str(i) for i in get_user_model().objects.filter(id__in={ids!r})"
             ".values_list('id',flat=True))))")
    recovered = json.loads(run("exec", "-T", "backend", "/app/.venv/bin/python", "manage.py",
                               "shell", "--verbosity", "0", "-c", query).splitlines()[-1])
    assert created == recovered == sorted(ids), "Account persistence failed"
    try:
        run("stop", "db")
        live = request("health/live")
        ready = request("health/ready")
        assert live[:2] == (200, {"status": "ok"}), "Liveness depends on DB"
        assert ready[:2] == (503, {"status": "unavailable"}), "Outage falsely reports ready"
        assert ready[2] < 8, "Readiness exceeds timeout budget"
    finally:
        run("start", "db")
        wait_ready()
    assert request("_test/probe")[0] == 404, "Test endpoint exposed in delivery backend"
    assert before == other_containers(), "Unrelated container set changed"
    evidence = {
        "passed": True, "synthetic_account_ids": ids, "restart_preserved": 2,
        "outage_live": live, "outage_ready": ready, "recovered": request("health/ready"),
        "production_probe": 404, "unrelated_containers_unchanged": True,
        "public_deployment": False,
    }
    target = ROOT / "docs/stage2/evidence/smoke.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()

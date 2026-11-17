"""Prove immutable installs reject drift using disposable copies, never edit real locks."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run(["docker", "build", "--target", "builder", "-t", "invest-dependencies",
                    "-f", "deploy/backend.Dockerfile", "."], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix="invest-lock-check-") as temp:
        work = Path(temp)
        backend = work / "backend"
        frontend = work / "frontend"
        backend.mkdir()
        frontend.mkdir()
        for name in ("pyproject.toml", "uv.lock"):
            shutil.copy2(ROOT / "backend" / name, backend / name)
        manifest = backend / "pyproject.toml"
        manifest.write_text(manifest.read_text().replace('  "gunicorn==27.0.1",\n', ""))
        uv = subprocess.run([
            "docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
            "-e", "UV_CACHE_DIR=/tmp/uv-cache", "-e", "UV_PROJECT_ENVIRONMENT=/tmp/venv",
            "-v", f"{backend}:/work", "-w", "/work", "invest-dependencies",
            "uv", "sync", "--locked", "--no-dev",
        ], capture_output=True, text=True, timeout=120)
        assert uv.returncode != 0 and "lockfile" in uv.stderr.lower(), "uv drift was not rejected"
        for name in ("package.json", "package-lock.json", ".npmrc"):
            shutil.copy2(ROOT / "frontend" / name, frontend / name)
        lock_path = frontend / "package-lock.json"
        lock = json.loads(lock_path.read_text())
        lock["packages"]["node_modules/react"]["version"] = "0.0.0"
        lock_path.write_text(json.dumps(lock))
        npm = subprocess.run(["npm", "ci", "--offline", "--ignore-scripts"], cwd=frontend,
                             capture_output=True, text=True, timeout=120)
        assert npm.returncode != 0 and "EUSAGE" in npm.stderr, "npm drift was not rejected"
    evidence = {"passed": True, "uv_locked_rejected_manifest_drift": True,
                "npm_ci_rejected_lock_drift": True, "real_manifests_unchanged": True,
                "uv_exit": uv.returncode, "npm_exit": npm.returncode}
    target = ROOT / "docs/stage2/evidence/lock-drift.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()

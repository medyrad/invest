"""Record S04 source and delivery evidence without reading configuration secrets."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/stage4/evidence/manifest.json"
SKIP = {"node_modules", ".next", ".venv", "__pycache__", "test-results", ".pytest_cache", ".ruff_cache"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def included(path):
    return not path.name.startswith(".env") and not (set(path.relative_to(ROOT).parts) & SKIP) and path.suffix not in {".pyc", ".tsbuildinfo"}


def main():
    code = {}
    for directory in ("backend", "frontend", "contracts", "deploy", "scripts", ".github"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and included(path):
                code[str(path.relative_to(ROOT))] = digest(path)
    code["Makefile"] = digest(ROOT / "Makefile")
    tree = hashlib.sha256(json.dumps(code, sort_keys=True).encode()).hexdigest()
    evidence = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / "docs/stage4").rglob("*"))
                if p.is_file() and p != OUT}
    specification = {str(p.relative_to(ROOT)): digest(p)
                     for p in sorted((ROOT / "specs/006-home-catalog").rglob("*")) if p.is_file()}
    history = {}
    before_path = ROOT / ".tools/s04/before.json"
    if before_path.exists():
        before = json.loads(before_path.read_text())
        history = {k: v for k, v in before.items() if k.startswith(("docs/stage1/", "docs/stage2/", "docs/stage3/"))}
        assert all((ROOT / k).is_file() and digest(ROOT / k) == v for k, v in history.items())
    runtime = json.loads((ROOT / "docs/stage4/evidence/runtime.json").read_text())
    for row in runtime["images"]:
        cid = subprocess.check_output([
            "docker", "compose", "--env-file", ".env", "-f", "deploy/compose.yaml",
            "ps", "-q", row["service"],
        ], cwd=ROOT, text=True).strip()
        actual = subprocess.check_output(["docker", "inspect", "--format", "{{.Image}}", cid], text=True).strip()
        assert actual == row["image_id"], "Runtime evidence must match the running image"
    build_id = subprocess.check_output([
        "docker", "compose", "--env-file", ".env", "-f", "deploy/compose.yaml", "exec", "-T",
        "web", "node", "-e", "process.stdout.write(require('fs').readFileSync('/app/.next/BUILD_ID','utf8'))",
    ], cwd=ROOT, text=True).strip()
    data = {"mission": "PROGRAMMER-S04-01", "version": "S04-" + tree[:12], "source_sha256": tree,
            "status": "آماده آزمون مستقل PROGRAMMER-S04-01", "source_files": code,
            "specification": specification, "evidence": evidence, "delivery_build_id": build_id,
            "browser_build_id": (ROOT / "frontend/.next/BUILD_ID").read_text().strip(),
            "runtime_images": runtime["images"], "protected_history": history,
            "human_visual_approved": False, "full_s04_complete": False, "public_deployed": False}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"version": data["version"], "source_files": len(code),
                      "historical_files_preserved": len(history), "delivery_build_id": build_id}))


if __name__ == "__main__":
    main()

"""Read reference ZIPs without executing their code; regenerate planning evidence."""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


class Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag in ("input", "textarea", "select"):
            self.items.append({"tag": tag, "attributes": dict(attrs), "line": self.getpos()[0]})


def literal(text, name):
    start = re.search(r"export const " + name + r"[^=]*=", text).end()
    return json.JSONDecoder().raw_decode(text[start:].lstrip())[0]


def build(advisor, ham):
    inventory = []
    archives = []
    source = {}
    for key, path in (("advisor", advisor), ("ham", ham)):
        archives.append({"id": key, "path": str(path), "sha256": hashlib.file_digest(path.open("rb"), "sha256").hexdigest()})
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                parts = Path(member.filename).parts[1:]
                if member.is_dir() or not parts or set(parts) & {".git", "node_modules", "__pycache__", ".venv", ".next"}:
                    continue
                data = archive.read(member)
                relative = "/".join(parts)
                inventory.append({"archive": key, "path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
                source[key + "/" + relative] = data

    def read(path):
        return source["advisor/" + path].decode("utf-8")

    fields = []
    match = read("src/lib/match.ts")
    for line, text in enumerate(read("src/data/fields.ts").splitlines(), 1):
        found = re.search(r'id: "([^"]+)", label: "([^"]+)"', text)
        if not found:
            continue
        field_id, label = found.groups()
        placement = re.search(r'placement: "([^"]+)"', text).group(1)
        fields.append({"id": field_id, "label": label, "placement": placement,
                       "source": "advisor/src/data/fields.ts", "line": line,
                       "mentioned_in_match_source": bool(re.search(r'[\"\']' + re.escape(field_id) + r'[\"\']|c\.' + re.escape(field_id) + r'\b', match)),
                       "classification": "needs-semantic-review", "definition": text.strip()})
    groups = literal(read("src/data/taxonomy.ts"), "projectGroups")
    data = read("src/data/opportunities.ts")
    counts = {name: len(literal(data, name)) for name in ("opportunities", "generatedOpportunities", "funds", "saleItems")}
    advisories = literal(read("src/data/advisories.ts"), "advisories")
    parser = Controls()
    parser.feed(read("public/engine/advisor.html"))
    pages = sorted(key.removeprefix("advisor/") for key in source if key.startswith("advisor/src/app/") and key.endswith("/page.tsx"))
    summary = {
        "analysis_date": "2026-11-17", "method": "static extraction without executing archived scripts",
        "archives": archives, "inventory_entries": len(inventory), "listing_counts": counts,
        "total_listings": sum(counts.values()), "project_groups": len(groups),
        "project_subtypes": sum(len(group["subtypes"]) for group in groups),
        "field_counts": dict(Counter(field["placement"] for field in fields)),
        "advisory_configurations": len(advisories), "static_html_controls": len(parser.items),
        "page_sources": pages,
        "speckit_paths_in_ham": [row["path"] for row in inventory if row["archive"] == "ham" and (".specify" in row["path"] or "speckit" in row["path"].lower())],
        "limitations": ["Metadata hashing does not mean every file was semantically reviewed.",
                        "Static HTML controls exclude controls generated dynamically by JavaScript.",
                        "Textual mention in match.ts is not proof that a field is implemented correctly.",
                        "No browser, application, migration or production verification performed."]}
    csv_file = io.StringIO(newline="")
    writer = csv.DictWriter(csv_file, fieldnames=list(fields[0]))
    writer.writeheader()
    writer.writerows(fields)
    dumps = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    return {"source-inventory.json": dumps(inventory), "source-summary.json": dumps(summary),
            "fields.csv": csv_file.getvalue(), "legacy-controls.json": dumps(parser.items),
            "taxonomy.json": dumps(groups), "advisory-inventory.json": dumps([
                {"id": key, "questions": value.get("questions", []), "baseChecks": value.get("baseChecks", []),
                 "context": value.get("context"), "source": "advisor/src/data/advisories.ts"}
                for key, value in advisories.items()])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--advisor", type=Path, required=True)
    parser.add_argument("--ham", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "docs" / "catalogs"
    generated = build(args.advisor, args.ham)
    if args.check:
        mismatches = [name for name, value in generated.items() if not (output / name).exists() or (output / name).read_bytes() != value.encode("utf-8")]
        if mismatches:
            raise SystemExit("Catalog drift: " + ", ".join(mismatches))
    else:
        output.mkdir(parents=True, exist_ok=True)
        for name, value in generated.items():
            (output / name).write_bytes(value.encode("utf-8"))
    print(json.dumps({"mode": "check" if args.check else "build", "files": len(generated), "status": "passed"}))


if __name__ == "__main__":
    main()

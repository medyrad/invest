#!/usr/bin/env python3
"""Build review-only contact sheets for the mandated 12-group/four-width sample."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MATRIX = ROOT / "docs/experience-complete/tech-evidence-01/design-slot-matrix.csv"
PICKS = {
    "G01": "DES-023",
    "G02": "DES-025",
    "G03": "DES-034",
    "G04": "DES-030",
    "G05": "DES-032",
    "G06": "DES-031",
    "G07": "DES-007",
    "G08": "DES-033",
    "G09": "DES-009",
    "G10": "DES-035",
    "G11": "DES-036",
    "G12": "DES-039",
}
WIDTHS = (360, 390, 768, 1440)
RISK_ROWS = ("DES-025", "DES-026", "DES-033", "DES-035", "DES-036", "DES-037", "DES-038", "DES-039", "DES-040")


def main() -> None:
    rows = list(csv.DictReader(MATRIX.open()))
    index = []
    font = ImageFont.load_default()
    for group, row_id in PICKS.items():
        chosen = {
            int(row["viewport_width"]): row
            for row in rows
            if row["group"] == group and row["row_id"] == row_id
        }
        assert set(chosen) == set(WIDTHS), (group, chosen.keys())
        cards = []
        for width in WIDTHS:
            row = chosen[width]
            path = ROOT / row["product_evidence"]
            assert path.exists(), path
            with Image.open(path) as source:
                source = source.convert("RGB")
                source.thumbnail((340, 760))
                card = Image.new("RGB", (360, 820), "white")
                card.paste(source, ((360 - source.width) // 2, 48))
                draw = ImageDraw.Draw(card)
                draw.text((10, 8), f"{group} {row_id} | {width}px", fill="black", font=font)
                draw.text((10, 24), row["classification"], fill="black", font=font)
                cards.append(card)
            index.append(
                {
                    "group": group,
                    "row_id": row_id,
                    "width": width,
                    "state": row["state"],
                    "classification": row["classification"],
                    "product_evidence": row["product_evidence"],
                    "reference_evidence": row["reference_evidence"],
                }
            )
        sheet = Image.new("RGB", (1440, 820), "#dddddd")
        for offset, card in enumerate(cards):
            sheet.paste(card, (offset * 360, 0))
        sheet.save(HERE / f"visual-sample-{group}.png", optimize=True)
    for row_id in RISK_ROWS:
        chosen = {int(row["viewport_width"]): row for row in rows if row["row_id"] == row_id}
        cards = []
        for width in WIDTHS:
            row = chosen[width]
            with Image.open(ROOT / row["product_evidence"]) as source:
                source = source.convert("RGB")
                source.thumbnail((340, 760))
                card = Image.new("RGB", (360, 820), "white")
                card.paste(source, ((360 - source.width) // 2, 48))
                draw = ImageDraw.Draw(card)
                draw.text((10, 8), f"{row_id} | {width}px", fill="black", font=font)
                draw.text((10, 24), row["classification"], fill="black", font=font)
                cards.append(card)
        sheet = Image.new("RGB", (1440, 820), "#dddddd")
        for offset, card in enumerate(cards):
            sheet.paste(card, (offset * 360, 0))
        sheet.save(HERE / f"visual-risk-{row_id}.png", optimize=True)
    (HERE / "visual-sample-index.json").write_text(
        json.dumps({"groups": 12, "slots": len(index), "items": index}, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()

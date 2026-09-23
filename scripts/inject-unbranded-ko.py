#!/usr/bin/env python3
"""Inject verified no-maker Transformers KOs onto company `unbranded`.

Source: TFSafari Shopify "No Brand" collection, pulled 2026-09-23.
Catalog: scripts/figure_oneshot/unbranded_ko_catalog.json

Each row is a listing whose producer line is no-brand / 4th party / N/A and
whose title does not name a maker. Named studios (WeiJiang, Black Mamba, Rose
Toys, Yuexing, Baiwei, Metal Club, QQT, …) are not in the catalog. Official
Hasbro/Takara MP-10 stays put. Barcodes on these variants are empty, so `sku`
stays unset and the shop listing code is an alias only.

Does NOT Build Publish Live.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import clean_code  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
STATS = ROOT / "src/data/figure-archive/unbranded-ko-inject-stats.json"
CATALOG = SCRIPTS / "figure_oneshot/unbranded_ko_catalog.json"
SOURCE = "inject-unbranded-ko"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def norm_code(c: str | None) -> str:
    if not c:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(c).upper())


def ensure_alias_doc(doc: dict) -> dict:
    doc.setdefault("version", 1)
    doc.setdefault("policy", "gtin-canonical")
    doc.setdefault("aliasesByFigureId", {})
    doc.setdefault("aliasToFigureId", {})
    doc.setdefault("collapsed", [])
    doc.setdefault("flagged", [])
    return doc


def add_aliases(doc: dict, figure_id: str, codes: list[str]) -> int:
    by = doc["aliasesByFigureId"]
    to = doc["aliasToFigureId"]
    cur = list(by.get(figure_id) or [])
    added = 0
    for c in codes:
        c2 = clean_code(c) or str(c).strip()
        if not c2:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def main() -> None:
    rows: list[dict] = load_json(ARCHIVE)
    aliases = ensure_alias_doc(load_json(ALIASES))
    catalog = load_json(CATALOG)
    items: list[dict] = catalog["items"]

    ids = {r["id"] for r in rows}
    name_keys = {(r.get("company"), (r.get("name") or "").lower()) for r in rows}
    identity = {
        (
            (r.get("name") or "").lower(),
            (r.get("line") or "").lower(),
            (r.get("releaseDate") or "")[:4],
            (r.get("subtitle") or "").lower(),
        )
        for r in rows
    }
    code_keys: set[str] = set()
    for r in rows:
        for t in r.get("tags") or []:
            if isinstance(t, str) and t.startswith("code:"):
                code_keys.add(norm_code(t[5:]))
    alias_to: dict[str, str] = aliases.get("aliasToFigureId") or {}
    alias_norm = {norm_code(k): v for k, v in alias_to.items() if norm_code(k)}

    added: list[str] = []
    skipped: list[dict] = []
    alias_added = 0
    dropped_aliases: list[dict] = []

    for item in items:
        rid = item["id"]
        name = item["name"]
        line = item["line"]
        release = item["releaseDate"]
        subtitle = item["subtitle"]
        if rid in ids:
            skipped.append({"id": rid, "reason": "id-exists"})
            continue
        if ("unbranded", name.lower()) in name_keys:
            skipped.append({"id": rid, "reason": "name-exists", "name": name})
            continue
        ident = (name.lower(), line.lower(), release[:4], subtitle.lower())
        if ident in identity:
            skipped.append({"id": rid, "reason": "identity-exists", "name": name})
            continue

        keep_aliases: list[str] = []
        for raw in item.get("aliases") or []:
            c2 = clean_code(raw) or ""
            nc = norm_code(c2)
            if not c2 or not nc:
                dropped_aliases.append({"id": rid, "code": raw, "reason": "empty"})
                continue
            if re.search(r"[\u4e00-\u9fff]", c2):
                dropped_aliases.append({"id": rid, "code": raw, "reason": "non-ascii"})
                continue
            owner = alias_to.get(c2) or alias_norm.get(nc)
            if owner and owner != rid:
                dropped_aliases.append({"id": rid, "code": c2, "reason": "alias-collision", "owner": owner})
                continue
            if nc in code_keys:
                dropped_aliases.append({"id": rid, "code": c2, "reason": "code-tag-collision"})
                continue
            keep_aliases.append(c2)

        row = {
            "id": rid,
            "name": name,
            "subtitle": subtitle,
            "line": line,
            "company": "unbranded",
            "kind": "figure",
            "releaseDate": release,
            "msrp": float(item["msrp"]),
            "scale": item["scale"],
            "demand": 1.25,
            "tags": [
                "unbranded",
                "transformers",
                "3p",
                "ko",
                "curated",
                SOURCE,
                "src:tfsafari",
                *[f"code:{a}" for a in keep_aliases],
            ],
            "source": SOURCE,
            "property": "transformers",
            "party": "3p",
            "imageUrl": item["imageUrl"],
        }
        rows.append(row)
        ids.add(rid)
        name_keys.add(("unbranded", name.lower()))
        identity.add(ident)
        for a in keep_aliases:
            code_keys.add(norm_code(a))
        alias_added += add_aliases(aliases, rid, [*keep_aliases, f"id:{rid}"])
        added.append(rid)

    aliases["updatedAt"] = now_iso()
    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    stats = {
        "source": SOURCE,
        "retailer": catalog.get("source"),
        "pulled": catalog.get("pulled"),
        "updatedAt": aliases["updatedAt"],
        "added": len(added),
        "ids": added,
        "skipped": skipped,
        "droppedAliases": dropped_aliases,
        "omitted": [
            "QQT-vendored TV-01/TV-02/TV-03 deformation Predaking limbs (vendor names QQT)",
            "Black Mamba, WeiJiang, Rose Toys, Yuexing, Baiwei, Metal Club, and KFC-filed listings",
            "Trailer-only accessories",
            "MP-28 Hot Rod listing whose producer line says Takara and note says not a KO",
            "Official Hasbro/Takara MP-10",
        ],
        "gtin": "none — Shopify barcodes were null; listing codes are aliases only",
    }
    write_json(STATS, stats)
    print(json.dumps({"added": len(added), "skipped": skipped, "droppedAliases": dropped_aliases}, indent=2))


if __name__ == "__main__":
    main()

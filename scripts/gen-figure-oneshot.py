#!/usr/bin/env python3
"""One-shot permanent figure archive dump.

Fetches ALL Shopify AF storefront pages + curated major-line expansions,
writes src/data/figure-archive/oneshot.json, and rewires figures.ts to import it.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_backlog_common import parse_existing_ts  # noqa: E402
from figure_oneshot.curated import build_curated  # noqa: E402
from figure_oneshot.shopify_dump import dump_all_storefronts  # noqa: E402

ARCHIVE_DIR = ROOT / "src/data/figure-archive"
ARCHIVE_JSON = ARCHIVE_DIR / "oneshot.json"
STATS_JSON = ARCHIVE_DIR / "oneshot-stats.json"
FIGURES_TS = ROOT / "src/data/figures.ts"
MANIFEST = ROOT / "src/data/figure-backlog/manifest.json"
TODAY = date.today().isoformat()


def fig_key(f: dict) -> str:
    return f"{f['name']}|{f['subtitle']}|{f['line']}|{f['company']}".lower()


def clean_for_json(f: dict) -> dict:
    out = {
        "id": f["id"],
        "name": f["name"],
        "subtitle": f["subtitle"],
        "line": f["line"],
        "company": f["company"],
        "kind": f.get("kind", "figure"),
        "releaseDate": f["releaseDate"],
        "msrp": float(f["msrp"]),
        "scale": f["scale"],
        "demand": float(f.get("demand", 1)),
        "tags": f["tags"] if isinstance(f["tags"], list) else [t for t in str(f["tags"]).split(",") if t],
    }
    if f.get("sku"):
        out["sku"] = f["sku"]
    if f.get("exclusive"):
        out["exclusive"] = f["exclusive"]
    if f.get("imageUrl"):
        out["imageUrl"] = f["imageUrl"]
    if f.get("source"):
        out["source"] = f["source"]
    return out


def ensure_figures_ts_imports_archive():
    """Ensure figures.ts imports and merges oneshot archive (idempotent)."""
    src = FIGURES_TS.read_text()
    if "figure-archive/oneshot.json" in src and "ARCHIVE_FIGURES" in src:
        print("figures.ts already wired for archive import")
        return

    # Inject import after existing imports
    if "import archiveRows" not in src:
        src = src.replace(
            'import type { CatalogFigure, CompanyId, ItemKind } from "@/lib/types";\n',
            'import type { CatalogFigure, CompanyId, ItemKind } from "@/lib/types";\n'
            'import archiveRows from "./figure-archive/oneshot.json";\n',
            1,
        )

    # Replace FIGURES export block
    old = """export const FIGURES: CatalogFigure[] = rows.map(
  ([id, name, subtitle, line, company, kind, releaseDate, msrp, scale, demand, tags, extra]) => ({
    id,
    name,
    subtitle,
    line,
    company,
    kind,
    releaseDate,
    msrp,
    scale,
    demand,
    tags: tags.split(","),
    sku: extra?.sku,
    exclusive: extra?.exclusive,
  }),
);"""

    new = """function rowToFigure(
  [id, name, subtitle, line, company, kind, releaseDate, msrp, scale, demand, tags, extra]: Row,
): CatalogFigure {
  return {
    id,
    name,
    subtitle,
    line,
    company,
    kind,
    releaseDate,
    msrp,
    scale,
    demand,
    tags: tags.split(","),
    sku: extra?.sku,
    exclusive: extra?.exclusive,
  };
}

type ArchiveRow = {
  id: string;
  name: string;
  subtitle: string;
  line: string;
  company: CompanyId;
  kind: ItemKind;
  releaseDate: string;
  msrp: number;
  scale: string;
  demand: number;
  tags: string[];
  sku?: string;
  exclusive?: string;
  imageUrl?: string;
};

function archiveToFigure(r: ArchiveRow): CatalogFigure {
  return {
    id: r.id,
    name: r.name,
    subtitle: r.subtitle,
    line: r.line,
    company: r.company,
    kind: r.kind,
    releaseDate: r.releaseDate,
    msrp: r.msrp,
    scale: r.scale,
    demand: r.demand,
    tags: r.tags,
    sku: r.sku,
    exclusive: r.exclusive,
    imageUrl: r.imageUrl,
  };
}

function dedupeAppend(base: CatalogFigure[], extra: CatalogFigure[]): CatalogFigure[] {
  const ids = new Set(base.map((f) => f.id));
  const keys = new Set(base.map((f) => `${f.name}|${f.subtitle}|${f.line}|${f.company}`.toLowerCase()));
  const out = [...base];
  for (const f of extra) {
    const k = `${f.name}|${f.subtitle}|${f.line}|${f.company}`.toLowerCase();
    if (ids.has(f.id) || keys.has(k)) continue;
    ids.add(f.id);
    keys.add(k);
    out.push(f);
  }
  return out;
}

const SEED_FIGURES: CatalogFigure[] = rows.map(rowToFigure);
const ARCHIVE_FIGURES: CatalogFigure[] = (archiveRows as ArchiveRow[]).map(archiveToFigure);

/** Permanent catalog: seed rows + one-shot archive dump (Shopify + curated). */
export const FIGURES: CatalogFigure[] = dedupeAppend(SEED_FIGURES, ARCHIVE_FIGURES);"""

    if old not in src:
        raise SystemExit("figures.ts FIGURES map block not found — update wiring manually")
    src = src.replace(old, new, 1)
    FIGURES_TS.write_text(src)
    print("wired figures.ts to import oneshot archive")


def update_manifest(shopify_n: int, curated_n: int, total_n: int):
    man = {
        "strategy": "one-shot-permanent-dump",
        "note": "Batches are optional legacy only. Growth is the oneshot archive + weekly Shopify N&N ingest.",
        "oneshotInjectedAt": TODAY,
        "oneshotFile": "src/data/figure-archive/oneshot.json",
        "oneshotCounts": {
            "shopify": shopify_n,
            "curated": curated_n,
            "archiveTotal": total_n,
        },
        "targetBatchSize": [180, 250],
        "lastInjectedAt": "2026-09-05",
        "lastInjectedBatch": "batch-001",
        "queued": [],
        "injected": ["batch-001"],
        "legacyBatchesOptional": True,
    }
    MANIFEST.write_text(json.dumps(man, indent=2) + "\n")


def main():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    existing_ids, existing_keys = parse_existing_ts()
    print(f"existing seed/injected figures: {len(existing_ids)}")

    print("=== Shopify full pagination ===")
    shopify_rows, shopify_stats = dump_all_storefronts()

    print("=== Curated expansions ===")
    curated_rows = build_curated()
    print(f"curated raw: {len(curated_rows)}")

    kept_shopify = []
    kept_curated = []
    seen_ids = set(existing_ids)
    seen_keys = set(existing_keys)

    for src_name, bucket, dest in (
        ("shopify", shopify_rows, kept_shopify),
        ("curated", curated_rows, kept_curated),
    ):
        for f in bucket:
            if f["id"] in seen_ids:
                continue
            k = fig_key(f)
            if k in seen_keys:
                continue
            # release floor
            if f.get("releaseDate", "9999") < "1980-01-01":
                f["releaseDate"] = "1980-01-01"
            seen_ids.add(f["id"])
            seen_keys.add(k)
            dest.append(clean_for_json(f))

    archive = kept_shopify + kept_curated
    archive.sort(key=lambda r: (r["releaseDate"], r["company"], r["name"]), reverse=True)

    ARCHIVE_JSON.write_text(json.dumps(archive, indent=2) + "\n")
    stats = {
        "generatedAt": TODAY,
        "priorSeedAndInjected": len(existing_ids),
        "shopifyRaw": shopify_stats.get("raw"),
        "shopifyKeptByShop": shopify_stats.get("kept"),
        "shopifyAdded": len(kept_shopify),
        "curatedRaw": len(curated_rows),
        "curatedAdded": len(kept_curated),
        "archiveTotal": len(archive),
        "projectedFIGURES": len(existing_ids) + len(archive),
        "byCompany": dict(Counter(r["company"] for r in archive).most_common()),
        "withImageUrl": sum(1 for r in archive if r.get("imageUrl")),
    }
    STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))

    ensure_figures_ts_imports_archive()
    update_manifest(len(kept_shopify), len(kept_curated), len(archive))
    print(f"wrote {ARCHIVE_JSON} ({ARCHIVE_JSON.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Ingest AF rows into the live figure SKU overlay (figure_catalog).

Lyra weekday BBTS/EE monitor entrypoint. Validates rows, then upserts via the
Node helper (DATABASE_URL → Neon/Postgres). Skip if already in baked FIGURES
or the live overlay (sku → id → name|subtitle|line|company).

Usage:
  python3 scripts/ingest-figure-sku-overlay.py path/to/batch.json
  python3 scripts/ingest-figure-sku-overlay.py --stdin < batch.json
  python3 scripts/ingest-figure-sku-overlay.py --dry-run batch.json

JSON shape: array of objects, or { "figures": [ ... ] }.
Required fields per row:
  id, name, subtitle, line, company, kind, releaseDate, msrp, scale,
  demand, tags, sku
Optional: exclusive, imageUrl, source

Constraints: AF (kind figure|kit), releaseDate >= 1980-01-01, real http(s)
imageUrl when set, no fabricated empty SKUs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RELEASE_FLOOR = "1980-01-01"
TYPES_TS = ROOT / "src/lib/types.ts"
HELPER = ROOT / "scripts/ingest-figure-sku-overlay.mjs"

VALID_KINDS = {"figure", "kit"}


def load_company_ids() -> set[str]:
    text = TYPES_TS.read_text()
    block = text.split("export type CompanyId", 1)[1].split("export type ItemKind", 1)[0]
    return set(re.findall(r'"([a-z0-9]+)"', block))


COMPANIES = load_company_ids()


def is_http_url(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.scheme in ("http", "https") and bool(u.netloc)
    except Exception:
        return False


def validate_row(raw: object, idx: int) -> tuple[dict | None, str | None]:
    if not isinstance(raw, dict):
        return None, f"row[{idx}]: not an object"
    req = ["id", "name", "line", "company", "kind", "releaseDate", "msrp", "scale", "demand", "sku"]
    for k in req:
        if k not in raw or raw[k] is None or (isinstance(raw[k], str) and not str(raw[k]).strip()):
            return None, f"row[{idx}]: missing {k}"

    sku = str(raw["sku"]).strip()
    if not sku or sku.lower() in {"unknown", "n/a", "none", "null", "todo", "tbd"}:
        return None, f"row[{idx}]: invalid/fake sku"

    kind = str(raw.get("kind") or "figure").strip()
    if kind not in VALID_KINDS:
        return None, f"row[{idx}]: kind must be figure|kit (AF only)"

    company = str(raw["company"]).strip()
    if company not in COMPANIES:
        return None, f"row[{idx}]: unknown company {company!r}"

    release = str(raw["releaseDate"]).strip()
    if release < RELEASE_FLOOR:
        return None, f"row[{idx}]: releaseDate before {RELEASE_FLOOR}"

    try:
        msrp = float(raw["msrp"])
        demand = float(raw["demand"])
    except (TypeError, ValueError):
        return None, f"row[{idx}]: msrp/demand must be numbers"
    if msrp < 0 or demand <= 0:
        return None, f"row[{idx}]: msrp/demand out of range"

    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif isinstance(tags, list):
        tags = [str(t).strip() for t in tags if str(t).strip()]
    else:
        return None, f"row[{idx}]: tags must be list or csv string"

    image_url = raw.get("imageUrl")
    if image_url is not None and str(image_url).strip():
        image_url = str(image_url).strip()
        if not is_http_url(image_url):
            return None, f"row[{idx}]: imageUrl must be http(s)"
    else:
        image_url = None

    exclusive = raw.get("exclusive")
    exclusive = str(exclusive).strip() if exclusive else None
    source = raw.get("source")
    source = str(source).strip() if source else None

    out = {
        "id": str(raw["id"]).strip(),
        "name": str(raw["name"]).strip(),
        "subtitle": str(raw.get("subtitle") or "").strip(),
        "line": str(raw["line"]).strip(),
        "company": company,
        "kind": kind,
        "releaseDate": release,
        "msrp": msrp,
        "scale": str(raw["scale"]).strip() or '6"',
        "demand": demand,
        "tags": tags,
        "sku": sku,
    }
    if exclusive:
        out["exclusive"] = exclusive
    if image_url:
        out["imageUrl"] = image_url
    if source:
        out["source"] = source
    return out, None


def load_payload(path: Path | None) -> list:
    if path is None:
        data = json.load(sys.stdin)
    else:
        data = json.loads(path.read_text())
    if isinstance(data, dict) and "figures" in data:
        data = data["figures"]
    if not isinstance(data, list):
        raise SystemExit("payload must be a JSON array or {figures: [...]}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_path", nargs="?", help="JSON file of figure rows")
    ap.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    ap.add_argument("--dry-run", action="store_true", help="Validate only; do not write DB")
    ap.add_argument("--out", type=Path, help="Write validated JSON to this path")
    args = ap.parse_args()

    if args.stdin:
        raw_rows = load_payload(None)
    elif args.json_path:
        raw_rows = load_payload(Path(args.json_path))
    else:
        ap.error("provide json_path or --stdin")

    valid: list[dict] = []
    errors: list[str] = []
    for i, row in enumerate(raw_rows):
        fig, err = validate_row(row, i)
        if err:
            errors.append(err)
        else:
            assert fig is not None
            valid.append(fig)

    print(f"[ingest-figure-overlay] input={len(raw_rows)} valid={len(valid)} invalid={len(errors)}")
    for e in errors[:30]:
        print(f"  ! {e}")
    if len(errors) > 30:
        print(f"  ! … {len(errors) - 30} more")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"figures": valid}, indent=2) + "\n")
        print(f"[ingest-figure-overlay] wrote {args.out}")

    if args.dry_run or not valid:
        if errors and not valid:
            return 2
        return 0 if not errors else 1

    env = os.environ.copy()
    if not env.get("DATABASE_URL", "").strip():
        # Prefer app .env.local without printing secrets
        env_path = ROOT / ".env.local"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DATABASE_URL=") and not env.get("DATABASE_URL"):
                    env["DATABASE_URL"] = line.split("=", 1)[1].strip().strip('"').strip("'")
        if not env.get("DATABASE_URL", "").strip():
            print(
                "[ingest-figure-overlay] DATABASE_URL not set — validated only.\n"
                "  Set DATABASE_URL (Neon) and re-run to upsert into figure_catalog.",
                file=sys.stderr,
            )
            return 3

    payload = {"figures": valid}
    proc = subprocess.run(
        ["node", str(HELPER)],
        input=json.dumps(payload),
        text=True,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
    )
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

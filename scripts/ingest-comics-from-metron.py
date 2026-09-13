#!/usr/bin/env python3
"""Metron catalog ingest — DISABLED BY DEFAULT.

Glyph owns the shared Metron daily cap (10 req/min, 2500/day) for keep-set UPC
enrich via scripts/backfill-comic-upcs-metron.py. Do NOT call metron.cloud unless
Glyph has released the cap AND you pass --force-metron.

Prefer:
  python3 scripts/ingest-comics-from-shopify.py
  python3 scripts/ingest-comics-from-comicvine.py
"""
from __future__ import annotations
import argparse, sys

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force-metron", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args, _ = ap.parse_known_args()
    if not args.force_metron:
        print("REFUSED: Metron ingest default-OFF (Glyph owns shared Metron daily cap). Use Shopify/Comic Vine ingest.", file=sys.stderr)
        return 2
    print("ERROR: --force-metron set but Metron new-row body not enabled (pivot to Shopify/CV).", file=sys.stderr)
    return 3

if __name__ == "__main__":
    raise SystemExit(main())

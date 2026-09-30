#!/usr/bin/env python3
"""Studio Series follow-up (2026-09-30): SS-114 Transformers One Megatron.

- ss5-ss-megatron-tlk carries code HAS265216 and an image named 195166265216 = Hasbro F9849,
  Studio Series Deluxe Transformers One 114 Megatron (TFWiki 2024 Deluxe Wave 26; UPC on
  Amazon, TF Robots, Toys"R"Us TW). Relabel: subtitle "SS-114 Transformers One", Deluxe,
  year-only 2024, sku 195166265216, msrp 27.99 (list price at toysf.com / Third Eye Comics,
  = Hasbro Deluxe MSRP). Old sku HAS265216 and item codes F9849 / HASF9849 kept as aliases.
- Move id:ss6-ss-megatron-tfone and TFSS-TF1-D-MEGATRON from tfss-ss-one-megatron (now the
  MTMTE WFC Voyager Megatron) onto it.
- tfss-ssge04-megatron: remove the wrong code HASF9849 (row sku + baked sku map); row
  otherwise unchanged.

  python3 scripts/studio-series-tfone-megatron.py          # dry run
  python3 scripts/studio-series-tfone-megatron.py --apply
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKUMAP = ROOT / "src/data/figure-sku-map.json"
TID, GE = "ss5-ss-megatron-tlk", "tfss-ssge04-megatron"
OLD = {"subtitle": "The Last Knight", "scale": "6\"", "releaseDate": "2026-01-01", "msrp": 24.99, "sku": "HAS265216"}
NEW = {"subtitle": "SS-114 Transformers One", "scale": "Deluxe", "releaseDate": "2024", "msrp": 27.99, "sku": "195166265216"}
MOVE = ["id:ss6-ss-megatron-tfone", "TFSS-TF1-D-MEGATRON"]
FROM = "tfss-ss-one-megatron"
ADD_ALIASES = ["HAS265216", "F9849", "HASF9849"]


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args = ap.parse_args()
    rows = json.loads(ONESHOT.read_text()); al = json.loads(ALIASES.read_text()); sm = json.loads(SKUMAP.read_text())
    by = {r["id"]: r for r in rows}; to_fig, by_fig = al["aliasToFigureId"], al["aliasesByFigureId"]
    before = (len(rows), sum(1 for v in to_fig.values() if v not in by))
    p = []
    t, g = by.get(TID), by.get(GE)
    if not t or any(t.get(k) != v for k, v in OLD.items()): p.append(f"{TID} not in expected state")
    if not g or g.get("sku") != "HASF9849": p.append(f"{GE} sku not HASF9849")
    for a in MOVE:
        if to_fig.get(a) != FROM: p.append(f"{a} not on {FROM}")
    for a in ADD_ALIASES + [NEW["sku"]]:
        if a in to_fig: p.append(f"{a} already aliased to {to_fig[a]}")
    if any(r.get("sku") == NEW["sku"] for r in rows): p.append("UPC already on a row")
    if p: print(json.dumps({"problems": p}, indent=2)); raise SystemExit(1)

    t.update(NEW)
    for tag in ["fix:ss-relabel", "sku-gtin"]:
        if tag not in t["tags"]: t["tags"].append(tag)
    del g["sku"]
    if sm.get(GE) == "HASF9849": del sm[GE]
    if TID in sm: sm[TID] = NEW["sku"]
    lst = by_fig.setdefault(TID, [])
    for a in MOVE:
        by_fig[FROM] = [x for x in by_fig[FROM] if x != a]; lst.append(a); to_fig[a] = TID
    for a in ADD_ALIASES:
        lst.append(a); to_fig[a] = TID
    al.setdefault("collapsed", []).append({
        "keepId": TID, "dropId": None, "canonicalSku": NEW["sku"], "aliasesAdded": MOVE + ADD_ALIASES,
        "reason": "Studio Series TF One follow-up 2026-09-30: ss5-ss-megatron-tlk relabelled SS-114 Transformers One "
                  "Megatron (F9849, UPC 195166265216); TF One Megatron aliases moved from tfss-ss-one-megatron; "
                  "wrong code HASF9849 removed from tfss-ssge04-megatron. Sources: https://tfwiki.net/wiki/Studio_Series; "
                  "https://www.amazon.com/dp/B0CSH7FD61"})
    ids = [r["id"] for r in rows]
    rep = {"dryRun": not args.apply, "rows": len(rows), "duplicateIds": len(ids) - len(set(ids)),
           "danglingAliasesBefore": before[1], "danglingAliasesAfter": sum(1 for v in to_fig.values() if v not in set(ids)),
           "danglingSetIds": sum(1 for r in rows if r.get("setId") and r["setId"] not in set(ids)),
           "relabelled": {k: t[k] for k in ("id", "name", "subtitle", "scale", "releaseDate", "msrp", "sku")},
           "aliasesOnTarget": by_fig[TID], "ge04Sku": g.get("sku"), "ge04BakedSku": sm.get(GE)}
    print(json.dumps(rep, indent=2))
    if rep["duplicateIds"] or rep["danglingAliasesAfter"] > before[1] or rep["danglingSetIds"]: raise SystemExit("integrity regression")
    if args.apply:
        ONESHOT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        ALIASES.write_text(json.dumps(al, indent=2, ensure_ascii=False) + "\n")
        SKUMAP.write_text(json.dumps(sm, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

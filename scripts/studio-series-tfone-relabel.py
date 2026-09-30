#!/usr/bin/env python3
"""Studio Series follow-up (2026-09-30): relabel the two rows that carry the MTMTE War for
Cybertron Voyager EANs/images, and add the real Transformers One 112 Optimus Prime.

- tfss-ss-one-optimus: EAN 5010996346179 + image = G1789 MTMTE WFC Voyager Optimus Prime (2025,
  Target). TFWiki: 2025 Exclusives, MTMTE Collection Voyager Class (unnumbered; 2025 packaging
  dropped ID numbers). actionfigure411: retail $34.99.
- tfss-ss-one-megatron: EAN 5010996346049 + image = G1790 MTMTE WFC Voyager Megatron. Same.
  Ids, sku and image are kept.
- New tfss-ss112-optimus-prime: TFWiki 2024 Deluxe Wave 24 "112 Optimus Prime (One)";
  Hasbro item G0221, MSRP $27.99 (shop.hasbro.com); EAN 5010996232328 (Midtown Comics,
  Kokochao, King Soopers); image = cmdstore "Optimus Prime #112" listing.
  TF One-specific aliases move to it: id:ss6-ss-optimus-tfone (the TF One row wrongly merged
  into tfss-ss-one-optimus; its sku was G02215L00 = G0221), TFSS-TF1-D-OPTIMUSPRIME, and G0221
  (was on tfss-ss86-optimus-cmd; G0221 is the TF One 112 Optimus per shop.hasbro.com).
- 114 Megatron (One) is NOT added: unsure row ss5-ss-megatron-tlk already carries its code
  (HAS265216) and an image named 195166265216 (= F9849 TF One 114 Megatron).

  python3 scripts/studio-series-tfone-relabel.py          # dry run
  python3 scripts/studio-series-tfone-relabel.py --apply
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
TFW = "https://tfwiki.net/wiki/Studio_Series"

RELABEL = {
    "tfss-ss-one-optimus": {
        "old": {"subtitle": "SS-112 Transformers One", "scale": "Deluxe", "releaseDate": "2024-09-01", "msrp": 24.99},
        "new": {"subtitle": "WFC Voyager 2025 (MTMTE Collection)", "scale": "Voyager", "releaseDate": "2025", "msrp": 34.99,
                "exclusive": "Target"},
    },
    "tfss-ss-one-megatron": {
        "old": {"subtitle": "SS-114 Transformers One", "scale": "Deluxe", "releaseDate": "2024-09-01", "msrp": 24.99},
        "new": {"subtitle": "WFC Voyager 2025 (MTMTE Collection)", "scale": "Voyager", "releaseDate": "2025", "msrp": 34.99,
                "exclusive": "Target"},
    },
}
EXPECT_SKU = {"tfss-ss-one-optimus": "5010996346179", "tfss-ss-one-megatron": "5010996346049"}
RELABEL_TAGS = ["mtmte-collection", "exclusive", "date-precision:year", "fix:ss-relabel"]

NEW_ROW = {
    "id": "tfss-ss112-optimus-prime", "name": "Optimus Prime", "subtitle": "SS-112 Transformers One",
    "line": "Transformers Studio Series", "company": "hasbro", "kind": "figure", "releaseDate": "2024",
    "msrp": 27.99, "scale": "Deluxe", "demand": 1.0,
    "tags": ["transformers", "studio-series", "tfwiki", "ss-audit-add", "date-precision:year", "sku-gtin",
             "image-sku", "imgsku:cmdstore"],
    "source": "tfwiki-studio-series",
    "imageUrl": "https://cdn.shopify.com/s/files/1/0432/8397/2262/files/transformers-studio-series-deluxe-class-level-optimus-prime-112-5010996247544-pkg.jpg?v=1720818267",
    "sku": "5010996232328",
}
MOVE = [("id:ss6-ss-optimus-tfone", "tfss-ss-one-optimus"), ("TFSS-TF1-D-OPTIMUSPRIME", "tfss-ss-one-optimus"),
        ("G0221", "tfss-ss86-optimus-cmd")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rows = json.loads(ONESHOT.read_text())
    al = json.loads(ALIASES.read_text())
    by_id = {r["id"]: r for r in rows}
    to_fig, by_fig = al["aliasToFigureId"], al["aliasesByFigureId"]
    problems = []
    before = (len(rows), sum(1 for v in to_fig.values() if v not in by_id))

    for rid, ch in RELABEL.items():
        r = by_id.get(rid)
        if not r:
            problems.append(f"{rid} missing"); continue
        if r.get("sku") != EXPECT_SKU[rid]:
            problems.append(f"{rid} sku changed: {r.get('sku')}")
        bad = {k: r.get(k) for k, v in ch["old"].items() if r.get(k) != v}
        if bad:
            problems.append(f"{rid} differs from expected: {bad}")
    n = NEW_ROW
    used = set(by_id) | set(by_fig) | {k[3:] for k in to_fig if k.startswith("id:")}
    if n["id"] in used:
        problems.append("new id collides")
    if any((r.get("sku") or "") == n["sku"] for r in rows) or n["sku"] in to_fig:
        problems.append("new sku already in catalog")
    for a, frm in MOVE:
        if to_fig.get(a) != frm:
            problems.append(f"alias {a} not on {frm} (on {to_fig.get(a)})")
    if problems:
        print(json.dumps({"problems": problems}, indent=2)); raise SystemExit(1)

    for rid, ch in RELABEL.items():
        r = by_id[rid]
        r.update(ch["new"])
        for t in RELABEL_TAGS:
            if t not in r["tags"]:
                r["tags"].append(t)
    key = f"{n['name']}|{n['subtitle']}|{n['line']}|{n['company']}".lower()
    if any(f"{r['name']}|{r['subtitle']}|{r['line']}|{r['company']}".lower() == key for r in rows):
        raise SystemExit("name|subtitle key collision")
    rows.append(n)
    moved = []
    for a, frm in MOVE:
        by_fig[frm] = [x for x in by_fig.get(frm, []) if x != a]
        by_fig.setdefault(n["id"], []).append(a)
        to_fig[a] = n["id"]
        moved.append({"alias": a, "from": frm, "to": n["id"]})
    al.setdefault("collapsed", []).append({
        "keepId": n["id"], "dropId": None, "canonicalSku": n["sku"], "aliasesAdded": [a for a, _ in MOVE],
        "reason": "Studio Series TF One follow-up 2026-09-30: tfss-ss-one-optimus relabelled as MTMTE WFC Voyager "
                  "Optimus Prime (its EAN/image); TF One 112 Optimus Prime aliases moved to new row. Sources: "
                  f"{TFW}; https://shop.hasbro.com/en-us/product/transformers-studio-series-deluxe-transformers-one-112-optimus-prime-4-5-action-figure-8-plus/G0221"})
    ids = [r["id"] for r in rows]
    after = (len(rows), sum(1 for v in to_fig.values() if v not in set(ids)))
    rep = {"dryRun": not args.apply, "rowsBefore": before[0], "rowsAfter": after[0],
           "danglingAliasesBefore": before[1], "danglingAliasesAfter": after[1],
           "duplicateIds": len(ids) - len(set(ids)),
           "danglingSetIds": sum(1 for r in rows if r.get("setId") and r["setId"] not in set(ids)),
           "relabelled": list(RELABEL), "added": [n["id"]], "aliasesMoved": moved}
    print(json.dumps(rep, indent=2))
    if rep["duplicateIds"] or after[1] > before[1] or rep["danglingSetIds"]:
        raise SystemExit("integrity regression; nothing written")
    if args.apply:
        ONESHOT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        ALIASES.write_text(json.dumps(al, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Oct 20 QC fixes (Shelby approved 2026-10-20): Captain Carrot UPC move + DC Multiverse w24 vehicle fixes.

Review: vera-qc-notes/oct20-carrot-w24-review.csv
  1. Captain Carrot 787926170146: Vault W2 row -> CE #08 row (2023); blocked on the Vault row.
     787926182163 (Vault W2, AF411-only) NOT applied. Gold Label GITD (AF411 10238) skipped: CSV marks it
     "optional, not part of this fix" (AF411-only, medium).
  2. Rename 5 mislabeled rows to the vehicle/playset they actually carry.
  3. Strip vehicle UPC (+ same-source baked photo) from 6 real-figure rows, block re-attach, add vehicle rows.
  4. Add 8 missing McFarlane DC Multiverse vehicle/set rows.
"""
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKUMAP = ROOT / "src/data/figure-sku-map.json"
IMGS = ROOT / "src/data/figure-image-urls.json"
STATS = ROOT / "src/data/figure-archive/qc-oct20-carrot-w24-stats.json"
TAG = "Shelby 2026-10-20 QC carrot/w24 fixes"
FIX = "fix:qc-oct20"
SOURCE = "curated-qc-oct20"
SKU_TAG = re.compile(r"^(sku-bake|sku-gtin|sku-alias|sku:.+|alias:.+)$")
IMG_TAG = re.compile(r"^(image-bake|image-sku|imgsku:.+|img:.+)$")

VAULT = "mcf-vault-w20-captain-carrot-vault-collection-justice-league-incarnate-13946"
CE08 = "mcf-mce-w19-captain-carrot-justice-league-incarnate-ce-08-captain-carrot"

RENAME = {  # id: (name, subtitle, kind, year, msrp, af411)
    "mf10-mf-04": ("Batwing (Gold Label - The Flash Movie)", "Vehicles & Playsets McFarlane Store Exclusive", "vehicle", 2023, 249.99, "6182"),
    "mf10-mf-07": ("The Joker Interrogation Room (Gold Label - The Dark Knight)", "Vehicles & Playsets", "playset", 2023, 39.99, "7189"),
    "mcf3-mcf-redhood-outlaw": ("Red Hood's Sportsbike (Outlaw)", "Vehicles & Playsets", "vehicle", 2024, 29.99, "12486"),
    "mf8-mf-09": ("Batmissile (Batman Returns)", "Vehicles & Playsets", "vehicle", 2026, 99.99, "13604"),
    "mcfc-lobo": ("Spacehog (Supergirl Movie)", "Vehicles & Playsets", "vehicle", 2026, 49.99, "13377"),
}
# strip from: (new name, subtitle, kind, year, msrp, af411, expected upc, carry image?, why)
STRIP_ADD = {
    "mcfdc-batman-red-death": ("Batcycle (Dark Nights: Death Metal)", "Vehicles & Playsets", "vehicle", 2021, 19.99, "3041", "787926157055", True,
                               "barcode + cmdstore photo are the Death Metal Batcycle vehicle, not The Red Death figure"),
    "mcf6-mcf-batman-who": ("Batman & Bat-Raptor (Gold Label)", "Vehicles & Playsets GameStop Exclusive", "vehicle", 2023, 49.99, "7161", "787926150674", False,
                            "Mephitsu barcode + unverified wix photo are Batman & Bat-Raptor (Gold Label), not Batman Who Laughs"),
    "mcf-dc-super-pow-the-batmobile-vehicle": ("Batmobile (The Flash Movie)", "Vehicles & Playsets", "vehicle", 2023, 79.99, "6186", "787926155297", False,
                            "Mephitsu barcode + wix photo are the 7in Flash Movie Batmobile, not the 4.5in Super Powers Batmobile"),
    "mcf6-mcf-aquaman-plat": ("Storm (The Lost Kingdom)", "Vehicles & Playsets", "vehicle", 2023, 29.99, "7393", "787926155495", True,
                              "barcode + cmdstore photo are Storm (Aquaman and the Lost Kingdom), not the Aquaman Platinum chase"),
    "mcf-w2-alfred-pennyworth-batman-v-superman": ("Batmobile & Alfred Pennyworth (Gold Label - Batman Forever)", "Vehicles & Playsets", "vehicle", 2024, 99.99, "8997", "787926150193", False,
                            "Mephitsu barcode + wix photo are the Batman Forever Batmobile & Alfred set, not the BvS Alfred figure"),
    "mcf3-mcf-flash-movie": ("Batcycle with Batman (The Flash)", "Vehicles & Playsets Walmart Exclusive", "vehicle", 2025, 69.99, "12145", "787926174779", True,
                             "barcode + cmdstore photo are the Walmart Batcycle with Batman, not The Flash movie figure"),
}
# new: (name, subtitle, kind, year, msrp, af411, upc|None, move-from id|None, carry image?)
NEW = [
    ("Batman & Batmobile (Gold Label - Batman 1989)", "Vehicles & Playsets Amazon Exclusive", "vehicle", 2023, 74.99, "6857", "787926170917",
     "afmon-mcfarlane-batman-dc-multiverse-collector-edition-the-joker-action-figure-bbts-183610", False),
    ("Lucius Fox & Tumbler (Gold Label - The Dark Knight)", "Vehicles & Playsets", "vehicle", 2024, 99.99, "8576", "787926151930", None, False),
    ("Camouflage Tumbler (Gold Label - The Dark Knight Rises)", "Vehicles & Playsets Amazon Exclusive", "vehicle", 2024, 69.99, "8577", None, None, False),
    ("Catwoman and Batpod (Gold Label - The Dark Knight Rises)", "Vehicles & Playsets McFarlane Store Exclusive", "vehicle", 2024, 69.99, "7941", "787926157345",
     "mcf4-multiverse-catwoman-classic", True),
    ("Batman and Batpod (Gold Label - The Dark Knight Rises)", "Vehicles & Playsets Target Exclusive", "vehicle", 2025, 69.99, "12464", "787926176292",
     "mcf6-mcf-batman-gold", True),
    ("Batmobile (Classic TV Series)", "Vehicles & Playsets", "vehicle", 2025, 79.99, "12482", "787926176728", None, False),
    ("Batmobile (Gold Label - The Batman - Muscle Car)", "Vehicles & Playsets", "vehicle", 2025, 79.99, "11653", "787926174847", None, False),
    ("The Joker (Joker Movie) Limited Edition Deluxe Collector Set", "Limited Edition Deluxe Collector Set", "figure", 2025, 249.99, "9047", "787926173338", None, False),
]


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and"))).strip("-")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args = ap.parse_args()
    now = datetime.now(timezone.utc).isoformat()
    rows = json.loads(ONESHOT.read_text()); aliases = json.loads(ALIASES.read_text())
    skumap = json.loads(SKUMAP.read_text()); imgs = json.loads(IMGS.read_text())
    by = {r["id"]: r for r in rows}
    problems = []
    log = {"stripped": [], "renamed": [], "added": [], "updated": [], "skipped": [
        {"upc": "787926182163", "why": "Vault W2 candidate UPC unverified (AF411 only); not applied"},
        {"upc": "787926175998", "why": "Captain Carrot Gold Label GITD (AF411 10238): CSV marks it optional / not part of this fix, AF411-only medium; row not added"},
        {"upc": "787926172966", "why": "Camouflage Tumbler UPC unverified (UPCitemdb only); row added without sku"},
        {"id": "mf10-mf-07", "why": "UPC 787926153996 left as-is (store image filename says ...3993)"}]}

    def ensure(r, t):
        if t not in r["tags"]: r["tags"].append(t)

    def strip(fid, code, clear_img, why):
        r = by[fid]
        if r.get("sku") != code:
            problems.append(f"{fid}: sku {r.get('sku')!r} != {code}"); return None
        img = r.get("imageUrl") if clear_img else None
        r.pop("sku", None); skumap.pop(fid, None)
        r["tags"] = [t for t in r["tags"] if not SKU_TAG.match(t)]
        if img:
            r["imageUrl"] = None; imgs.pop(fid, None)
            r["tags"] = [t for t in r["tags"] if not IMG_TAG.match(t)]
        ensure(r, FIX)
        for c, o in list(aliases["aliasToFigureId"].items()):
            if o == fid and c == code: del aliases["aliasToFigureId"][c]
        aliases["strippedCodes"].append({"figureId": fid, "codes": [code], "imageDropped": bool(img),
                                         "imageUrls": [img] if img else [], "reason": f"{TAG}: {why}"})
        log["stripped"].append({"id": fid, "code": code, "imageCleared": img})
        return img

    def holders(code):
        return [r["id"] for r in rows if r.get("sku") == code] + \
               [k for k, v in skumap.items() if v == code] + \
               ([aliases["aliasToFigureId"][code]] if code in aliases["aliasToFigureId"] else [])

    def add(name, subtitle, kind, year, msrp, af, upc, img):
        nid = f"mcf-veh-qc1020-{slug(name)}-{af}"
        if nid in by: problems.append(f"dup id {nid}"); return
        if upc and holders(upc): problems.append(f"{upc} still held by {holders(upc)}"); return
        tags = ["dc", "af-checklist", "mcfarlane", "dc-multiverse", "date-precision:year", f"af411:{af}", FIX]
        if kind in ("vehicle", "playset"): tags[3:3] = ["vehicle", "vehicles-and-playsets"]
        if "Gold Label" in name: tags.append("gold-label")
        r = {"id": nid, "name": name, "subtitle": subtitle, "line": "DC Multiverse", "company": "mcfarlane", "kind": kind,
             "releaseDate": f"{year}-01-01", "msrp": msrp, "scale": "7\"", "demand": 1.2, "tags": tags, "source": SOURCE}
        if upc:
            r["sku"] = upc; tags.append("sku:af411"); skumap[nid] = upc
        if img:
            r["imageUrl"] = img; tags += ["image-sku", "imgsku:cmdstore"]; imgs[nid] = img
        rows.append(r); by[nid] = r
        log["added"].append({"id": nid, "name": name, "sku": upc, "imageUrl": img})

    # 1. Carrot
    strip(VAULT, "787926170146", False, "UPC 787926170146 is Captain Carrot (JLI) McFarlane Collector Edition #08 2023 (AF411 7521, UPCitemdb, cmdstore), "
          "not the 2026 Vault Collection Wave 2 (AF411 13946); Mephitsu bake 2026-10-19 re-attached the Oct 14 reject")
    ce = by[CE08]
    if ce.get("sku") or holders("787926170146"): problems.append("CE08 already has sku / 170146 still held")
    ce["sku"] = "787926170146"; skumap[CE08] = "787926170146"; ce["releaseDate"] = "2023-01-01"
    for t in ("sku:af411", "date-precision:year", FIX): ensure(ce, t)
    log["updated"].append({"id": CE08, "sku": "787926170146", "releaseDate": "2023-01-01"})

    # 2. renames
    for fid, (name, sub, kind, year, msrp, af) in RENAME.items():
        r = by[fid]; before = {k: r.get(k) for k in ("name", "subtitle", "line", "kind", "releaseDate", "msrp")}
        r.update(name=name, subtitle=sub, line="DC Multiverse", kind=kind, releaseDate=f"{year}-01-01", msrp=msrp)
        r["tags"] = [t for t in r["tags"] if t not in ("date-unverified", "spawn")]
        for t in ("vehicle", "vehicles-and-playsets", "date-precision:year", f"af411:{af}", FIX): ensure(r, t)
        log["renamed"].append({"id": fid, "before": before, "after": {k: r.get(k) for k in before}, "skuKept": r.get("sku")})

    # 3. strip + add
    for fid, (name, sub, kind, year, msrp, af, code, carry, why) in STRIP_ADD.items():
        img = strip(fid, code, True, why)
        add(name, sub, kind, year, msrp, af, code, img if carry else None)

    # 4. new rows
    for name, sub, kind, year, msrp, af, upc, src, carry in NEW:
        img = None
        if src:
            img = strip(src, upc, carry, f"barcode{' + cmdstore photo' if carry else ''} {upc} is {name} (AF411 {af}), not this row")
        add(name, sub, kind, year, msrp, af, upc, img)

    # integrity
    ids = [r["id"] for r in rows]
    from collections import Counter
    dup_sku = {k: v for k, v in Counter(r["sku"] for r in rows if r.get("sku")).items() if v > 1}
    mine = {r.get("sku") for r in rows if FIX in r.get("tags", [])} - {None}
    stats = {"at": now, "dryRun": not args.apply, "rowsBefore": len(rows) - len(log["added"]), "rowsAfter": len(rows),
             "dupIds": len(ids) - len(set(ids)), "dupSkusTouched": {k: v for k, v in dup_sku.items() if k in mine},
             "dupSkusTotal": len(dup_sku), "problems": problems, **log}
    print(json.dumps({k: v for k, v in stats.items() if k not in log}, indent=1))
    if problems or stats["dupIds"] or stats["dupSkusTouched"]:
        print("NOT WRITTEN"); sys.exit(1)
    if args.apply:
        aliases["updatedAt"] = now
        aliases["stats"]["qcOct20CarrotW24"] = {"at": now, "added": len(log["added"]), "renamed": len(log["renamed"]), "stripped": len(log["stripped"])}
        dump = lambda o: json.dumps(o, indent=2, ensure_ascii=False) + "\n"
        ONESHOT.write_text(dump(rows)); ALIASES.write_text(dump(aliases))
        SKUMAP.write_text(dump(skumap)); IMGS.write_text(dump(imgs)); STATS.write_text(dump(stats))
        print("WRITTEN")


if __name__ == "__main__":
    main()

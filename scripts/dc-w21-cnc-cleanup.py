#!/usr/bin/env python3
"""DC gap wave 21 CNC cleanup (Shelby approved 2026-10-17).

Review: vera-qc-notes/dc-w21-cnc-review.csv (51 DUPLICATE + 4 UNIQUE-MATTEL).
  1. Merge 51 mcf-cnc-w21-* duplicates into their mat-mmv-w4-* Mattel row
     (af411 tag + id:/af411:/verified 887961 UPC aliases; image only if keeper has none).
  2. Keep 4 unique rows as Mattel DC Multiverse Mattel 2016 (company/line/tags/subtitle/scale).
  3. Merge mf8-mf-04 (Joker DKR 887961385175) into mat-mmv-w4-the-joker-dark-knight-returns-2017.
  4. Strip Mattel 887961 barcodes (+ images from the same cmdstore record) off 8 McFarlane rows.
  5. Lex Luthor BvS subtitle -> Prison Jumpsuit.
  6. product-sku-index: cmdstore 887961 records labelled mcfarlane -> mattel.
  7. Drop deleted ids from figure-sku-map / figure-image-urls / aliases.
  python3 scripts/dc-w21-cnc-cleanup.py [--apply]
"""
from __future__ import annotations
import argparse, csv, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import data_shards  # noqa: E402

ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKUMAP = ROOT / "src/data/figure-sku-map.json"
IMGS = ROOT / "src/data/figure-image-urls.json"
SKUIDX = ROOT / "src/data/figure-archive/product-sku-index.json"
STATS = ROOT / "src/data/figure-archive/dc-w21-cnc-cleanup-stats.json"
CSV = Path("/workspace/vera-qc-notes/dc-w21-cnc-review.csv")
TAG = "Shelby 2026-10-17 DC wave 21 CNC cleanup"
SKIP_UPC = {"617390971690"}
UNIQUE_SUBTITLE = {
    "mcf-cnc-w21-grapnel-blaster-cnc-3084": "Collect & Connect Grapnel Blaster",
    "mcf-cnc-w21-harley-quinn-gold-black-dress-suicide-squad-3179": "Collect & Connect Killer Croc Amazon Exclusive",
    "mcf-cnc-w21-harley-quinn-mallet-suicide-squad-3178": "Collect & Connect Killer Croc Toys R Us Exclusive",
    "mcf-cnc-w21-joker-silver-suit-suicide-squad-3180": "Collect & Connect Killer Croc Toys R Us Exclusive",
}
STRIP = {  # figureId -> (clear image?, reason)
    "mcfc-killer-croc": (False, "barcode is Mattel DC Multiverse Suicide Squad Katana (cmdstore #5 of 6); photo is the Mephitsu McFarlane Killer Croc listing (not the Mattel record) so kept"),
    "mcfc-robin-damian": (True, "barcode + photo are cmdstore 887961484069 'Robin Damian Wayne ... Court Of Owls Series' (Mattel GTIN, King Shark-wave TRU Robin), not McFarlane 2022"),
    "mcfdc-flash-season-7": (True, "barcode + photo are Mattel DC Multiverse The Flash CW Earth-2 Flash (cmdstore #1 of 6), not McFarlane Flash Season 7"),
    "d14mcf-batman-inj": (True, "barcode + photo are Mattel DC Multiverse Game Series Injustice 2 Batman (cmdstore), not McFarlane"),
    "d14mcf-ww-blackest": (True, "barcode + photo are Mattel DC Multiverse Dr. Psycho Series Dark Knight Returns Wonder Woman (cmdstore), not McFarlane Blackest Night WW"),
    "d14mcf-ww-tas": (True, "barcode + photo are Mattel DC Multiverse Lex Luthor Series Wonder Woman (cmdstore), not McFarlane Animated WW"),
    "mf10-mf-36": (True, "barcode + photo are Mattel DC Multiverse Batman Ninja series BAF listing (cmdstore 'Baf'), not McFarlane Beast Boy"),
    "mcfdc-batman-arkham-city": (False, "barcode is Mattel DC Multiverse Lex Luthor Series Batman (cmdstore); row has no photo"),
}
SKU_TAG = re.compile(r"^(sku-bake|sku-gtin|sku:.+)$")
IMG_TAG = re.compile(r"^(image-bake|image-sku|imgsku:.+|img:.+)$")


def upc_ok(u: str) -> bool:
    if not re.fullmatch(r"\d{12}", u) or not u.startswith("887961"):
        return False
    s = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(u[:11]))
    return (10 - s % 10) % 10 == int(u[11])


def ensure_tag(r, t):
    if t not in r["tags"]:
        r["tags"].append(t)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args = ap.parse_args()
    now = datetime.now(timezone.utc).isoformat()
    rows = json.loads(ONESHOT.read_text()); aliases = json.loads(ALIASES.read_text())
    skumap = json.loads(SKUMAP.read_text()); imgs = json.loads(IMGS.read_text())
    by = {r["id"]: r for r in rows}
    by_fig = aliases["aliasesByFigureId"]; to_fig = aliases["aliasToFigureId"]
    review = list(csv.DictReader(CSV.open()))
    problems, log = [], {"merges": [], "unique": [], "stripped": [], "skuIndexRecords": [], "gtinAliases": [], "skippedUpc": []}
    drop = set()

    # 4 first so freed GTINs are not owned by McFarlane rows
    for fid, (clear_img, why) in STRIP.items():
        r = by[fid]; code = r.get("sku")
        if not code or not code.startswith("887961"):
            problems.append(f"{fid}: sku {code!r} not 887961"); continue
        img = r.get("imageUrl")
        r.pop("sku", None); skumap.pop(fid, None)
        r["tags"] = [t for t in r["tags"] if not SKU_TAG.match(t)]
        urls = []
        if clear_img and img:
            urls = [img]; r["imageUrl"] = None; imgs.pop(fid, None)
            r["tags"] = [t for t in r["tags"] if not IMG_TAG.match(t)]
        aliases["strippedCodes"].append({"figureId": fid, "codes": [code], "imageDropped": bool(urls),
                                         "imageUrls": urls, "reason": f"{TAG}: {why} (wrong company)"})
        log["stripped"].append({"id": fid, "code": code, "imageCleared": urls, "imageKept": None if urls else img})

    def add_alias(keep_id, code, added):
        owner = to_fig.get(code)
        if owner not in (None, keep_id):
            problems.append(f"alias {code} already -> {owner}"); return
        to_fig[code] = keep_id
        lst = by_fig.setdefault(keep_id, [])
        if code not in lst:
            lst.append(code); added.append(code)

    def merge(drop_id, keep_id, extra_codes, reason):
        d, k = by[drop_id], by[keep_id]
        if any(x.get("setId") == drop_id for x in rows):
            problems.append(f"{drop_id} is a set parent"); return
        added = []
        codes = list(by_fig.pop(drop_id, []) or [])
        codes += [c for c, o in to_fig.items() if o == drop_id and c not in codes]
        for c in codes + extra_codes + [f"id:{drop_id}"]:
            add_alias(keep_id, c, added)
        img = False
        if d.get("imageUrl") and not k.get("imageUrl") and not imgs.get(keep_id):
            k["imageUrl"] = d["imageUrl"]; img = True
            for t in d["tags"]:
                if IMG_TAG.match(t): ensure_tag(k, t)
        imgs.pop(drop_id, None); skumap.pop(drop_id, None)
        drop.add(drop_id)
        aliases["collapsed"].append({"keepId": keep_id, "dropId": drop_id, "canonicalSku": k.get("sku"),
                                     "aliasesAdded": added, "reason": f"{TAG}: {reason}"})
        aliases["removed"].append({"keepId": keep_id, "dropId": drop_id, "canonicalSku": k.get("sku"),
                                   "aliasesAdded": added, "aliasesMoved": {drop_id: added}, "aliasesDropped": [],
                                   "reason": f"{TAG}: {reason}"})
        log["merges"].append({"dropId": drop_id, "keepId": keep_id, "aliasesAdded": added, "imageCarried": d.get("imageUrl") if img else None})

    for rv in review:
        wid = rv["w21_id"]; w = by[wid]
        af = [t for t in w["tags"] if t.startswith("af411:")]
        if rv["aliases_to_carry"] and rv["aliases_to_carry"] not in af:
            problems.append(f"{wid}: csv alias {rv['aliases_to_carry']} not in tags {af}")
        if rv["verdict"] == "DUPLICATE":
            keep_id = rv["mattel_match_id"]; k = by[keep_id]
            if k["company"] != "mattel" or not keep_id.startswith("mat-mmv-w4-"):
                problems.append(f"{keep_id} not a mattel w4 row"); continue
            for t in af: ensure_tag(k, t)
            upcs = sorted(set(re.findall(r"UPC (\d{12,13})", rv["notes"])))
            extra = list(af)
            for u in upcs:
                if u in SKIP_UPC or not upc_ok(u):
                    log["skippedUpc"].append({"id": wid, "upc": u}); continue
                extra.append(u); log["gtinAliases"].append({"keepId": keep_id, "gtin": u})
            merge(wid, keep_id, extra, f"{rv['name']} (AF411 {', '.join(af)}) is the same Mattel DC Multiverse figure as {keep_id}; "
                  f"AF411 UPC(s) carried: {', '.join(u for u in upcs if u not in SKIP_UPC and upc_ok(u)) or 'none'}.")
        elif rv["verdict"] == "UNIQUE-MATTEL":
            before = {k2: w.get(k2) for k2 in ("company", "line", "subtitle", "releaseDate", "scale")}
            w["company"] = "mattel"; w["line"] = "DC Multiverse Mattel"; w["releaseDate"] = "2016-01-01"
            w["subtitle"] = UNIQUE_SUBTITLE[wid]; w["scale"] = "6in"
            w["tags"] = ["mattel" if t == "mcfarlane" else t for t in w["tags"]]
            ensure_tag(w, "dc-multiverse"); ensure_tag(w, "fix:dc-w21-cleanup")
            log["unique"].append({"id": wid, "before": before, "after": {k2: w.get(k2) for k2 in before}})
        else:
            problems.append(f"{wid}: verdict {rv['verdict']}")

    # 3. mf8-mf-04
    kj = "mat-mmv-w4-the-joker-dark-knight-returns-2017"
    m8 = by["mf8-mf-04"]
    merge("mf8-mf-04", kj, [m8["sku"]] if upc_ok(m8.get("sku") or "") else [],
          "mf8-mf-04 'Joker (The Dark Knight Returns)' (curated-bbts-wave8, mislabelled 'DC Multiverse Hush' + mcfarlane/spawn tags) is the same "
          "Mattel DKR Joker (cmdstore 'Dark Knight Returns Joker #6 of 6', 887961385175); sku moved as GTIN alias, cmdstore photo carried.")

    # 5. Lex subtitle
    lex = by["mat-mmv-w4-lex-luthor-bvs-battle-armor"]
    if lex["subtitle"] == "BvS Battle Armor":
        lex["subtitle"] = "BvS Prison Jumpsuit"; ensure_tag(lex, "fix:dc-w21-cleanup")
    else:
        problems.append(f"lex subtitle is {lex['subtitle']!r}")

    out = [r for r in rows if r["id"] not in drop]
    # 7. dangling references
    for c, o in list(to_fig.items()):
        if o in drop: problems.append(f"dangling alias {c}->{o}")
    for fid in drop:
        by_fig.pop(fid, None)

    # 6. sku index
    idx = data_shards.load_array(SKUIDX)
    for rec in idx:
        codes = [str(rec.get("barcode") or ""), str(rec.get("sku") or "")]
        if rec.get("company") == "mcfarlane" and any(c.lstrip("0").startswith("887961") for c in codes):
            if rec.get("shop") != "cmdstore":
                problems.append(f"non-cmdstore 887961/mcfarlane {rec['id']}"); continue
            rec["company"] = "mattel"; log["skuIndexRecords"].append({"id": rec["id"], "barcode": rec.get("barcode"), "name": rec.get("name")})

    ids = [r["id"] for r in out]
    idset = set(ids)
    integ = {"dupIds": len(ids) - len(idset),
             "danglingAliases": sum(1 for o in to_fig.values() if o not in idset) - sum(1 for o in json.loads(ALIASES.read_text())["aliasToFigureId"].values() if o not in by),
             "danglingSet": [r["id"] for r in out if r.get("setId") and r["setId"] not in idset]}
    stats = {"at": now, "dryRun": not args.apply, "rowsBefore": len(rows), "rowsAfter": len(out), "removed": len(drop),
             "gtinAliasesAdded": len(log["gtinAliases"]), "skuIndexFixed": len(log["skuIndexRecords"]),
             "integrity": integ, "problems": problems, **log}
    print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, list) or k == "problems"}, indent=1))
    if problems or integ["dupIds"] or integ["danglingAliases"] > 0 or integ["danglingSet"]:
        print("NOT WRITTEN"); sys.exit(1)
    if args.apply:
        aliases["updatedAt"] = now
        aliases["stats"]["dcW21CncCleanup"] = {"at": now, "merged": len(drop), "dropIds": sorted(drop),
                                                "gtinAliasesAdded": len(log["gtinAliases"]), "stripped": len(log["stripped"]),
                                                "skuIndexCompanyFixed": len(log["skuIndexRecords"])}
        dump = lambda o: json.dumps(o, indent=2, ensure_ascii=False) + "\n"
        ONESHOT.write_text(dump(out)); ALIASES.write_text(dump(aliases))
        SKUMAP.write_text(dump(skumap)); IMGS.write_text(dump(imgs)); STATS.write_text(dump(stats))
        data_shards.save_array(SKUIDX, idx)
        print("WRITTEN")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Queue a comic backlog batch from the offline GCD dump (mains only, US publishers).

Picks dump issues (variant_of_id empty, not deleted, key_date >= floor) whose
gcdIssueId is not in the catalog, for the given GCD publisher names and year
bands, then drops anything already in the catalog under another series label
(base-title + issue + publisher family, year-compatible) — the post-audit used
on batch-041/042. Rows need a USD price (US edition signal). ISBN-only items
without a barcode (likely collected editions) are skipped. DC/Marvel 1985-2000
is always excluded (Glyph/Meph lanes).

  python3 scripts/gen-batch-gcd-gap.py --batch-id batch-045-x --title "..." \
      --pub "Marvel=Marvel Comics" --pub "DC=DC Comics" --min-year 2001 --cap-series 30
"""
from __future__ import annotations
import argparse, collections, glob, json, re, sqlite3, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "src/data/comic-backlog"
YR = re.compile(r"\s*\((\d{4})\)\s*$")
PALETTE = {"DC Comics": "1e3a8a,e30613,f8fafc", "Marvel Comics": "dc2626,1e3a8a,f8fafc",
           "Image Comics": "111827,7f1d1d,eab308", "Dark Horse": "dc2626,111827,eab308",
           "IDW Publishing": "166534,1e3a8a,dc2626", "Image": "111827,7f1d1d,eab308",
           "IDW": "166534,1e3a8a,dc2626"}
PREFIX = {"DC Comics": "dc", "Marvel Comics": "mv", "Image Comics": "im", "Dark Horse": "dh",
          "IDW Publishing": "idw", "Image": "im", "IDW": "idw", "Viz": "viz",
          "Antarctic Press": "anta", "Eclipse": "ecl", "Kitchen Sink Press": "ksp"}

def base(s):
    s = YR.sub("", s).strip().lower()
    return s[4:] if s.startswith("the ") else s

def fam(p):
    p = p.lower()
    for k, v in (("dc", "dc"), ("marvel", "mv"), ("image", "im"), ("idw", "idw"), ("dark horse", "dh")):
        if p.startswith(k) or f" {k}" in p:
            return v
    return p

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def usd(price):
    m = re.search(r"(\d+(?:\.\d+)?)\s*USD", price or "")
    return float(m.group(1)) if m else None

def fix_date(d):
    if not d or not re.match(r"^\d{4}", d):
        return None
    y, m, dd = (d.split("-") + ["01", "01"])[:3]
    m = m if m and m != "00" else "01"
    dd = dd if dd and dd != "00" else "01"
    try:
        if not (1 <= int(m) <= 12 and 1 <= int(dd) <= 31):
            return None
    except ValueError:
        return None
    return f"{y}-{m}-{dd}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--focus", default="")
    ap.add_argument("--created", required=True)
    ap.add_argument("--pub", action="append", required=True, help="GCD publisher name=catalog publisher label")
    ap.add_argument("--min-year", type=int, default=1980)
    ap.add_argument("--max-year", type=int, default=2025)
    ap.add_argument("--cap-series", type=int, default=30)
    ap.add_argument("--cap-pub", type=int, default=500)
    ap.add_argument("--size", type=int, default=500)
    ap.add_argument("--max-price", type=float, default=9.99, help="skip pricier items (likely collected editions)")
    ap.add_argument("--exclude-gids", default="", help="comma list of other batch ids whose gcd ids to avoid")
    ap.add_argument("--skip-band", action="append", default=[],
                    help="GCDPUB:Y0:Y1 to skip, e.g. Image:1985:2000 (Glyph's WildStorm-from-Image lane)")
    ap.add_argument("--dump-sqlite", default="/workspace/gcd-dump/gcd.sqlite")
    a = ap.parse_args()
    pubmap = dict(p.split("=", 1) for p in a.pub)

    ids, gids, cat_key, gid_label = set(), set(), collections.defaultdict(list), {}
    for f in glob.glob(str(ROOT / "src/data/comics/shards/*.json")):
        for e in json.load(open(f)).get("entries", []):
            r = e["row"]; ids.add(r[0])
            ex = r[13] if len(r) > 13 and isinstance(r[13], dict) else {}
            cat_key[(base(r[1]), str(r[2]), fam(r[3]))].append((r[1], bool(ex.get("variant")), str(r[4])[:4]))
            if ex.get("gcdIssueId"):
                gids.add(str(ex["gcdIssueId"])); gid_label[str(ex["gcdIssueId"])] = r[1]
    for b in json.load(open(BACKLOG / "manifest.json")).get("queued", []):
        p = BACKLOG / f"{b}.json"
        if p.exists():
            for r in json.load(open(p))["rows"]:
                ids.add(r[0]); gids.add(str((r[13] if len(r) > 13 else {}).get("gcdIssueId", "")))
                cat_key[(base(r[1]), str(r[2]), fam(r[3]))].append((r[1], False, str(r[4])[:4]))

    db = sqlite3.connect(a.dump_sqlite)
    q = f"""select p.name, i.id, i.number, i.key_date, i.on_sale_date, i.price, i.barcode, i.valid_isbn,
            i.title, s.id, s.name, s.year_began
      from gcd_issue i join gcd_series s on s.id=i.series_id join gcd_publisher p on p.id=s.publisher_id
      where (i.variant_of_id is null or i.variant_of_id='') and coalesce(i.deleted,0) in (0,'0','')
        and coalesce(s.deleted,0) in (0,'0','') and p.name in ({','.join('?'*len(pubmap))})
        and i.key_date >= ? and i.key_date < ?"""
    cand = collections.defaultdict(list)
    for row in db.execute(q, (*pubmap, str(a.min_year), str(a.max_year + 1))):
        gp, iid, num, kd, osd, price, bc, isbn, title, sid, sname, syb = row
        if str(iid) in gids:
            continue
        y = int(kd[:4])
        if gp in ("DC", "Marvel") and 1985 <= y <= 2000:
            continue
        if any(gp == sb.split(":")[0] and int(sb.split(":")[1]) <= y <= int(sb.split(":")[2]) for sb in a.skip_band):
            continue
        num = (num or "").strip()
        if not num or usd(price) is None or usd(price) > a.max_price:
            continue
        if isbn and not (bc or "").strip():
            continue
        cand[sid].append(row)

    # series labels already used by the catalog for each GCD series
    series_labels = collections.defaultdict(collections.Counter)
    for sid in cand:
        for (iid,) in db.execute("select id from gcd_issue where series_id=?", (sid,)):
            lab = gid_label.get(str(iid))
            if lab:
                series_labels[sid][lab] += 1

    stats = collections.Counter(); rows = []; seen = set(); per_pub = collections.Counter()
    order = sorted(cand, key=lambda s: -len(cand[s]))
    for sid in order:
        taken = 0
        for gp, iid, num, kd, osd, price, bc, isbn, title, _sid, sname, syb in sorted(cand[sid], key=lambda r: r[3]):
            pub = pubmap[gp]
            if taken >= a.cap_series or per_pub[pub] >= a.cap_pub or len(rows) >= a.size:
                break
            date = fix_date(kd)
            if not date:
                stats["bad-date"] += 1; continue
            y = int(date[:4])
            lab = series_labels[sid].most_common(1)[0][0] if series_labels[sid] else sname
            f = fam(pub)
            hits = cat_key.get((base(sname), num, f), []) + cat_key.get((base(lab), num, f), [])
            def compat(l):
                m = YR.search(l)
                return (not m) or abs(int(m.group(1)) - (syb or y)) <= 1 or l == lab
            def near(cy):
                return cy.isdigit() and abs(int(cy) - y) <= 1
            # dup if a main exists under a compatible label, or any row of the same title+issue
            # carries a cover date within a year (catches mislabeled volumes in the catalog)
            if any(compat(l) for l, v, cy in hits if not v) or any(near(cy) for l, v, cy in hits):
                stats["drop-dup"] += 1; continue
            if not series_labels[sid] and any(not v for l, v, cy in hits):
                # same base title exists under a different volume label: disambiguate by volume year
                lab = f"{sname} ({syb})"
                if any(l == lab for l, v, cy in hits):
                    stats["drop-dup"] += 1; continue
            m = YR.search(lab)
            if m and int(m.group(1)) > y + 1:
                stats["drop-badlabel"] += 1; continue
            k = (base(lab), num, f)
            if k in seen:
                stats["drop-intra"] += 1; continue
            rid = f"{PREFIX.get(pub, slug(pub)[:4])}-{slug(sname)[:40]}-{syb}-{slug(num) or 'nn'}"
            if rid in ids:
                rid = f"{rid}-g{iid}"
            if rid in ids:
                stats["drop-id"] += 1; continue
            extra = {}
            digits = re.sub(r"\D", "", bc or "")
            if len(digits) >= 12:
                extra["upc"] = digits
            sd = fix_date(osd) if osd and len(osd) >= 10 else None
            if sd:
                extra["streetDate"] = sd
            extra["gcdIssueId"] = str(iid)
            desc = (title or "").strip() or f"{YR.sub('', lab)} #{num}"
            rows.append([rid, lab, num, pub, date, "", "", desc, usd(price), "single",
                         0.8 if num == "1" else 0.55, 0, PALETTE.get(pub, "111827,e5e7eb,f8fafc"), extra])
            seen.add(k); ids.add(rid); per_pub[pub] += 1; taken += 1
    rows.sort(key=lambda r: (r[4], r[1]), reverse=True)
    batch = {"id": a.batch_id, "title": a.title, "created": a.created, "status": "queued",
             "focus": a.focus, "source": "gcd-dump", "addedCount": len(rows),
             "byPublisher": dict(collections.Counter(r[3] for r in rows).most_common()), "rows": rows}
    (BACKLOG / f"{a.batch_id}.json").write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n")
    man = json.load(open(BACKLOG / "manifest.json"))
    if a.batch_id not in man.get("queued", []):
        man.setdefault("queued", []).append(a.batch_id)
    (BACKLOG / "manifest.json").write_text(json.dumps(man, indent=2) + "\n")
    print(json.dumps({"count": len(rows), "stats": stats, "byPublisher": batch["byPublisher"],
                      "series": collections.Counter(r[1] for r in rows).most_common(25)}, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()

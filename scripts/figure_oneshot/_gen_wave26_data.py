"""Generate curated DC gap wave26 rows from non-Multiverse AF411 DC checklists.

Sections: Kenner Super Powers vehicles/playsets (1984), Hot Toys DC 1:6, Mondo BTAS
1:6 variants, McFarlane Batman: The Animated Series (2023-2026), McFarlane DC Direct
Digital Series (2024-2025). Picks hand-checked against the whole oneshot.json (every
company, name fuzzy + UPC) on 2026-10-21; cross-maker/same-maker fuzzy hits and UPC
collisions skipped (listed in _af411_dc_checklists_wave26.json "dropped").
No imageUrl. sku = AF411 UPC/EAN only when the check digit is valid and unused.
MSRP = AF411 retail only.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave26.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def gtin_ok(c):
    if not c or not c.isdigit() or len(c) not in (12, 13):
        return False
    d = [int(x) for x in c]
    body, chk = d[:-1], d[-1]
    s = sum(v * (3 if i % 2 == 0 else 1) for i, v in enumerate(reversed(body)))
    return (10 - s % 10) % 10 == chk

SEC = {
    "kenner-super-powers": dict(pre="ken-sp-w26", company="kenner", line="Super Powers", sub="Super Powers Vehicles & Playsets", scale='4.5"', kind="vehicle", tags=["kenner", "super-powers"]),
    "hot-toys": dict(pre="ht-w26", company="hottoys", line="Hot Toys", sub="Hot Toys DC", scale="1:6", kind="figure", tags=["hot-toys"]),
    "mondo": dict(pre="mo-w26", company="mondo", line="Mondo BTAS", sub="Batman: The Animated Series 1/6", scale="1:6", kind="figure", tags=["mondo", "btas"]),
    "batman-animated-series": dict(pre="mcf-btas-w26", company="mcfarlane", line="McFarlane Batman: The Animated Series", sub="Batman: The Animated Series", scale='6"', kind="figure", tags=["mcfarlane", "btas"]),
    "dc-direct-digital": dict(pre="mcf-dcdd-w26", company="mcfarlane", line="DC Direct Digital Series", sub="DC Direct Digital", scale='7"', kind="figure", tags=["mcfarlane", "dc-direct-digital"]),
}
RETAIL = {"Walmart": "Walmart", "Target": "Target"}
out = []
for a in snap["picked"]:
    s = SEC[a["page"]]
    name = a["name"].replace("\u2019", "'")
    wave = (a.get("wave") or "").strip()
    sub = s["sub"]
    if wave in RETAIL:
        sub += f" {RETAIL[wave]} Exclusive"
    elif wave.isdigit():
        sub += f" Wave {wave}"
    kind = "playset" if "Hall of Justice" in name or "Playset" in name else s["kind"]
    row = dict(id=f"{s['pre']}-{slug(name)[:60]}-{a['fid']}", name=name, subtitle=sub, line=s["line"],
               company=s["company"], kind=kind,
               releaseDate=f"{a['year']}-01-01", scale=s["scale"], demand=1.3,
               tags=["dc", "af-checklist", "wave26", *s["tags"], "date-precision:year", "af411:" + a["fid"]]
                    + (["vehicle"] if kind == "vehicle" else []) + (["playset"] if kind == "playset" else [])
                    + (["baf"] if "(BAF)" in name else []),
               source="curated-dc-gap-wave26")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    if a.get("upc") and gtin_ok(a["upc"]):
        row["sku"] = a["upc"]
        row["tags"].append("sku:af411")
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave26_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["company"], "|", o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"), o.get("sku"))

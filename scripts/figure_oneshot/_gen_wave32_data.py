"""Generate curated DC gap wave32 rows from AF411 McFarlane DC Multiverse checklist.

Sections: main-line single holes (2021-2026), Red Platinum GameStop, Collector Edition packs,
Clock King BAF, Darkseid vs Orion MegaFig multipack. Picks hand-checked against the whole
oneshot.json + figures.ts inline rows (every company: af411 id, name fuzzy incl. cross-maker
within ~2 years, UPC) on 2026-10-29; fuzzy hits and UPC collisions skipped (listed in
_af411_dc_checklists_wave32.json "dropped"). No imageUrl. sku = AF411 UPC only when the check
digit is valid and unused. MSRP = AF411 retail only. All 787926 UPCs / 2020+ -> McFarlane.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave32.json"))

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

out = []
for a in snap["picked"]:
    name = a["name"]
    wave = (a.get("wave") or "").strip()
    sec = a["section"]
    assert int(a["year"]) >= 2020 and not (a.get("upc") or "").startswith("887961")
    tags = ["dc", "af-checklist", "wave32", "mcfarlane"]
    excl = ""
    if wave and not wave.isdigit() and wave != "MegaFig":
        excl = f" {wave} Exclusive"
    if sec == "mcfarlane-collector-edition":
        sub = "McFarlane Collector Edition" + excl
        tags.append("collector-edition")
    elif sec == "clock-king-baf":
        sub = "Build-A Clock King" + excl
        tags.append("baf")
    elif sec == "multipacks":
        sub = ("MegaFig Multipack" if wave == "MegaFig" else "Multipack") + excl
        tags.append("multipack")
    elif sec == "gold-label":
        sub = "Gold Label" + excl
    else:
        sub = (f"Wave {wave}" if wave.isdigit() else ("MegaFig" if wave == "MegaFig" else "DC Multiverse")) + excl
    if "Gold Label" in name:
        tags.append("gold-label")
    if "Red Platinum" in name:
        tags.append("platinum")
    tags += ["date-precision:year", "af411:" + a["fid"]]
    row = dict(id=f"mcf-w32-{slug(name)[:60]}-{a['fid']}", name=name, subtitle=sub,
               line="DC Multiverse", company="mcfarlane", kind="figure",
               releaseDate=f"{a['year']}-01-01", scale='7"', demand=1.2, tags=tags,
               source="curated-dc-gap-wave32")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    if a.get("upc") and gtin_ok(a["upc"]) and not a.get("upc_collision"):
        row["sku"] = a["upc"]
        row["tags"].append("sku:af411")
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave32_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["company"], "|", o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"), o.get("sku"))

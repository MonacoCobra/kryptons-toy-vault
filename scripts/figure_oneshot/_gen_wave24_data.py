"""Generate curated DC gap wave24 rows from AF411 Multiverse Vehicles and Playsets.

McFarlane DC Multiverse vehicles/playsets 2020-2026 not yet in the catalog.
Picks hand-verified against the whole oneshot.json (every company, name fuzzy
+ UPC) on 2026-10-19. Source snapshot: _af411_dc_checklists_wave24.json.
No imageUrl. sku = AF411 UPC only when the UPC-A check digit is valid (and the
UPC is not on any existing row). MSRP = AF411 retail only.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave24.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

RETAIL = {"Walmart": "Walmart", "Target": "Target", "Amazon": "Amazon", "Gamestop": "GameStop",
          "McFarlane": "McFarlane Store", "Club": "McFarlane Toys Club"}
out = []
for a in snap["picked"]:
    name = a["name"].replace("\u2019", "'").replace("\u2018", "'").replace("  ", " ")
    wave = (a.get("wave") or "").strip()
    excl = f" {RETAIL[wave]} Exclusive" if wave in RETAIL else ""
    row = dict(
        id=f"mcf-veh-w24-{slug(name)[:60]}-{a['fid']}",
        name=name,
        subtitle=f"Vehicles & Playsets{excl}",
        line="DC Multiverse",
        company="mcfarlane",
        kind="vehicle",
        releaseDate=f"{a['year']}-01-01",
        scale='7"',
        demand=1.2,
        tags=["dc", "af-checklist", "wave24", "mcfarlane", "vehicle", "vehicles-and-playsets",
              "date-precision:year", "af411:" + a["fid"]] + (["gold-label"] if "Gold Label" in name else []),
        source="curated-dc-gap-wave24",
    )
    if a.get("retail") is not None:
        row["msrp"] = float(a["retail"])
    if a.get("upc") and a.get("upcValid"):
        row["sku"] = a["upc"]
        row["tags"].append("sku:af411")
    out.append(row)

ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave24_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"), o.get("sku"))

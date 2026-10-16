"""Generate curated DC gap wave23 rows from AF411 Multiverse CNC/BAF subsections.

Sections: remaining Mattel Collect & Connect 2017-2019 (Steppenwolf retailer
exclusives, Batman Ninja, Killer Croc 80th) + McFarlane Build-A holes Joker Bot
(Futures End), The Monitor (Crisis Gold Label), Starro (Crime Syndicate),
Darkest Knight (Speed Metal), Atrocitus (Blackest Night). Picks hand-verified
against oneshot.json on 2026-10-16. Source snapshot: _af411_dc_checklists_wave23.json.
No imageUrl / no GTINs. MSRP = AF411 retail only.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave23.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

RETAIL = {"Walmart": "Walmart", "Toys R Us": "Toys R Us", "Target": "Target", "Amazon": "Amazon"}
out = []
for a in snap["picked"]:
    name = a["name"].replace("\u2019", "'").replace("\u2018", "'").replace("  ", " ")
    baf = a["baf"]
    wave = (a.get("wave") or "").strip()
    excl = f" {RETAIL[wave]} Exclusive" if wave in RETAIL else ""
    if a["maker"] == "mattel":
        row = dict(
            id=f"mat-cnc-w23-{slug(name)[:60]}-{a['fid']}",
            name=name,
            subtitle=f"Collect & Connect {baf}{excl}",
            line="DC Multiverse Mattel",
            company="mattel",
            kind="figure",
            releaseDate=f"{a['year']}-01-01",
            scale='6"',
            demand=1.2,
            tags=["dc", "af-checklist", "wave23", "mattel", "cnc", "collect-and-connect",
                  "date-precision:year", "af411:" + a["fid"], "cnc:" + slug(baf)],
            source="curated-dc-gap-wave23",
        )
    else:
        row = dict(
            id=f"mcf-baf-w23-{slug(name)[:60]}-{a['fid']}",
            name=name,
            subtitle=f"Build-A {baf}{excl}",
            line="DC Multiverse",
            company="mcfarlane",
            kind="figure",
            releaseDate=f"{a['year']}-01-01",
            scale='7"',
            demand=1.3,
            tags=["dc", "af-checklist", "wave23", "mcfarlane", "baf", "build-a",
                  "date-precision:year", "af411:" + a["fid"], "baf:" + slug(baf)],
            source="curated-dc-gap-wave23",
        )
    if a.get("retail") is not None:
        row["msrp"] = float(a["retail"])
    out.append(row)

ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave23_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"))

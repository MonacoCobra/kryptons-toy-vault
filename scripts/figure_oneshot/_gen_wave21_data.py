"""Generate curated DC gap wave21 rows from AF411 Multiverse CNC subsections.

Sections: Justice Buster, New 52 Doomsday, Grapnel Blaster, Killer Croc (SS),
King Shark, Ares, Rookie (McFarlane DC Multiverse Collect-and-Connect 2016-2017).
Picks hand-verified against oneshot.json on 2026-10-14. Source snapshot:
_af411_dc_checklists_wave21.json. No imageUrl / no GTINs.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave21.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

EXCL = ("Walmart", "Target", "SDCC", "GameStop", "EE", "Amazon", "Club", "MegaFig",
        "Toys R Us", "ToysRUs")
out = []
for a in snap["picked"]:
    name = a["name"].replace("\u2019", "'").replace("\u2018", "'").replace("  ", " ")
    baf = a["baf"]
    wave = (a.get("wave") or "").strip()
    line = "DC Multiverse"
    sub = f"Collect-and-Connect {baf}"
    if wave in EXCL:
        sub = f"{sub} {wave} Exclusive"
    elif wave and wave not in ("1", "2", "3", "4", "5", "6", "7", "8"):
        # retailer / special wave labels already handled; numeric wave unused in subtitle
        pass
    retail = a.get("retail")
    # CNC assembly figures often have empty retail on AF411; leave null
    row = dict(
        id=f"mcf-cnc-w21-{slug(name)[:60]}-{a['fid']}",
        name=name,
        subtitle=sub,
        line=line,
        company="mcfarlane",
        kind="figure",
        releaseDate=f"{a['year']}-01-01",
        scale='7"',
        demand=1.3,
        tags=["dc", "af-checklist", "wave21", "mcfarlane", "cnc", "collect-and-connect",
              "date-precision:year", "af411:" + a["fid"], "cnc:" + slug(baf)],
        source="curated-dc-gap-wave21",
    )
    if retail is not None:
        row["msrp"] = float(retail)
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave21_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"))

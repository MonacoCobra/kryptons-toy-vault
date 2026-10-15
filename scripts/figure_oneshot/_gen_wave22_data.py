"""Generate curated DC gap wave22 rows from AF411 Multiverse BAF + MAFEX gaps.

Sections: Darkseid (JLTF), Plastic Man (JLA), Nightmare Bat (Forever holes),
plus 8 MAFEX DC checklist gaps. Picks hand-verified against oneshot.json on
2026-10-15. Source snapshot: _af411_dc_checklists_wave22.json.
No imageUrl / no GTINs.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave22.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

out = []
for a in snap["picked"]:
    name = a["name"].replace("\u2019", "'").replace("\u2018", "'").replace("  ", " ")
    baf = a["baf"]
    row = dict(
        id=f"mcf-baf-w22-{slug(name)[:60]}-{a['fid']}",
        name=name,
        subtitle=f"Build-A {baf}",
        line="DC Multiverse",
        company="mcfarlane",
        kind="figure",
        releaseDate=f"{a['year']}-01-01",
        scale='7"',
        demand=1.3,
        tags=["dc", "af-checklist", "wave22", "mcfarlane", "baf", "build-a",
              "date-precision:year", "af411:" + a["fid"], "baf:" + slug(baf)],
        source="curated-dc-gap-wave22",
    )
    if a.get("retail") is not None:
        row["msrp"] = float(a["retail"])
    out.append(row)

for m in snap.get("mafex", []):
    name = m["name"].replace("\u2019", "'")
    row = dict(
        id=f"mafex-w22-{slug(name)[:50]}-no{m['no']}",
        name=name,
        subtitle=m["sub"],
        line="MAFEX",
        company="mafex",
        kind="figure",
        releaseDate=f"{m['year']}-01-01",
        msrp=float(m["retail"]),
        scale='6"',
        demand=1.4,
        tags=["dc", "af-checklist", "wave22", "mafex", "date-precision:year",
              f"mafex-no:{m['no']}"],
        source="curated-dc-gap-wave22",
    )
    out.append(row)

ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave22_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"))

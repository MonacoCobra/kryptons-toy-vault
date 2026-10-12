"""Generate curated DC gap wave19 rows from the AF411 McFarlane Collector Edition checklist.

Picks were hand-verified against oneshot.json (company + line + character +
year/variant) on 2026-10-12. Dropped ambiguous Batman multipacks, CE numbers
already present under McFarlane Collector Edition, and Starfire/Deathstroke/
Red Hood overlaps with existing Multiverse/CE rows. Source: AF411 Multiverse
checklist — McFarlane Collector Edition section only (one subsection).
No imageUrl / no GTINs.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave19.json"))
PICK = {a["fid"]: a for a in snap["picked"]}

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

out = []
for fid, a in PICK.items():
    name = a["name"].replace("\u2019", "'").replace("\u2018", "'")
    num = a["num"]
    m = re.search(r"\(([^()]*)\)\s*$", name)
    inner = m.group(1) if m else ""
    sub = f"McFarlane Collector Edition #{num}"
    if inner:
        sub = f"McFarlane Collector Edition #{num} {inner}"
    wave = a.get("wave") or ""
    if wave in ("Walmart", "Target", "SDCC", "GameStop", "EE", "Amazon"):
        sub = f"{sub} {wave}"
    out.append(dict(
        id=f"mcf-mce-w19-{slug(name)}-{fid}",
        name=name,
        subtitle=sub,
        line="McFarlane Collector Edition",
        company="mcfarlane",
        kind="figure",
        releaseDate=f"{a['year']}-01-01",
        msrp=float(a["retail"]),
        scale='7"',
        demand=1.35,
        tags=["dc", "af-checklist", "wave19", "mcfarlane", "collector-edition", "af411:" + fid],
        source="curated-dc-gap-wave19",
    ))

ids = [o["id"] for o in out]
assert len(ids) == len(set(ids))
json.dump(out, open(HERE / "_dc_gap_wave19_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["company"], "|", o["name"], "|", o["subtitle"], o["releaseDate"][:4], o["msrp"])

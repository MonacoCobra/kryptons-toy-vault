"""Generate curated DC gap wave29 rows from AF411 DC checklists.

Section: AF411 McFarlane DC Multiverse Collector Edition holes (2-packs / deluxe).
Picks hand-checked against the whole oneshot.json (every company: af411 id, name fuzzy
incl. cross-maker within ~2 years, UPC) on 2026-10-26; fuzzy hits and UPC collisions
skipped (listed in _af411_dc_checklists_wave29.json "dropped"). No imageUrl.
sku = AF411 UPC only when the check digit is valid and unused. MSRP = AF411 retail only.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave29.json"))

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
    sub = "Collector Edition" + (f" {wave} Exclusive" if wave else "")
    if "Gold Label" in name:
        sub += " Gold Label"
    tags = ["dc", "af-checklist", "wave29", "mcfarlane", "collector-edition", "date-precision:year", "af411:" + a["fid"]]
    if " vs " in name or " & " in name:
        tags.append("multipack")
    row = dict(id=f"mcf-ce-w29-{slug(name)[:60]}-{a['fid']}", name=name, subtitle=sub,
               line="McFarlane Collector Edition", company="mcfarlane", kind="figure",
               releaseDate=f"{a['year']}-01-01", scale='7"', demand=1.3, tags=tags,
               source="curated-dc-gap-wave29")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    if a.get("upc") and gtin_ok(a["upc"]) and not a.get("upc_collision"):
        row["sku"] = a["upc"]
        row["tags"].append("sku:af411")
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave29_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["company"], "|", o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"), o.get("sku"))

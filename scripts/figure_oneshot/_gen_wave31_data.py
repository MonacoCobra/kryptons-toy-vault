"""Generate curated DC gap wave31 rows from AF411 DC Multiverse checklist.

Sections: AF411 DC Multiverse Gold Label section holes + BAF/CNC leftovers (Mattel Orm 2018,
Endless Winter Black Adam, Project Superman Gold Label, White Gold Label Catwoman).
Picks hand-checked against the whole oneshot.json (every company: af411 id, name fuzzy
incl. cross-maker within ~2 years, UPC) on 2026-10-28; fuzzy hits and UPC collisions
skipped (listed in _af411_dc_checklists_wave31.json "dropped"). No imageUrl.
sku = AF411 UPC only when the check digit is valid and unused. MSRP = AF411 retail only.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave31.json"))

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
    gold = "Gold Label" in name
    tags = ["dc", "af-checklist", "wave31"]
    if a["section"] == "mattel" or (a.get("upc") or "").startswith("887961") or int(a["year"]) < 2020:
        company, line, sub, scale = "mattel", "DC Multiverse Mattel", "Trench Warrior Collect & Connect", '6"'
        tags += ["mattel", "cnc"]
    else:
        company, line, scale = "mcfarlane", "DC Multiverse", '7"'
        tags += ["mcfarlane"]
        sec = {"frost-king-baf": "Build-A Frost King", "cyborg-baf": "Build-A Cyborg",
               "solomon-grundy-white-gold-label-baf": "Build-A Solomon Grundy White Gold Label"}.get(a["section"])
        if sec:
            sub = ("Gold Label " if gold and "White Gold" not in sec else "") + sec + (f" {wave} Exclusive" if wave else "")
            tags.append("baf")
        else:
            sub = "Gold Label" + (f" {wave} Exclusive" if wave else "")
    if gold:
        tags.append("gold-label")
    tags += ["date-precision:year", "af411:" + a["fid"]]
    pre = "mat-w31" if company == "mattel" else "mcf-w31"
    row = dict(id=f"{pre}-{slug(name)[:60]}-{a['fid']}", name=name, subtitle=sub,
               line=line, company=company, kind="figure",
               releaseDate=f"{a['year']}-01-01", scale=scale, demand=1.2, tags=tags,
               source="curated-dc-gap-wave31")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    if a.get("upc") and gtin_ok(a["upc"]) and not a.get("upc_collision"):
        row["sku"] = a["upc"]
        row["tags"].append("sku:af411")
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave31_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["company"], "|", o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"), o.get("sku"))

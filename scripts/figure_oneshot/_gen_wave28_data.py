"""Generate curated DC gap wave28 rows from AF411 DC checklists.

Sections: AF411 Retro 66 (McFarlane DC Retro Super Friends waves 4-7, Red Platinum,
Batman '66 playsets and exclusives) and Kenner Batman: The Animated Series playset holes.
Picks hand-checked against the whole oneshot.json (every company: af411 id, name fuzzy
incl. cross-maker within ~2 years, UPC) on 2026-10-23; fuzzy hits and UPC collisions
skipped (listed in _af411_dc_checklists_wave28.json "dropped"). No imageUrl.
sku = AF411 UPC only when the check digit is valid and unused. MSRP = AF411 retail only.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave28.json"))

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

EXCL = {"Target": "Target Exclusive", "NYCC": "NYCC Exclusive", "Gamestop": "GameStop Exclusive",
        "EE": "Entertainment Earth Exclusive"}
out = []
for a in snap["picked"]:
    raw = a["name"].replace("\u2019", "'").replace("Villian's", "Villain's")
    wave = (a.get("wave") or "").strip()
    if a["page"] == "kenner-batman-animated-series":
        name, line, company, scale, pre = raw, "Kenner Batman The Animated Series", "kenner", '5"', "ken-btas-w28"
        sub, tags = "Batman: The Animated Series", ["kenner", "batman-animated"]
    else:
        line, company, scale, pre = "DC Retro", "mcfarlane", '6"', "mcf-dcretro-w28"
        tags = ["mcfarlane", "dc-retro"]
        if "Super Friends" in raw:
            name = re.sub(r"\s*\((Red Platinum) - DC Retro: Super Friends\)", r" (\1)", raw)
            name = re.sub(r"\s*\(DC Retro: Super Friends\)", "", name)
            sub = f"Super Friends Wave {wave}" if wave.isdigit() else f"Super Friends {EXCL.get(wave, wave)}"
            tags.append("super-friends")
        elif "Classic TV Series" in raw:
            name = "The Joker (Gold Label - Black Light)"
            sub = "Batman: Classic TV Series Gold Label " + EXCL[wave]
            tags.append("batman-66")
        else:
            name = re.sub(r"\s*\(Retro 66\)", "", raw)
            sub = f"Batman '66 {EXCL.get(wave, wave)}".strip()
            tags.append("batman-66")
    grp = a.get("group", "")
    kind = "playset" if grp.startswith("Vehicles") and "Lunch Box" not in raw else "figure"
    row = dict(id=f"{pre}-{slug(name)[:60]}-{a['fid']}", name=name, subtitle=sub, line=line, company=company,
               kind=kind, releaseDate=f"{a['year']}-01-01", scale=scale, demand=1.3,
               tags=["dc", "af-checklist", "wave28", *tags, "date-precision:year", "af411:" + a["fid"]]
                    + (["playset"] if kind == "playset" else []) + (["multipack"] if "Pack" in raw else []),
               source="curated-dc-gap-wave28")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    if a.get("upc") and gtin_ok(a["upc"]) and not a.get("upc_collision"):
        row["sku"] = a["upc"]
        row["tags"].append("sku:af411")
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave28_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["company"], "|", o["kind"], "|", o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"), o.get("sku"))

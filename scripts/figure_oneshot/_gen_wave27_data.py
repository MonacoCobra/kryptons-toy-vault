"""Generate curated DC gap wave27 rows from AF411 DC checklists.

Sections: MAFEX DC (Medicom) holes, McFarlane DC Super Powers holes (crowdfund 3,
Dr. Midnight), McFarlane Page Punchers holes. Picks hand-checked against the whole
oneshot.json (every company: af411 id, name fuzzy incl. cross-maker, UPC incl. MAFEX
MED-code tails) on 2026-10-22; fuzzy hits and UPC collisions skipped (listed in
_af411_dc_checklists_wave27.json "dropped"). No imageUrl. sku = AF411 UPC/EAN only
when the check digit is valid and unused. MSRP = AF411 retail only.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave27.json"))

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
    "mafex": dict(pre="mafex-w27", company="mafex", line="MAFEX", sub="", scale='6"', kind="figure", tags=["mafex", "medicom"]),
    "mcfarlane-super-powers": dict(pre="mcf-sp-w27", company="mcfarlane", line="DC Super Powers", sub="", scale='4.5"', kind="figure", tags=["mcfarlane", "super-powers"]),
    "page-punchers": dict(pre="mcf-pp-w27", company="mcfarlane", line="Page Punchers", sub="Page Punchers", scale='7"', kind="figure", tags=["mcfarlane", "page-punchers"]),
}
RETAIL = {"Walmart": "Walmart", "Target": "Target"}
out = []
for a in snap["picked"]:
    s = SEC[a["page"]]
    name = a["name"].replace("\u2019", "'")
    wave = (a.get("wave") or "").strip()
    m = re.search(r"\((.*)\)\s*$", name)
    ver = m.group(1) if m else ""
    if a["page"] == "mafex":
        num = re.sub(r"\D", "", a.get("num") or "")
        sub = f"No.{int(num)} {ver}".strip() if num else ver
    else:
        sub = " ".join(x for x in [s["sub"], ver] if x)
        if wave in RETAIL:
            sub += f" {RETAIL[wave]} Exclusive"
        elif wave.isdigit():
            sub += f" Wave {wave}"
        elif wave and wave.lower() not in sub.lower():
            sub += f" {wave}"
    sub = sub.strip()
    kind = "playset" if "Hall of Justice" in name or "Playset" in name else s["kind"]
    row = dict(id=f"{s['pre']}-{slug(name)[:60]}-{a['fid']}", name=name, subtitle=sub, line=s["line"],
               company=s["company"], kind=kind,
               releaseDate=f"{a['year']}-01-01", scale=s["scale"], demand=1.3,
               tags=["dc", "af-checklist", "wave27", *s["tags"], "date-precision:year", "af411:" + a["fid"]]
                    + (["vehicle"] if kind == "vehicle" else []) + (["playset"] if kind == "playset" else [])
                    + (["baf"] if "(BAF)" in name else []),
               source="curated-dc-gap-wave27")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    if a.get("upc") and gtin_ok(a["upc"]):
        row["sku"] = a["upc"]
        row["tags"].append("sku:af411")
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids)), "duplicate ids"
json.dump(out, open(HERE / "_dc_gap_wave27_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["company"], "|", o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"), o.get("sku"))

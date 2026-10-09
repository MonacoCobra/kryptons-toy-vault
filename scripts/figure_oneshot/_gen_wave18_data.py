"""Generate curated DC gap wave18 rows from the AF411 MAFEX DC checklist snapshot.

Picks were hand-verified against oneshot.json (company + line + character +
year/variant) on 2026-10-09. Catalog MAFEX No. labels are often wrong/messy —
matched by character name + variant + year, not by No. alone. Only AF411
figure ids listed in PICK_FIDS are emitted. 2026+ skipped.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
af = json.load(open(HERE / "_af411_dc_checklists_wave18.json"))["mafex-dc-comics"]

PICK_FIDS = {
  "11826","11836","11837","11838","11842","11853","11858","11859","11864",
  "11891","11893","11894","11895","11898","11905","11907","11911","11912",
  "11913","11914","11915","11919","11920","11921","11922","11923","11924",
  "11925","11926","11927","11929","11933",
}

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def money(s):
    m = re.search(r"[\d.]+", (s or "").replace(",", ""))
    return float(m.group()) if m else 0.0

def mafex_no(wave):
    m = re.match(r"N0*(\d+)", wave or "")
    return m.group(1) if m else ""

out = []
for a in af:
    if a["fid"] not in PICK_FIDS:
        continue
    if int(a.get("year") or 0) >= 2026:
        continue
    name = a["name"].replace("\u2019", "'").replace("\u2018", "'")
    no = mafex_no(a.get("wave") or "")
    kind = "vehicle" if "batpod" in name.lower() else "figure"
    m = re.search(r"\(([^()]*)\)\s*$", name)
    inner = m.group(1) if m else ""
    sub = f"No.{no}" if no else "MAFEX"
    if inner:
        sub = f"No.{no} {inner}" if no else inner
    out.append(dict(
        id=f"mafex-w18-{slug(name)}-{a['fid']}",
        name=name,
        subtitle=sub,
        line="MAFEX",
        company="mafex",
        kind=kind,
        releaseDate=f"{a['year']}-01-01",
        msrp=money(a["retail"]),
        scale='6"',
        demand=1.4,
        tags=["dc", "af-checklist", "wave18", "mafex", "af411:" + a["fid"]]
             + (["vehicle"] if kind == "vehicle" else []),
        source="curated-dc-gap-wave18",
    ))

ids = [o["id"] for o in out]
assert len(ids) == len(set(ids))
json.dump(out, open(HERE / "_dc_gap_wave18_data.json", "w"), indent=1, ensure_ascii=False)
from collections import Counter
print(len(out), Counter(o["kind"] for o in out))
for o in out:
    print(o["company"], "|", o["name"], "|", o["subtitle"], o["releaseDate"][:4], o["msrp"])

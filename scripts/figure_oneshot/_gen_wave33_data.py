"""Generate curated gap wave33 rows: AF411 Mattel Masters of the Universe Origins checklist holes.

DC AF411 checklists (multiverse, DCUC, DC Collectibles, Mezco, Mondo) re-checked 2026-10-30: saturated
(remaining non-tagged items all hand-matched to existing rows), so wave33 moves to the next thin brand
section: MOTU Origins (Mattel, 2020+). Picks hand-checked against the whole oneshot.json + figures.ts
(every company: af411 id, name fuzzy within +/-2 yrs, core-name substring 2019+). Fuzzy/same-figure
hits skipped (listed in _af411_motu_origins_wave33.json "dropped"). No imageUrl, no sku (UPCs not
fetched this run). MSRP = AF411 retail only. Release year from checklist.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_motu_origins_wave33.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

SEC = {"origins-action-figures": ("Masters of the Universe Origins", "Wave {w}"),
       "origins-deluxe": ("Masters of the Universe Origins", "Deluxe Wave {w}"),
       "origins-exclusives": ("Masters of the Universe Origins", "{w} Exclusive"),
       "turtles-of-grayskull": ("Masters of the Universe Origins Turtles of Grayskull", "Turtles of Grayskull Wave {w}"),
       "masters-of-the-wwe-universe-action-figures": ("Masters of the WWE Universe", "Masters of the WWE Universe Wave {w}"),
       "transformers-collaboration": ("Masters of the Universe Origins", "Transformers Collaboration {w} Exclusive")}
out = []
for a in snap["picked"]:
    line, fmt = SEC[a["section"]]
    w = a["wave"]
    sub = fmt.format(w=w)
    if not w.isdigit() and a["section"] in ("turtles-of-grayskull", "masters-of-the-wwe-universe-action-figures", "origins-deluxe"):
        sub = ("Deluxe" if a["section"] == "origins-deluxe" else line.replace("Masters of the Universe Origins ", "")) + f" {w} Exclusive"
    if w == "Creations":
        sub = sub.replace("Creations Exclusive", "Mattel Creations Exclusive")
    tags = ["motu", "af-checklist", "wave33", "mattel", "date-precision:year", "af411:" + a["fid"]]
    if "wwe" in a["section"]:
        tags.insert(0, "wwe")
    row = dict(id=f"mat-w33-{slug(a['name'])[:60]}-{a['fid']}", name=a["name"], subtitle=sub,
               line=line, company="mattel", kind="figure", releaseDate=f"{a['year']}-01-01",
               scale='5.5"', demand=1.1, tags=tags, source="curated-dc-gap-wave33")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids))
json.dump(out, open(HERE / "_dc_gap_wave33_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["line"], "|", o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"))

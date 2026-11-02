"""Generate curated gap wave34 rows: AF411 Mattel MOTU Masterverse checklist holes.

Wave33 did MOTU Origins; wave34 moves to the Masterverse (7in, Mattel 2021+) checklist. Picks hand-checked
against the whole oneshot.json (every company: af411 id, core-name substring vs Mattel Masterverse-family rows,
whole-catalog keyword check). Fuzzy/same-figure hits and multi-figure packs skipped (listed in
_af411_motu_masterverse_wave34.json "dropped"). No imageUrl, no sku. MSRP = AF411 retail. Year from checklist.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_motu_masterverse_wave34.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

SEC = {"New Adventures Checklist": "New Adventures", "New Eternia Checklist": "New Eternia",
       "Revelation Action Figures Checklist": "Revelation", "Revelation Deluxe Checklist": "Revelation Deluxe",
       "Revolution Checklist": "Revolution", "Rulers of the Sun Checklist": "Rulers of the Sun",
       "Vintage Collection Checklist": "Vintage Collection"}
EXCL = {"Creations": "Mattel Creations Exclusive", "SDCC": "SDCC Exclusive", "Walmart": "Walmart Exclusive", "EE": "Entertainment Earth Exclusive"}
out = []
for a in snap["picked"]:
    base = SEC[a["section"]]
    name = re.sub(r"\s*\((Deluxe|Rulers of the Sun)\)", "", a["name"]).strip()
    if "(Deluxe)" in a["name"] and "Deluxe" not in base:
        base += " Deluxe"
    w = a["wave"]
    sub = f"{base} Wave {w}" if w.isdigit() else (f"{base} {EXCL[w]}" if w else base)
    row = dict(id=f"mat-w34-{slug(name)[:60]}-{a['fid']}", name=name, subtitle=sub,
               line="Masters of the Universe Masterverse", company="mattel", kind="figure",
               releaseDate=f"{a['year']}-01-01", scale='7"', demand=1.1,
               tags=["motu", "masterverse", "af-checklist", "wave34", "mattel", "date-precision:year", "af411:" + a["fid"]],
               source="curated-dc-gap-wave34")
    if a.get("retail"):
        row["msrp"] = float(a["retail"])
    out.append(row)
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids))
json.dump(out, open(HERE / "_dc_gap_wave34_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["name"], "|", o["subtitle"], "|", o["releaseDate"][:4], o.get("msrp"))

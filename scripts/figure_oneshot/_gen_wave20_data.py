"""Generate curated DC gap wave20 rows from AF411 Multiverse checklist subsections.

Sections: Deluxe Theatrical Edition, Vault Collection, Multipacks (McFarlane DC
Multiverse). Picks hand-verified against oneshot.json (company + line +
character + year/variant) on 2026-10-13; see snapshot note for drops.
Source snapshot: _af411_dc_checklists_wave20.json. No imageUrl / no GTINs.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
snap = json.load(open(HERE / "_af411_dc_checklists_wave20.json"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

EXCL = ("Walmart", "Target", "SDCC", "GameStop", "EE", "Amazon", "Club", "MegaFig")
out = []
for a in snap["picked"]:
    name = a["name"].replace("\u2019", "'").replace("\u2018", "'").replace("  ", " ")
    sec, wave = a["section"], (a.get("wave") or "").strip()
    if sec == "Deluxe Theatrical Edition":
        line, sub, tag, pre = "DC Multiverse Deluxe Theatrical", "Deluxe Theatrical Edition", "theatrical", "mcf-dte-w20"
    elif sec == "Vault Collection":
        line, sub, tag, pre = "DC Multiverse", f"McFarlane Vault Collection Wave {wave}", "vault-collection", "mcf-vault-w20"
        wave = ""
    else:
        line, sub, tag, pre = "DC Multiverse", "Multipack", "multipack", "mcf-mp-w20"
    if wave in EXCL:
        sub = f"{sub} {'Megafig' if wave == 'MegaFig' else wave + ' Exclusive'}"
    out.append(dict(
        id=f"{pre}-{slug(name)[:60]}-{a['fid']}",
        name=name, subtitle=sub, line=line, company="mcfarlane", kind="figure",
        releaseDate=f"{a['year']}-01-01", msrp=a["retail"], scale='7"', demand=1.3,
        tags=["dc", "af-checklist", "wave20", "mcfarlane", tag, "date-precision:year", "af411:" + a["fid"]],
        source="curated-dc-gap-wave20",
    ))
ids = [o["id"] for o in out]
assert len(ids) == len(set(ids))
json.dump(out, open(HERE / "_dc_gap_wave20_data.json", "w"), indent=1, ensure_ascii=False)
print(len(out))
for o in out:
    print(o["name"], "|", o["subtitle"], "|", o["line"], o["releaseDate"][:4], o["msrp"])

"""BBTS AF brand expansion wave 7 — densify majors + 12 new AF brands.

New CompanyIds: generationtoy, zeta, mechfans, toywolf, evolutiontoy,
starace, exo6, blitzway, toynami, creativebeast, alertline, snailshell.

Densify: bandai, figma, beastkingdom, enterbay, hottoys, threezero,
valaverse, premiumdna, acidrain, fourhorsemen, jada, jakks, toybiz, kenner.

Skipped: ToyWorld / Unique Toys (not in BBTS universe); Unique Art Studio
(statues); Perfect Effect / DNA Design (upgrade kits); Good Smile separate
id (figma densify covers Max Factory / GSC figma AF).

Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave7_data.json")


def F(rid, name, subtitle, line, company, release, msrp, scale, demand, tags):
    if release < FLOOR:
        release = FLOOR
    return {
        "id": rid,
        "name": name,
        "subtitle": subtitle,
        "line": line,
        "company": company,
        "kind": "figure",
        "releaseDate": release,
        "msrp": float(msrp),
        "scale": scale,
        "demand": float(demand),
        "tags": [t for t in tags.split(",") if t],
        "source": "curated-bbts-wave7",
    }


def _rows(raw_list, prefix, line, company, scale, default_msrp, tags):
    out = []
    for row in raw_list:
        if len(row) == 6:
            suf, name, sub, date, demand, msrp = row
        elif len(row) == 5:
            suf, name, sub, date, demand = row
            msrp = default_msrp
        else:
            continue
        out.append(
            F(f"{prefix}-{suf}" if not suf.startswith(prefix) else suf,
              name, sub, line, company, date, msrp, scale, demand, tags)
        )
    return out


def _simple(raw, id_prefix, line, company, scale, default_msrp, tags, line_fn=None):
    out = []
    for row in raw:
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else default_msrp
        use_line = line_fn(name, sub) if line_fn else line
        rid = suf if suf.startswith(id_prefix) else f"{id_prefix}-{suf}"
        out.append(F(rid, name, sub, use_line, company, date, msrp, scale, demand, tags))
    return out


def build_bbts_wave7() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # NEW: Generation Toy
    def gt_line(_n, sub):
        if "Combiner" in sub and "limb" not in sub.lower() and "Upgrade" not in sub:
            return "Generation Toy Combiner"
        if "limb" in sub.lower() or "Train set" in sub:
            return "Generation Toy Combiner Limb"
        if sub == "Mini":
            return "Generation Toy Mini"
        if sub == "Special":
            return "Generation Toy Special"
        return "Generation Toy"
    rows += _simple(raw.get("generationtoy", []), "gt7", "Generation Toy", "generationtoy",
                    '1:24', 90.0, "generation-toy,transformers,3p,curated", gt_line)

    # NEW: Zeta
    def zeta_line(_n, sub):
        if "Combiner" in sub:
            return "Zeta Combiner"
        if "ZA" in sub:
            return "Zeta ZA Series"
        if "ZB" in sub:
            return "Zeta ZB Series"
        if "ZE" in sub:
            return "Zeta ZE Series"
        if sub == "Mini":
            return "Zeta Mini"
        if sub == "Special":
            return "Zeta Special"
        return "Zeta Toys"
    rows += _simple(raw.get("zeta", []), "zt7", "Zeta Toys", "zeta",
                    '1:24', 120.0, "zeta,transformers,3p,curated", zeta_line)

    # NEW: Mech Fans / ToyWolf / Evolution-Toy
    for key, cid, tag, idp in [
        ("mechfans", "mechfans", "mech-fans,transformers,3p,curated", "mf7"),
        ("toywolf", "toywolf", "toywolf,transformers,3p,curated", "tw7"),
        ("evolutiontoy", "evolutiontoy", "evolution-toy,transformers,3p,curated", "et7"),
    ]:
        def line_fn(_n, sub, _cid=cid):
            if "Combiner" in sub:
                return f"{_cid} Combiner".replace("mechfans", "Mech Fans").replace(
                    "toywolf", "ToyWolf").replace("evolutiontoy", "Evolution-Toy")
            if sub == "Mini":
                return f"{_cid} Mini".replace("mechfans", "Mech Fans").replace(
                    "toywolf", "ToyWolf").replace("evolutiontoy", "Evolution-Toy")
            if sub == "Special":
                return f"{_cid} Special".replace("mechfans", "Mech Fans").replace(
                    "toywolf", "ToyWolf").replace("evolutiontoy", "Evolution-Toy")
            return {"mechfans": "Mech Fans Toys", "toywolf": "ToyWolf",
                    "evolutiontoy": "Evolution-Toy"}[_cid]
        rows += _simple(raw.get(key, []), idp, "3P Transformers", cid,
                        '1:24', 90.0, tag, line_fn)

    # NEW: Star Ace
    rows += _simple(raw.get("starace", []), "sa7", "Star Ace", "starace",
                    '1:6', 280.0, "star-ace,sixth-scale,curated")

    # NEW: EXO-6
    rows += _simple(raw.get("exo6", []), "exo7", "EXO-6", "exo6",
                    '1:6', 245.0, "exo-6,star-trek,sixth-scale,curated")

    # NEW: Blitzway
    def bw_line(name, sub):
        if "Carbotix" in name or "Getter" in name:
            return "Blitzway Carbotix"
        if "Figure Complex" in name or "Mazinger" in sub:
            return "Blitzway Figure Complex"
        if "Superb Scale" in name:
            return "Blitzway Superb Scale"
        if "Ultraman" in name or "Ultraseven" in name or sub == "Ultraman":
            return "Blitzway Ultraman"
        return "Blitzway"
    rows += _simple(raw.get("blitzway", []), "bw7", "Blitzway", "blitzway",
                    '1:6', 320.0, "blitzway,sixth-scale,curated", bw_line)

    # NEW: Toynami
    def tn_line(name, sub):
        if "VF-" in name or "Macross VF" in sub or "Robotech VF" in sub:
            return "Toynami Valkyrie"
        if "Destroid" in name or "Pod" in name or "Quead" in name:
            return "Toynami Mecha"
        if "New Generation" in sub:
            return "Toynami New Generation"
        return "Toynami Robotech"
    rows += _simple(raw.get("toynami", []), "tn7", "Toynami Robotech", "toynami",
                    '6"', 40.0, "toynami,robotech,macross,curated", tn_line)

    # NEW: Creative Beast
    def cb_line(_n, sub):
        if "Raptor" in sub:
            return "Beasts of the Mesozoic Raptors"
        if "Tyrannosaur" in sub:
            return "Beasts of the Mesozoic Tyrannosaurs"
        if "Ceratopsian" in sub:
            return "Beasts of the Mesozoic Ceratopsians"
        return "Beasts of the Mesozoic"
    rows += _simple(raw.get("creativebeast", []), "cb7", "Beasts of the Mesozoic",
                    "creativebeast", '1:18', 55.0,
                    "creative-beast,beasts-of-the-mesozoic,dinosaur,curated", cb_line)

    # NEW: Alert Line
    rows += _simple(raw.get("alertline", []), "al7", "Alert Line", "alertline",
                    '1:6', 165.0, "alert-line,military,sixth-scale,curated")

    # NEW: Snail Shell
    def ss_line(_n, sub):
        return "Snail Shell Special" if sub == "Special" else "Snail Shell"
    rows += _simple(raw.get("snailshell", []), "ss7", "Snail Shell", "snailshell",
                    '1:12', 68.0, "snail-shell,1-12,curated", ss_line)

    # Densify: Bandai
    def bn_line(name, sub):
        if "Gundam Universe" in sub or "Gundam Universe" in name:
            return "Gundam Universe"
        return "Robot Spirits"
    rows += _simple(raw.get("bandai", []), "bn7", "Robot Spirits", "bandai",
                    '6"', 65.0, "bandai,gundam,robot-spirits,af,curated", bn_line)

    # Densify: figma
    rows += _simple(raw.get("figma", []), "fg7", "figma", "figma",
                    '6"', 75.0, "figma,max-factory,good-smile,curated")

    # Densify: Beast Kingdom
    rows += _simple(raw.get("beastkingdom", []), "bk7", "Dynamic Action Heroes",
                    "beastkingdom", '1:9', 125.0, "beast-kingdom,dah,curated")

    # Densify: Enterbay
    rows += _simple(raw.get("enterbay", []), "eb7", "Enterbay", "enterbay",
                    '1:6', 280.0, "enterbay,sixth-scale,curated")

    # Densify: Hot Toys
    rows += _simple(raw.get("hottoys", []), "ht7", "Hot Toys", "hottoys",
                    '1:6', 350.0, "hot-toys,sixth-scale,curated")

    # Densify: threezero
    def tz_line(name, sub):
        if name.startswith("DLX") or "DLX" in sub or name.startswith("DLX"):
            return "threezero DLX"
        if "FigZero" in name:
            return "threezero FigZero"
        return "threezero"
    rows += _simple(raw.get("threezero", []), "tz7", "threezero", "threezero",
                    '1:6', 160.0, "threezero,dlx,figzero,curated", tz_line)

    # Densify: Valaverse
    rows += _simple(raw.get("valaverse", []), "vv7", "Action Force", "valaverse",
                    '1:12', 24.99, "valaverse,action-force,curated")

    # Densify: Premium DNA
    rows += _simple(raw.get("premiumdna", []), "pd7", "Premium DNA Filmation",
                    "premiumdna", '1:12', 55.0, "premium-dna,motu,filmation,curated")

    # Densify: Acid Rain
    rows += _simple(raw.get("acidrain", []), "ar7", "Acid Rain World", "acidrain",
                    '1:18', 35.0, "acid-rain,toys-alliance,curated")

    # Densify: Four Horsemen
    def fh_line(_n, sub):
        if "Cosmic" in sub:
            return "Cosmic Legions"
        if "Figura Obscura" in sub or "Figura Obscura" in _n:
            return "Figura Obscura"
        return "Mythic Legions"
    rows += _simple(raw.get("fourhorsemen", []), "fh7", "Mythic Legions",
                    "fourhorsemen", '6"', 48.0,
                    "four-horsemen,mythic-legions,curated", fh_line)

    # Densify: Jada
    def jd_line(name, sub):
        if "Nano" in name or sub == "DC":
            return "Jada Nano Metalfigs"
        if "Universal" in sub or "Universal" in name:
            return "Jada Universal Monsters"
        return "Jada Street Fighter"
    rows += _simple(raw.get("jada", []), "jd7", "Jada Street Fighter", "jada",
                    '6"', 24.99, "jada,curated", jd_line)

    # Densify: JAKKS
    def jk_line(_n, sub):
        if "Primal" in sub:
            return "MotU Primal Age"
        if "Nintendo" in sub:
            return "JAKKS Nintendo"
        if "2.5" in sub:
            return "Sonic 2.5-inch"
        if "Movie" in sub:
            return "Sonic Movie"
        return "Sonic the Hedgehog"
    rows += _simple(raw.get("jakks", []), "jk7", "Sonic the Hedgehog", "jakks",
                    '5"', 14.99, "jakks,sonic,curated", jk_line)

    # Densify: ToyBiz
    rows += _simple(raw.get("toybiz", []), "tb7", "Marvel Legends (Toy Biz)",
                    "toybiz", '6"', 8.99, "toybiz,marvel,vintage,curated")

    # Densify: Kenner
    def kn_line(_n, sub):
        if "Super Powers" in sub:
            return "Super Powers"
        return f"Kenner {sub}"
    rows += _simple(raw.get("kenner", []), "kn7", "Super Powers", "kenner",
                    '4.5"', 5.99, "kenner,super-powers,dc,curated", kn_line)

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out

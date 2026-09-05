"""BBTS AF brand expansion wave 8 — densify majors + 12 new AF brands.

New CompanyIds: asmus, herocross, fanshobby, fansproject, transart,
bingotoys, heatboys, ccstoys, tbleague, coomodel, did, moshow.

Densify: joytoy, sentinel, thousandtoys, spinmaster, freshmonkey,
mafex, mezco, storm, hiya, mondo, shfiguarts, kaiyodo, hasbro, mcfarlane.

Skipped: statue-primary (Gecco / First 4 Figures / Unique Art / XM);
upgrade kits (Perfect Effect / DNA Design); brick lines (Pantasy /
Keeppley); ToyWorld / Unique Toys (not in BBTS universe).

Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave8_data.json")


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
        "source": "curated-bbts-wave8",
    }


def _simple(raw, id_prefix, line, company, scale, default_msrp, tags, line_fn=None):
    out = []
    for row in raw:
        suf, name, sub, date, demand = row[:5]
        msrp = row[5] if len(row) > 5 else default_msrp
        use_line = line_fn(name, sub) if line_fn else line
        rid = suf if suf.startswith(id_prefix) else f"{id_prefix}-{suf}"
        out.append(F(rid, name, sub, use_line, company, date, msrp, scale, demand, tags))
    return out


def build_bbts_wave8() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # NEW: Asmus
    def as_line(_n, sub):
        if "Witcher" in sub:
            return "Asmus The Witcher"
        if "Hobbit" in sub:
            return "Asmus The Hobbit"
        return "Asmus Lord of the Rings"
    rows += _simple(raw.get("asmus", []), "as8", "Asmus Lord of the Rings", "asmus",
                    '1:6', 280.0, "asmus,sixth-scale,lotr,curated", as_line)

    # NEW: HeroCross
    def hx_line(_n, sub):
        if "Combiner" in sub:
            return "HeroCross Hybrid Metal Combiner"
        if sub == "Movie":
            return "HeroCross Hybrid Metal Movie"
        if sub == "Mini":
            return "HeroCross Mini"
        if sub == "Special":
            return "HeroCross Special"
        return "HeroCross Hybrid Metal"
    rows += _simple(raw.get("herocross", []), "hx8", "HeroCross Hybrid Metal", "herocross",
                    '1:18', 150.0, "herocross,transformers,3p,curated", hx_line)

    # NEW: Fans Hobby
    def fhb_line(_n, sub):
        if "Combiner" in sub:
            return "Fans Hobby Combiner"
        if sub == "Mini":
            return "Fans Hobby Mini"
        if sub == "Special":
            return "Fans Hobby Special"
        return "Fans Hobby Master Builder"
    rows += _simple(raw.get("fanshobby", []), "fhb8", "Fans Hobby Master Builder", "fanshobby",
                    '1:24', 180.0, "fans-hobby,transformers,3p,curated", fhb_line)

    # NEW: FansProject
    def fp_line(_n, sub):
        if "Seacon" in sub or "Seacon" in _n:
            return "FansProject Seacon"
        if "Function" in sub:
            return "FansProject Function X"
        if "Causality" in sub or "Causality" in _n:
            return "FansProject Causality"
        if sub == "Mini":
            return "FansProject Mini"
        if sub == "Special":
            return "FansProject Special"
        return "FansProject"
    rows += _simple(raw.get("fansproject", []), "fp8", "FansProject", "fansproject",
                    '1:24', 150.0, "fansproject,transformers,3p,curated", fp_line)

    # NEW: TransArt
    def ta_line(_n, sub):
        if "Combiner" in sub:
            return "TransArt Combiner"
        if "Beast" in sub or _n.startswith("BWM"):
            return "TransArt Beast Wars Metal"
        if sub == "Mini":
            return "TransArt Mini"
        if sub == "Special":
            return "TransArt Special"
        return "TransArt Toys"
    rows += _simple(raw.get("transart", []), "ta8", "TransArt Toys", "transart",
                    '1:24', 130.0, "transart,transformers,3p,curated", ta_line)

    # NEW: BingoToys / Heatboys (patterned 3P)
    for key, cid, tag, idp, line_name in [
        ("bingotoys", "bingotoys", "bingotoys,transformers,3p,curated", "bt8", "BingoToys"),
        ("heatboys", "heatboys", "heatboys,transformers,3p,curated", "hb8", "Heatboys"),
    ]:
        def line_fn(_n, sub, _ln=line_name):
            if "Combiner" in sub:
                return f"{_ln} Combiner"
            if sub == "Mini":
                return f"{_ln} Mini"
            if sub == "Special":
                return f"{_ln} Special"
            return _ln
        rows += _simple(raw.get(key, []), idp, line_name, cid, '1:24', 120.0, tag, line_fn)

    # NEW: CCS Toys
    def ccs_line(_n, sub):
        if "1/12" in sub:
            return "CCS Toys Mortal Kombat 1/12"
        if "Special" in sub:
            return "CCS Toys Special"
        return "CCS Toys Mortal Kombat 1/6"
    rows += _simple(raw.get("ccstoys", []), "ccs8", "CCS Toys Mortal Kombat", "ccstoys",
                    '1:6', 270.0, "ccs-toys,mortal-kombat,curated", ccs_line)

    # NEW: TBLeague
    def tb_line(_n, sub):
        if "Seamless" in sub:
            return "TBLeague Seamless Body"
        if sub == "Special":
            return "TBLeague Special"
        if sub == "Licensed":
            return "TBLeague Licensed"
        return f"TBLeague {sub}"
    rows += _simple(raw.get("tbleague", []), "tbl8", "TBLeague", "tbleague",
                    '1:6', 200.0, "tbleague,phicen,sixth-scale,curated", tb_line)

    # NEW: COO Model
    def cm_line(_n, sub):
        if "Empire" in sub:
            return "COO Model Empire Series"
        if "Nose Art" in sub:
            return "COO Model Nose Art"
        if "Paladin" in sub:
            return "COO Model Paladin Empire"
        return "COO Model Special"
    rows += _simple(raw.get("coomodel", []), "cm8", "COO Model", "coomodel",
                    '1:6', 220.0, "coo-model,military,sixth-scale,curated", cm_line)

    # NEW: DiD
    def did_line(_n, sub):
        if sub == "Special":
            return "DiD Special"
        if sub == "Historical":
            return "DiD Historical"
        return f"DiD {sub}"
    rows += _simple(raw.get("did", []), "did8", "DiD", "did",
                    '1:6', 195.0, "did,military,sixth-scale,curated", did_line)

    # NEW: MoShow
    def ms_line(_n, sub):
        if "Progenitor" in sub or "Progenitor" in _n:
            return "MoShow Progenitor Effect"
        if "Combiner" in sub:
            return "MoShow Combiner"
        if sub == "Mini":
            return "MoShow Mini"
        if sub == "Special":
            return "MoShow Special"
        return "MoShow Metal Build Style"
    rows += _simple(raw.get("moshow", []), "ms8", "MoShow Toys", "moshow",
                    '1:9', 250.0, "moshow,mecha,curated", ms_line)

    # Densify: JoyToy
    def jt_line(_n, sub):
        if "Dark Source" in sub:
            return "JoyToy Dark Source"
        return "JoyToy Warhammer 40K"
    rows += _simple(raw.get("joytoy", []), "jt8", "JoyToy Warhammer 40K", "joytoy",
                    '1:18', 55.0, "joytoy,warhammer,40k,curated", jt_line)

    # Densify: Sentinel
    def sn_line(_n, sub):
        if "Riobot" in sub or "Riobot" in _n:
            return "Sentinel Riobot"
        if "Wonderful Acts" in sub or "Wonderful Acts" in _n:
            return "Sentinel Wonderful Acts"
        return "Sentinel Fighting Armor"
    rows += _simple(raw.get("sentinel", []), "sn8", "Sentinel Fighting Armor", "sentinel",
                    '6"', 95.0, "sentinel,fighting-armor,riobot,curated", sn_line)

    # Densify: 1000Toys
    def tt_line(_n, sub):
        if "Synthetic" in sub or "Synthetic" in _n:
            return "1000Toys Synthetic Human"
        return "1000Toys Tough Guys"
    rows += _simple(raw.get("thousandtoys", []), "tt8", "1000Toys Tough Guys", "thousandtoys",
                    '6"', 85.0, "1000toys,synthetic-human,curated", tt_line)

    # Densify: Spin Master
    def sm_line(_n, sub):
        if "Character" in sub:
            return "Bakugan Character AF"
        if "Legacy" in sub:
            return "Bakugan Legacy"
        if "Special" in sub:
            return "Bakugan Special"
        return f"Bakugan {sub}"
    rows += _simple(raw.get("spinmaster", []), "sm8", "Bakugan", "spinmaster",
                    '2"', 14.99, "spin-master,bakugan,curated", sm_line)

    # Densify: Fresh Monkey
    def fm_line(_n, sub):
        if "Army of Darkness" in sub or "Ash" in _n or "Deadite" in _n:
            return "Fresh Monkey Army of Darkness"
        if "Fresh Retro" in sub:
            return "Fresh Retro"
        if sub == "Special":
            return "Fresh Monkey Special"
        return f"Fresh Monkey {sub}"
    rows += _simple(raw.get("freshmonkey", []), "fm8", "Fresh Monkey Fiction", "freshmonkey",
                    '6"', 25.0, "fresh-monkey,fresh-retro,curated", fm_line)

    # Densify: MAFEX
    rows += _simple(raw.get("mafex", []), "mx8", "MAFEX", "mafex",
                    '6"', 95.0, "mafex,medicom,curated")

    # Densify: Mezco
    rows += _simple(raw.get("mezco", []), "mz8", "One:12 Collective", "mezco",
                    '1:12', 112.0, "mezco,one12,curated")

    # Densify: Storm
    def st_line(_n, sub):
        if "Mortal Kombat" in sub:
            return "Storm Mortal Kombat"
        if sub == "KOF":
            return "Storm King of Fighters"
        if sub == "Tekken":
            return "Storm Tekken"
        if sub == "Special":
            return "Storm Special"
        return "Storm Street Fighter"
    rows += _simple(raw.get("storm", []), "st8", "Storm Collectibles", "storm",
                    '1:12', 110.0, "storm,fighting-game,curated", st_line)

    # Densify: Hiya
    def hy_line(_n, sub):
        if "Exquisite" in sub:
            return "Hiya Exquisite Mini"
        if sub == "Classic":
            return "Hiya Godzilla Classic"
        if sub == "Special":
            return "Hiya Special"
        return "Hiya Godzilla"
    rows += _simple(raw.get("hiya", []), "hy8", "Hiya Toys", "hiya",
                    '6"', 55.0, "hiya,godzilla,exquisite-mini,curated", hy_line)

    # Densify: Mondo
    def md_line(_n, sub):
        if "TMNT" in sub or "TMNT" in _n or "Shredder" in _n or "Krang" in _n or "Casey" in _n or "April" in _n:
            return "Mondo TMNT 1/6"
        return "Mondo Masters of the Universe 1/6"
    rows += _simple(raw.get("mondo", []), "md8", "Mondo 1/6", "mondo",
                    '1:6', 200.0, "mondo,sixth-scale,curated", md_line)

    # Densify: SHFiguarts
    def sf_line(_n, sub):
        if "Dragon Ball" in sub:
            return "S.H.Figuarts Dragon Ball"
        if "Naruto" in sub:
            return "S.H.Figuarts Naruto"
        if "Avengers" in sub:
            return "S.H.Figuarts Marvel"
        if sub == "DC":
            return "S.H.Figuarts DC"
        if "Ultraman" in sub:
            return "S.H.Figuarts Ultraman"
        if "Kamen" in sub:
            return "S.H.Figuarts Kamen Rider"
        return "S.H.Figuarts"
    rows += _simple(raw.get("shfiguarts", []), "sf8", "S.H.Figuarts", "shfiguarts",
                    '6"', 75.0, "shfiguarts,tamashii,curated", sf_line)

    # Densify: Kaiyodo
    def ky_line(_n, sub):
        if "Amazing Yamaguchi" in _n or "Amazing Yamaguchi" in sub:
            return "Amazing Yamaguchi"
        if "Evangelion" in sub:
            return "Revoltech Evangelion"
        if "Godzilla" in sub or "Godzilla" in _n:
            return "Revoltech Godzilla"
        if "Ultraman" in sub:
            return "Revoltech Ultraman"
        if "Mecha" in sub:
            return "Revoltech Mecha"
        return "Revoltech"
    rows += _simple(raw.get("kaiyodo", []), "ky8", "Kaiyodo Revoltech", "kaiyodo",
                    '6"', 90.0, "kaiyodo,revoltech,amazing-yamaguchi,curated", ky_line)

    # Densify: Hasbro
    def hs_line(_n, sub):
        if "Marvel Legends" in sub:
            return "Marvel Legends"
        if "Black Series" in sub:
            return "Star Wars Black Series"
        if "Classified" in sub:
            return "GI Joe Classified"
        if "Studio Series" in sub:
            return "Transformers Studio Series"
        return "Hasbro"
    rows += _simple(raw.get("hasbro", []), "hs8", "Hasbro", "hasbro",
                    '6"', 24.99, "hasbro,curated", hs_line)

    # Densify: McFarlane
    def mf_line(_n, sub):
        if "Spawn" in sub or "Spawn" in _n:
            return "McFarlane Spawn"
        if "Page Punchers" in sub:
            return "McFarlane Page Punchers"
        if "Gold Label" in sub:
            return "DC Multiverse Gold Label"
        if "Platinum" in sub:
            return "DC Multiverse Platinum"
        return "DC Multiverse"
    rows += _simple(raw.get("mcfarlane", []), "mf8", "DC Multiverse", "mcfarlane",
                    '7"', 22.99, "mcfarlane,dc,spawn,curated", mf_line)

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out

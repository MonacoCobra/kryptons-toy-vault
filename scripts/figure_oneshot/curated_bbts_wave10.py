"""BBTS AF brand expansion wave 10 (FINAL) — densify majors + 12 new AF brands.

New CompanyIds: haoyu, bigchief, iconiq, figurestoy, toynotch, actoys,
newwave, flirtygirl, firegirl, i8toys, nanmu, vtoys.

Densify: hasbro, mcfarlane, mezco, mafex, storm, hiya, mondo,
shfiguarts, kaiyodo, figma, jakks, joytoy, sentinel, kenner.

Skipped: statue-primary (Gecco / First 4 Figures / Unique Art / XM /
Prime 1 / Queen / Iron Studios / Tweeterhead / PCS / Sideshow statues /
Gentle Giant / Weta); MegaHouse scales-only; Kids Logic statue-leaning;
Quantum Mechanix diorama-leaning; Super Duck accessory heads; brick /
garage-kit / upgrade-kit lines.

Floor 1980; no imageUrl; AF only. Final expansion wave — no wave 11.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave10_data.json")


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
        "source": "curated-bbts-wave10",
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


def build_bbts_wave10() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    def hy_line(_n, sub):
        if sub == "Accessories":
            return "HaoYu Accessories"
        if sub == "Special":
            return "HaoYu Special"
        return f"HaoYu {sub}"
    rows += _simple(raw.get("haoyu", []), "hy10", "HaoYu Toys", "haoyu",
                    "1:6", 189.0, "haoyu,military,sixth-scale,curated", hy_line)

    def bc_line(_n, sub):
        if sub == "Doctor Who":
            return "BIG Chief Doctor Who"
        if sub == "Film":
            return "BIG Chief Film"
        if sub == "Accessories":
            return "BIG Chief Accessories"
        return "BIG Chief Special"
    rows += _simple(raw.get("bigchief", []), "bc10", "BIG Chief Studios", "bigchief",
                    "1:6", 250.0, "bigchief,doctor-who,sixth-scale,curated", bc_line)

    def iq_line(_n, sub):
        if sub == "Accessories":
            return "Iconiq Accessories"
        if sub == "Special":
            return "Iconiq Special"
        return f"Iconiq {sub}"
    rows += _simple(raw.get("iconiq", []), "iq10", "Iconiq Studios", "iconiq",
                    "1:6", 260.0, "iconiq,fighters,sixth-scale,curated", iq_line)

    def ftc_line(_n, sub):
        if "WGSH" in sub:
            return "Figures Toy Company WGSH Style"
        if "Marvel" in sub:
            return "Figures Toy Company Marvel Style"
        if "TV" in sub:
            return "Figures Toy Company TV Heroes"
        if sub == "Bodies":
            return "Figures Toy Company Bodies"
        if sub == "Accessories":
            return "Figures Toy Company Accessories"
        return "Figures Toy Company Special"
    rows += _simple(raw.get("figurestoy", []), "ftc10", "Figures Toy Company", "figurestoy",
                    '8"', 19.99, "figures-toy-company,retro,curated", ftc_line)

    def tn_line(_n, sub):
        if sub == "Accessories":
            return "Toy Notch Accessories"
        if sub == "Special":
            return "Toy Notch Special"
        return f"Toy Notch {sub}"
    rows += _simple(raw.get("toynotch", []), "tn10", "Toy Notch", "toynotch",
                    "1:6", 210.0, "toynotch,historical,sixth-scale,curated", tn_line)

    def ac_line(_n, sub):
        if sub == "Accessories":
            return "ACToys Accessories"
        if sub == "Special":
            return "ACToys Special"
        return f"ACToys {sub}"
    rows += _simple(raw.get("actoys", []), "ac10", "ACToys", "actoys",
                    "1:6", 185.0, "actoys,military,sixth-scale,curated", ac_line)

    def nw_line(_n, sub):
        if sub == "Replicade":
            return "New Wave Replicade"
        if "Street Fighter" in sub:
            return "New Wave Street Fighter"
        if "Arcade" in sub:
            return "New Wave Arcade Heroes"
        if sub == "Accessories":
            return "New Wave Accessories"
        return "New Wave Special"
    rows += _simple(raw.get("newwave", []), "nw10", "New Wave Toys", "newwave",
                    '3.75"', 22.99, "newwave,arcade,reaction-style,curated", nw_line)

    def fg_line(_n, sub):
        if sub == "Accessories":
            return "Flirty Girl Accessories"
        if sub == "Special":
            return "Flirty Girl Special"
        return f"Flirty Girl {sub}"
    rows += _simple(raw.get("flirtygirl", []), "fg10", "Flirty Girl Collectibles", "flirtygirl",
                    "1:6", 220.0, "flirtygirl,sixth-scale,curated", fg_line)

    def frg_line(_n, sub):
        if sub == "Accessories":
            return "Fire Girl Accessories"
        if sub == "Special":
            return "Fire Girl Special"
        return f"Fire Girl {sub}"
    rows += _simple(raw.get("firegirl", []), "frg10", "Fire Girl Toys", "firegirl",
                    "1:6", 210.0, "firegirl,sixth-scale,curated", frg_line)

    def i8_line(_n, sub):
        if sub == "Accessories":
            return "i8Toys Accessories"
        if sub == "Special":
            return "i8Toys Special"
        return f"i8Toys {sub}"
    rows += _simple(raw.get("i8toys", []), "i810", "i8Toys", "i8toys",
                    "1:6", 195.0, "i8toys,sixth-scale,curated", i8_line)

    def nm_line(_n, sub):
        if sub == "Accessories":
            return "Nanmu Accessories"
        if sub == "Special":
            return "Nanmu Special"
        return f"Nanmu {sub}"
    rows += _simple(raw.get("nanmu", []), "nm10", "Nanmu Studio", "nanmu",
                    "varies", 120.0, "nanmu,dinosaur,creature,curated", nm_line)

    def vt_line(_n, sub):
        if sub == "Bodies":
            return "VTOYS Bodies"
        if sub == "Heads":
            return "VTOYS Heads"
        if sub == "Accessories":
            return "VTOYS Accessories"
        if sub == "Special":
            return "VTOYS Special"
        return f"VTOYS {sub}"
    rows += _simple(raw.get("vtoys", []), "vt10", "VTOYS", "vtoys",
                    "1:6", 150.0, "vtoys,bodies,sixth-scale,curated", vt_line)

    # Densify
    def hs_line(_n, sub):
        if "Marvel Legends" in sub or _n.startswith("Marvel Legends") or _n.startswith("ML "):
            return "Marvel Legends"
        if "Black Series" in sub or _n.startswith("Black Series") or _n.startswith("BS "):
            return "Star Wars Black Series"
        if "Classified" in sub or _n.startswith("Classified"):
            return "GI Joe Classified"
        if "Studio Series" in sub or _n.startswith("Studio Series") or _n.startswith("SS86"):
            return "Transformers Studio Series"
        if "Lightning" in sub or _n.startswith("Lightning") or _n.startswith("LC "):
            return "Power Rangers Lightning Collection"
        return "Hasbro Special"
    rows += _simple(raw.get("hasbro", []), "hs10", "Marvel Legends", "hasbro",
                    '6"', 24.99, "hasbro,marvel-legends,curated", hs_line)

    def mf_line(_n, sub):
        if "Spawn" in sub or _n.startswith("Spawn"):
            return "McFarlane Spawn"
        if "Megafigs" in sub:
            return "McFarlane Megafigs"
        if sub == "Special":
            return "McFarlane Special"
        return "DC Multiverse"
    rows += _simple(raw.get("mcfarlane", []), "mf10", "DC Multiverse", "mcfarlane",
                    '7"', 22.99, "mcfarlane,dc-multiverse,spawn,curated", mf_line)

    def mz_line(_n, sub):
        if sub == "Accessories":
            return "Mezco Accessories"
        if sub == "Special":
            return "Mezco Special"
        return "Mezco One:12 Collective"
    rows += _simple(raw.get("mezco", []), "mz10", "Mezco One:12 Collective", "mezco",
                    "1:12", 112.0, "mezco,one12,curated", mz_line)

    def mx_line(_n, sub):
        if sub == "Accessories":
            return "MAFEX Accessories"
        if sub == "Special":
            return "MAFEX Special"
        return "MAFEX"
    rows += _simple(raw.get("mafex", []), "mx10", "MAFEX", "mafex",
                    "1:12", 95.0, "mafex,medicom,curated", mx_line)

    def st_line(_n, sub):
        if sub == "Accessories":
            return "Storm Accessories"
        if sub == "Special":
            return "Storm Special"
        return f"Storm Collectibles {sub}"
    rows += _simple(raw.get("storm", []), "st10", "Storm Collectibles", "storm",
                    "1:12", 110.0, "storm,fighters,curated", st_line)

    def hi_line(_n, sub):
        if sub == "Accessories":
            return "Hiya Accessories"
        if sub == "Special":
            return "Hiya Special"
        if "Exquisite Mini" in sub:
            return "Hiya Exquisite Mini"
        if "Exquisite Super" in sub:
            return "Hiya Exquisite Super Series"
        return f"Hiya {sub}"
    rows += _simple(raw.get("hiya", []), "hi10", "Hiya Toys", "hiya",
                    "varies", 90.0, "hiya,godzilla,curated", hi_line)

    def md_line(_n, sub):
        if "MotU" in sub:
            return "Mondo MotU 1/6"
        if "TMNT" in sub:
            return "Mondo TMNT 1/6"
        if "Soft Vinyl" in sub:
            return "Mondo Soft Vinyl"
        if "Movie" in sub:
            return "Mondo Movie 1/6"
        if sub == "Accessories":
            return "Mondo Accessories"
        return "Mondo Special"
    rows += _simple(raw.get("mondo", []), "md10", "Mondo", "mondo",
                    "1:6", 300.0, "mondo,sixth-scale,curated", md_line)

    def sh_line(_n, sub):
        if sub == "Accessories":
            return "SHFiguarts Accessories"
        if sub == "Special":
            return "SHFiguarts Special"
        return f"S.H.Figuarts {sub}"
    rows += _simple(raw.get("shfiguarts", []), "sh10", "S.H.Figuarts", "shfiguarts",
                    "1:12", 75.0, "shfiguarts,tamashii,curated", sh_line)

    def ky_line(_n, sub):
        if "Amazing Yamaguchi" in sub or _n.startswith("Amazing Yamaguchi") or _n.startswith("AY "):
            return "Amazing Yamaguchi"
        if "Revoltech" in sub or _n.startswith("Revoltech"):
            return "Revoltech"
        if sub == "Accessories":
            return "Kaiyodo Accessories"
        return "Kaiyodo Special"
    rows += _simple(raw.get("kaiyodo", []), "ky10", "Amazing Yamaguchi", "kaiyodo",
                    "1:12", 95.0, "kaiyodo,amazing-yamaguchi,revoltech,curated", ky_line)

    def fgm_line(_n, sub):
        if sub == "Accessories":
            return "figma Accessories"
        if sub == "Special":
            return "figma Special"
        return f"figma {sub}"
    rows += _simple(raw.get("figma", []), "fgm10", "figma", "figma",
                    "1:12", 75.0, "figma,good-smile,curated", fgm_line)

    def jk_line(_n, sub):
        if "Sonic" in sub or _n.startswith("Sonic") or _n.startswith("Shadow"):
            return "JAKKS Sonic"
        if "Nintendo" in sub or _n.startswith("Nintendo"):
            return "JAKKS Nintendo"
        if sub == "WWE" or _n.startswith("WWE"):
            return "JAKKS WWE"
        if "Primal" in sub or _n.startswith("Primal"):
            return "Masters of the Universe Primal Age"
        if sub == "Accessories":
            return "JAKKS Accessories"
        return "JAKKS Special"
    rows += _simple(raw.get("jakks", []), "jk10", "JAKKS Pacific", "jakks",
                    '2.5"', 12.99, "jakks,sonic,nintendo,curated", jk_line)

    def jt_line(_n, sub):
        if "40K" in sub or "Warhammer" in sub:
            return "JoyToy Warhammer 40K"
        if "Dark Source" in sub:
            return "JoyToy Dark Source"
        if "Mecha" in sub:
            return "JoyToy 1/18 Mecha"
        if sub == "Accessories":
            return "JoyToy Accessories"
        return "JoyToy Special"
    rows += _simple(raw.get("joytoy", []), "jt210", "JoyToy", "joytoy",
                    "1:18", 45.0, "joytoy,warhammer,dark-source,curated", jt_line)

    def sn_line(_n, sub):
        if "Fighting Armor" in sub or _n.startswith("Fighting Armor"):
            return "Sentinel Fighting Armor"
        if "Riobot" in sub or _n.startswith("Riobot"):
            return "Sentinel Riobot"
        if "Wonderful Acts" in sub:
            return "Sentinel Wonderful Acts"
        if sub == "Accessories":
            return "Sentinel Accessories"
        return "Sentinel Special"
    rows += _simple(raw.get("sentinel", []), "sn10", "Sentinel", "sentinel",
                    "varies", 120.0, "sentinel,fighting-armor,riobot,curated", sn_line)

    def kn_line(_n, sub):
        if "Super Powers" in sub or _n.startswith("Super Powers"):
            return "Kenner Super Powers"
        if "Batman" in sub or _n.startswith("Batman"):
            return "Kenner Batman Movie"
        if sub == "Accessories":
            return "Kenner Accessories"
        return "Kenner Special"
    rows += _simple(raw.get("kenner", []), "kn10", "Kenner Super Powers", "kenner",
                    '5"', 5.99, "kenner,super-powers,batman,curated", kn_line)

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out

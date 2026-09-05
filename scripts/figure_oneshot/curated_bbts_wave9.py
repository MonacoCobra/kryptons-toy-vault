"""BBTS AF brand expansion wave 9 — densify majors + 12 new AF brands.

New CompanyIds: mego, worldbox, kaustic, poptoys, deviltoys, kingarts,
jtstudio, artspirits, artstorm, fiftytwo, actiontoys, underverse.

Densify: neca, super7, threezero, hottoys, beastkingdom, enterbay,
fourhorsemen, valaverse, bossfight, loyalsubjects, jada, bandai,
playmates, mattel.

Skipped: statue-primary (Gecco / First 4 Figures / Unique Art / XM /
Prime 1 / Queen / Iron Studios / Tweeterhead / PCS / Sideshow statues /
Gentle Giant / Weta); upgrade kits (Perfect Effect / DNA Design);
brick lines (Pantasy / Keeppley); garage kits; dolls; ToyWorld / Unique
Toys / APC Toys (not in BBTS universe or non-target).

Floor 1980; no imageUrl; AF only.
"""
from __future__ import annotations

import json
from pathlib import Path

FLOOR = "1980-01-01"
DATA = Path(__file__).with_name("bbts_wave9_data.json")


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
        "source": "curated-bbts-wave9",
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


def build_bbts_wave9() -> list[dict]:
    raw = json.loads(DATA.read_text())
    rows: list[dict] = []

    # NEW: Mego
    def mg_line(_n, sub):
        if sub == "WGSH":
            return "Mego World's Greatest Super Heroes"
        if sub == "Marvel":
            return "Mego Marvel"
        if sub == "Star Trek":
            return "Mego Star Trek"
        if sub == "Horror":
            return "Mego Horror"
        if sub == "Bodies":
            return "Mego Bodies"
        return "Mego Special"
    rows += _simple(raw.get("mego", []), "mg9", "Mego", "mego",
                    '8"', 22.99, "mego,retro,curated", mg_line)

    # NEW: World Box
    def wb_line(_n, sub):
        if sub == "Bodies":
            return "World Box Bodies"
        if sub == "Heads":
            return "World Box Heads"
        if sub == "Accessories":
            return "World Box Accessories"
        if sub == "Special":
            return "World Box Special"
        return f"World Box {sub}"
    rows += _simple(raw.get("worldbox", []), "wb9", "World Box", "worldbox",
                    '1:6', 150.0, "worldbox,sixth-scale,curated", wb_line)

    # NEW: Kaustic Plastik
    def kp_line(_n, sub):
        if sub == "Special":
            return "Kaustic Plastik Special"
        return f"Kaustic Plastik {sub}"
    rows += _simple(raw.get("kaustic", []), "kp9", "Kaustic Plastik", "kaustic",
                    '1:6', 200.0, "kaustic,historical,sixth-scale,curated", kp_line)

    # NEW: POP Toys
    def pt_line(_n, sub):
        if "EX" in sub or sub == "EX Series":
            return "POP Toys EX Series"
        if sub == "Special":
            return "POP Toys Special"
        if sub == "Accessories":
            return "POP Toys Accessories"
        return f"POP Toys {sub}"
    rows += _simple(raw.get("poptoys", []), "pt9", "POP Toys", "poptoys",
                    '1:6', 190.0, "poptoys,historical,sixth-scale,curated", pt_line)

    # NEW: Devil Toys
    def dv_line(_n, sub):
        if sub == "Mini":
            return "Devil Toys Mini"
        if sub == "Special":
            return "Devil Toys Special"
        return f"Devil Toys {sub}"
    rows += _simple(raw.get("deviltoys", []), "dv9", "Devil Toys", "deviltoys",
                    '6"', 120.0, "deviltoys,designer,curated", dv_line)

    # NEW: King Arts
    def ka_line(_n, sub):
        if sub == "Diecast":
            return "King Arts Diecast"
        if sub == "Accessories":
            return "King Arts Accessories"
        return "King Arts Special"
    rows += _simple(raw.get("kingarts", []), "ka9", "King Arts", "kingarts",
                    '1:9', 280.0, "kingarts,diecast,curated", ka_line)

    # NEW: JT Studio
    def jts_line(_n, sub):
        if sub == "Special":
            return "JT Studio Special"
        if sub == "Accessories":
            return "JT Studio Accessories"
        return f"JT Studio {sub}"
    rows += _simple(raw.get("jtstudio", []), "jts9", "JT Studio", "jtstudio",
                    '1:6', 220.0, "jtstudio,sixth-scale,curated", jts_line)

    # NEW: Art Spirits
    def asp_line(_n, sub):
        if sub == "Sonic":
            return "Art Spirits Sonic"
        if sub == "Mecha":
            return "Art Spirits Mecha"
        if sub == "Tokusatsu":
            return "Art Spirits Tokusatsu"
        if sub == "Mini":
            return "Art Spirits Mini"
        if sub == "Accessories":
            return "Art Spirits Accessories"
        return "Art Spirits Special"
    rows += _simple(raw.get("artspirits", []), "asp9", "Art Spirits", "artspirits",
                    '6"', 95.0, "artspirits,sonic,mecha,curated", asp_line)

    # NEW: Art Storm
    def ast_line(_n, sub):
        if sub == "Mini":
            return "Art Storm Mini"
        if sub == "Special":
            return "Art Storm Special"
        if sub == "Accessories":
            return "Art Storm Accessories"
        return f"Art Storm {sub}"
    rows += _simple(raw.get("artstorm", []), "ast9", "Art Storm", "artstorm",
                    '6"', 100.0, "artstorm,mecha,curated", ast_line)

    # NEW: 52Toys
    def ft_line(_n, sub):
        if "BeastBOX" in sub or _n.startswith("BeastBOX") or _n.startswith("BB"):
            return "52Toys BeastBOX"
        if "MegaBOX" in sub or _n.startswith("MegaBOX") or _n.startswith("MB"):
            return "52Toys MegaBOX"
        if "Combiner" in sub:
            return "52Toys Combiner"
        if sub == "Mini":
            return "52Toys Mini"
        if sub == "Accessories":
            return "52Toys Accessories"
        return "52Toys Special"
    rows += _simple(raw.get("fiftytwo", []), "ft9", "52Toys BeastBOX", "fiftytwo",
                    '4"', 55.0, "52toys,beastbox,transformable,curated", ft_line)

    # NEW: Action Toys
    def at_line(_n, sub):
        if "ES Gokin" in sub or "ES Gokin" in _n:
            return "Action Toys ES Gokin"
        if "Mini Action" in sub or "Mini Action" in _n:
            return "Action Toys Mini Action"
        if "Hero Action" in sub or "Hero Action" in _n:
            return "Action Toys Hero Action"
        if "Combiner" in sub:
            return "Action Toys Combiner"
        if sub == "Accessories":
            return "Action Toys Accessories"
        return "Action Toys Special"
    rows += _simple(raw.get("actiontoys", []), "at9", "Action Toys", "actiontoys",
                    '6"', 110.0, "actiontoys,mecha,tokusatsu,curated", at_line)

    # NEW: Underverse
    def uv_line(_n, sub):
        if "Sci-Fi" in sub:
            return "Underverse 1/12 Sci-Fi"
        if "Fantasy" in sub:
            return "Underverse 1/12 Fantasy"
        if "Street" in sub:
            return "Underverse 1/12 Street"
        if sub == "Bodies":
            return "Underverse Bodies"
        if sub == "Accessories":
            return "Underverse Accessories"
        if sub == "Special":
            return "Underverse Special"
        return "Underverse 1/12"
    rows += _simple(raw.get("underverse", []), "uv9", "Underverse", "underverse",
                    '1:12', 55.0, "underverse,1-12,curated", uv_line)

    # Densify: NECA
    def nc_line(_n, sub):
        return f"NECA Ultimate {sub}" if sub != "Special" else "NECA Ultimate Special"
    rows += _simple(raw.get("neca", []), "nc9", "NECA Ultimate", "neca",
                    '7"', 35.0, "neca,ultimate,curated", nc_line)

    # Densify: Super7
    def s7_line(_n, sub):
        if "ReAction" in sub or _n.startswith("ReAction"):
            return "Super7 ReAction"
        if sub == "Special":
            return "Super7 Special"
        return "Super7 ULTIMATES!"
    rows += _simple(raw.get("super7", []), "s79", "Super7 ULTIMATES!", "super7",
                    '7"', 55.0, "super7,ultimates,reaction,curated", s7_line)

    # Densify: threezero
    def tz_line(_n, sub):
        if "FigZero" in sub or _n.startswith("FigZero"):
            return "threezero FigZero"
        if sub == "Accessories":
            return "threezero Accessories"
        if sub == "Special":
            return "threezero Special"
        return "threezero DLX"
    rows += _simple(raw.get("threezero", []), "tz9", "threezero DLX", "threezero",
                    '1:12', 180.0, "threezero,dlx,figzero,curated", tz_line)

    # Densify: Hot Toys
    def ht_line(_n, sub):
        if sub == "Special":
            return "Hot Toys Special"
        return "Hot Toys MMS"
    rows += _simple(raw.get("hottoys", []), "ht9", "Hot Toys MMS", "hottoys",
                    '1:6', 350.0, "hottoys,mms,sixth-scale,curated", ht_line)

    # Densify: Beast Kingdom
    def bk_line(_n, sub):
        if sub == "Accessories":
            return "Beast Kingdom Accessories"
        if sub == "Special":
            return "Beast Kingdom Special"
        return "Beast Kingdom DAH"
    rows += _simple(raw.get("beastkingdom", []), "bk9", "Beast Kingdom DAH", "beastkingdom",
                    '1:9', 150.0, "beast-kingdom,dah,curated", bk_line)

    # Densify: Enterbay
    def eb_line(_n, sub):
        if sub == "NBA":
            return "Enterbay NBA"
        if sub == "Movie":
            return "Enterbay Movie"
        if sub == "Accessories":
            return "Enterbay Accessories"
        return "Enterbay Special"
    rows += _simple(raw.get("enterbay", []), "eb9", "Enterbay", "enterbay",
                    '1:6', 280.0, "enterbay,nba,sixth-scale,curated", eb_line)

    # Densify: Four Horsemen
    def fh_line(_n, sub):
        if "Mythic" in sub:
            return "Mythic Legions"
        if "Cosmic" in sub:
            return "Cosmic Legions"
        if "Figura Obscura" in sub or "Figura Obscura" in _n:
            return "Figura Obscura"
        if sub == "Accessories":
            return "Four Horsemen Accessories"
        return "Four Horsemen Special"
    rows += _simple(raw.get("fourhorsemen", []), "fh9", "Mythic Legions", "fourhorsemen",
                    '6"', 45.0, "four-horsemen,mythic-legions,curated", fh_line)

    # Densify: Valaverse
    def vv_line(_n, sub):
        if sub == "Accessories":
            return "Valaverse Accessories"
        if sub == "Special":
            return "Valaverse Special"
        return "Valaverse Action Force"
    rows += _simple(raw.get("valaverse", []), "vv9", "Valaverse Action Force", "valaverse",
                    '1:12', 25.0, "valaverse,action-force,curated", vv_line)

    # Densify: Boss Fight
    def bf_line(_n, sub):
        if sub == "Accessories":
            return "Boss Fight Accessories"
        if sub == "Special":
            return "Boss Fight Special"
        return "Boss Fight H.A.C.K.S."
    rows += _simple(raw.get("bossfight", []), "bf9", "Boss Fight H.A.C.K.S.", "bossfight",
                    '4"', 20.0, "bossfight,hacks,curated", bf_line)

    # Densify: Loyal Subjects
    def ls_line(_n, sub):
        if sub == "Accessories":
            return "Loyal Subjects Accessories"
        if sub == "Special":
            return "Loyal Subjects Special"
        return "BST AXN"
    rows += _simple(raw.get("loyalsubjects", []), "ls9", "BST AXN", "loyalsubjects",
                    '5"', 20.0, "loyal-subjects,bst-axn,curated", ls_line)

    # Densify: Jada
    def jd_line(_n, sub):
        if "Street Fighter" in sub:
            return "Jada Street Fighter"
        if "Universal" in sub:
            return "Jada Universal Monsters"
        if sub == "DC":
            return "Jada DC"
        if sub == "Marvel":
            return "Jada Marvel"
        if sub == "Nano":
            return "Jada Nano Metalfigs"
        if sub == "Accessories":
            return "Jada Accessories"
        return "Jada Special"
    rows += _simple(raw.get("jada", []), "jd9", "Jada Toys", "jada",
                    '6"', 25.0, "jada,street-fighter,curated", jd_line)

    # Densify: Bandai
    def bn_line(_n, sub):
        if "Robot Spirits" in sub or _n.startswith("Robot Spirits"):
            return "Bandai Robot Spirits"
        if "Gundam Universe" in sub or _n.startswith("Gundam Universe"):
            return "Gundam Universe"
        if "G Frame" in sub or _n.startswith("G Frame"):
            return "Bandai G Frame"
        if "MSiA" in sub or _n.startswith("MSiA"):
            return "Bandai MSiA"
        if sub == "Accessories":
            return "Bandai Accessories"
        return "Bandai Special"
    rows += _simple(raw.get("bandai", []), "bn9", "Bandai Robot Spirits", "bandai",
                    '6"', 75.0, "bandai,robot-spirits,gundam,curated", bn_line)

    # Densify: Playmates
    def pm_line(_n, sub):
        if "Mutant Mayhem" in sub:
            return "Playmates Mutant Mayhem"
        if sub == "Tales":
            return "Playmates Tales of TMNT"
        if "Classic Collection" in sub:
            return "Playmates Classic Collection"
        if "Exo-Squad" in sub:
            return "Playmates Exo-Squad"
        if sub == "Accessories":
            return "Playmates Accessories"
        if sub == "Special":
            return "Playmates Special"
        return "Playmates TMNT Classic"
    rows += _simple(raw.get("playmates", []), "pm9", "Playmates TMNT", "playmates",
                    '5"', 8.0, "playmates,tmnt,curated", pm_line)

    # Densify: Mattel
    def mt_line(_n, sub):
        if "Masterverse" in sub or _n.startswith("Masterverse"):
            return "Mattel Masterverse"
        if "WWE Elite" in sub or _n.startswith("WWE Elite"):
            return "WWE Elite"
        if "WWE Ultimate" in sub or _n.startswith("WWE Ultimate"):
            return "WWE Ultimate Edition"
        if "Origins" in sub or _n.startswith("Origins"):
            return "MotU Origins"
        if sub == "Accessories":
            return "Mattel Accessories"
        return "Mattel Special"
    rows += _simple(raw.get("mattel", []), "mt9", "Mattel Masterverse", "mattel",
                    '7"', 22.99, "mattel,masterverse,wwe,curated", mt_line)

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append(r)
    return out

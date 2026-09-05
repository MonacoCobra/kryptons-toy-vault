#!/usr/bin/env python3
"""Generate comic-backlog batch-002: DC Batman family, modern → Oct 1986 floor.

Adds in priority order and stops near TARGET_MAX so modern flagship runs are not
trimmed away by a late cap pass.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/collection-app")
COMICS_TS = ROOT / "src/data/comics.ts"
BATCH001 = ROOT / "src/data/comic-backlog/batch-001.json"
OUT = ROOT / "src/data/comic-backlog/batch-002.json"
MANIFEST = ROOT / "src/data/comic-backlog/manifest.json"
PAL = "111827,eab308,1e3a8a"
PUB = "DC Comics"
FLOOR = "1986-10-01"
TARGET_MIN, TARGET_MAX = 450, 500

def parse_existing_ts():
    src = COMICS_TS.read_text()
    id_set, key_set = set(), set()
    for m in re.finditer(r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"', src):
        id_set.add(m.group(1))
        key_set.add(f"{m.group(2)}|{m.group(3)}|{m.group(4)}".lower())
    return id_set, key_set

def parse_batch001():
    data = json.loads(BATCH001.read_text())
    id_set, key_set = set(), set()
    for r in data["rows"]:
        id_set.add(r[0])
        key_set.add(f"{r[1]}|{r[2]}|{r[3]}".lower())
    return id_set, key_set

EXISTING_IDS, EXISTING_KEYS = parse_existing_ts()
B1_IDS, B1_KEYS = parse_batch001()
EXISTING_IDS |= B1_IDS
EXISTING_KEYS |= B1_KEYS

ARCHIVE_BATMAN_ISSUES = {k.split("|")[1] for k in EXISTING_KEYS if k.startswith("batman|") and k.endswith("|dc comics")}
ARCHIVE_DET_ISSUES = {k.split("|")[1] for k in EXISTING_KEYS if k.startswith("detective comics|") and k.endswith("|dc comics")}

skipped = []
rows = []
used_ids, used_keys = set(), set()

def add_months(y, m, n):
    m0 = y * 12 + (m - 1) + n
    return m0 // 12, m0 % 12 + 1

def cover(y, m, day=1):
    return f"{y:04d}-{m:02d}-{day:02d}"

def interp_date(n, n0, y0, m0, n1, y1, m1):
    if n1 == n0:
        return cover(y0, m0)
    t = (n - n0) / (n1 - n0)
    months0 = y0 * 12 + (m0 - 1)
    months1 = y1 * 12 + (m1 - 1)
    mid = int(round(months0 + t * (months1 - months0)))
    return cover(mid // 12, mid % 12 + 1)

def room(n=1):
    return len(rows) + n <= TARGET_MAX

def try_add(rid, series, issue, cover_date, writers, artists, desc, msrp,
            fmt="single", demand=0.6, key=0, palette=PAL, also_block_bare=None,
            force=False):
    issue = str(issue)
    skey = f"{series}|{issue}|{PUB}".lower()
    if not force and not room():
        skipped.append({"reason": "full", "id": rid, "series": series, "issue": issue})
        return False
    if rid in EXISTING_IDS or rid in used_ids:
        skipped.append({"reason": "id", "id": rid, "series": series, "issue": issue})
        return False
    if skey in EXISTING_KEYS:
        skipped.append({"reason": "archive-key", "id": rid, "series": series, "issue": issue})
        return False
    if also_block_bare:
        bare = f"{also_block_bare}|{issue}|{PUB}".lower()
        if bare in EXISTING_KEYS:
            skipped.append({"reason": "archive-bare", "id": rid, "series": series, "issue": issue})
            return False
    if skey in used_keys:
        skipped.append({"reason": "batch-key", "id": rid, "series": series, "issue": issue})
        return False
    if cover_date < FLOOR:
        skipped.append({"reason": "pre-floor", "id": rid, "series": series, "issue": issue, "date": cover_date})
        return False
    rows.append([
        rid, series, issue, PUB, cover_date, writers, artists, desc,
        float(msrp), fmt, float(demand), int(key), palette,
    ])
    used_ids.add(rid)
    used_keys.add(skey)
    return True

# =============================================================================
# PRIORITY 1 — Absolute + Batman (2025) + full Batman (2016)
# =============================================================================
abs_dates = {
    2:(2024,11),3:(2024,12),4:(2025,1),5:(2025,2),6:(2025,3),7:(2025,4),
    8:(2025,5),9:(2025,6),10:(2025,7),11:(2025,8),13:(2025,10),
    14:(2025,11),15:(2025,12),16:(2026,1),17:(2026,2),18:(2026,3),19:(2026,4),
    20:(2026,5),21:(2026,6),22:(2026,7),23:(2026,8),
}
abs_artists = {
    4: "Gabriel Hernández Walta", 7: "Marcos Martín", 8: "Marcos Martín",
    11: "Clay Mann", 15: "Jock", 17: "Eric Canete", 18: "Eric Canete",
    22: "Werther Dell'Edera",
}
abs_descs = {
    2: "Absolute Batman continues The Zoo.",
    7: "Abomination era; Absolute Bane enters.",
    15: "The Joker chapter of Absolute Batman.",
    19: "Scarecrow / Straw Man era begins.",
    23: "Absolute Batman year-two escalation.",
}
for n in sorted(abs_dates):
    y, m = abs_dates[n]
    try_add(f"dc-abs-batman-{n}", "Absolute Batman", n, cover(y, m),
            "Scott Snyder", abs_artists.get(n, "Nick Dragotta"),
            abs_descs.get(n, f"Absolute Universe Batman issue {n}."),
            4.99, demand=1.4 if n <= 6 else 1.0, key=1 if n in (2, 7, 15) else 0, force=True)
try_add("dc-abs-batman-annual-2025", "Absolute Batman 2025 Annual", "1", cover(2025, 10),
        "Scott Snyder", "Nick Dragotta",
        "Absolute Batman 2025 Annual — Absolute Zero / Mr. Freeze.", 5.99, demand=1.1, key=1, force=True)
try_add("dc-abs-batman-ark-m-1", "Absolute Batman: Ark M", "1", cover(2026, 1),
        "Scott Snyder", "Nick Dragotta", "Absolute Batman Ark M Special.", 5.99, demand=1.0, key=1, force=True)

for n in range(1, 14):
    y, m = add_months(2025, 9, n - 1)
    try_add(f"dc-batman-2025-{n}", "Batman (2025)", n, cover(y, m),
            "Matt Fraction", "Jorge Jiménez",
            ("Fraction/Jiménez Batman Vol. 4 begins. Daylight era." if n == 1
             else f"Batman (2025) by Matt Fraction, issue {n}."),
            4.99, demand=2.0 if n == 1 else 1.1, key=1 if n == 1 else 0, force=True)

def bat2016_credits(n):
    if n <= 85:
        return "Tom King", ("David Finch" if n <= 5 else ("Mikel Janín" if n <= 35 else "Various"))
    if n <= 116:
        return "James Tynion IV", "Jorge Jiménez" if n <= 105 else "Various"
    if n <= 124:
        return "Joshua Williamson", "Various"
    if n <= 157:
        return "Chip Zdarsky", ("Jorge Jiménez" if n in (125,126,127,128,129,130,135,145,146,147,148,150,153,154,157)
                                else "Various")
    return "Jeph Loeb", "Jim Lee"

bat2016_desc = {
    1: "Rebirth Batman begins. I Am Gotham.",
    14: "I Am Suicide arc.", 24: "The War of Jokes and Riddles begins.",
    50: "Cold Days. Tom King milestone.", 51: "The Wedding.",
    75: "City of Bane.", 86: "The Joker War begins (Tynion).",
    100: "Batman #100 anniversary issue.", 106: "Fear State begins.",
    125: "Zdarsky Batman begins. Failsafe.",
    135: "Batman #900 legacy commemorative (Dawn of DC).",
    145: "Dark Prisons era.", 153: "The Dying City.",
    159: "Hush 2 continues (Loeb/Lee).",
    163: "Batman (2016) Vol. 3 finale. Hush 2 concludes.",
}
for n in range(1, 164):
    if n == 158:
        skipped.append({"reason": "archive-known", "id": f"dc-batman-2016-{n}",
                        "series": "Batman (2016)", "issue": str(n)})
        continue
    cd = interp_date(n, 1, 2016, 8, 163, 2026, 7)
    w, a = bat2016_credits(n)
    msrp = 2.99 if n < 50 else (3.99 if n < 125 else 4.99)
    demand = 1.8 if n == 1 else (1.2 if n in (50, 51, 86, 100, 125, 135, 163) else 0.55)
    key = 1 if n in (1, 50, 51, 86, 100, 125, 135, 163) else 0
    try_add(f"dc-batman-2016-{n}", "Batman (2016)", n, cd, w, a,
            bat2016_desc.get(n, f"Batman (2016) issue {n}."),
            msrp, demand=demand, key=key, force=True)

for n, (y, m) in [(1,(2017,1)),(2,(2018,1)),(3,(2019,1)),(4,(2019,10)),(5,(2020,5))]:
    try_add(f"dc-batman-2016-annual-{n}", "Batman Annual (2016)", n, cover(y, m),
            "Tom King" if n <= 2 else "Various", "Various",
            f"Batman Rebirth Annual #{n}.", 4.99, demand=0.7, force=True)
try_add("dc-batman-2021-annual-1", "Batman 2021 Annual", "1", cover(2021, 9),
        "James Tynion IV", "Various", "Batman 2021 Annual.", 4.99, demand=0.7, force=True)
try_add("dc-batman-2022-annual-1", "Batman 2022 Annual", "1", cover(2022, 9),
        "Chip Zdarsky", "Various", "Batman 2022 Annual.", 4.99, demand=0.7, force=True)

print("P1", len(rows))  # ~205

# =============================================================================
# PRIORITY 2 — New 52 Batman + curated Detective Rebirth + B&R
# =============================================================================
# Batman (2011) #0, 3–52
for n in [0] + list(range(3, 53)):
    if n == 0:
        cd, w, a = cover(2012, 11), "Scott Snyder", "Greg Capullo"
        desc = "New 52 Batman #0. Court of Owls prologue beat."
    else:
        cd = interp_date(n, 3, 2012, 1, 52, 2016, 7)
        w, a = "Scott Snyder", "Greg Capullo"
        descs = {3: "Court of Owls continues.", 6: "Night of the Owls.",
                 13: "Death of the Family begins.", 21: "Zero Year begins.",
                 28: "Zero Year: Dark City.", 35: "Endgame begins. Joker returns.",
                 40: "Superheavy. Jim Gordon as Batman.",
                 52: "New 52 Batman finale. The List."}
        desc = descs.get(n, f"New 52 Batman (2011) issue {n}.")
    try_add(f"dc-batman-n52-{n}", "Batman (2011)", n, cd, w, a, desc,
            2.99 if n < 40 else 3.99,
            demand=1.5 if n in (0, 13, 21, 35) else 0.7,
            key=1 if n in (0, 6, 13, 21, 35, 40, 52) else 0, force=True)

# Detective Rebirth curated (~70): 934–980, 1001–1010, 1050, 1062–1066, 1100
det_issues = list(range(934, 961)) + list(range(1001, 1011)) + [1050] + list(range(1062, 1067)) + [1100]

def det_credits(n):
    if n <= 981:
        return "James Tynion IV", "Eddy Barrows" if n <= 946 else "Various"
    if n <= 1033:
        return "Peter J. Tomasi", "Various"
    if n <= 1060:
        return "Mariko Tamaki", "Various"
    if n < 1100:
        return "Ram V", "Rafael Albuquerque"
    return "Tom Taylor", "Mikel Janín"

det_desc = {
    934: "Rebirth Detective Comics resumes legacy numbering.",
    950: "A Lonely Place of Living. Tim Drake returns.",
    1001: "Post-#1000 Detective Comics continues.",
    1050: "Detective Comics #1050 milestone.",
    1062: "Ram V Gotham Nocturne begins.",
    1100: "Detective Comics #1100 anniversary.",
}
for n in det_issues:
    cd = interp_date(n, 934, 2016, 8, 1110, 2026, 8)
    w, a = det_credits(n)
    msrp = 2.99 if n < 1000 else (3.99 if n < 1060 else 4.99)
    key = 1 if n in (934, 950, 1001, 1050, 1062, 1100) else 0
    try_add(f"dc-det-{n}", "Detective Comics", n, cd, w, a,
            det_desc.get(n, f"Detective Comics legacy issue {n}."),
            msrp, demand=1.3 if n == 934 else (0.9 if key else 0.5), key=key, force=True)

# Batman and Robin (2011) #1–25 + 33 + 40 (trim mid)
for n in list(range(1, 19)) + [0, 33, 40]:
    cd = cover(2012, 11) if n == 0 else interp_date(max(n, 1), 1, 2011, 11, 40, 2015, 5)
    w, a = "Peter J. Tomasi", "Patrick Gleason"
    descs = {0: "New 52 Batman and Robin #0.",
             1: "New 52 Batman and Robin begins. Born to Kill.",
             33: "Robin Rises. Damian returns.",
             40: "Batman and Robin New 52 finale."}
    try_add(f"dc-batman-robin-n52-{n}", "Batman and Robin (2011)", n, cd, w, a,
            descs.get(n, f"New 52 Batman and Robin issue {n}."),
            2.99, demand=1.2 if n == 1 else (0.9 if n in (33, 40) else 0.55),
            key=1 if n in (1, 33, 40) else 0, force=True)

print("P2", len(rows))  # ~205+51+64+28 ≈ 348

# =============================================================================
# PRIORITY 3 — Landmarks (Long Halloween, Dark Victory, Hush, Morrison, floor)
# =============================================================================
lh_months = {2:(1997,1),3:(1997,2),4:(1997,3),5:(1997,4),6:(1997,5),7:(1997,6),
             8:(1997,7),9:(1997,8),10:(1997,9),11:(1997,10),12:(1997,11),13:(1997,12)}
for n, (y, m) in lh_months.items():
    try_add(f"dc-longhalloween-{n}", "Batman: The Long Halloween", n, cover(y, m),
            "Jeph Loeb", "Tim Sale",
            ("Long Halloween finale." if n == 13 else f"Batman: The Long Halloween issue {n}."),
            2.95, demand=1.5 if n == 13 else 1.0, key=1 if n == 13 else 0, force=True)

dv = {0:(2000,1),2:(2000,1),3:(2000,2),4:(2000,3),5:(2000,4),6:(2000,5),
      7:(2000,6),8:(2000,7),9:(2000,8),10:(2000,9),11:(2000,10),12:(2000,11),13:(2000,12)}
for n, (y, m) in dv.items():
    try_add(f"dc-darkvictory-{n}", "Batman: Dark Victory", n, cover(y, m),
            "Jeph Loeb", "Tim Sale",
            ("Dark Victory prologue." if n == 0 else
             ("Dark Victory finale." if n == 13 else f"Batman: Dark Victory issue {n}.")),
            2.50, demand=1.2 if n in (0, 13) else 0.8, key=1 if n in (0, 13) else 0, force=True)

for n in range(609, 620):
    cd = interp_date(n, 608, 2002, 12, 619, 2003, 11)
    try_add(f"dc-batman-{n}", "Batman", n, cd, "Jeph Loeb", "Jim Lee",
            f"Hush chapter. Batman #{n}.",
            2.25, demand=1.5 if n in (609, 619) else 1.0, key=1 if n in (609, 619) else 0, force=True)

# Morrison RIP core #656–663, 670–681
for n in list(range(656, 664)) + list(range(670, 682)):
    cd = interp_date(n, 655, 2006, 9, 681, 2008, 11)
    a = "Andy Kubert" if n <= 666 else "Tony Daniel"
    descs = {676: "Batman R.I.P. begins.", 681: "Batman R.I.P. concludes."}
    try_add(f"dc-batman-{n}", "Batman", n, cd, "Grant Morrison", a,
            descs.get(n, f"Morrison-era Batman #{n}."),
            2.99, demand=1.3 if n in (676, 681) else 0.7, key=1 if n in (676, 681) else 0, force=True)

# Knightfall + Death in Family + Year One middle + #400 floor
for n in list(range(492, 497)) + list(range(498, 505)):
    cd = interp_date(n, 492, 1993, 5, 504, 1994, 2)
    try_add(f"dc-batman-{n}", "Batman", n, cd, "Doug Moench",
            "Jim Aparo" if n <= 500 else "Various",
            ("Knightfall prelude." if n < 497 else f"Knightfall / Knightquest Batman #{n}."),
            1.25, demand=1.2 if n in (492, 500) else 0.6, key=1 if n in (492, 500) else 0, force=True)

for n, m in [(405, 3), (406, 4)]:
    try_add(f"dc-batman-{n}", "Batman", n, cover(1987, m),
            "Frank Miller", "David Mazzucchelli", f"Year One part {n - 403}.",
            0.75, demand=2.0, key=1, force=True)
for n in [426, 427, 429, 430]:
    cd = interp_date(n, 426, 1988, 10, 430, 1989, 2)
    try_add(f"dc-batman-{n}", "Batman", n, cd, "Jim Starlin", "Jim Aparo",
            ("A Death in the Family begins." if n == 426 else f"Death in the Family era, Batman #{n}."),
            1.00, demand=1.5 if n == 426 else 0.9, key=1 if n == 426 else 0, force=True)
for n, (y, m) in [(400,(1986,10)),(401,(1986,11)),(402,(1986,12)),(403,(1987,1))]:
    try_add(f"dc-batman-{n}", "Batman", n, cover(y, m),
            "Jim Starlin" if n >= 401 else "Doug Moench",
            "Jim Aparo" if n >= 401 else "Various",
            ("Batman #400 anniversary issue." if n == 400 else
             ("Ten Nights of the Beast begins." if n == 401 else f"Batman #{n}.")),
            0.75, demand=1.5 if n == 400 else 0.8, key=1 if n in (400, 401) else 0, force=True)

print("P3", len(rows))

# =============================================================================
# PRIORITY 4 — Family titles (breadth first, then depth fill)
# =============================================================================
# All-Star Batman #2–14
for n in range(2, 15):
    cd = interp_date(n, 1, 2016, 8, 14, 2017, 10)
    artists = "John Romita Jr." if n <= 5 else ("Declan Shalvey" if n <= 9 else "Various")
    try_add(f"dc-allstar-batman-{n}", "All-Star Batman", n, cd, "Scott Snyder", artists,
            f"All-Star Batman issue {n}.", 3.99, demand=0.8 if n <= 5 else 0.5)

# Nightwing (2016) core #1–20 + Taylor #78–87
for n in list(range(1, 21)) + list(range(78, 88)):
    if n <= 20:
        cd = interp_date(n, 1, 2016, 9, 20, 2017, 7)
        w, a = "Tim Seeley", "Javi Fernandez" if n <= 15 else "Various"
    else:
        cd = interp_date(n, 78, 2021, 3, 87, 2021, 12)
        w, a = "Tom Taylor", "Bruno Redondo"
    descs = {1: "Rebirth Nightwing begins. Better Than Batman.",
             78: "Tom Taylor / Bruno Redondo Nightwing begins.",
             87: "Leaping into the Light landmark."}
    try_add(f"dc-nightwing-2016-{n}", "Nightwing (2016)", n, cd, w, a,
            descs.get(n, f"Nightwing (2016) issue {n}."),
            2.99 if n < 50 else 3.99,
            demand=1.3 if n == 1 else (1.1 if n in (78, 87) else 0.5),
            key=1 if n in (1, 78, 87) else 0)

# Detective Comics (2011) #0–12
for n in [0] + list(range(1, 13)):
    if n == 0:
        cd, w, a = cover(2012, 11), "Tony S. Daniel", "Tony S. Daniel"
        desc = "New 52 Detective Comics #0."
    else:
        cd = interp_date(n, 1, 2011, 11, 12, 2012, 10)
        w, a = "Tony S. Daniel", "Tony S. Daniel"
        descs = {1: "New 52 Detective Comics #1. Faces of Death."}
        desc = descs.get(n, f"New 52 Detective Comics (2011) issue {n}.")
    try_add(f"dc-det-n52-{n}", "Detective Comics (2011)", n, cd, w, a, desc,
            2.99, demand=1.2 if n == 1 else 0.5, key=1 if n in (0, 1) else 0)

# Catwoman (2018) #1–12
for n in range(1, 13):
    cd = interp_date(n, 1, 2018, 9, 12, 2019, 8)
    try_add(f"dc-catwoman-2018-{n}", "Catwoman (2018)", n, cd,
            "Joëlle Jones", "Joëlle Jones" if n <= 12 else "Various",
            ("Catwoman (2018) relaunch by Joëlle Jones." if n == 1 else f"Catwoman (2018) issue {n}."),
            3.99, demand=1.1 if n == 1 else 0.45, key=1 if n == 1 else 0)

# Batgirl (2011) #1–10 + Burnside #35–38
for n in list(range(1, 11)) + list(range(35, 39)):
    cd = interp_date(n, 1, 2011, 11, 38, 2015, 3)
    if n < 35:
        w, a = ("Gail Simone", "Ardian Syaf" if n <= 6 else "Various")
    else:
        w, a = "Cameron Stewart, Brenden Fletcher", "Babs Tarr"
    try_add(f"dc-batgirl-n52-{n}", "Batgirl (2011)", n, cd, w, a,
            ("New 52 Batgirl begins." if n == 1 else
             ("Batgirl of Burnside era begins." if n == 35 else f"New 52 Batgirl issue {n}.")),
            2.99, demand=1.1 if n in (1, 35) else 0.45, key=1 if n in (1, 35) else 0)

# Shadow of the Bat #1–8, LOTDK #1–8, Robin #1–8
for n in range(1, 9):
    cd = interp_date(n, 1, 1992, 6, 8, 1993, 1)
    try_add(f"dc-shadow-bat-{n}", "Batman: Shadow of the Bat", n, cd,
            "Alan Grant", "Norm Breyfogle" if n <= 7 else "Various",
            ("Shadow of the Bat #1. The Last Arkham." if n == 1 else f"Shadow of the Bat #{n}."),
            1.25, demand=1.0 if n == 1 else 0.45, key=1 if n == 1 else 0)
for n in range(1, 9):
    cd = interp_date(n, 1, 1989, 11, 8, 1990, 6)
    try_add(f"dc-lotdk-{n}", "Batman: Legends of the Dark Knight", n, cd,
            "Various", "Various",
            ("Legends of the Dark Knight #1. Shaman begins." if n == 1 else f"Legends of the Dark Knight #{n}."),
            1.50 if n == 1 else 1.00, demand=1.3 if n == 1 else 0.45, key=1 if n == 1 else 0)
for n in range(1, 9):
    cd = interp_date(n, 1, 1993, 11, 8, 1994, 6)
    try_add(f"dc-robin-1993-{n}", "Robin (1993)", n, cd,
            "Chuck Dixon", "Tom Grummett",
            ("Robin ongoing begins. Tim Drake solo." if n == 1 else f"Robin (1993) #{n}."),
            1.25, demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0)

# Nightwing (2011) #1–8, Dark Knight #1–8, Gotham Central #2–8
for n in range(1, 9):
    cd = interp_date(n, 1, 2011, 11, 8, 2012, 6)
    try_add(f"dc-nightwing-n52-{n}", "Nightwing (2011)", n, cd,
            "Kyle Higgins", "Eddy Barrows" if n <= 7 else "Various",
            ("New 52 Nightwing begins." if n == 1 else f"New 52 Nightwing issue {n}."),
            2.99, demand=1.0 if n == 1 else 0.45, key=1 if n == 1 else 0)
for n in range(1, 9):
    cd = interp_date(n, 1, 2011, 11, 8, 2012, 6)
    try_add(f"dc-batman-tdk-n52-{n}", "Batman: The Dark Knight (2011)", n, cd,
            "David Finch", "David Finch",
            ("New 52 Batman: The Dark Knight begins." if n == 1 else f"Batman: The Dark Knight (2011) #{n}."),
            2.99, demand=1.0 if n == 1 else 0.45, key=1 if n == 1 else 0)
for n in range(2, 9):
    cd = interp_date(n, 1, 2003, 2, 8, 2003, 9)
    try_add(f"dc-gothamcentral-{n}", "Gotham Central", n, cd,
            "Ed Brubaker, Greg Rucka", "Michael Lark", f"Gotham Central #{n}.",
            2.50, demand=0.8)

# Batwoman #1–6, Catwoman N52 #1–6, Batman/Superman 2019 #1–6
for n in range(1, 7):
    cd = interp_date(n, 1, 2017, 5, 6, 2017, 10)
    try_add(f"dc-batwoman-2017-{n}", "Batwoman (2017)", n, cd,
            "Marguerite Bennett, James Tynion IV", "Various",
            ("Rebirth Batwoman begins." if n == 1 else f"Batwoman (2017) issue {n}."),
            2.99, demand=0.9 if n == 1 else 0.4, key=1 if n == 1 else 0)
for n in range(1, 7):
    cd = interp_date(n, 1, 2011, 11, 6, 2012, 4)
    try_add(f"dc-catwoman-n52-{n}", "Catwoman (2011)", n, cd,
            "Judd Winick", "Guillem March" if n <= 4 else "Various",
            ("New 52 Catwoman begins." if n == 1 else f"New 52 Catwoman issue {n}."),
            2.99, demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0)
for n in range(1, 7):
    cd = interp_date(n, 1, 2019, 11, 6, 2020, 4)
    try_add(f"dc-batman-superman-2019-{n}", "Batman/Superman (2019)", n, cd,
            "Joshua Williamson", "David Marquez",
            ("Batman/Superman (2019) begins." if n == 1 else f"Batman/Superman (2019) issue {n}."),
            3.99, demand=1.0 if n == 1 else 0.45, key=1 if n == 1 else 0)

# Detective Comics Oct 1986 floor fill
for n in list(range(568, 580)) + [600, 700]:
    if str(n) in ARCHIVE_DET_ISSUES:
        skipped.append({"reason": "archive-bare", "id": f"dc-det-{n}",
                        "series": "Detective Comics", "issue": str(n)})
        continue
    if n < 600:
        cd = interp_date(n, 568, 1986, 10, 579, 1987, 10)
    elif n == 600:
        cd = cover(1989, 5)
    else:
        cd = cover(1996, 8)
    descs = {568: "Detective Comics at Oct 1986 floor.",
             575: "Batman Year Two begins (Detective).",
             600: "Detective Comics #600 anniversary.",
             700: "Detective Comics #700."}
    try_add(f"dc-det-{n}", "Detective Comics", n, cd, "Various", "Various",
            descs.get(n, f"Detective Comics #{n}."),
            0.75 if n < 600 else 1.75,
            demand=0.9 if n in (568, 600, 700) else 0.4,
            key=1 if n in (568, 600, 700) else 0)

print("P4", len(rows))

# If still under TARGET_MIN, extend with more Nightwing Taylor / Detective N52 / Batman post-Crisis
if len(rows) < TARGET_MIN:
    for n in range(91, 111):
        if len(rows) >= TARGET_MIN:
            break
        cd = interp_date(n, 91, 2022, 4, 110, 2023, 11)
        try_add(f"dc-nightwing-2016-{n}", "Nightwing (2016)", n, cd,
                "Tom Taylor", "Bruno Redondo", f"Nightwing (2016) issue {n}.",
                3.99, demand=0.7, key=1 if n == 100 else 0)

if len(rows) < TARGET_MIN:
    for n in range(21, 35):
        if len(rows) >= TARGET_MIN:
            break
        cd = interp_date(n, 21, 2013, 8, 34, 2014, 10)
        w, a = "Francis Manapul, Brian Buccellato", "Francis Manapul" if n >= 27 else ("John Layman", "Jason Fabok")
        if n < 27:
            w, a = "John Layman", "Jason Fabok"
        try_add(f"dc-det-n52-{n}", "Detective Comics (2011)", n, cd, w, a,
                f"New 52 Detective Comics (2011) issue {n}.", 2.99, demand=0.45)

if len(rows) < TARGET_MIN:
    for n in range(408, 420):
        if len(rows) >= TARGET_MIN:
            break
        if str(n) in ARCHIVE_BATMAN_ISSUES:
            continue
        cd = interp_date(n, 408, 1987, 6, 419, 1988, 5)
        try_add(f"dc-batman-{n}", "Batman", n, cd, "Various", "Various",
                f"Post-Year One Batman #{n}.", 0.75, demand=0.45)

# Soft fill up toward 480–500 if still room
if len(rows) < 480:
    for n in range(26, 36):
        if len(rows) >= 480:
            break
        cd = interp_date(n, 26, 2014, 6, 35, 2015, 1)
        try_add(f"dc-batman-robin-n52-{n}", "Batman and Robin (2011)", n, cd,
                "Peter J. Tomasi", "Patrick Gleason",
                f"New 52 Batman and Robin issue {n}.", 2.99, demand=0.5)

if len(rows) < 480:
    for n in range(15, 26):
        if len(rows) >= 480:
            break
        cd = interp_date(n, 15, 2019, 11, 25, 2020, 9)
        try_add(f"dc-catwoman-2018-{n}", "Catwoman (2018)", n, cd,
                "Joëlle Jones", "Various", f"Catwoman (2018) issue {n}.",
                3.99, demand=0.4)

if len(rows) < 480:
    for n in range(11, 21):
        if len(rows) >= 480:
            break
        cd = interp_date(n, 11, 2012, 9, 20, 2013, 7)
        try_add(f"dc-batman-tdk-n52-{n}", "Batman: The Dark Knight (2011)", n, cd,
                "Gregg Hurwitz", "Various",
                f"Batman: The Dark Knight (2011) #{n}.", 2.99, demand=0.4)

if len(rows) < TARGET_MAX:
    for n in range(981, 1000):
        if len(rows) >= TARGET_MAX:
            break
        cd = interp_date(n, 981, 2018, 5, 999, 2019, 2)
        try_add(f"dc-det-{n}", "Detective Comics", n, cd,
                "James Tynion IV", "Various",
                f"Detective Comics legacy issue {n}.", 2.99, demand=0.5)

if len(rows) < TARGET_MAX:
    for n in range(13, 21):
        if len(rows) >= TARGET_MAX:
            break
        cd = interp_date(n, 13, 2012, 11, 20, 2013, 7)
        try_add(f"dc-nightwing-n52-{n}", "Nightwing (2011)", n, cd,
                "Kyle Higgins", "Various", f"New 52 Nightwing issue {n}.",
                2.99, demand=0.4)

print("FINAL_PRE_SORT", len(rows))

assert len(rows) <= TARGET_MAX + 5, f"overbuilt {len(rows)}"
# If slightly over due to force=True on P1-P3, trim only from lowest-priority non-keys
PRIORITY_SERIES = {
    "Absolute Batman", "Absolute Batman 2025 Annual", "Absolute Batman: Ark M",
    "Batman (2025)", "Batman (2016)", "Batman Annual (2016)", "Batman 2021 Annual",
    "Batman 2022 Annual", "Batman (2011)", "Detective Comics",
    "Batman and Robin (2011)", "Batman: The Long Halloween", "Batman: Dark Victory",
}
while len(rows) > TARGET_MAX:
    cands = [i for i, r in enumerate(rows)
             if r[1] not in PRIORITY_SERIES and r[11] == 0]
    if not cands:
        cands = [i for i, r in enumerate(rows) if r[11] == 0 and r[1] != "Batman (2016)"]
    if not cands:
        break
    # drop oldest among candidates (prefer keeping modern)
    drop_i = min(cands, key=lambda i: rows[i][4])
    skipped.append({"reason": "cap", "id": rows[drop_i][0],
                    "series": rows[drop_i][1], "issue": rows[drop_i][2]})
    rows.pop(drop_i)

rows.sort(key=lambda r: (r[4], r[1], int(re.sub(r"\D", "", str(r[2])) or 0)), reverse=True)

assert len(rows) >= TARGET_MIN, f"Only {len(rows)} rows (need ≥{TARGET_MIN})"
assert len(rows) <= TARGET_MAX, f"Too many rows {len(rows)}"
assert len({r[0] for r in rows}) == len(rows)
for r in rows:
    assert r[0] not in EXISTING_IDS
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", r[4])
    assert r[4] >= FLOOR, f"pre-floor {r}"
    assert r[9] in ("single", "facsimile", "tpb", "hardcover", "omnibus")
    assert r[3] == PUB

batch = {
    "id": "batch-002",
    "title": "DC Batman family — modern to Oct 1986",
    "created": "2026-09-05",
    "status": "queued",
    "focus": "Batman titles, modern → Oct 1986 floor",
    "rows": rows,
}
OUT.write_text(json.dumps(batch, indent=2) + "\n")
MANIFEST.write_text(json.dumps({
    "strategy": "inject-one-batch-every-~3-weeks-with-noteworthy-promotion",
    "targetBatchSize": [400, 500],
    "lastInjectedAt": None,
    "lastInjectedBatch": None,
    "queued": ["batch-001", "batch-002"],
    "injected": [],
}, indent=2) + "\n")

c = Counter(r[1] for r in rows)
dates = [r[4] for r in rows]
archive_skips = [s for s in skipped if s["reason"] in ("id", "archive-key", "archive-known", "archive-bare")]
print("FINAL_COUNT", len(rows))
print("DATE_RANGE", max(dates), "→", min(dates))
print("ARCHIVE_SKIPPED", len(archive_skips))
print("TOTAL_SKIPPED", len(skipped))
print("BREAKDOWN")
for k, v in c.most_common():
    print(f"  {k}: {v}")
must = [
    "Absolute Batman", "Batman (2025)", "Batman (2016)", "Batman (2011)",
    "Detective Comics", "Detective Comics (2011)", "Batman and Robin (2011)",
    "Nightwing (2016)", "All-Star Batman", "Batman: The Long Halloween",
    "Batman: Dark Victory", "Batman: Shadow of the Bat",
    "Batman: Legends of the Dark Knight", "Catwoman (2018)", "Batgirl (2011)",
    "Batman", "Robin (1993)",
]
for m in must:
    print(f"  HAS {m}: {c.get(m, 0)}")
print("PRE_1990", sum(1 for r in rows if r[4] < "1990-01-01"))
print("1990_2000", sum(1 for r in rows if "1990-01-01" <= r[4] < "2000-01-01"))
print("2000_2011", sum(1 for r in rows if "2000-01-01" <= r[4] < "2011-09-01"))
print("2011_2016", sum(1 for r in rows if "2011-09-01" <= r[4] < "2016-01-01"))
print("2016_PLUS", sum(1 for r in rows if r[4] >= "2016-01-01"))
Path("/tmp/batch-002-skipped.json").write_text(json.dumps(skipped, indent=2))
print("OK")

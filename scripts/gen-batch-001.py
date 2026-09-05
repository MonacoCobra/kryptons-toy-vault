#!/usr/bin/env python3
"""Generate comic-backlog batch-001: DC Superman family, modern → classic."""
from __future__ import annotations
import json, re
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/collection-app")
COMICS_TS = ROOT / "src/data/comics.ts"
OUT = ROOT / "src/data/comic-backlog/batch-001.json"
MANIFEST = ROOT / "src/data/comic-backlog/manifest.json"
PAL = "1e3a8a,e30613,ffd200"
PUB = "DC Comics"

def parse_existing():
    src = COMICS_TS.read_text()
    id_set, key_set = set(), set()
    for m in re.finditer(r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"', src):
        id_set.add(m.group(1))
        key_set.add(f"{m.group(2)}|{m.group(3)}|{m.group(4)}".lower())
    return id_set, key_set

EXISTING_IDS, EXISTING_KEYS = parse_existing()
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

def try_add(rid, series, issue, cover_date, writers, artists, desc, msrp,
            fmt="single", demand=0.6, key=0, palette=PAL):
    issue = str(issue)
    skey = f"{series}|{issue}|{PUB}".lower()
    if rid in EXISTING_IDS or rid in used_ids:
        skipped.append({"reason": "id", "id": rid, "series": series, "issue": issue})
        return False
    if skey in EXISTING_KEYS:
        skipped.append({"reason": "archive-key", "id": rid, "series": series, "issue": issue})
        return False
    if skey in used_keys:
        skipped.append({"reason": "batch-key", "id": rid, "series": series, "issue": issue})
        return False
    rows.append([
        rid, series, issue, PUB, cover_date, writers, artists, desc,
        float(msrp), fmt, float(demand), int(key), palette,
    ])
    used_ids.add(rid)
    used_keys.add(skey)
    return True

# =============================================================================
# TIER A — Complete modern runs (priority)
# =============================================================================

# Absolute Superman #2–23
abs_dates = {
    2:(2024,12),3:(2025,1),4:(2025,2),5:(2025,3),6:(2025,4),7:(2025,5),
    8:(2025,6),9:(2025,7),10:(2025,8),11:(2025,9),12:(2025,10),13:(2025,11),
    14:(2025,12),15:(2026,1),16:(2026,2),17:(2026,3),18:(2026,4),19:(2026,5),
    20:(2026,6),21:(2026,7),22:(2026,8),23:(2026,9),
}
for n in range(2, 24):
    y, m = abs_dates[n]
    artist = "Juan Ferreyra" if n >= 23 else "Rafa Sandoval"
    descs = {2:"Absolute Superman continues Last Dust of Krypton.",
             7:"Son of the Demon arc begins.",
             15:"The Neverending Begins arc.",
             23:"Superman confronts Absolute Toyman while hunting Brainiac."}
    try_add(f"dc-abs-superman-{n}", "Absolute Superman", n, cover(y, m),
            "Jason Aaron", artist, descs.get(n, f"Absolute Universe Superman issue {n}."),
            4.99, demand=1.2 if n <= 6 else 0.9, key=1 if n in (2, 7, 15) else 0)

# Superman (2023) #1–42 + Annual
for n in range(1, 43):
    if n <= 5:
        cd = cover(2023, 3 + n)
        artists = "Jamal Campbell"
    else:
        cd = interp_date(n, 6, 2023, 11, 42, 2026, 9)
        artists = "Gleb Melnikov" if n <= 12 else "Various"
    descs = {1:"Dawn of DC Superman #1. Supercorp era begins.",
             6:"The Chained arc begins.",
             16:"House of Brainiac / Dark Path era.",
             25:"Rise of the Superwoman era.",
             28:"Legion of Darkseid arc."}
    try_add(f"dc-superman-2023-{n}", "Superman (2023)", n, cd,
            "Joshua Williamson", artists,
            descs.get(n, f"Superman (2023) by Joshua Williamson, issue {n}."),
            4.99, demand=1.5 if n == 1 else (0.9 if n <= 12 else 0.7), key=1 if n == 1 else 0)
try_add("dc-superman-2023-annual-1", "Superman 2023 Annual", "1", cover(2023, 9),
        "Joshua Williamson", "Jamal Campbell",
        "Superman 2023 Annual bridging Supercorp and The Chained.", 5.99, demand=0.8)

# Action Comics legacy #957–1087 (skip archived 1000, 1050; 1088 not in range)
def action_date(n):
    anchors = [(957,2016,8),(1000,2018,6),(1001,2018,9),(1050,2023,2),(1051,2023,3),(1088,2026,9)]
    for i in range(len(anchors)-1):
        n0,y0,m0 = anchors[i]; n1,y1,m1 = anchors[i+1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(2026, 9)

for n in range(957, 1088):
    if n in (1000, 1050):
        skipped.append({"reason": "archive-known", "id": f"dc-action-{n}", "series": "Action Comics", "issue": str(n)})
        continue
    if n <= 999:
        writers, artists, msrp = "Dan Jurgens", "Various", (2.99 if n < 980 else 3.99)
        key = 1 if n in (957, 975, 985) else 0
        descs = {957:"DC Rebirth Action Comics resumes legacy numbering.",
                 975:"Superman Reborn crossover chapter.", 985:"The Oz Effect begins."}
        desc = descs.get(n, f"Action Comics Rebirth era, issue {n}.")
        demand = 1.0 if n == 957 else 0.55
    elif n <= 1028:
        writers = "Brian Michael Bendis"
        artists = "Patrick Gleason" if n <= 1011 else "Various"
        msrp, demand, key = 3.99, (0.85 if n == 1001 else 0.55), (1 if n == 1001 else 0)
        desc = ("Bendis Action Comics Invisible Mafia era begins." if n == 1001
                else f"Action Comics Bendis run, issue {n}.")
    else:
        writers, artists = "Phillip Kennedy Johnson", "Various"
        msrp = 3.99 if n < 1051 else 4.99
        key = 1 if n in (1030, 1051) else 0
        demand = 0.75 if key else 0.55
        descs = {1030:"Warworld Saga begins.",
                 1051:"Post-Warworld Action Comics; Super-Family anthology format."}
        desc = descs.get(n, f"Action Comics PKJ era, issue {n}.")
    try_add(f"dc-action-{n}", "Action Comics", n, action_date(n),
            writers, artists, desc, msrp, demand=demand, key=key)

# Superman (2018) #1–32
for n in range(1, 33):
    cd = interp_date(n, 1, 2018, 9, 32, 2021, 8)
    writers = "Brian Michael Bendis" if n <= 28 else "Phillip Kennedy Johnson"
    artists = ("Ivan Reis, Joe Prado" if n <= 16 else ("John Timms" if n >= 30 else "Various"))
    descs = {1:"Bendis Superman Vol. 5 begins. The Unity Saga.",
             7:"Unity Saga: The House of El.", 18:"The Truth arc.",
             25:"Mythological arc begins.", 30:"The One Who Fell."}
    try_add(f"dc-superman-2018-{n}", "Superman (2018)", n, cd, writers, artists,
            descs.get(n, f"Superman (2018) issue {n}."),
            3.99, demand=1.3 if n == 1 else 0.6, key=1 if n == 1 else 0)

# Son of Kal-El #1–18 + Annual
for n in range(1, 19):
    cd = interp_date(n, 1, 2021, 9, 18, 2022, 12)
    try_add(f"dc-son-of-kal-el-{n}", "Superman: Son of Kal-El", n, cd,
            "Tom Taylor", "John Timms",
            ("Jon Kent takes up the Superman mantle." if n == 1 else f"Superman: Son of Kal-El issue {n}."),
            3.99, demand=1.4 if n == 1 else (1.1 if n == 5 else 0.7), key=1 if n in (1, 5) else 0)
try_add("dc-son-of-kal-el-annual-1", "Superman: Son of Kal-El Annual", "1", cover(2022, 5),
        "Tom Taylor", "Cian Tormey", "Son of Kal-El Annual.", 4.99, demand=0.7)

# Superman (2016) Rebirth #1–45 + one-shot + Annual
try_add("dc-superman-rebirth-1", "Superman: Rebirth", "1", cover(2016, 8),
        "Peter J. Tomasi, Patrick Gleason", "Doug Mahnke",
        "Rebirth one-shot launching Tomasi/Gleason Superman.", 2.99, demand=1.4, key=1)
for n in range(1, 46):
    cd = interp_date(n, 1, 2016, 8, 45, 2018, 4)
    if n == 26: writers = "Michael Moreci"
    elif n in (29, 30): writers = "Keith Champagne"
    elif n in (31, 32): writers = "James Bonny"
    elif n in (40, 41): writers = "James Robinson"
    else: writers = "Peter J. Tomasi, Patrick Gleason"
    if n in (1,2,4,10,11,18,19,20,21,24,25,42,43,45): artists = "Patrick Gleason"
    elif n in (5,6,8,9,12,13,22,23,29,33,36,40,44): artists = "Doug Mahnke"
    else: artists = "Various"
    descs = {1:"Son of Superman. Rebirth Superman ongoing begins.",
             18:"Superman Reborn crossover.",
             34:"Legacy Superman #800 commemorative issue.",
             42:"Bizarroverse arc begins."}
    try_add(f"dc-superman-2016-{n}", "Superman (2016)", n, cd, writers, artists,
            descs.get(n, f"Superman Rebirth (Vol. 4) issue {n}."),
            2.99 if n < 34 else 3.99,
            demand=1.2 if n == 1 else (0.9 if n in (18, 19) else 0.55),
            key=1 if n in (1, 18, 34) else 0)
try_add("dc-superman-2016-annual-1", "Superman Annual (2016)", "1", cover(2017, 1),
        "Peter J. Tomasi, Patrick Gleason", "Various",
        "Superman Rebirth Annual (Vol. 4).", 4.99, demand=0.6)

print("TIER_A", len(rows))

# =============================================================================
# TIER B — New 52 complete Superman + Action
# =============================================================================
for n in [0] + list(range(1, 53)):
    if n == 0:
        cd, writers, artists = cover(2012, 11), "Grant Morrison", "Ben Oliver"
        desc = "New 52 Action Comics #0. Young Clark origin beat."
    else:
        cd = interp_date(n, 1, 2011, 11, 52, 2016, 7)
        if 1 <= n <= 18: writers, artists = "Grant Morrison", "Rags Morales"
        elif 19 <= n <= 24: writers, artists = "Grant Morrison", "Various"
        elif 25 <= n <= 29: writers, artists = "Andy Diggle, Scott Lobdell", "Various"
        elif 30 <= n <= 40: writers, artists = "Greg Pak", "Various"
        else: writers, artists = "Various", "Various"
        descs = {1:"New 52 Action Comics #1. Morrison year-one Superman.",
                 9:"Hybrid / Brainiac era landmark.",
                 30:"Superman: Doomed crossover.",
                 51:"Final Days of Superman."}
        desc = descs.get(n, f"New 52 Action Comics (Vol. 2) issue {n}.")
    try_add(f"dc-action-n52-{n}", "Action Comics (2011)", n, cd, writers, artists, desc,
            2.99 if n < 40 else 3.99,
            demand=1.6 if n == 1 else (0.9 if n in (0, 9, 30) else 0.5),
            key=1 if n in (0, 1, 9, 30, 51) else 0)

for n in [0] + list(range(2, 53)):  # skip #1 archived
    if n == 0:
        cd, writers, artists = cover(2012, 11), "Scott Lobdell", "Kenneth Rocafort"
        desc = "New 52 Superman #0."
    else:
        cd = interp_date(n, 2, 2011, 12, 52, 2016, 7)
        if n <= 6: writers, artists = "George Pérez", "George Pérez"
        elif n <= 12: writers, artists = "Dan Jurgens", "Dan Jurgens"
        elif n <= 17: writers, artists = "Scott Lobdell", "Kenneth Rocafort"
        elif 32 <= n <= 39: writers, artists = "Geoff Johns", "John Romita Jr."
        elif n >= 40: writers, artists = "Gene Luen Yang", "Various"
        else: writers, artists = "Various", "Various"
        descs = {13:"H'el on Earth crossover.",
                 32:"Johns/Romita Jr. Men of Tomorrow begins.",
                 51:"Final Days of Superman."}
        desc = descs.get(n, f"New 52 Superman (Vol. 3) issue {n}.")
    try_add(f"dc-superman-n52-{n}", "Superman (2011)", n, cd, writers, artists, desc, 2.99,
            demand=0.8 if n in (0, 13, 32) else 0.5, key=1 if n in (0, 32, 51) else 0)

print("TIER_B", len(rows))

# =============================================================================
# TIER C — Landmark minis & All-Star (must keep)
# =============================================================================
allstar = {2:(2006,4),3:(2006,8),4:(2007,1),5:(2007,7),6:(2007,11),
           7:(2008,4),8:(2008,8),9:(2008,12),10:(2009,3),11:(2009,7),12:(2010,8)}
for n in range(2, 13):
    y, m = allstar[n]
    try_add(f"dc-allstar-supes-{n}", "All-Star Superman", n, cover(y, m),
            "Grant Morrison", "Frank Quitely",
            ("All-Star Superman finale." if n == 12 else "Morrison/Quitely All-Star Superman continues."),
            2.99, demand=2.0 if n == 12 else 1.5, key=1 if n in (10, 12) else 0)

unchained = {1:(2013,8),2:(2013,9),3:(2013,12),4:(2014,3),5:(2014,7),
             6:(2014,11),7:(2015,1),8:(2015,4),9:(2015,12)}
for n,(y,m) in unchained.items():
    try_add(f"dc-superman-unchained-{n}", "Superman: Unchained", n, cover(y, m),
            "Scott Snyder", "Jim Lee",
            ("Snyder/Lee Superman Unchained begins." if n == 1 else f"Superman: Unchained issue {n}."),
            3.99, demand=1.3 if n == 1 else 0.7, key=1 if n == 1 else 0)

for n in range(1, 7):
    y, m = add_months(2009, 11, n - 1)
    try_add(f"dc-superman-secret-origin-{n}", "Superman: Secret Origin", n, cover(y, m),
            "Geoff Johns", "Gary Frank",
            ("Johns/Frank modern origin retelling." if n == 1 else f"Superman: Secret Origin issue {n}."),
            3.99, demand=1.2 if n == 1 else 0.7, key=1 if n == 1 else 0)

for n in range(1, 13):
    y, m = add_months(2003, 9, n - 1)
    try_add(f"dc-superman-birthright-{n}", "Superman: Birthright", n, cover(y, m),
            "Mark Waid", "Leinil Francis Yu",
            ("Waid/Yu Superman origin maxiseries begins." if n == 1 else f"Superman: Birthright issue {n}."),
            2.99, demand=1.1 if n == 1 else 0.65, key=1 if n == 1 else 0)

for n, month in enumerate([9, 10, 11, 12], 1):
    season = ["Spring", "Summer", "Fall", "Winter"][n - 1]
    try_add(f"dc-superman-for-all-seasons-{n}", "Superman for All Seasons", n, cover(1998, month),
            "Jeph Loeb", "Tim Sale", f"Loeb/Sale origin tale — {season}.",
            2.95, demand=1.8 if n == 1 else 1.2, key=1 if n == 1 else 0)

for n, month in enumerate([6, 7, 8], 1):
    try_add(f"dc-superman-red-son-{n}", "Superman: Red Son", n, cover(2003, month),
            "Mark Millar", "Dave Johnson, Killian Plunkett",
            ("Elseworlds: Superman lands in the Soviet Union." if n == 1 else f"Superman: Red Son issue {n}."),
            5.95, demand=2.5 if n == 1 else 1.5, key=1)

mos = {1:(1986,10),2:(1986,10),3:(1986,11),4:(1986,11),5:(1986,12),6:(1986,12)}
for n,(y,m) in mos.items():
    try_add(f"dc-man-of-steel-{n}", "The Man of Steel", n, cover(y, m),
            "John Byrne", "John Byrne",
            ("Byrne post-Crisis Superman reboot begins." if n == 1 else f"The Man of Steel issue {n}."),
            0.75, demand=3.0 if n == 1 else 1.5, key=1 if n in (1, 6) else 0)

print("TIER_C", len(rows))

# =============================================================================
# TIER D — Superman/Batman (full or partial to fill target)
# =============================================================================
def sb_credits(n):
    if n <= 6: return "Jeph Loeb", "Ed McGuinness"
    if n == 7: return "Jeph Loeb", "Pat Lee"
    if 8 <= n <= 13: return "Jeph Loeb", "Michael Turner"
    if 14 <= n <= 18: return "Jeph Loeb", "Carlos Pacheco"
    if 19 <= n <= 25: return "Jeph Loeb", "Ed McGuinness"
    if n <= 36: return "Mark Verheiden", "Various"
    if n <= 42: return "Alan Burnett", "Various"
    if 44 <= n <= 56 or 60 <= n <= 63: return "Michael Green, Mike Johnson", "Shane Davis" if n <= 49 else "Various"
    return "Various", "Various"

sb_desc = {1:"Public Enemies. World's Finest ongoing begins.",
           8:"The Supergirl from Krypton. Kara Zor-El returns.",
           14:"Absolute Power arc.", 50:"Superman/Batman #50 anniversary.",
           87:"Series finale. The Secret concludes."}
# Cap so Tier C landmarks are not trimmed away (Tier C ~447 → +53 = 500)
for n in range(1, 54):
    cd = interp_date(n, 1, 2003, 10, 87, 2011, 10)
    w, a = sb_credits(n)
    try_add(f"dc-superman-batman-{n}", "Superman/Batman", n, cd, w, a,
            sb_desc.get(n, f"Superman/Batman issue {n}."),
            2.25 if n < 20 else (2.99 if n < 50 else 3.99),
            demand=2.0 if n in (1, 8) else (1.0 if n in (14, 50) else 0.55),
            key=1 if n in (1, 8, 50) else 0)

print("TIER_D", len(rows))

# =============================================================================
# TIER E — Fill to 450–500 with related family / post-Crisis landmarks
# =============================================================================
TARGET_MIN, TARGET_MAX = 450, 500

# Death of Superman triangle essentials from Adventures / Man of Steel ongoing
triangle = [
    ("dc-adv-superman-497", "Adventures of Superman", "497", "1993-01-01", "Various", "Various",
     "Doomsday! Death of Superman triangle chapter.", 1.25, 2.5, 1),
    ("dc-adv-superman-500", "Adventures of Superman", "500", "1993-06-01", "Various", "Various",
     "Adventures of Superman #500. Funeral for a Friend era.", 1.50, 2.0, 1),
    ("dc-man-of-steel-ong-1", "Superman: The Man of Steel", "1", "1991-07-01", "Louise Simonson", "Jon Bogdanove",
     "Superman: The Man of Steel #1. Triangle-era fourth ongoing begins.", 1.00, 1.2, 1),
    ("dc-man-of-steel-ong-18", "Superman: The Man of Steel", "18", "1992-12-01", "Louise Simonson", "Jon Bogdanove",
     "Doomsday! Death of Superman triangle chapter.", 1.25, 3.0, 1),
    ("dc-man-of-steel-ong-22", "Superman: The Man of Steel", "22", "1993-06-01", "Louise Simonson", "Jon Bogdanove",
     "Reign of the Supermen begins (Steel).", 1.50, 1.5, 1),
    ("dc-superman-v2-82", "Superman (1987)", "82", "1993-10-01", "Dan Jurgens", "Dan Jurgens",
     "Reign of the Supermen — Eradicator.", 1.50, 1.5, 1),
    ("dc-superman-v2-1", "Superman (1987)", "1", "1987-01-01", "John Byrne", "John Byrne",
     "Post-Crisis Superman Vol. 2 #1 by John Byrne.", 0.75, 2.0, 1),
    ("dc-adv-superman-424", "Adventures of Superman", "424", "1987-01-01", "John Byrne", "Various",
     "Title becomes Adventures of Superman (continues from Superman #423).", 0.75, 1.0, 1),
    ("dc-action-583", "Action Comics", "583", "1986-09-01", "John Byrne", "John Byrne",
     "Post-Crisis Action Comics begins Byrne era.", 0.75, 1.5, 1),
    ("dc-action-687", "Action Comics", "687", "1993-03-01", "Various", "Various",
     "Doomsday Death of Superman triangle chapter.", 1.25, 2.0, 1),
    ("dc-action-690", "Action Comics", "690", "1993-06-01", "Various", "Various",
     "Reign of the Supermen begins.", 1.50, 1.5, 1),
]
for rid, series, issue, cd, w, a, desc, msrp, demand, key in triangle:
    if len(rows) >= TARGET_MAX:
        break
    try_add(rid, series, issue, cd, w, a, desc, msrp, demand=demand, key=key)

# Supergirl Rebirth #1–20 (partial)
for n in range(1, 21):
    if len(rows) >= TARGET_MAX:
        break
    cd = interp_date(n, 1, 2016, 10, 20, 2018, 5)
    try_add(f"dc-supergirl-2016-{n}", "Supergirl (2016)", n, cd,
            "Steve Orlando", "Brian Ching" if n <= 8 else "Various",
            ("Rebirth Supergirl ongoing begins." if n == 1 else f"Supergirl Rebirth issue {n}."),
            2.99, demand=1.0 if n == 1 else 0.5, key=1 if n == 1 else 0)

# Superboy New 52 #1–15
for n in range(1, 16):
    if len(rows) >= TARGET_MAX:
        break
    cd = interp_date(n, 1, 2011, 11, 15, 2013, 1)
    try_add(f"dc-superboy-n52-{n}", "Superboy (2011)", n, cd,
            "Scott Lobdell", "R.B. Silva" if n <= 12 else "Various",
            ("New 52 Superboy begins." if n == 1 else f"New 52 Superboy issue {n}."),
            2.99, demand=0.9 if n == 1 else 0.45, key=1 if n == 1 else 0)

# Batman/Superman New 52 #1–15
for n in range(1, 16):
    if len(rows) >= TARGET_MAX:
        break
    cd = interp_date(n, 1, 2013, 8, 15, 2014, 10)
    try_add(f"dc-batman-superman-n52-{n}", "Batman/Superman (2013)", n, cd,
            "Greg Pak", "Jae Lee" if n <= 4 else "Various",
            ("New 52 Batman/Superman begins. Cross World." if n == 1 else f"Batman/Superman (New 52) issue {n}."),
            2.99, demand=1.0 if n == 1 else 0.5, key=1 if n == 1 else 0)

# Superman/Wonder Woman #1–12
for n in range(1, 13):
    if len(rows) >= TARGET_MAX:
        break
    cd = interp_date(n, 1, 2013, 12, 12, 2014, 11)
    try_add(f"dc-superman-ww-{n}", "Superman/Wonder Woman", n, cd,
            "Charles Soule", "Tony S. Daniel" if n <= 6 else "Various",
            ("Superman/Wonder Woman ongoing begins." if n == 1 else f"Superman/Wonder Woman issue {n}."),
            2.99, demand=0.9 if n == 1 else 0.45, key=1 if n == 1 else 0)


# More Adventures of Superman early Byrne/post-Crisis if still under min
for n in range(425, 450):
    if len(rows) >= TARGET_MAX:
        break
    cd = interp_date(n, 424, 1987, 1, 450, 1989, 3)
    try_add(f"dc-adv-superman-{n}", "Adventures of Superman", n, cd,
            "Various", "Various", f"Adventures of Superman issue {n}.",
            0.75, demand=0.4)

# Man of Steel ongoing more if needed
for n in list(range(2, 18)) + list(range(19, 22)) + list(range(23, 36)):
    if len(rows) >= TARGET_MAX:
        break
    cd = interp_date(n, 1, 1991, 7, 35, 1994, 5)
    try_add(f"dc-man-of-steel-ong-{n}", "Superman: The Man of Steel", n, cd,
            "Louise Simonson" if n <= 20 else "Various",
            "Jon Bogdanove" if n <= 20 else "Various",
            f"Superman: The Man of Steel issue {n}.",
            1.00 if n < 20 else 1.50, demand=0.4)

print("TIER_E", len(rows))

# If slightly over, drop highest Superman/Batman issue numbers first (preserve landmarks)
while len(rows) > TARGET_MAX:
    sb = [i for i,r in enumerate(rows) if r[1]=="Superman/Batman"]
    if not sb:
        break
    # drop highest issue
    drop_i = max(sb, key=lambda i: int(rows[i][2]))
    skipped.append({"reason":"cap", "id": rows[drop_i][0], "series": rows[drop_i][1], "issue": rows[drop_i][2]})
    rows.pop(drop_i)

# Sort newest → oldest for modern-first presentation in file
rows.sort(key=lambda r: (r[4], r[1], int(re.sub(r"\D", "", r[2]) or 0)), reverse=True)
assert len(rows) >= TARGET_MIN, f"Only {len(rows)} rows (need ≥{TARGET_MIN})"
assert len(rows) <= TARGET_MAX, f"Too many rows {len(rows)}"

# Validate
assert len({r[0] for r in rows}) == len(rows)
for r in rows:
    assert r[0] not in EXISTING_IDS
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", r[4])
    assert r[9] in ("single", "facsimile", "tpb", "hardcover", "omnibus")

batch = {
    "id": "batch-001",
    "title": "DC Superman family — modern to classic",
    "created": "2026-09-05",
    "status": "queued",
    "focus": "Superman titles, modern → older",
    "rows": rows,
}
OUT.write_text(json.dumps(batch, indent=2) + "\n")
MANIFEST.write_text(json.dumps({
    "strategy": "inject-one-batch-every-~3-weeks-with-noteworthy-promotion",
    "targetBatchSize": [400, 500],
    "lastInjectedAt": None,
    "lastInjectedBatch": None,
    "queued": ["batch-001"],
    "injected": [],
}, indent=2) + "\n")

c = Counter(r[1] for r in rows)
dates = [r[4] for r in rows]
archive_skips = [s for s in skipped if s["reason"] in ("id", "archive-key", "archive-known")]
print("FINAL_COUNT", len(rows))
print("DATE_RANGE", max(dates), "→", min(dates))
print("ARCHIVE_SKIPPED", len(archive_skips))
print("BREAKDOWN")
for k, v in c.most_common():
    print(f"  {k}: {v}")
# Must-have series presence checks
must = ["Absolute Superman", "Superman (2023)", "Action Comics", "Superman (2018)",
        "Superman (2016)", "All-Star Superman", "Superman: Birthright", "Superman: Red Son",
        "Superman for All Seasons", "Superman: Unchained", "Superman: Secret Origin",
        "The Man of Steel", "Superman/Batman", "Action Comics (2011)", "Superman (2011)"]
for m in must:
    print(f"  HAS {m}: {c.get(m, 0)}")
Path("/tmp/batch-001-skipped.json").write_text(json.dumps(skipped, indent=2))
print("OK")

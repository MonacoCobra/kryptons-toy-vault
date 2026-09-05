#!/usr/bin/env python3
"""Generate comic-backlog batch-004: Marvel Spider-Man family, modern → Oct 1986 floor."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comic_backlog_common import (
    BatchBuilder, load_blocklists, cover, interp_date, add_months, BACKLOG,
)

PUB = "Marvel Comics"
PAL = "111827,166534,dc2626"
TARGET_MIN, TARGET_MAX = 450, 500

EXISTING_IDS, EXISTING_KEYS = load_blocklists(("batch-003.json",))
b = BatchBuilder(PUB, PAL, EXISTING_IDS, EXISTING_KEYS, TARGET_MIN, TARGET_MAX)

ARCHIVE_ASM = {k.split("|")[1] for k in EXISTING_KEYS
               if k.startswith("the amazing spider-man|") and k.endswith("|marvel comics")}
ARCHIVE_SSM = {k.split("|")[1] for k in EXISTING_KEYS
               if k.startswith("the spectacular spider-man|") and k.endswith("|marvel comics")}

def add(rid, series, issue, cd, w, a, desc, msrp, demand=0.55, key=0, force=False, bare=None):
    return b.try_add(rid, series, issue, cd, w, a, desc, msrp,
                     demand=demand, key=key, force=force, also_block_bare=bare)

# =============================================================================
# P1 — Modern flagships (force)
# =============================================================================
# Amazing Spider-Man (2022) #2–70 (skip archived #1 under bare The Amazing Spider-Man)
for n in range(2, 71):
    cd = interp_date(n, 1, 2022, 4, 70, 2025, 3)
    if n <= 18 or (21 <= n <= 60):
        w = "Zeb Wells"
    elif n in (19, 20) or n >= 61:
        w = "Joe Kelly"
    else:
        w = "Zeb Wells"
    if n <= 5 or n in (7, 8) or 11 <= n <= 13 or 21 <= n <= 26 or n in (31, 39, 40, 41, 42, 43, 44, 49) or 56 <= n <= 59:
        a = "John Romita Jr."
    elif n in (6, 15, 16, 17, 18) or 27 <= n <= 30 or 36 <= n <= 38 or 50 <= n <= 54 or n in (61, 62, 69, 70):
        a = "Ed McGuinness"
    else:
        a = "Various"
    add(f"mv-asm-2022-{n}", "Amazing Spider-Man (2022)", n, cd, w, a,
        ({2: "Amazing Spider-Man (2022) continues Wells/JRJr era.",
          26: "Dead Language climax.",
          31: "Gang War lead-in.",
          50: "Amazing Spider-Man (2022) #50.",
          61: "Eight Deaths of Spider-Man begins (Kelly).",
          70: "Amazing Spider-Man (2022) finale."}.get(n, f"Amazing Spider-Man (2022) issue {n}.")),
        4.99, demand=1.5 if n in (26, 50, 61, 70) else 0.9,
        key=1 if n in (26, 50, 61, 70) else 0, force=True,
        bare="The Amazing Spider-Man")

# Ultimate Spider-Man (2024) #2–17 (skip #1 and #18 archived)
for n in range(2, 18):
    cd = interp_date(n, 1, 2024, 1, 18, 2026, 9)
    add(f"mv-ult-spidey-2024-{n}", "Ultimate Spider-Man (2024)", n, cd,
        "Jonathan Hickman", "Marco Checchetto",
        f"Ultimate Spider-Man (2024) Hickman/Checchetto issue {n}.",
        4.99, demand=1.4 if n <= 5 else 1.0, key=1 if n in (5, 10) else 0, force=True,
        bare="Ultimate Spider-Man")

# Amazing Spider-Man (2018) #1–93 (Spencer Fresh Start)
for n in range(1, 94):
    cd = interp_date(n, 1, 2018, 7, 93, 2022, 3)
    add(f"mv-asm-2018-{n}", "Amazing Spider-Man (2018)", n, cd,
        "Nick Spencer", "Ryan Ottley" if n <= 5 else ("Humberto Ramos" if n <= 25 else "Various"),
        ("Fresh Start Amazing Spider-Man begins. Back to Basics." if n == 1
         else ({25: "Hunted.", 50: "Amazing Spider-Man (2018) #50.",
                74: "Last Remains.", 93: "Amazing Spider-Man (2018) finale / Sins Rising fallout."
                }.get(n, f"Amazing Spider-Man (2018) issue {n}."))),
        3.99 if n < 50 else 4.99,
        demand=1.6 if n == 1 else (1.1 if n in (25, 50, 74, 93) else 0.55),
        key=1 if n in (1, 25, 50, 74, 93) else 0, force=True,
        bare="The Amazing Spider-Man")

print("P1", len(b.rows))

# =============================================================================
# P2 — 2014–2017 volumes + Superior + Miles
# =============================================================================
# Amazing Spider-Man (2015) #1–32 + legacy #789–801
for n in range(1, 33):
    cd = interp_date(n, 1, 2015, 12, 32, 2017, 9)
    add(f"mv-asm-2015-{n}", "Amazing Spider-Man (2015)", n, cd,
        "Dan Slott", "Giuseppe Camuncoli" if n <= 20 else "Various",
        ("Post-Secret Wars Amazing Spider-Man begins." if n == 1
         else f"Amazing Spider-Man (2015) issue {n}."),
        3.99, demand=1.3 if n == 1 else 0.55, key=1 if n in (1, 32) else 0, force=True,
        bare="The Amazing Spider-Man")
for n in range(789, 802):
    cd = interp_date(n, 789, 2017, 10, 801, 2018, 6)
    add(f"mv-asm-lgy-{n}", "Amazing Spider-Man (2017)", n, cd,
        "Dan Slott" if n < 800 else "Various", "Various",
        ("Marvel Legacy Amazing Spider-Man resumes legacy numbering." if n == 789
         else ("Amazing Spider-Man #800 milestone." if n == 800
               else f"Amazing Spider-Man legacy #{n}.")),
        3.99 if n != 800 else 9.99,
        demand=1.4 if n in (789, 800) else 0.6, key=1 if n in (789, 800) else 0, force=True,
        bare="The Amazing Spider-Man")

# Amazing Spider-Man (2014) #1–18 (Slott post-Superior)
for n in range(1, 19):
    cd = interp_date(n, 1, 2014, 6, 18, 2015, 10)
    add(f"mv-asm-2014-{n}", "Amazing Spider-Man (2014)", n, cd,
        "Dan Slott", "Humberto Ramos" if n <= 6 else "Various",
        ("Amazing Spider-Man (2014) begins. Parker Industries." if n == 1
         else f"Amazing Spider-Man (2014) issue {n}."),
        3.99, demand=1.3 if n == 1 else 0.55, key=1 if n == 1 else 0, force=True,
        bare="The Amazing Spider-Man")

# Superior Spider-Man #2–31 (skip #1)
for n in range(2, 32):
    cd = interp_date(n, 1, 2013, 1, 31, 2014, 5)
    add(f"mv-superior-{n}", "The Superior Spider-Man", n, cd,
        "Dan Slott", "Ryan Stegman" if n <= 10 else ("Giuseppe Camuncoli" if n <= 20 else "Various"),
        ({10: "Superior Spider-Man vs Green Goblin.",
          31: "Superior Spider-Man finale. Peter returns."
          }.get(n, f"The Superior Spider-Man issue {n}.")),
        3.99, demand=1.3 if n in (10, 31) else 0.7, key=1 if n in (10, 31) else 0, force=True)

# Ultimate Comics Spider-Man (Miles) #2–28 + Miles Morales: Ultimate Spider-Man #1–12
# Archive has Ultimate Comics Spider-Man #1 (Miles)
for n in range(2, 29):
    cd = interp_date(n, 1, 2011, 11, 28, 2013, 10)
    add(f"mv-miles-ucs-{n}", "Ultimate Comics Spider-Man", n, cd,
        "Brian Michael Bendis", "Sara Pichelli",
        f"Ultimate Comics Spider-Man (Miles) issue {n}.",
        2.99, demand=1.0 if n <= 5 else 0.55, key=1 if n == 28 else 0, force=True)

for n in range(1, 13):
    cd = interp_date(n, 1, 2014, 5, 12, 2015, 4)
    add(f"mv-miles-ult-{n}", "Miles Morales: Ultimate Spider-Man", n, cd,
        "Brian Michael Bendis", "David Marquez",
        ("Miles Morales: Ultimate Spider-Man begins." if n == 1
         else f"Miles Morales: Ultimate Spider-Man issue {n}."),
        3.99, demand=1.2 if n == 1 else 0.55, key=1 if n == 1 else 0, force=True)

# Spider-Man (2016) Miles #1–25 (All-New All-Different)
for n in range(1, 16):
    cd = interp_date(n, 1, 2016, 1, 25, 2017, 10)
    add(f"mv-spiderman-2016-{n}", "Spider-Man (2016)", n, cd,
        "Brian Michael Bendis", "Sara Pichelli" if n <= 10 else "Various",
        ("Miles Morales joins main Marvel U as Spider-Man." if n == 1
         else f"Spider-Man (2016) Miles Morales issue {n}."),
        3.99, demand=1.4 if n == 1 else 0.55, key=1 if n == 1 else 0, force=True)

# Miles Morales: Spider-Man (2018) #1–30
for n in range(1, 21):
    cd = interp_date(n, 1, 2018, 12, 30, 2021, 6)
    add(f"mv-miles-2018-{n}", "Miles Morales: Spider-Man (2018)", n, cd,
        "Saladin Ahmed", "Javier Garrón" if n <= 10 else "Various",
        ("Miles Morales: Spider-Man (2018) begins." if n == 1
         else f"Miles Morales: Spider-Man (2018) issue {n}."),
        3.99, demand=1.2 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True)

print("P2", len(b.rows))

# =============================================================================
# P3 — Ultimate (2000), ASM 500–699 curated, vol2, Spectacular, classic ASM
# =============================================================================
# --- Floor block first (force) so date range hits Oct 1986 ---
for n in range(281, 320):
    if str(n) in ARCHIVE_ASM:
        b.skipped.append({"reason": "archive-known", "id": f"mv-asm-{n}",
                          "series": "The Amazing Spider-Man", "issue": str(n)})
        continue
    cd = interp_date(n, 281, 1986, 10, 319, 1989, 9)
    w, a = ("David Michelinie", "Todd McFarlane") if n >= 298 else ("Various", "Various")
    descs = {281: "Amazing Spider-Man at Oct 1986 floor.",
             298: "McFarlane art era begins.",
             300: "First full Venom era (skip if archived)."}
    add(f"mv-asm-{n}", "The Amazing Spider-Man", n, cd, w, a,
        descs.get(n, f"The Amazing Spider-Man #{n}."),
        0.75 if n < 300 else 1.00,
        demand=1.5 if n in (281, 298) else 0.5,
        key=1 if n in (281, 298) else 0, force=True)

for n in range(120, 150):
    cd = interp_date(n, 120, 1986, 11, 149, 1989, 4)
    add(f"mv-ssm-{n}", "The Spectacular Spider-Man", n, cd,
        "Peter David" if n <= 136 else "Various", "Various",
        ({120: "Spectacular near Oct 1986 floor.",
          134: "Title shortens to The Spectacular Spider-Man."
          }.get(n, f"The Spectacular Spider-Man #{n}.")),
        0.75, demand=0.7 if n in (120, 134) else 0.35,
        key=1 if n == 134 else 0, force=True)

for n in range(1, 11):
    cd = interp_date(n, 1, 1990, 8, 10, 1991, 5)
    add(f"mv-spiderman-1990-{n}", "Spider-Man (1990)", n, cd,
        "Todd McFarlane", "Todd McFarlane",
        ("Spider-Man (1990) #1. Torment. McFarlane." if n == 1
         else f"Spider-Man (1990) issue {n}."),
        1.00, demand=2.0 if n == 1 else 0.7, key=1 if n == 1 else 0, force=True)

print("P2b floor", len(b.rows))

# Ultimate Spider-Man (2000) curated #2–60 (skip #1)
for n in range(2, 61):
    cd = interp_date(n, 1, 2000, 10, 133, 2009, 8)
    w = "Brian Michael Bendis"
    a = "Mark Bagley"
    add(f"mv-ultimate-sm-{n}", "Ultimate Spider-Man", n, cd, w, a,
        ({13: "Ultimate Green Goblin.",
          33: "Ultimate Carnage.",
          40: "Ultimate Venom.",
          50: "Ultimate Spider-Man #50."
          }.get(n, f"Ultimate Spider-Man issue {n}.")),
        2.25 if n < 50 else 2.99,
        demand=1.2 if n in (13, 33, 40, 50) else 0.5,
        key=1 if n in (13, 33, 40, 50) else 0, force=True,
        bare="Ultimate Spider-Man")

# ASM #501–650 curated (not full to 699)
for n in list(range(501, 538)) + list(range(539, 651)):
    if not b.room():
        break
    if str(n) in ARCHIVE_ASM:
        b.skipped.append({"reason": "archive-known", "id": f"mv-asm-{n}",
                          "series": "The Amazing Spider-Man", "issue": str(n)})
        continue
    cd = interp_date(n, 500, 2003, 12, 700, 2013, 2)
    if n <= 545:
        w, a = "J. Michael Straczynski", "John Romita Jr." if n <= 518 else "Various"
    elif n <= 647:
        w, a = "Various", "Various"  # Brand New Day
    else:
        w, a = "Dan Slott", "Humberto Ramos" if n <= 660 else "Various"
    descs = {
        501: "Post-#500 Amazing Spider-Man continues.",
        539: "One More Day fallout / Brand New Day begins era.",
        546: "Brand New Day.",
        583: "Obama / assassination attempt landmark era.",
        600: "Amazing Spider-Man #600.",
        648: "Big Time begins (Slott).",
        654: "Spider-Island lead-in.",
        666: "Ends of the Earth.",
        692: "Dying Wish lead-in.",
        699: "Dying Wish. Lead to Superior.",
    }
    add(f"mv-asm-{n}", "The Amazing Spider-Man", n, cd, w, a,
        descs.get(n, f"The Amazing Spider-Man #{n}."),
        2.25 if n < 550 else (2.99 if n < 650 else 3.99),
        demand=1.3 if n in (539, 600, 648, 699) else 0.5,
        key=1 if n in (539, 600, 648, 699) else 0)

print("P3a", len(b.rows))

# ASM vol2 (1999) #1–58
for n in range(1, 59):
    if not b.room():
        break
    cd = interp_date(n, 1, 1999, 1, 58, 2003, 11)
    add(f"mv-asm-v2-{n}", "Amazing Spider-Man (1999)", n, cd,
        "Howard Mackie" if n <= 29 else "J. Michael Straczynski",
        "John Byrne" if n <= 18 else ("John Romita Jr." if n >= 30 else "Various"),
        ("Amazing Spider-Man vol. 2 relaunch begins." if n == 1
         else ("JMS / JRJr Amazing Spider-Man begins." if n == 30
               else f"Amazing Spider-Man (1999) issue {n}.")),
        1.99 if n < 30 else 2.25,
        demand=1.2 if n in (1, 30) else 0.45, key=1 if n in (1, 30) else 0,
        bare="The Amazing Spider-Man")

# Spectacular Spider-Man post-floor: #120–263 (approx #120 = Nov 1986)
# Archive has Spectacular #1 only
for n in list(range(120, 200)) + list(range(200, 264)):
    if not b.room():
        break
    if str(n) in ARCHIVE_SSM:
        continue
    if n <= 200:
        cd = interp_date(n, 120, 1986, 11, 200, 1993, 5)
    else:
        cd = interp_date(n, 200, 1993, 5, 263, 1998, 11)
    add(f"mv-ssm-{n}", "The Spectacular Spider-Man", n, cd,
        "Peter David" if n <= 136 else ("J.M. DeMatteis" if 178 <= n <= 203 else "Various"),
        "Various",
        ({134: "Title shortens to The Spectacular Spider-Man.",
          200: "Spectacular Spider-Man #200.",
          263: "Spectacular Spider-Man series finale."
          }.get(n, f"The Spectacular Spider-Man #{n}.")),
        0.75 if n < 150 else (1.00 if n < 220 else 1.99),
        demand=0.9 if n in (134, 200, 263) else 0.35, key=1 if n in (200, 263) else 0)

# Classic ASM #281–441 (Oct 1986 floor → end of vol1), skip archived
classic_asm = list(range(281, 298)) + list(range(299, 300)) + list(range(301, 316)) + \
              list(range(317, 318)) + list(range(319, 361)) + list(range(362, 441))
# Actually simpler: 281-441 except archive set
for n in range(281, 442):
    if not b.room():
        break
    if str(n) in ARCHIVE_ASM:
        b.skipped.append({"reason": "archive-known", "id": f"mv-asm-{n}",
                          "series": "The Amazing Spider-Man", "issue": str(n)})
        continue
    cd = interp_date(n, 281, 1986, 10, 441, 1998, 11)
    if n <= 289:
        w, a = "Various", "Various"
    elif 298 <= n <= 328:
        w, a = "David Michelinie", "Todd McFarlane" if n <= 323 else "Erik Larsen"
    elif n <= 350:
        w, a = "David Michelinie", "Mark Bagley" if n >= 345 else "Various"
    else:
        w, a = "Various", "Various"
    descs = {
        281: "Amazing Spider-Man at Oct 1986 floor.",
        290: "Kraven's Last Hunt lead-in era.",
        298: "McFarlane art era begins.",
        300: "First full Venom (archived if present).",
        316: "Cosmic Spider-Man era.",
        361: "Carnage first appearance (archived if present).",
        375: "Maximum Carnage era.",
        400: "Amazing Spider-Man #400. Aunt May.",
        441: "Amazing Spider-Man vol. 1 finale era.",
    }
    add(f"mv-asm-{n}", "The Amazing Spider-Man", n, cd, w, a,
        descs.get(n, f"The Amazing Spider-Man #{n}."),
        0.75 if n < 300 else (1.00 if n < 350 else (1.50 if n < 400 else 1.99)),
        demand=1.5 if n in (298, 400) else (0.9 if n in (281, 375, 441) else 0.4),
        key=1 if n in (298, 375, 400, 441) else 0)

# Spider-Man (1990) #1–20 (McFarlane), Web of Spider-Man curated post-floor
for n in range(1, 21):
    if not b.room():
        break
    cd = interp_date(n, 1, 1990, 8, 20, 1992, 3)
    add(f"mv-spiderman-1990-{n}", "Spider-Man (1990)", n, cd,
        "Todd McFarlane" if n <= 14 else "Various",
        "Todd McFarlane" if n <= 14 else "Various",
        ("Spider-Man (1990) #1. Torment. McFarlane." if n == 1
         else f"Spider-Man (1990) issue {n}."),
        1.00, demand=2.0 if n == 1 else 0.7, key=1 if n == 1 else 0)

for n in range(20, 51):
    if not b.room():
        break
    cd = interp_date(n, 20, 1986, 11, 50, 1989, 5)
    add(f"mv-web-{n}", "Web of Spider-Man", n, cd, "Various", "Various",
        f"Web of Spider-Man #{n}.",
        0.75, demand=0.4)

# Spider-Man 2099 #2–25 (skip #1), Friendly Neighborhood Spider-Man (2005) #1–12
for n in range(2, 26):
    if not b.room():
        break
    cd = interp_date(n, 1, 1992, 11, 25, 1994, 11)
    add(f"mv-sm2099-{n}", "Spider-Man 2099", n, cd,
        "Peter David", "Rick Leonardi",
        f"Spider-Man 2099 issue {n}.",
        1.25, demand=0.7 if n <= 5 else 0.4, bare="Spider-Man 2099")

for n in range(1, 13):
    if not b.room():
        break
    cd = interp_date(n, 1, 2005, 12, 12, 2006, 11)
    add(f"mv-fnsm-{n}", "Friendly Neighborhood Spider-Man", n, cd,
        "Peter David", "Mike Wieringo",
        ("Friendly Neighborhood Spider-Man begins." if n == 1
         else f"Friendly Neighborhood Spider-Man issue {n}."),
        2.99, demand=0.9 if n == 1 else 0.4, key=1 if n == 1 else 0)

print("P4", len(b.rows))

PRIORITY = {
    "Amazing Spider-Man (2022)", "Ultimate Spider-Man (2024)", "Amazing Spider-Man (2018)",
    "Amazing Spider-Man (2015)", "Amazing Spider-Man (2017)", "Amazing Spider-Man (2014)",
    "The Superior Spider-Man", "Ultimate Comics Spider-Man", "Miles Morales: Ultimate Spider-Man",
    "Spider-Man (2016)", "Miles Morales: Spider-Man (2018)", "Ultimate Spider-Man",
    "The Amazing Spider-Man", "Amazing Spider-Man (1999)", "The Spectacular Spider-Man",
    "Spider-Man (1990)",
}
b.finalize(PRIORITY)
assert len(b.rows) >= TARGET_MIN, f"Only {len(b.rows)} rows"
assert len(b.rows) <= TARGET_MAX
b.write("batch-004", "Marvel Spider-Man family — modern to Oct 1986",
        "Spider-Man titles, modern → Oct 1986 floor")
b.report()
Path("/tmp/batch-004-skipped.json").write_text(
    __import__("json").dumps(b.skipped, indent=2))
print("OK")

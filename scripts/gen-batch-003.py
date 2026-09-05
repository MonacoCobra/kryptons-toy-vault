#!/usr/bin/env python3
"""Generate comic-backlog batch-003: Marvel X-Men family, modern → Oct 1986 floor."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comic_backlog_common import (
    BatchBuilder, load_blocklists, cover, interp_date, add_months,
)

PUB = "Marvel Comics"
PAL = "7c2d12,a16207,111827"
TARGET_MIN, TARGET_MAX = 450, 500

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
b = BatchBuilder(PUB, PAL, EXISTING_IDS, EXISTING_KEYS, TARGET_MIN, TARGET_MAX)

ARCHIVE_UXM = {k.split("|")[1] for k in EXISTING_KEYS
               if k.startswith("the uncanny x-men|") and k.endswith("|marvel comics")}

def add(rid, series, issue, cd, w, a, desc, msrp, demand=0.55, key=0, force=False, bare=None):
    return b.try_add(rid, series, issue, cd, w, a, desc, msrp,
                     demand=demand, key=key, force=force, also_block_bare=bare)

# =============================================================================
# P1 — From the Ashes / current (~150) force
# =============================================================================
for n in range(1, 35):
    cd = interp_date(n, 1, 2024, 10, 34, 2026, 8)
    add(f"mv-uxm-2024-{n}", "Uncanny X-Men (2024)", n, cd,
        "Gail Simone", "David Marquez" if n <= 12 else "Various",
        ("From the Ashes Uncanny X-Men begins. Red Wave." if n == 1
         else f"Uncanny X-Men (2024) by Gail Simone, issue {n}."),
        4.99, demand=1.8 if n == 1 else 0.9, key=1 if n in (1, 5, 10, 25) else 0, force=True)

for n in range(1, 26):
    cd = interp_date(n, 1, 2024, 9, 25, 2026, 8)
    add(f"mv-xmen-2024-{n}", "X-Men (2024)", n, cd, "Jed MacKay", "Various",
        ("From the Ashes X-Men begins." if n == 1 else f"X-Men (2024) issue {n}."),
        4.99, demand=1.6 if n == 1 else 0.85, key=1 if n in (1, 10, 25) else 0, force=True,
        bare="X-Men")

for n in range(1, 14):
    cd = interp_date(n, 1, 2024, 11, 13, 2025, 11)
    add(f"mv-exxmen-{n}", "Exceptional X-Men", n, cd, "Eve L. Ewing", "Carmen Carnero",
        ("Exceptional X-Men begins." if n == 1 else f"Exceptional X-Men issue {n}."),
        3.99, demand=1.0 if n == 1 else 0.55, key=1 if n == 1 else 0, force=True)

for n in range(1, 11):
    cd = interp_date(n, 1, 2024, 9, 10, 2025, 6)
    add(f"mv-xforce-2024-{n}", "X-Force (2024)", n, cd, "Geoffrey Thorne", "Marcus To",
        ("X-Force (2024) begins." if n == 1 else f"X-Force (2024) issue {n}."),
        3.99, demand=0.9 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True, bare="X-Force")
for n in range(1, 11):
    cd = interp_date(n, 1, 2024, 9, 10, 2025, 6)
    add(f"mv-xfactor-2024-{n}", "X-Factor (2024)", n, cd, "Mark Russell", "Bob Quinn",
        ("X-Factor (2024) begins." if n == 1 else f"X-Factor (2024) issue {n}."),
        3.99, demand=0.9 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True, bare="X-Factor")
for n in range(1, 13):
    cd = interp_date(n, 1, 2024, 10, 12, 2025, 9)
    add(f"mv-storm-2024-{n}", "Storm (2024)", n, cd, "Murewa Ayodele", "Bernard Chang",
        ("Storm (2024) solo begins." if n == 1 else f"Storm (2024) issue {n}."),
        3.99, demand=1.0 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True)
for n in range(1, 16):
    cd = interp_date(n, 1, 2024, 10, 15, 2025, 12)
    add(f"mv-phoenix-2024-{n}", "Phoenix (2024)", n, cd, "Stephanie Phillips", "Alessandro Miracolo",
        ("Phoenix (2024) begins." if n == 1 else f"Phoenix (2024) issue {n}."),
        3.99, demand=0.95 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True)

for n in range(2, 25):
    cd = interp_date(n, 1, 2024, 5, 24, 2026, 4)
    add(f"mv-ult-xmen-2024-{n}", "Ultimate X-Men (2024)", n, cd, "Peach Momoko", "Peach Momoko",
        f"Ultimate X-Men (2024) issue {n}.",
        4.99, demand=1.1 if n <= 5 else 0.7, key=1 if n == 10 else 0, force=True,
        bare="Ultimate X-Men")

for n in range(2, 19):
    cd = interp_date(n, 1, 2022, 5, 18, 2023, 10)
    add(f"mv-immortalx-{n}", "The Immortal X-Men", n, cd, "Kieron Gillen",
        "Lucas Werneck" if n <= 10 else "Various",
        f"Immortal X-Men issue {n}.",
        3.99, demand=0.8, key=1 if n == 18 else 0, force=True)

print("P1", len(b.rows))  # ~156

# =============================================================================
# P2 — Krakoa curated (~120) force
# =============================================================================
for n in range(2, 22):
    cd = interp_date(n, 1, 2019, 12, 21, 2021, 6)
    add(f"mv-xmen-2019-{n}", "X-Men (2019)", n, cd, "Jonathan Hickman",
        "Leinil Francis Yu" if n <= 10 else "Various",
        f"Hickman-era X-Men (2019) issue {n}.",
        3.99, demand=1.2 if n <= 5 else 0.7, key=1 if n in (5, 21) else 0, force=True,
        bare="X-Men")

for n in range(1, 21):  # first 20 of 35
    cd = interp_date(n, 1, 2021, 9, 35, 2024, 4)
    add(f"mv-xmen-2021-{n}", "X-Men (2021)", n, cd, "Gerry Duggan",
        "Pepe Larraz" if n <= 10 else "Various",
        ("X-Men (2021) begins." if n == 1 else f"X-Men (2021) issue {n}."),
        3.99, demand=1.3 if n == 1 else 0.6, key=1 if n == 1 else 0, force=True, bare="X-Men")

for n in range(1, 26):  # 25 of 50
    cd = interp_date(n, 1, 2019, 11, 50, 2024, 3)
    add(f"mv-xforce-2019-{n}", "X-Force (2019)", n, cd, "Benjamin Percy",
        "Joshua Cassara" if n <= 20 else "Various",
        ("Krakoa X-Force begins." if n == 1 else f"X-Force (2019) issue {n}."),
        3.99, demand=1.2 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True, bare="X-Force")

for n in range(1, 16):
    cd = interp_date(n, 1, 2019, 12, 27, 2022, 4)
    add(f"mv-marauders-2019-{n}", "Marauders (2019)", n, cd, "Gerry Duggan", "Stefano Caselli",
        ("Marauders begins. Kate Pryde captain." if n == 1 else f"Marauders (2019) issue {n}."),
        3.99, demand=1.1 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True)

for n in range(1, 13):
    cd = interp_date(n, 1, 2019, 11, 25, 2022, 2)
    add(f"mv-nm-2019-{n}", "New Mutants (2019)", n, cd,
        "Ed Brisson" if n <= 12 else "Vita Ayala", "Various",
        ("New Mutants (2019) Krakoa begins." if n == 1 else f"New Mutants (2019) issue {n}."),
        3.99, demand=1.0 if n == 1 else 0.45, key=1 if n == 1 else 0, force=True)

for n in range(1, 13):
    cd = interp_date(n, 1, 2019, 12, 26, 2021, 12)
    add(f"mv-excalibur-2019-{n}", "Excalibur (2019)", n, cd, "Tini Howard", "Marcus To",
        ("Excalibur (2019) begins. Otherworld." if n == 1 else f"Excalibur (2019) issue {n}."),
        3.99, demand=1.0 if n == 1 else 0.45, key=1 if n == 1 else 0, force=True, bare="Excalibur")

for n in range(1, 13):
    cd = interp_date(n, 1, 2022, 4, 18, 2023, 9)
    add(f"mv-xmenred-2022-{n}", "X-Men: Red (2022)", n, cd, "Al Ewing", "Stefano Caselli",
        ("X-Men: Red (2022) begins. Arakko." if n == 1 else f"X-Men: Red (2022) issue {n}."),
        3.99, demand=1.1 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True)

for n in range(1, 26):  # 25 of 50
    cd = interp_date(n, 1, 2020, 4, 50, 2024, 3)
    add(f"mv-wolverine-2020-{n}", "Wolverine (2020)", n, cd, "Benjamin Percy",
        "Adam Kubert" if n <= 15 else "Various",
        ("Wolverine (2020) Krakoa begins." if n == 1 else f"Wolverine (2020) issue {n}."),
        3.99, demand=1.3 if n == 1 else 0.55, key=1 if n == 1 else 0, force=True,
        bare="Wolverine")

print("P2", len(b.rows))  # ~156+132 ≈ 288

# =============================================================================
# P3 — Landmarks (~100) force
# =============================================================================
for n in range(2, 25):  # Whedon Astonishing core
    cd = interp_date(n, 1, 2004, 9, 24, 2008, 6)
    add(f"mv-astx-{n}", "Astonishing X-Men", n, cd, "Joss Whedon", "John Cassaday",
        ({7: "Danger Room / Breakworld.", 13: "Torn.", 19: "Unstoppable.",
          24: "Whedon/Cassaday Astonishing finale."}.get(n, f"Astonishing X-Men issue {n}.")),
        2.99, demand=1.2 if n in (7, 13, 24) else 0.65, key=1 if n in (13, 24) else 0, force=True)

for n in range(115, 155):
    cd = interp_date(n, 114, 2001, 7, 154, 2004, 5)
    add(f"mv-newxmen-{n}", "New X-Men", n, cd, "Grant Morrison",
        "Frank Quitely" if n <= 126 else "Various",
        ({116: "Morrison New X-Men — E is for Extinction.",
          121: "Imperial.", 146: "Here Comes Tomorrow begins.",
          154: "Morrison New X-Men finale."}.get(n, f"New X-Men issue {n}.")),
        2.25 if n < 140 else 2.99,
        demand=1.4 if n in (116, 121, 146, 154) else 0.65,
        key=1 if n in (116, 121, 146, 154) else 0, force=True)

for n in range(1, 13):
    cd = interp_date(n, 1, 2011, 12, 20, 2012, 10)
    add(f"mv-uxm-2011-{n}", "Uncanny X-Men (2011)", n, cd, "Kieron Gillen",
        "Carlos Pacheco" if n <= 10 else "Various",
        ("Post-Schism Uncanny Extinction Team begins." if n == 1
         else f"Uncanny X-Men (2011) issue {n}."),
        2.99, demand=1.1 if n == 1 else 0.5, key=1 if n in (1, 20) else 0, force=True)

for n in list(range(1, 21)) + [600]:  # Bendis first 20 + #600
    cd = cover(2015, 11) if n == 600 else interp_date(n, 1, 2013, 4, 35, 2015, 9)
    add(f"mv-uxm-2013-{n}", "Uncanny X-Men (2013)", n, cd, "Brian Michael Bendis",
        "Chris Bachalo" if n != 600 else "Various",
        ("Bendis Uncanny X-Men begins." if n == 1
         else ("Uncanny X-Men #600 legacy milestone." if n == 600
               else f"Uncanny X-Men (2013) issue {n}.")),
        3.99 if n == 600 else 2.99,
        demand=1.4 if n in (1, 600) else 0.5, key=1 if n in (1, 600) else 0, force=True)

for n in range(1, 13):
    cd = interp_date(n, 1, 2012, 1, 41, 2015, 4)
    add(f"mv-anxmen-{n}", "All-New X-Men (2012)", n, cd, "Brian Michael Bendis",
        "Stuart Immonen" if n <= 18 else "Various",
        ("All-New X-Men begins. Past X-Men arrive." if n == 1
         else f"All-New X-Men (2012) issue {n}."),
        2.99, demand=1.3 if n == 1 else 0.5, key=1 if n == 1 else 0, force=True)

for n in range(1, 13):
    cd = interp_date(n, 1, 2010, 12, 35, 2012, 12)
    add(f"mv-uxforce-{n}", "Uncanny X-Force (2010)", n, cd, "Rick Remender",
        "Jerome Opena" if n <= 18 else "Various",
        ("Uncanny X-Force begins. The Torment." if n == 1
         else f"Uncanny X-Force (2010) issue {n}."),
        3.99, demand=1.2 if n == 1 else 0.55, key=1 if n == 1 else 0, force=True)

print("P3", len(b.rows))  # ~288+142 ≈ 430

# =============================================================================
# P3b — Oct 1986 floor landmarks (force; ensure date range hits floor)
# =============================================================================
for n in [210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225,
          226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240,
          241, 242, 243, 245, 246, 247, 248, 249]:
    if str(n) in ARCHIVE_UXM:
        b.skipped.append({"reason": "archive-known", "id": f"mv-uxm-{n}",
                          "series": "The Uncanny X-Men", "issue": str(n)})
        continue
    cd = interp_date(n, 210, 1986, 10, 249, 1989, 9)
    w, a = "Chris Claremont", ("Jim Lee" if n >= 248 else ("Marc Silvestri" if n >= 225 else "Various"))
    descs = {210: "Uncanny at Oct 1986 floor.", 213: "Mutant Massacre begins.",
             225: "Fall of the Mutants era.", 248: "Jim Lee art era begins."}
    add(f"mv-uxm-{n}", "The Uncanny X-Men", n, cd, w, a,
        descs.get(n, f"The Uncanny X-Men #{n}."),
        0.75, demand=1.5 if n in (210, 213, 225) else 0.5,
        key=1 if n in (210, 213, 225, 248) else 0, force=True)

for n in range(10, 25):
    cd = interp_date(n, 10, 1986, 11, 24, 1987, 11)
    add(f"mv-xfactor-{n}", "X-Factor", n, cd, "Louise Simonson", "Walter Simonson",
        ({10: "X-Factor near Oct 1986 floor.", 15: "Mutant Massacre X-Factor.",
          24: "Fall of the Mutants X-Factor."}.get(n, f"X-Factor #{n}.")),
        0.75, demand=0.9 if n in (15, 24) else 0.4, key=1 if n in (15, 24) else 0, force=True)

for n in range(2, 12):
    cd = interp_date(n, 1, 1988, 11, 11, 1989, 9)
    add(f"mv-wolverine-1988-{n}", "Wolverine (1988)", n, cd,
        "Chris Claremont", "John Buscema",
        f"Wolverine (1988) #{n}.", 1.00, demand=0.6, force=True, bare="Wolverine")

print("P3b", len(b.rows))

# =============================================================================
# P4 — Classic fill to Oct 1986 (no force; soft room)
# =============================================================================
# X-Men (1991) #2–40
for n in range(2, 41):
    cd = interp_date(n, 1, 1991, 10, 40, 1995, 1)
    w = "Chris Claremont" if n <= 3 else ("Fabian Nicieza" if n <= 30 else "Scott Lobdell")
    a = "Jim Lee" if n <= 11 else ("Andy Kubert" if n <= 30 else "Various")
    add(f"mv-xmen-1991-{n}", "X-Men (1991)", n, cd, w, a,
        ({2: "X-Men (1991) continues Blue/Gold.", 11: "Jim Lee era landmark.",
          25: "Fatal Attractions era X-Men."}.get(n, f"X-Men (1991) issue {n}.")),
        1.00 if n < 20 else 1.50,
        demand=1.2 if n in (2, 11, 25) else 0.5, key=1 if n in (11, 25) else 0,
        bare="X-Men")

# Uncanny classic modern→floor: 500-544, 400-450, 300-320, 266-299 skip arch, 210-265
uxm_issues = (
    list(range(500, 545))
    + list(range(400, 451))
    + list(range(300, 321))
    + list(range(266, 300))
    + list(range(210, 266))
)
for n in uxm_issues:
    if str(n) in ARCHIVE_UXM:
        b.skipped.append({"reason": "archive-known", "id": f"mv-uxm-{n}",
                          "series": "The Uncanny X-Men", "issue": str(n)})
        continue
    if n <= 266:
        cd = interp_date(n, 210, 1986, 10, 266, 1990, 8)
    elif n <= 300:
        cd = interp_date(n, 266, 1990, 8, 300, 1993, 9)
    elif n <= 400:
        cd = interp_date(n, 300, 1993, 9, 400, 2002, 1)
    elif n <= 500:
        cd = interp_date(n, 400, 2002, 1, 500, 2008, 7)
    else:
        cd = interp_date(n, 500, 2008, 7, 544, 2011, 10)
    if n < 248:
        w, a = "Chris Claremont", "Marc Silvestri" if n >= 225 else "Various"
    elif n <= 269:
        w, a = "Chris Claremont", "Jim Lee"
    elif n <= 320:
        w, a = "Various", "Various"
    elif 500 <= n <= 514:
        w, a = "Matt Fraction", "Greg Land"
    elif n >= 534:
        w, a = "Kieron Gillen", "Carlos Pacheco"
    else:
        w, a = "Various", "Various"
    descs = {
        210: "Uncanny at Oct 1986 floor.",
        213: "Mutant Massacre begins.",
        225: "Fall of the Mutants era.",
        248: "Jim Lee art era begins.",
        275: "X-Tinction Agenda era.",
        300: "Uncanny X-Men #300 milestone.",
        400: "Uncanny X-Men #400.",
        500: "Uncanny X-Men #500.",
        544: "Uncanny X-Men vol. 1 finale.",
    }
    add(f"mv-uxm-{n}", "The Uncanny X-Men", n, cd, w, a,
        descs.get(n, f"The Uncanny X-Men #{n}."),
        0.75 if n < 250 else (1.00 if n < 350 else (2.25 if n < 450 else 2.99)),
        demand=1.5 if n in (213, 300, 500, 544) else 0.45,
        key=1 if n in (213, 225, 300, 400, 500, 544) else 0)

# Wolverine 1988 #2–30, X-Force 1991 #2–20, X-Factor #10–35
for n in range(2, 31):
    cd = interp_date(n, 1, 1988, 11, 30, 1990, 8)
    add(f"mv-wolverine-1988-{n}", "Wolverine (1988)", n, cd,
        "Chris Claremont" if n <= 8 else "Various",
        "John Buscema" if n <= 8 else "Various",
        f"Wolverine (1988) #{n}.",
        1.00, demand=0.55, bare="Wolverine")

for n in range(2, 21):
    cd = interp_date(n, 1, 1991, 8, 20, 1993, 3)
    add(f"mv-xforce-1991-{n}", "X-Force (1991)", n, cd, "Fabian Nicieza",
        "Rob Liefeld" if n <= 12 else "Various",
        ({2: "X-Force continues.", 15: "X-Cutioner's Song era X-Force."
          }.get(n, f"X-Force (1991) #{n}.")),
        1.00, demand=0.9 if n == 15 else 0.4, key=1 if n == 15 else 0, bare="X-Force")

for n in range(10, 36):
    cd = interp_date(n, 10, 1986, 11, 35, 1988, 12)
    add(f"mv-xfactor-{n}", "X-Factor", n, cd, "Louise Simonson",
        "Walter Simonson" if n <= 30 else "Various",
        ({10: "X-Factor near Oct 1986 floor.", 15: "Mutant Massacre X-Factor.",
          24: "Fall of the Mutants X-Factor."}.get(n, f"X-Factor #{n}.")),
        0.75, demand=0.9 if n in (15, 24) else 0.4, key=1 if n in (15, 24) else 0)

print("P4", len(b.rows))

# Soft extend if under min
if len(b.rows) < TARGET_MIN:
    for n in range(21, 36):
        if len(b.rows) >= TARGET_MIN:
            break
        cd = interp_date(n, 1, 2021, 9, 35, 2024, 4)
        add(f"mv-xmen-2021-{n}", "X-Men (2021)", n, cd, "Gerry Duggan", "Various",
            f"X-Men (2021) issue {n}.", 3.99, demand=0.55, bare="X-Men")

if len(b.rows) < TARGET_MIN:
    for n in range(26, 41):
        if len(b.rows) >= TARGET_MIN:
            break
        cd = interp_date(n, 1, 2019, 11, 50, 2024, 3)
        add(f"mv-xforce-2019-{n}", "X-Force (2019)", n, cd, "Benjamin Percy", "Various",
            f"X-Force (2019) issue {n}.", 3.99, demand=0.5, bare="X-Force")

if len(b.rows) < 480:
    for n in range(26, 36):
        if len(b.rows) >= 480:
            break
        cd = interp_date(n, 1, 2020, 4, 50, 2024, 3)
        add(f"mv-wolverine-2020-{n}", "Wolverine (2020)", n, cd, "Benjamin Percy", "Various",
            f"Wolverine (2020) issue {n}.", 3.99, demand=0.5, bare="Wolverine")

if len(b.rows) < TARGET_MAX:
    for n in range(21, 36):
        if len(b.rows) >= TARGET_MAX:
            break
        cd = interp_date(n, 1, 2012, 1, 41, 2015, 4)
        add(f"mv-anxmen-{n}", "All-New X-Men (2012)", n, cd, "Brian Michael Bendis", "Various",
            f"All-New X-Men (2012) issue {n}.", 2.99, demand=0.45)

PRIORITY = {
    "Uncanny X-Men (2024)", "X-Men (2024)", "Exceptional X-Men", "X-Force (2024)",
    "X-Factor (2024)", "Storm (2024)", "Phoenix (2024)", "Ultimate X-Men (2024)",
    "The Immortal X-Men", "X-Men (2019)", "X-Men (2021)", "X-Force (2019)",
    "Wolverine (2020)", "Marauders (2019)", "New Mutants (2019)", "Excalibur (2019)",
    "X-Men: Red (2022)", "Astonishing X-Men", "New X-Men", "Uncanny X-Men (2011)",
    "Uncanny X-Men (2013)", "All-New X-Men (2012)", "Uncanny X-Force (2010)",
    "The Uncanny X-Men", "X-Men (1991)", "Wolverine (1988)", "X-Force (1991)", "X-Factor",
}
b.finalize(PRIORITY)
assert len(b.rows) >= TARGET_MIN, f"Only {len(b.rows)} rows"
assert len(b.rows) <= TARGET_MAX
b.write("batch-003", "Marvel X-Men family — modern to Oct 1986",
        "X-Men titles, modern → Oct 1986 floor")
b.report()
Path("/tmp/batch-003-skipped.json").write_text(__import__("json").dumps(b.skipped, indent=2))
print("OK")

#!/usr/bin/env python3
"""
Mass Marvel Comics permanent-archive fill: 1980-01-01 → present.

Priority: Amazing Spider-Man family → Uncanny/X-Men → Avengers → Daredevil /
Hulk / Thor / Cap / Iron Man / FF → Venom / Deadpool / Wolverine → events.
Dedupes against comics.ts + all batch-*.json. Comic Vine rate-limited (420);
dates/numbering use bibliographic anchors with monthly interpolation.
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter

from comic_backlog_common import (
    FLOOR, BatchBuilder, load_blocklists, cover, interp_date, add_months, BACKLOG,
)

PUB = "Marvel Comics"
PAL_ASM = "dc2626,1e3a8a,f8fafc"
PAL_X = "fbbf24,1e3a8a,dc2626"
PAL_AVE = "1e3a8a,dc2626,fbbf24"
PAL_DD = "7f1d1d,111827,f8fafc"
PAL_HULK = "166534,fbbf24,111827"
PAL_THOR = "1e3a8a,fbbf24,f8fafc"
PAL_CAP = "1e3a8a,dc2626,f8fafc"
PAL_IM = "a16207,dc2626,111827"
PAL_FF = "1e3a8a,fbbf24,dc2626"
PAL_VEN = "111827,166534,dc2626"
PAL_DP = "111827,dc2626,f8fafc"
PAL_WOLV = "a16207,111827,f8fafc"
PAL_EVT = "7c2d12,1e3a8a,e5e7eb"

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
b = BatchBuilder(PUB, PAL_ASM, EXISTING_IDS, EXISTING_KEYS, target_min=1, target_max=30000)


def msrp_era(y):
    if y < 1988: return 0.75
    if y < 1992: return 1.00
    if y < 1996: return 1.50
    if y < 2000: return 1.99
    if y < 2006: return 2.25
    if y < 2011: return 2.99
    if y < 2018: return 3.99
    if y < 2022: return 3.99
    return 4.99


def date_msrp(cd):
    return msrp_era(int(cd[:4]))


def anchor_date(n, anchors):
    """anchors: list of (issue, year, month) sorted by issue."""
    if n <= anchors[0][0]:
        return cover(anchors[0][1], anchors[0][2])
    if n >= anchors[-1][0]:
        return cover(anchors[-1][1], anchors[-1][2])
    for i in range(len(anchors) - 1):
        n0, y0, m0 = anchors[i]
        n1, y1, m1 = anchors[i + 1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(anchors[-1][1], anchors[-1][2])


def era_credits(n, eras):
    """eras: list of (max_issue_inclusive, writer, artist)."""
    for mx, w, a in eras:
        if n <= mx:
            return w, a
    return eras[-1][1], eras[-1][2]


# =============================================================================
# AMAZING SPIDER-MAN Vol. 1 — #200 (Jan 1980) → #700
# =============================================================================
ASM_ANCHORS = [
    (200, 1980, 1), (212, 1981, 1), (230, 1982, 7), (252, 1984, 5),
    (265, 1985, 6), (290, 1987, 7), (300, 1988, 5), (320, 1989, 9),
    (350, 1991, 8), (361, 1992, 4), (375, 1993, 3), (400, 1995, 4),
    (441, 1998, 11), (465, 2001, 7), (500, 2003, 12), (519, 2005, 6),
    (539, 2007, 4), (546, 2008, 1), (580, 2009, 3), (600, 2009, 9),
    (647, 2010, 12), (666, 2011, 7), (700, 2013, 2),
]
ASM_ERAS = [
    (225, "Denny O'Neil", "John Romita Jr."),
    (251, "Roger Stern", "John Romita Jr."),
    (284, "Tom DeFalco", "Ron Frenz"),
    (299, "David Michelinie", "Various"),
    (328, "David Michelinie", "Todd McFarlane"),
    (360, "David Michelinie", "Erik Larsen"),
    (388, "David Michelinie", "Mark Bagley"),
    (406, "J.M. DeMatteis", "Mark Bagley"),
    (440, "Howard Mackie", "Various"),
    (499, "Various", "Various"),
    (545, "J. Michael Straczynski", "John Romita Jr."),
    (647, "Dan Slott", "Various"),
    (700, "Dan Slott", "Humberto Ramos"),
]
ASM_KEYS = {
    200, 238, 252, 265, 298, 299, 300, 316, 317, 361, 375, 400,
    500, 538, 539, 546, 583, 600, 654, 700,
}
ASM_DESCS = {
    200: "Amazing Spider-Man #200 — anniversary landmark entering the 1980s.",
    238: "Nothing Can Stop the Juggernaut!",
    252: "Secret Wars black costume debut on cover / costume change.",
    265: "First appearance of Silver Sable.",
    298: "McFarlane art begins.",
    299: "Venom cameo / teaser.",
    300: "First full appearance of Venom.",
    316: "Venom vs Spider-Man classic.",
    317: "Venom arc continues.",
    361: "First full appearance of Carnage.",
    375: "Maximum Carnage era beat.",
    400: "Amazing Spider-Man #400 — Aunt May death (later retconned).",
    500: "Amazing Spider-Man #500 anniversary.",
    538: "One More Day setup.",
    539: "One More Day concludes / Brand New Day lead-in.",
    546: "Brand New Day begins.",
    583: "Obama cover / election era ASM.",
    600: "Amazing Spider-Man #600.",
    654: "Spider-Island lead-in.",
    700: "Dying Wish — Amazing Spider-Man #700.",
}
for n in range(200, 701):
    cd = anchor_date(n, ASM_ANCHORS)
    w, a = era_credits(n, ASM_ERAS)
    b.try_add(
        f"mv-asm-v1-{n}", "The Amazing Spider-Man", n, cd, w, a,
        ASM_DESCS.get(n, f"The Amazing Spider-Man #{n}."),
        date_msrp(cd),
        demand=2.5 if n in (300, 361, 700) else (1.3 if n in ASM_KEYS else 0.45),
        key=1 if n in ASM_KEYS else 0, palette=PAL_ASM,
    )
print("ASM_V1", len(b.rows))

# =============================================================================
# SPECTACULAR SPIDER-MAN — #39 (Feb 1980) → #263 (1998)
# =============================================================================
SPEC_ANCHORS = [
    (39, 1980, 2), (60, 1981, 11), (90, 1984, 5), (111, 1986, 2),
    (120, 1986, 11), (149, 1989, 4), (178, 1991, 7), (200, 1993, 5),
    (226, 1995, 7), (241, 1996, 12), (263, 1998, 11),
]
SPEC_KEYS = {39, 64, 90, 111, 134, 200, 221, 240, 263}
for n in range(39, 264):
    cd = anchor_date(n, SPEC_ANCHORS)
    w = "Bill Mantlo" if n < 80 else ("Peter David" if n < 140 else ("J.M. DeMatteis" if n < 200 else "Various"))
    a = "Various"
    b.try_add(
        f"mv-ssm-{n}", "The Spectacular Spider-Man", n, cd, w, a,
        ("Spectacular Spider-Man enters 1980." if n == 39
         else ("Final Spectacular Spider-Man issue." if n == 263
               else f"The Spectacular Spider-Man #{n}.")),
        date_msrp(cd), demand=1.0 if n in SPEC_KEYS else 0.35,
        key=1 if n in SPEC_KEYS else 0, palette=PAL_ASM,
    )
print("SPEC", len(b.rows))

# =============================================================================
# WEB OF SPIDER-MAN #1–129 (1985–1995)
# =============================================================================
WEB_ANCHORS = [(1, 1985, 4), (30, 1987, 9), (50, 1989, 5), (75, 1991, 4),
               (90, 1992, 7), (117, 1994, 10), (129, 1995, 10)]
WEB_KEYS = {1, 18, 32, 90, 117, 129}
for n in range(1, 130):
    cd = anchor_date(n, WEB_ANCHORS)
    b.try_add(
        f"mv-web-{n}", "Web of Spider-Man", n, cd,
        "Various", "Various",
        ("Web of Spider-Man #1 begins." if n == 1 else f"Web of Spider-Man #{n}."),
        date_msrp(cd), demand=1.2 if n == 1 else (0.9 if n in WEB_KEYS else 0.35),
        key=1 if n in WEB_KEYS else 0, palette=PAL_ASM,
    )
print("WEB", len(b.rows))

# =============================================================================
# PETER PARKER: SPIDER-MAN / Friendly Neighborhood gaps — skip; focus majors
# Spider-Man (1990) McFarlane #11–75 remaining (have 1–10)
# =============================================================================
SM90_ANCHORS = [(11, 1991, 6), (25, 1992, 8), (50, 1994, 9), (75, 1996, 12)]
for n in range(11, 76):
    cd = anchor_date(n, SM90_ANCHORS)
    w, a = ("Todd McFarlane", "Todd McFarlane") if n <= 14 else ("Various", "Various")
    b.try_add(
        f"mv-sm1990-{n}", "Spider-Man (1990)", n, cd, w, a,
        f"Spider-Man (1990) #{n}.", date_msrp(cd),
        demand=1.5 if n <= 14 else 0.4, key=1 if n in (11, 13, 50, 75) else 0, palette=PAL_ASM,
    )

# =============================================================================
# UNCANNY X-MEN — #129 (Jan 1980) → #544 (2004)
# =============================================================================
UXM_ANCHORS = [
    (129, 1980, 1), (137, 1980, 9), (141, 1981, 1), (150, 1981, 10),
    (162, 1982, 10), (171, 1983, 7), (183, 1984, 7), (200, 1985, 12),
    (201, 1986, 1), (210, 1986, 10), (225, 1988, 1), (244, 1989, 5),
    (266, 1990, 8), (280, 1991, 9), (300, 1993, 5), (350, 1997, 12),
    (375, 1999, 12), (400, 2001, 12), (444, 2004, 7), (486, 2007, 7),
    (500, 2008, 9), (544, 2011, 10),
]
# Claremont classic through ~280, then various; Morrison New X-Men used separate title
UXM_ERAS = [
    (143, "Chris Claremont", "John Byrne"),
    (175, "Chris Claremont", "Dave Cockrum"),
    (200, "Chris Claremont", "John Romita Jr."),
    (209, "Chris Claremont", "Various"),
    (245, "Chris Claremont", "Marc Silvestri"),
    (280, "Chris Claremont", "Jim Lee"),
    (304, "Various", "Various"),
    (350, "Various", "Various"),
    (380, "Various", "Various"),
    (450, "Various", "Various"),
    (544, "Various", "Various"),
]
UXM_KEYS = {
    129, 132, 135, 136, 137, 141, 142, 150, 162, 171, 172, 183,
    200, 201, 210, 211, 212, 213, 221, 266, 268, 275, 281, 300,
    350, 375, 400, 444, 500, 544,
}
UXM_DESCS = {
    129: "Proteus saga — Uncanny enters 1980.",
    132: "Kitty Pryde joins / early 80s Claremont-Byrne.",
    135: "Dark Phoenix lead-up.",
    136: "Dark Phoenix Saga peak.",
    137: "Dark Phoenix conclusion.",
    141: "Days of Future Past part 1.",
    142: "Days of Future Past part 2.",
    150: "Uncanny X-Men #150.",
    162: "Brood saga era.",
    171: "Rogue joins the X-Men.",
    172: "Binary / Carol era beat.",
    183: "First appearance of Forge.",
    200: "Uncanny X-Men #200 — Trial of Magneto.",
    201: "Mutant Massacre lead-in / Storm loses powers era.",
    210: "Mutant Massacre begins.",
    211: "Mutant Massacre continues.",
    212: "Mutant Massacre.",
    213: "Mutant Massacre aftermath.",
    221: "Fall of the Mutants era.",
    266: "First appearance of Gambit.",
    268: "Gambit / Storm classic.",
    275: "X-Tinction Agenda era.",
    281: "Muir Island Saga / Jim Lee peak.",
    300: "Uncanny X-Men #300.",
    350: "Uncanny X-Men #350.",
    375: "Uncanny X-Men #375.",
    400: "Uncanny X-Men #400.",
    444: "Reload / mid-2000s Uncanny.",
    500: "Uncanny X-Men #500.",
    544: "Final pre-Schism Uncanny numbering beat.",
}
for n in range(129, 545):
    cd = anchor_date(n, UXM_ANCHORS)
    w, a = era_credits(n, UXM_ERAS)
    b.try_add(
        f"mv-uxm-{n}", "The Uncanny X-Men", n, cd, w, a,
        UXM_DESCS.get(n, f"The Uncanny X-Men #{n}."),
        date_msrp(cd),
        demand=2.0 if n in (136, 137, 141, 142, 266) else (1.2 if n in UXM_KEYS else 0.45),
        key=1 if n in UXM_KEYS else 0, palette=PAL_X,
    )
print("UXM", len(b.rows))

# =============================================================================
# X-MEN (1991) #26–113 (have 2–25; #1 exists under "X-Men")
# =============================================================================
XM91_ANCHORS = [
    (26, 1993, 11), (40, 1995, 1), (50, 1996, 3), (70, 1997, 12),
    (90, 1999, 7), (100, 2000, 5), (113, 2001, 6),
]
XM91_KEYS = {26, 41, 50, 70, 90, 100, 113}
for n in range(26, 114):
    cd = anchor_date(n, XM91_ANCHORS)
    b.try_add(
        f"mv-xm1991-{n}", "X-Men (1991)", n, cd, "Various", "Various",
        ("X-Men (1991) continues past early Jim Lee run." if n == 26
         else ("Final X-Men (1991) before New X-Men renumber." if n == 113
               else f"X-Men (1991) #{n}.")),
        date_msrp(cd), demand=1.0 if n in XM91_KEYS else 0.4,
        key=1 if n in XM91_KEYS else 0, palette=PAL_X,
    )
# Ensure #1 under X-Men (1991) if missing (archive has X-Men #1 1991)
b.try_add("mv-xm1991-1", "X-Men (1991)", 1, cover(1991, 10),
          "Chris Claremont", "Jim Lee", "X-Men (1991) #1 — Jim Lee launch.",
          1.00, demand=2.5, key=1, palette=PAL_X)

# =============================================================================
# NEW MUTANTS #1–100 (1983–1991) — sparse archive
# =============================================================================
NM_ANCHORS = [(1, 1983, 3), (18, 1984, 8), (40, 1986, 6), (60, 1988, 2),
              (87, 1990, 3), (98, 1991, 2), (100, 1991, 4)]
NM_KEYS = {1, 18, 26, 87, 98, 100}
for n in range(1, 101):
    cd = anchor_date(n, NM_ANCHORS)
    w = "Chris Claremont" if n < 55 else ("Louise Simonson" if n < 98 else "Rob Liefeld / Fabian Nicieza")
    a = "Bob McLeod" if n < 5 else ("Bill Sienkiewicz" if 18 <= n <= 31 else ("Rob Liefeld" if n >= 87 else "Various"))
    b.try_add(
        f"mv-nm-{n}", "The New Mutants", n, cd, w, a,
        ("New Mutants #1 begins." if n == 1
         else ("Demon Bear saga." if n == 18
               else ("First Deadpool / Cable era New Mutants." if n == 87
                     else ("X-Force launch lead-in." if n == 100
                           else f"The New Mutants #{n}.")))),
        date_msrp(cd), demand=2.0 if n in (1, 87) else (1.0 if n in NM_KEYS else 0.4),
        key=1 if n in NM_KEYS else 0, palette=PAL_X,
    )

# X-Factor Vol 1 #17–70 (have early 1-ish sparse)
XF_ANCHORS = [(17, 1987, 6), (24, 1987, 11), (40, 1989, 5), (70, 1991, 9)]
for n in range(17, 71):
    cd = anchor_date(n, XF_ANCHORS)
    b.try_add(
        f"mv-xfactor-{n}", "X-Factor", n, cd,
        "Louise Simonson" if n < 70 else "Various", "Various",
        f"X-Factor #{n}.", date_msrp(cd),
        demand=1.2 if n in (24, 70) else 0.4, key=1 if n in (24, 70) else 0, palette=PAL_X,
    )

# X-Force (1991) #1–50
for n in range(1, 51):
    cd = interp_date(n, 1, 1991, 8, 50, 1995, 12)
    b.try_add(
        f"mv-xforce91-{n}", "X-Force (1991)", n, cd,
        "Fabian Nicieza" if n > 1 else "Rob Liefeld / Fabian Nicieza",
        "Rob Liefeld" if n <= 12 else "Various",
        ("X-Force #1 — polybag era smash." if n == 1 else f"X-Force (1991) #{n}."),
        date_msrp(cd), demand=2.2 if n == 1 else 0.45, key=1 if n in (1, 15, 25) else 0, palette=PAL_X,
    )
print("X_FAMILY", len(b.rows))

# =============================================================================
# AVENGERS Vol. 1 #194 (Apr 1980) → #402 (1996), then Heroes Return / Disassembled
# =============================================================================
AVE_ANCHORS = [
    (194, 1980, 4), (200, 1980, 10), (211, 1981, 9), (221, 1982, 7),
    (243, 1984, 5), (260, 1985, 10), (280, 1987, 6), (300, 1989, 2),
    (320, 1990, 8), (350, 1992, 8), (375, 1994, 6), (402, 1996, 9),
]
AVE_KEYS = {194, 200, 211, 221, 243, 260, 280, 300, 350, 375, 402}
for n in range(194, 403):
    cd = anchor_date(n, AVE_ANCHORS)
    w = "David Michelinie" if n < 212 else ("Roger Stern" if n < 264 else ("Various" if n < 350 else "Bob Harras"))
    b.try_add(
        f"mv-ave-v1-{n}", "The Avengers", n, cd, w, "Various",
        ("Avengers enter 1980." if n == 194
         else ("Final Avengers Vol. 1 before Heroes Reborn." if n == 402
               else f"The Avengers #{n}.")),
        date_msrp(cd), demand=1.1 if n in AVE_KEYS else 0.4,
        key=1 if n in AVE_KEYS else 0, palette=PAL_AVE,
    )

# Avengers Vol. 3 (Heroes Return) #1–84 (1998–2004)
for n in range(1, 85):
    cd = interp_date(n, 1, 1998, 2, 84, 2004, 8)
    b.try_add(
        f"mv-ave-v3-{n}", "Avengers (1998)", n, cd,
        "Kurt Busiek" if n <= 56 else "Geoff Johns",
        "George Pérez" if n <= 25 else "Various",
        ("Heroes Return Avengers #1." if n == 1 else f"Avengers (1998) #{n}."),
        date_msrp(cd), demand=1.4 if n == 1 else 0.4, key=1 if n in (1, 19, 56) else 0, palette=PAL_AVE,
    )

# Avengers #500–503 Disassembled (Vol 1 resume)
for n, m in [(500, 9), (501, 10), (502, 11), (503, 12)]:
    b.try_add(
        f"mv-ave-v1-{n}", "The Avengers", n, cover(2004, m),
        "Brian Michael Bendis", "David Finch",
        f"Avengers Disassembled — The Avengers #{n}.",
        2.25, demand=1.8, key=1, palette=PAL_AVE,
    )

# New Avengers (2005) #1–64
for n in range(1, 65):
    cd = interp_date(n, 1, 2005, 1, 64, 2010, 4)
    b.try_add(
        f"mv-newave-{n}", "New Avengers", n, cd,
        "Brian Michael Bendis", "David Finch" if n <= 10 else "Various",
        ("New Avengers #1 — Breakout." if n == 1 else f"New Avengers #{n}."),
        date_msrp(cd), demand=1.8 if n == 1 else 0.45, key=1 if n in (1, 25, 50) else 0, palette=PAL_AVE,
    )

# Mighty Avengers (2007) #1–36
for n in range(1, 37):
    cd = interp_date(n, 1, 2007, 5, 36, 2010, 4)
    b.try_add(
        f"mv-mightyave-{n}", "Mighty Avengers (2007)", n, cd,
        "Brian Michael Bendis" if n <= 20 else "Dan Slott", "Various",
        ("Mighty Avengers begins." if n == 1 else f"Mighty Avengers (2007) #{n}."),
        2.99, demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_AVE,
    )

# Avengers (2010) #1–34; Avengers (2012) #1–44; Avengers (2016)/(2018) samples denser
for n in range(1, 35):
    cd = interp_date(n, 1, 2010, 7, 34, 2013, 1)
    b.try_add(
        f"mv-ave-2010-{n}", "Avengers (2010)", n, cd,
        "Brian Michael Bendis", "John Romita Jr." if n <= 15 else "Various",
        ("Heroic Age Avengers begins." if n == 1 else f"Avengers (2010) #{n}."),
        3.99, demand=1.2 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_AVE,
    )
for n in range(1, 45):
    cd = interp_date(n, 1, 2013, 2, 44, 2015, 10)
    # archive has Avengers #1 2012-12 — key collision on series "Avengers" #1
    b.try_add(
        f"mv-ave-2012-{n}", "Avengers (2012)", n, cd,
        "Jonathan Hickman", "Various",
        ("Hickman Avengers begins." if n == 1 else f"Avengers (2012) #{n}."),
        3.99, demand=1.5 if n == 1 else 0.45, key=1 if n in (1, 24, 44) else 0, palette=PAL_AVE,
    )
for n in range(1, 39):
    cd = interp_date(n, 1, 2016, 12, 38, 2018, 3)
    b.try_add(
        f"mv-ave-2016-{n}", "Avengers (2016)", n, cd,
        "Mark Waid" if n <= 11 else "Various", "Various",
        ("All-New All-Different Avengers / 2016 Avengers." if n == 1 else f"Avengers (2016) #{n}."),
        3.99, demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_AVE,
    )
for n in range(1, 61):
    cd = interp_date(n, 1, 2018, 5, 60, 2023, 6)
    b.try_add(
        f"mv-ave-2018-{n}", "Avengers (2018)", n, cd,
        "Jason Aaron", "Various",
        ("Aaron Avengers begins." if n == 1 else f"Avengers (2018) #{n}."),
        3.99 if n < 40 else 4.99, demand=1.1 if n == 1 else 0.4,
        key=1 if n in (1, 50) else 0, palette=PAL_AVE,
    )
print("AVENGERS", len(b.rows))

# =============================================================================
# DAREDEVIL Vol. 1 #163 (Mar 1980) → #380; then Vol 2 / Waid / Soule / Zdarsky
# =============================================================================
DD_ANCHORS = [
    (163, 1980, 3), (168, 1981, 1), (181, 1982, 4), (191, 1983, 2),
    (227, 1986, 2), (250, 1988, 1), (282, 1990, 7), (300, 1992, 1),
    (320, 1993, 9), (340, 1995, 5), (360, 1997, 1), (380, 1998, 10),
]
DD_KEYS = {163, 168, 181, 184, 191, 227, 250, 300, 319, 344, 380}
DD_DESCS = {
    163: "Daredevil enters 1980 — pre-Miller buildup.",
    168: "Frank Miller art begins / Elektra debut era.",
    181: "Death of Elektra.",
    184: "Born Again lead-in.",
    191: "Born Again era.",
    227: "Miller / Mazzucchelli classic beat (archive also has key).",
    250: "Daredevil #250.",
    300: "Daredevil #300.",
    380: "Final Daredevil Vol. 1 issue.",
}
for n in range(163, 381):
    cd = anchor_date(n, DD_ANCHORS)
    if n < 191:
        w, a = "Frank Miller", "Frank Miller" if n < 177 else "Klaus Janson"
    elif n < 233:
        w, a = "Frank Miller" if n < 192 else "Various", "David Mazzucchelli" if 227 <= n <= 233 else "Various"
    else:
        w, a = "Various", "Various"
    b.try_add(
        f"mv-dd-v1-{n}", "Daredevil", n, cd, w, a,
        DD_DESCS.get(n, f"Daredevil #{n}."),
        date_msrp(cd), demand=2.0 if n in (168, 181, 227) else (1.1 if n in DD_KEYS else 0.4),
        key=1 if n in DD_KEYS else 0, palette=PAL_DD,
    )

# Daredevil Vol. 2 (1998) #1–119 Bendis/Brubaker era mostly
for n in range(1, 120):
    cd = interp_date(n, 1, 1998, 11, 119, 2009, 7)
    w = "Kevin Smith" if n <= 8 else ("Brian Michael Bendis" if n <= 50 else ("Ed Brubaker" if n <= 119 else "Various"))
    a = "Joe Quesada" if n <= 11 else ("Alex Maleev" if 26 <= n <= 50 else "Various")
    b.try_add(
        f"mv-dd-v2-{n}", "Daredevil (1998)", n, cd, w, a,
        ("Daredevil Vol. 2 #1 — Knights era." if n == 1 else f"Daredevil (1998) #{n}."),
        date_msrp(cd), demand=1.6 if n == 1 else 0.45, key=1 if n in (1, 16, 26, 50, 82) else 0, palette=PAL_DD,
    )

# Daredevil (2011) Waid #1–36; (2014) #1–21; (2015)/(2019)/(2022) denser
for n in range(1, 37):
    cd = interp_date(n, 1, 2011, 9, 36, 2014, 2)
    b.try_add(
        f"mv-dd-2011-{n}", "Daredevil (2011)", n, cd, "Mark Waid", "Marcos Martin" if n <= 5 else "Various",
        ("Waid Daredevil begins." if n == 1 else f"Daredevil (2011) #{n}."),
        2.99 if n < 20 else 3.99, demand=1.3 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_DD,
    )
for n in range(1, 22):
    cd = interp_date(n, 1, 2014, 5, 21, 2015, 9)
    b.try_add(
        f"mv-dd-2014-{n}", "Daredevil (2014)", n, cd, "Mark Waid", "Chris Samnee",
        ("Daredevil (2014) begins." if n == 1 else f"Daredevil (2014) #{n}."),
        3.99, demand=1.1 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_DD,
    )
for n in range(1, 29):
    cd = interp_date(n, 1, 2015, 12, 28, 2018, 4)
    b.try_add(
        f"mv-dd-2015-{n}", "Daredevil (2015)", n, cd, "Charles Soule", "Various",
        ("Soule Daredevil begins." if n == 1 else f"Daredevil (2015) #{n}."),
        3.99, demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_DD,
    )
for n in range(1, 37):
    cd = interp_date(n, 1, 2019, 4, 36, 2021, 9)
    b.try_add(
        f"mv-dd-2019-{n}", "Daredevil (2019)", n, cd, "Chip Zdarsky", "Marco Checchetto",
        ("Zdarsky Daredevil begins." if n == 1 else f"Daredevil (2019) #{n}."),
        3.99, demand=1.4 if n == 1 else 0.45, key=1 if n in (1, 25) else 0, palette=PAL_DD,
    )
print("DD", len(b.rows))

# =============================================================================
# INCREDIBLE HULK #242 (Dec 1979→1980 floor) → #474; then relaunches
# =============================================================================
HULK_ANCHORS = [
    (242, 1980, 1), (272, 1982, 6), (300, 1984, 10), (340, 1988, 2),
    (377, 1991, 1), (400, 1992, 12), (420, 1994, 8), (445, 1996, 9),
    (467, 1998, 8), (474, 1999, 3),
]
HULK_KEYS = {242, 272, 300, 340, 377, 400, 467, 474}
for n in range(242, 475):
    cd = anchor_date(n, HULK_ANCHORS)
    w = "Bill Mantlo" if n < 313 else ("John Byrne" if n < 330 else ("Peter David" if n < 468 else "Various"))
    b.try_add(
        f"mv-hulk-{n}", "The Incredible Hulk", n, cd, w, "Various",
        ("Incredible Hulk enters 1980." if n == 242
         else ("Peter David Hulk landmark." if n == 377
               else f"The Incredible Hulk #{n}.")),
        date_msrp(cd), demand=1.5 if n in (340, 377) else (1.0 if n in HULK_KEYS else 0.35),
        key=1 if n in HULK_KEYS else 0, palette=PAL_HULK,
    )

# Incredible Hulk (2000) #1–112; Immortal Hulk #2–50 (have #1)
for n in range(1, 113):
    cd = interp_date(n, 1, 2000, 2, 112, 2008, 1)
    b.try_add(
        f"mv-hulk-2000-{n}", "The Incredible Hulk (2000)", n, cd, "Various", "Various",
        ("Incredible Hulk (2000) begins." if n == 1 else f"The Incredible Hulk (2000) #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.35, key=1 if n in (1, 77, 92) else 0, palette=PAL_HULK,
    )
for n in range(2, 51):
    cd = interp_date(n, 1, 2018, 6, 50, 2021, 10)
    b.try_add(
        f"mv-immortal-hulk-{n}", "The Immortal Hulk", n, cd, "Al Ewing", "Joe Bennett",
        f"The Immortal Hulk #{n}.", 3.99, demand=1.2 if n in (2, 25, 50) else 0.5,
        key=1 if n in (25, 50) else 0, palette=PAL_HULK,
    )
print("HULK", len(b.rows))

# =============================================================================
# THOR #293 (Mar 1980) → #502; then various relaunches
# =============================================================================
THOR_ANCHORS = [
    (293, 1980, 3), (337, 1983, 11), (350, 1984, 12), (380, 1987, 6),
    (400, 1989, 2), (450, 1992, 8), (490, 1995, 9), (502, 1996, 9),
]
THOR_KEYS = {293, 337, 350, 380, 390, 400, 450, 502}
for n in range(293, 503):
    cd = anchor_date(n, THOR_ANCHORS)
    w = "Roy Thomas" if n < 307 else ("Doug Moench" if n < 337 else ("Walter Simonson" if n < 383 else "Various"))
    a = "Keith Pollard" if n < 320 else ("Walt Simonson" if 337 <= n <= 382 else "Various")
    b.try_add(
        f"mv-thor-{n}", "Thor", n, cd, w, a,
        ("Thor enters 1980." if n == 293
         else ("Walt Simonson Thor begins — #337." if n == 337
               else f"Thor #{n}.")),
        date_msrp(cd), demand=2.2 if n == 337 else (1.1 if n in THOR_KEYS else 0.4),
        key=1 if n in THOR_KEYS else 0, palette=PAL_THOR,
    )

# Thor Vol 2 (1998) #1–85; Thor (2007) #1–12; Thor (2014)/(2018)/(2020); Immortal Thor fill
for n in range(1, 86):
    cd = interp_date(n, 1, 1998, 7, 85, 2004, 12)
    b.try_add(
        f"mv-thor-v2-{n}", "Thor (1998)", n, cd,
        "Dan Jurgens" if n <= 79 else "Various", "Various",
        ("Heroes Return Thor begins." if n == 1 else f"Thor (1998) #{n}."),
        date_msrp(cd), demand=1.1 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_THOR,
    )
for n in range(1, 13):
    cd = interp_date(n, 1, 2007, 9, 12, 2008, 8)
    b.try_add(
        f"mv-thor-2007-{n}", "Thor (2007)", n, cd, "J. Michael Straczynski", "Olivier Coipel",
        ("Straczynski/Coipel Thor begins." if n == 1 else f"Thor (2007) #{n}."),
        2.99, demand=1.4 if n == 1 else 0.5, key=1 if n == 1 else 0, palette=PAL_THOR,
    )
for n in range(1, 25):
    cd = interp_date(n, 1, 2014, 12, 24, 2015, 11)
    b.try_add(
        f"mv-thor-2014-{n}", "Thor (2014)", n, cd, "Jason Aaron", "Russell Dauterman",
        ("Jane Foster Thor begins." if n == 1 else f"Thor (2014) #{n}."),
        3.99, demand=1.5 if n == 1 else 0.45, key=1 if n == 1 else 0, palette=PAL_THOR,
    )
for n in range(1, 17):
    cd = interp_date(n, 1, 2018, 8, 16, 2019, 9)
    b.try_add(
        f"mv-thor-2018-{n}", "Thor (2018)", n, cd, "Jason Aaron", "Various",
        ("Thor (2018) begins." if n == 1 else f"Thor (2018) #{n}."),
        3.99, demand=1.1 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_THOR,
    )
for n in range(1, 36):
    cd = interp_date(n, 1, 2020, 3, 35, 2023, 7)
    b.try_add(
        f"mv-thor-2020-{n}", "Thor (2020)", n, cd, "Donny Cates" if n <= 25 else "Various", "Various",
        ("Cates Thor begins." if n == 1 else f"Thor (2020) #{n}."),
        3.99, demand=1.2 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_THOR,
    )
for n in range(2, 26):
    cd = interp_date(n, 1, 2023, 8, 25, 2025, 8)
    b.try_add(
        f"mv-immortal-thor-{n}", "Immortal Thor", n, cd, "Al Ewing", "Various",
        f"Immortal Thor #{n}.", 4.99, demand=0.9 if n == 2 else 0.4, key=0, palette=PAL_THOR,
    )
print("THOR", len(b.rows))

# =============================================================================
# CAPTAIN AMERICA #241 (Jan 1980) → #454; then Brubaker etc.
# =============================================================================
CAP_ANCHORS = [
    (241, 1980, 1), (255, 1981, 3), (275, 1982, 11), (300, 1984, 12),
    (325, 1987, 1), (350, 1989, 2), (380, 1991, 10), (400, 1992, 5),
    (425, 1993, 11), (443, 1995, 9), (454, 1996, 8),
]
CAP_KEYS = {241, 255, 275, 300, 350, 383, 400, 454}
for n in range(241, 455):
    cd = anchor_date(n, CAP_ANCHORS)
    w = "Roger Stern" if n < 260 else ("J.M. DeMatteis" if n < 306 else ("Mark Gruenwald" if n < 444 else "Various"))
    b.try_add(
        f"mv-cap-{n}", "Captain America", n, cd, w, "Various",
        ("Captain America enters 1980." if n == 241
         else ("Cap #300 anniversary." if n == 300
               else f"Captain America #{n}.")),
        date_msrp(cd), demand=1.2 if n in CAP_KEYS else 0.35,
        key=1 if n in CAP_KEYS else 0, palette=PAL_CAP,
    )

# Cap Vol 4 / (2002) / Brubaker (2005) #1–50 denser; (2018) etc.
for n in range(1, 51):
    cd = interp_date(n, 1, 2005, 1, 50, 2009, 7)
    b.try_add(
        f"mv-cap-2005-{n}", "Captain America (2005)", n, cd,
        "Ed Brubaker", "Steve Epting" if n <= 25 else "Various",
        ("Brubaker Cap begins — Winter Soldier path." if n == 1 else f"Captain America (2005) #{n}."),
        date_msrp(cd), demand=2.0 if n == 1 else (1.5 if n in (25, 26) else 0.5),
        key=1 if n in (1, 25, 26) else 0, palette=PAL_CAP,
    )
for n in range(1, 26):
    cd = interp_date(n, 1, 2013, 1, 25, 2014, 10)
    b.try_add(
        f"mv-cap-2013-{n}", "Captain America (2013)", n, cd, "Rick Remender", "John Romita Jr.",
        ("Remender Cap begins." if n == 1 else f"Captain America (2013) #{n}."),
        3.99, demand=1.1 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_CAP,
    )
for n in range(1, 31):
    cd = interp_date(n, 1, 2018, 9, 30, 2021, 6)
    b.try_add(
        f"mv-cap-2018-{n}", "Captain America (2018)", n, cd, "Ta-Nehisi Coates", "Various",
        ("Coates Cap begins." if n == 1 else f"Captain America (2018) #{n}."),
        3.99, demand=1.3 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_CAP,
    )
print("CAP", len(b.rows))

# =============================================================================
# IRON MAN #130 (Jan 1980) → #332; then relaunches
# =============================================================================
IM_ANCHORS = [
    (130, 1980, 1), (150, 1981, 9), (170, 1983, 5), (200, 1985, 11),
    (218, 1987, 5), (231, 1988, 6), (250, 1989, 12), (280, 1992, 5),
    (300, 1994, 1), (320, 1995, 9), (332, 1996, 9),
]
IM_KEYS = {130, 150, 170, 192, 200, 218, 231, 250, 300, 332}
for n in range(130, 333):
    cd = anchor_date(n, IM_ANCHORS)
    w = "David Michelinie" if n < 155 else ("Various" if n < 215 else ("David Michelinie" if n < 250 else "Various"))
    a = "John Romita Jr." if n < 155 else ("Bob Layton" if n < 220 else "Various")
    b.try_add(
        f"mv-ironman-{n}", "Iron Man", n, cd, w, a,
        ("Iron Man enters 1980 — Demon in a Bottle aftermath era." if n == 130
         else ("Armor Wars begins." if n == 225
               else f"Iron Man #{n}.")),
        date_msrp(cd), demand=1.5 if n in (225, 231) else (1.0 if n in IM_KEYS else 0.35),
        key=1 if n in IM_KEYS or n in (225, 226) else 0, palette=PAL_IM,
    )
# Armor Wars key issues if in range — 225-232
for n in range(1, 90):
    cd = interp_date(n, 1, 1998, 11, 89, 2004, 12)
    b.try_add(
        f"mv-ironman-v3-{n}", "Iron Man (1998)", n, cd, "Various", "Various",
        ("Heroes Return Iron Man begins." if n == 1 else f"Iron Man (1998) #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_IM,
    )
for n in range(1, 34):
    cd = interp_date(n, 1, 2005, 1, 33, 2007, 8)
    b.try_add(
        f"mv-ironman-2005-{n}", "Iron Man (2005)", n, cd,
        "Warren Ellis" if n <= 6 else "Various", "Adi Granov" if n <= 6 else "Various",
        ("Extremis begins." if n == 1 else f"Iron Man (2005) #{n}."),
        2.99, demand=1.8 if n == 1 else 0.5, key=1 if n in (1, 5) else 0, palette=PAL_IM,
    )
for n in range(1, 29):
    cd = interp_date(n, 1, 2008, 5, 28, 2010, 6)
    b.try_add(
        f"mv-invincible-im-{n}", "Invincible Iron Man (2008)", n, cd, "Matt Fraction", "Salvador Larroca",
        ("Fraction/Larroca Iron Man begins." if n == 1 else f"Invincible Iron Man (2008) #{n}."),
        2.99, demand=1.3 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_IM,
    )
for n in range(1, 25):
    cd = interp_date(n, 1, 2012, 11, 24, 2014, 7)
    b.try_add(
        f"mv-ironman-2012-{n}", "Iron Man (2012)", n, cd, "Kieron Gillen", "Various",
        ("Gillen Iron Man begins." if n == 1 else f"Iron Man (2012) #{n}."),
        3.99, demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_IM,
    )
print("IRONMAN", len(b.rows))

# =============================================================================
# FANTASTIC FOUR #217 (Apr 1980) → #416; then Waid/Millar/Hickman/Slott
# =============================================================================
FF_ANCHORS = [
    (217, 1980, 4), (232, 1981, 7), (250, 1983, 1), (280, 1985, 7),
    (300, 1987, 3), (321, 1988, 12), (350, 1991, 3), (375, 1993, 4),
    (400, 1995, 5), (416, 1996, 9),
]
FF_KEYS = {217, 232, 236, 250, 280, 300, 347, 350, 400, 416}
for n in range(217, 417):
    cd = anchor_date(n, FF_ANCHORS)
    w = "John Byrne" if 232 <= n <= 293 else ("Various" if n < 232 else "Various")
    a = "John Byrne" if 232 <= n <= 293 else "Various"
    b.try_add(
        f"mv-ff-{n}", "Fantastic Four", n, cd, w, a,
        ("Fantastic Four enters 1980." if n == 217
         else ("Byrne Fantastic Four begins." if n == 232
               else f"Fantastic Four #{n}.")),
        date_msrp(cd), demand=1.5 if n == 232 else (1.0 if n in FF_KEYS else 0.4),
        key=1 if n in FF_KEYS else 0, palette=PAL_FF,
    )

for n in range(1, 71):
    cd = interp_date(n, 1, 1998, 1, 70, 2003, 8)
    b.try_add(
        f"mv-ff-v3-{n}", "Fantastic Four (1998)", n, cd, "Various", "Various",
        ("Heroes Return FF begins." if n == 1 else f"Fantastic Four (1998) #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_FF,
    )
for n in range(1, 61):
    # Vol 1 resume-ish / 2003 series often listed continuing — use FF (2003)
    cd = interp_date(n, 1, 2003, 6, 60, 2007, 12)
    w = "Mark Waid" if n <= 32 else ("J. Michael Straczynski" if n <= 45 else "Various")
    b.try_add(
        f"mv-ff-2003-{n}", "Fantastic Four (2003)", n, cd, w, "Mike Wieringo" if n <= 32 else "Various",
        ("Waid/Wieringo Fantastic Four begins." if n == 1 else f"Fantastic Four (2003) #{n}."),
        date_msrp(cd), demand=1.3 if n == 1 else 0.4, key=1 if n in (1, 30) else 0, palette=PAL_FF,
    )
for n in range(554, 589):  # Millar/Hitch bridge numbering commonly 554–569 then Hickman
    cd = interp_date(n, 554, 2008, 4, 588, 2011, 4)
    w = "Mark Millar" if n <= 569 else "Jonathan Hickman"
    b.try_add(
        f"mv-ff-v1-{n}", "Fantastic Four", n, cd, w, "Bryan Hitch" if n <= 569 else "Various",
        f"Fantastic Four #{n}.", 2.99, demand=1.2 if n in (554, 570) else 0.45,
        key=1 if n in (554, 570, 583) else 0, palette=PAL_FF,
    )
# Hickman FF continued into FF (2014) etc.; add 2014/2018/2022 runs
for n in range(1, 17):
    cd = interp_date(n, 1, 2014, 6, 16, 2015, 6)
    b.try_add(
        f"mv-ff-2014-{n}", "Fantastic Four (2014)", n, cd, "James Robinson" if n <= 5 else "Various", "Various",
        ("Fantastic Four (2014) begins." if n == 1 else f"Fantastic Four (2014) #{n}."),
        3.99, demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_FF,
    )
for n in range(1, 49):
    cd = interp_date(n, 1, 2018, 10, 48, 2022, 6)
    b.try_add(
        f"mv-ff-2018-{n}", "Fantastic Four (2018)", n, cd, "Dan Slott", "Various",
        ("Slott Fantastic Four begins." if n == 1 else f"Fantastic Four (2018) #{n}."),
        3.99, demand=1.2 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_FF,
    )
print("FF", len(b.rows))

# =============================================================================
# WOLVERINE (1988) #12–189 (have 2–11); mini already have #1 under Wolverine
# =============================================================================
WOLV_ANCHORS = [
    (12, 1989, 10), (50, 1991, 12), (75, 1993, 11), (100, 1996, 4),
    (125, 1998, 6), (150, 2000, 5), (175, 2002, 6), (189, 2003, 8),
]
WOLV_KEYS = {12, 41, 50, 75, 100, 125, 150, 175, 189}
for n in range(12, 190):
    cd = anchor_date(n, WOLV_ANCHORS)
    b.try_add(
        f"mv-wolv88-{n}", "Wolverine (1988)", n, cd, "Various", "Various",
        f"Wolverine (1988) #{n}.", date_msrp(cd),
        demand=1.0 if n in WOLV_KEYS else 0.35, key=1 if n in WOLV_KEYS else 0, palette=PAL_WOLV,
    )
# ensure #1
b.try_add("mv-wolv88-1", "Wolverine (1988)", 1, cover(1988, 11),
          "Chris Claremont", "John Buscema", "Wolverine ongoing #1 (1988).",
          1.50, demand=1.5, key=1, palette=PAL_WOLV)

# =============================================================================
# VENOM — Lethal Protector, along came a spider era, modern runs
# =============================================================================
for n in range(1, 7):
    b.try_add(
        f"mv-venom-lp-{n}", "Venom: Lethal Protector", n, cover(1993, 2 + n - 1),
        "David Michelinie", "Mark Bagley",
        ("Venom: Lethal Protector #1." if n == 1 else f"Venom: Lethal Protector #{n}."),
        1.75, demand=1.8 if n == 1 else 0.8, key=1 if n == 1 else 0, palette=PAL_VEN,
    )
for n in range(1, 5):
    b.try_add(
        f"mv-venom-funeral-{n}", "Venom: Funeral Pyre", n, cover(1993, 6 + n - 1),
        "Carl Potts", "John Estes", f"Venom: Funeral Pyre #{n}.",
        1.75, demand=0.7, key=0, palette=PAL_VEN,
    )
# Venom (2011) #1–42; (2016) #1–6; (2018) #2–35 (have #1); (2021)/(2023)
for n in range(1, 43):
    cd = interp_date(n, 1, 2011, 5, 42, 2013, 8)
    b.try_add(
        f"mv-venom-2011-{n}", "Venom (2011)", n, cd, "Rick Remender" if n <= 22 else "Various", "Various",
        ("Venom (2011) begins — Flash Thompson." if n == 1 else f"Venom (2011) #{n}."),
        2.99, demand=1.2 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_VEN,
    )
for n in range(1, 7):
    cd = cover(2016, 11 + n - 1) if n <= 2 else cover(2017, n - 2)
    b.try_add(
        f"mv-venom-2016-{n}", "Venom (2016)", n, cd, "Mike Costa", "Various",
        ("Venom (2016) begins." if n == 1 else f"Venom (2016) #{n}."),
        3.99, demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_VEN,
    )
for n in range(2, 36):
    cd = interp_date(n, 1, 2018, 5, 35, 2021, 4)
    b.try_add(
        f"mv-venom-2018-{n}", "Venom (2018)", n, cd, "Donny Cates", "Ryan Stegman",
        f"Venom (2018) #{n}.", 3.99, demand=1.3 if n in (2, 3) else 0.5,
        key=1 if n in (3, 25) else 0, palette=PAL_VEN,
    )
for n in range(1, 36):
    cd = interp_date(n, 1, 2021, 7, 35, 2024, 4)
    b.try_add(
        f"mv-venom-2021-{n}", "Venom (2021)", n, cd, "Al Ewing" if n <= 20 else "Various", "Various",
        ("Venom (2021) begins." if n == 1 else f"Venom (2021) #{n}."),
        3.99, demand=1.1 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_VEN,
    )
# Absolute Carnage / King in Black issue fills
for n in range(2, 6):
    b.try_add(f"mv-abs-carnage-{n}", "Absolute Carnage", n, cover(2019, 7 + n),
              "Donny Cates", "Ryan Stegman", f"Absolute Carnage #{n}.",
              4.99, demand=1.2, key=1, palette=PAL_VEN)
for n in range(2, 6):
    b.try_add(f"mv-kib-{n}", "King in Black", n, cover(2021, n),
              "Donny Cates", "Ryan Stegman", f"King in Black #{n}.",
              4.99, demand=1.3, key=1, palette=PAL_VEN)
print("VENOM", len(b.rows))

# =============================================================================
# DEADPOOL — early New Mutants/X-Force already; ongoing 1997 / 2008 / 2012 / 2015 / 2018 / 2022
# =============================================================================
for n in range(1, 5):
    b.try_add(
        f"mv-dp-minis94-{n}", "Deadpool: The Circle Chase", n, cover(1993, 8 + n - 1),
        "Fabian Nicieza", "Joe Madureira",
        ("Deadpool mini begins." if n == 1 else f"Deadpool: The Circle Chase #{n}."),
        1.75, demand=1.5 if n == 1 else 0.7, key=1 if n == 1 else 0, palette=PAL_DP,
    )
for n in range(1, 70):
    cd = interp_date(n, 1, 1997, 1, 69, 2002, 9)
    b.try_add(
        f"mv-dp-1997-{n}", "Deadpool (1997)", n, cd,
        "Joe Kelly" if n <= 33 else "Various", "Ed McGuinness" if n <= 11 else "Various",
        ("Deadpool ongoing #1 (1997)." if n == 1 else f"Deadpool (1997) #{n}."),
        date_msrp(cd), demand=1.8 if n == 1 else 0.45, key=1 if n in (1, 11) else 0, palette=PAL_DP,
    )
for n in range(1, 64):
    cd = interp_date(n, 1, 2008, 11, 63, 2012, 8)
    b.try_add(
        f"mv-dp-2008-{n}", "Deadpool (2008)", n, cd, "Daniel Way", "Various",
        ("Deadpool (2008) begins — modern hit era." if n == 1 else f"Deadpool (2008) #{n}."),
        2.99, demand=1.4 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_DP,
    )
for n in range(1, 46):
    cd = interp_date(n, 1, 2012, 11, 45, 2015, 2)
    b.try_add(
        f"mv-dp-2012-{n}", "Deadpool (2012)", n, cd, "Gerry Duggan / Brian Posehn", "Various",
        ("Deadpool (2012) begins." if n == 1 else f"Deadpool (2012) #{n}."),
        3.99, demand=1.2 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_DP,
    )
for n in range(1, 37):
    cd = interp_date(n, 1, 2015, 12, 36, 2017, 7)
    b.try_add(
        f"mv-dp-2015-{n}", "Deadpool (2015)", n, cd, "Gerry Duggan", "Various",
        ("Deadpool (2015) begins." if n == 1 else f"Deadpool (2015) #{n}."),
        3.99, demand=1.1 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_DP,
    )
for n in range(1, 11):
    cd = interp_date(n, 1, 2018, 5, 10, 2019, 2)
    b.try_add(
        f"mv-dp-2018-{n}", "Deadpool (2018)", n, cd, "Skottie Young" if n <= 6 else "Various", "Various",
        ("Deadpool (2018) begins." if n == 1 else f"Deadpool (2018) #{n}."),
        3.99, demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_DP,
    )
for n in range(1, 11):
    cd = interp_date(n, 1, 2022, 12, 10, 2023, 9)
    b.try_add(
        f"mv-dp-2022-{n}", "Deadpool (2022)", n, cd, "Various", "Various",
        ("Deadpool (2022) begins." if n == 1 else f"Deadpool (2022) #{n}."),
        4.99, demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_DP,
    )
print("DEADPOOL", len(b.rows))

# =============================================================================
# EVENTS / LIMITEDS essentials
# =============================================================================
events = []

def add_event(prefix, series, count, y0, m0, y1, m1, writer, artist, demand=1.5, msrp=None):
    for n in range(1, count + 1):
        cd = interp_date(n, 1, y0, m0, count, y1, m1)
        ms = msrp if msrp is not None else date_msrp(cd)
        events.append((
            f"{prefix}-{n}", series, str(n), cd, writer, artist,
            (f"{series} begins." if n == 1 else f"{series} #{n}."),
            ms, demand if n == 1 else demand * 0.75,
        ))

add_event("mv-sw", "Secret Wars", 12, 1984, 5, 1985, 4, "Jim Shooter", "Mike Zeck", 2.5, 0.75)
# archive has Secret Wars #1 1984 — will dedupe
add_event("mv-sw2", "Secret Wars II", 9, 1985, 7, 1986, 3, "Jim Shooter", "Al Milgrom", 1.2, 0.75)
add_event("mv-ig", "Infinity Gauntlet", 6, 1991, 7, 1991, 12, "Jim Starlin", "George Pérez", 2.2, 1.00)
add_event("mv-iw", "Infinity War", 6, 1992, 6, 1992, 11, "Jim Starlin", "Ron Lim", 1.3, 1.25)
add_event("mv-ic", "Infinity Crusade", 6, 1993, 6, 1993, 11, "Jim Starlin", "Ron Lim", 1.0, 1.50)
add_event("mv-onslaught", "Onslaught: Marvel Universe", 1, 1996, 10, 1996, 10, "Various", "Various", 1.0, 1.95)
# Heroes Reborn one-shots skipped; Civil War full
for n in range(1, 8):
    events.append((f"mv-cw-{n}", "Civil War", str(n),
                   interp_date(n, 1, 2006, 7, 7, 2007, 1),
                   "Mark Millar", "Steve McNiven",
                   ("Civil War begins." if n == 1 else f"Civil War #{n}."),
                   2.99, 2.2 if n == 1 else 1.5))
add_event("mv-wwih", "World War Hulk", 5, 2007, 8, 2007, 12, "Greg Pak", "John Romita Jr.", 1.4, 2.99)
# archive has WWH #1
add_event("mv-si", "Secret Invasion", 8, 2008, 6, 2009, 1, "Brian Michael Bendis", "Leinil Francis Yu", 1.6, 2.99)
add_event("mv-darkreign", "Dark Avengers", 16, 2009, 3, 2010, 6, "Brian Michael Bendis", "Mike Deodato", 1.3, 2.99)
add_event("mv-siege", "Siege", 4, 2010, 3, 2010, 6, "Brian Michael Bendis", "Olivier Coipel", 1.4, 3.99)
add_event("mv-fearitself", "Fear Itself", 7, 2011, 6, 2011, 12, "Matt Fraction", "Stuart Immonen", 1.3, 3.99)
add_event("mv-avx", "Avengers vs. X-Men", 12, 2012, 6, 2012, 12, "Various", "Various", 1.5, 3.99)
add_event("mv-infinity2013", "Infinity", 6, 2013, 9, 2014, 2, "Jonathan Hickman", "Various", 1.4, 3.99)
# archive has Infinity #1
add_event("mv-timelRuns", "Time Runs Out", 4, 2014, 12, 2015, 3, "Jonathan Hickman", "Various", 1.2, 3.99)
for n in range(1, 9):
    events.append((f"mv-sw2015-{n}", "Secret Wars (2015)", str(n),
                   interp_date(n, 1, 2015, 5, 9, 2016, 1),
                   "Jonathan Hickman", "Esad Ribić",
                   ("Secret Wars (2015) begins." if n == 1 else f"Secret Wars (2015) #{n}."),
                   4.99, 2.0 if n == 1 else 1.2))
add_event("mv-civilwar2", "Civil War II", 8, 2016, 6, 2016, 12, "Brian Michael Bendis", "David Marquez", 1.3, 3.99)
add_event("mv-se", "Secret Empire", 10, 2017, 4, 2017, 9, "Nick Spencer", "Various", 1.3, 3.99)
# archive has Secret Empire #0
add_event("mv-emp", "Empyre", 6, 2020, 7, 2020, 9, "Al Ewing / Dan Slott", "Various", 1.1, 4.99)
add_event("mv-dm", "Devil's Reign", 5, 2022, 2, 2022, 6, "Chip Zdarsky", "Marco Checchetto", 1.2, 4.99)
# archive has Devil's Reign #1 dated 2021-12
add_event("mv-judgw", "Judgment Day", 6, 2022, 7, 2022, 11, "Kieron Gillen", "Valerio Schiti", 1.2, 4.99)
add_event("mv-fh", "Fall of the House of X", 4, 2024, 3, 2024, 6, "Gerry Duggan", "Various", 1.0, 4.99)
add_event("mv-rh", "Rise of the Powers of X", 5, 2024, 3, 2024, 7, "Al Ewing", "Various", 1.0, 4.99)

# Infinity Gauntlet already; House of M
add_event("mv-hom", "House of M", 8, 2005, 8, 2005, 11, "Brian Michael Bendis", "Olivier Coipel", 1.6, 2.25)
add_event("mv-messiah", "X-Men: Messiah Complex", 1, 2007, 12, 2007, 12, "Various", "Various", 1.0, 2.99)
add_event("mv-schism", "X-Men: Schism", 5, 2011, 8, 2011, 11, "Jason Aaron", "Various", 1.2, 3.99)

for rid, series, issue, cd, w, a, desc, msrp, demand in events:
    b.try_add(rid, series, issue, cd, w, a, desc, msrp, demand=demand, key=1, palette=PAL_EVT)

print("EVENTS", len(b.rows))

# =============================================================================
# WEST COAST AVENGERS / ALPHA FLIGHT densify a bit + Moon Knight 1980
# =============================================================================
for n in range(1, 103):
    cd = interp_date(n, 1, 1984, 9, 102, 1994, 1) if n > 1 else cover(1984, 9)
    # archive has WCA #1
    b.try_add(
        f"mv-wca-{n}", "West Coast Avengers", n, cd,
        "Roger Stern" if n <= 10 else ("Steve Englehart" if n < 42 else "Various"), "Various",
        ("West Coast Avengers begins." if n == 1 else f"West Coast Avengers #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.3, key=1 if n in (1, 45) else 0, palette=PAL_AVE,
    )
for n in range(1, 131):
    cd = interp_date(n, 1, 1983, 8, 130, 1994, 3)
    b.try_add(
        f"mv-af-{n}", "Alpha Flight", n, cd,
        "John Byrne" if n <= 28 else "Various", "John Byrne" if n <= 28 else "Various",
        ("Alpha Flight #1." if n == 1 else f"Alpha Flight #{n}."),
        date_msrp(cd), demand=1.2 if n == 1 else 0.3, key=1 if n in (1, 12) else 0, palette=PAL_AVE,
    )
for n in range(1, 39):
    cd = interp_date(n, 1, 1980, 11, 38, 1984, 7)
    b.try_add(
        f"mv-mk-{n}", "Moon Knight", n, cd, "Doug Moench", "Bill Sienkiewicz" if n <= 15 else "Various",
        ("Moon Knight ongoing begins." if n == 1 else f"Moon Knight #{n}."),
        date_msrp(cd), demand=1.5 if n == 1 else 0.45, key=1 if n in (1, 15) else 0, palette=PAL_DD,
    )
print("SUPPORT", len(b.rows))

# Finalize
b.finalize(priority_series={
    "The Amazing Spider-Man", "The Uncanny X-Men", "The Avengers", "Daredevil",
    "The Incredible Hulk", "Thor", "Captain America", "Iron Man", "Fantastic Four",
    "Venom (2018)", "Deadpool (1997)", "Wolverine (1988)",
})
report = b.report()
out = b.write(
    "batch-007",
    "Marvel Comics mass archive fill — ASM → X-Men → Avengers → street/cosmic majors (1980→now)",
    "Marvel permanent archive gap-fill; floor 1980-01-01; major lines + events",
)
Path("/tmp/batch-007-skipped.json").write_text(json.dumps(b.skipped, indent=2))
Path("/tmp/batch-007-report.json").write_text(json.dumps({
    "count": report["count"],
    "date_max": report["date_max"],
    "date_min": report["date_min"],
    "archive_skipped": report["archive_skipped"],
    "total_skipped": report["total_skipped"],
    "breakdown": report["breakdown"][:100],
    "floor": FLOOR,
}, indent=2))
print("WROTE", out)

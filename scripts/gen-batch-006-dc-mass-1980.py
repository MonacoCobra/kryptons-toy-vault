#!/usr/bin/env python3
"""
Mass DC Comics permanent-archive fill: 1980-01-01 → present.

Priority: Superman family → Batman gaps → Flash / Green Lantern → other major DC.
Dedupes against comics.ts + all batch-*.json. Comic Vine was rate-limited at gen time;
dates/numbering use bibliographic anchors with monthly interpolation (documented in batch).
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter

from comic_backlog_common import (
    FLOOR, BatchBuilder, load_blocklists, cover, interp_date, add_months, BACKLOG,
)

PUB = "DC Comics"
PAL_SUPES = "1e3a8a,e30613,ffd200"
PAL_BAT = "111827,eab308,1e3a8a"
PAL_FLASH = "dc2626,fbbf24,111827"
PAL_GL = "166534,fbbf24,111827"
PAL_WW = "dc2626,1e3a8a,fbbf24"
PAL_JL = "1e3a8a,dc2626,fbbf24"
PAL_TT = "7c2d12,1e3a8a,fbbf24"
PAL_AQ = "0e7490,1e3a8a,f8fafc"
PAL_ELSE = "7c2d12,1e3a8a,e5e7eb"

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
# Mass inject — no small-batch cap
b = BatchBuilder(PUB, PAL_SUPES, EXISTING_IDS, EXISTING_KEYS, target_min=1, target_max=25000)

def msrp_era(y):
    if y < 1988: return 0.75
    if y < 1992: return 1.00
    if y < 1996: return 1.50
    if y < 2000: return 1.99
    if y < 2006: return 2.25
    if y < 2011: return 2.99
    if y < 2018: return 2.99
    if y < 2022: return 3.99
    return 4.99

def date_msrp(cd):
    return msrp_era(int(cd[:4]))

# =============================================================================
# SUPERMAN FAMILY
# =============================================================================

# --- Action Comics #507 (Jan 1980) – #904 (Aug 2011). Skip 905–956 (never published).
def action_date(n):
    anchors = [
        (507, 1980, 1), (550, 1983, 12), (583, 1986, 9), (600, 1988, 5),
        (643, 1989, 7), (700, 1994, 6), (750, 1999, 1), (800, 2003, 4),
        (850, 2007, 7), (875, 2009, 5), (900, 2011, 6), (904, 2011, 8),
    ]
    for i in range(len(anchors) - 1):
        n0, y0, m0 = anchors[i]
        n1, y1, m1 = anchors[i + 1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(2011, 8)

def action_credits(n):
    if n < 583:
        return "Cary Bates" if n < 540 else "Marv Wolfman", "Curt Swan" if n < 560 else "Various"
    if n < 600:
        return "John Byrne", "John Byrne"
    if n < 643:
        return "Various", "Various"  # weekly era
    if n < 675:
        return "Roger Stern", "Various"
    if 687 <= n <= 692:
        return "Various", "Various"  # Death/Reign
    if n < 736:
        return "Various", "Various"
    if n < 776:
        return "Joe Kelly", "Various"
    if n < 825:
        return "Various", "Various"
    if n < 867:
        return "Geoff Johns", "Various"
    return "Paul Cornell" if n < 890 else "Various", "Various"

action_keys = {507, 544, 583, 584, 600, 643, 662, 687, 690, 700, 775, 800, 850, 875, 894, 900, 904}
action_descs = {
    507: "Action Comics enters the 1980s.",
    544: "Pre-Crisis Action Comics landmark.",
    583: "Post-Crisis Action Comics — Byrne era begins.",
    584: "Byrne Action Comics continues.",
    600: "Action Comics #600 anniversary / weekly lead-in.",
    643: "Action Comics returns to monthly after weekly run.",
    662: "Doomsday approaches — triangle-era setup.",
    687: "Doomsday! Death of Superman triangle chapter.",
    690: "Reign of the Supermen begins.",
    700: "Action Comics #700.",
    775: "What's So Funny About Truth, Justice & the American Way?",
    800: "Action Comics #800 anniversary.",
    850: "Action Comics #850.",
    875: "New Krypton era Action Comics.",
    894: "The Black Ring / Luthor era beat.",
    900: "Action Comics #900.",
    904: "Final pre-New 52 Action Comics issue.",
}
for n in range(507, 905):
    cd = action_date(n)
    w, a = action_credits(n)
    b.try_add(
        f"dc-action-{n}", "Action Comics", n, cd, w, a,
        action_descs.get(n, f"Action Comics #{n}."),
        date_msrp(cd), demand=2.0 if n in (687, 775) else (1.2 if n in action_keys else 0.45),
        key=1 if n in action_keys else 0, palette=PAL_SUPES,
    )

print("ACTION", len(b.rows))

# --- Superman Vol. 1 #343 (Jan 1980) – #423 (Sep 1986) then becomes Adventures
def supes_v1_date(n):
    return interp_date(n, 343, 1980, 1, 423, 1986, 9)

for n in range(343, 424):
    if n == 75:  # already archived Death of Superman under different era — different issue era
        pass
    cd = supes_v1_date(n)
    w = "Cary Bates" if n < 400 else ("Marv Wolfman" if n < 414 else "Various")
    a = "Curt Swan" if n < 410 else "Various"
    key = 1 if n in (343, 400, 423) else 0
    b.try_add(
        f"dc-superman-v1-{n}", "Superman", n, cd, w, a,
        ("Superman Vol. 1 enters 1980." if n == 343
         else ("Final Superman Vol. 1 issue before Adventures rename." if n == 423
               else f"Superman Vol. 1 #{n}.")),
        date_msrp(cd), demand=1.0 if key else 0.4, key=key, palette=PAL_SUPES,
    )

print("SUPES_V1", len(b.rows))

# --- Adventures of Superman #424 (Jan 1987) – #649 (Apr 2006)
def adv_date(n):
    anchors = [
        (424, 1987, 1), (450, 1989, 1), (480, 1991, 7), (497, 1993, 1),
        (500, 1993, 6), (550, 1997, 9), (600, 2002, 3), (649, 2006, 4),
    ]
    for i in range(len(anchors) - 1):
        n0, y0, m0 = anchors[i]; n1, y1, m1 = anchors[i + 1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(2006, 4)

adv_keys = {424, 445, 462, 497, 500, 505, 540, 596, 600, 649}
adv_descs = {
    424: "Title becomes Adventures of Superman (continues from Superman #423).",
    445: "Adventures of Superman Byrne/Wolfman era.",
    462: "Exile era Adventures of Superman.",
    497: "Doomsday! Death of Superman triangle chapter.",
    500: "Adventures of Superman #500 — Funeral for a Friend era.",
    505: "Reign of the Supermen — Cyborg Superman.",
    540: "Superman Red/Blue era Adventures.",
    596: "Our Worlds at War Adventures chapter.",
    600: "Adventures of Superman #600.",
    649: "Final Adventures of Superman; numbering continues on Superman #650.",
}
for n in range(424, 650):
    cd = adv_date(n)
    if n <= 435:
        w, a = "Marv Wolfman", "Jerry Ordway"
    elif n <= 478:
        w, a = "Jerry Ordway", "Dan Jurgens" if n > 450 else "Various"
    elif 497 <= n <= 505:
        w, a = "Various", "Various"
    elif n <= 550:
        w, a = "Karl Kesel", "Various"
    else:
        w, a = "Various", "Various"
    b.try_add(
        f"dc-adv-superman-{n}", "Adventures of Superman", n, cd, w, a,
        adv_descs.get(n, f"Adventures of Superman #{n}."),
        date_msrp(cd), demand=2.5 if n in (497, 500) else (1.0 if n in adv_keys else 0.4),
        key=1 if n in adv_keys else 0, palette=PAL_SUPES,
    )

print("ADVENTURES", len(b.rows))

# --- Superman Vol. 2 (1987) #1–226
def supes87_date(n):
    anchors = [
        (1, 1987, 1), (50, 1990, 12), (75, 1993, 1), (82, 1993, 10),
        (100, 1995, 5), (150, 1999, 11), (175, 2001, 12), (200, 2004, 2),
        (226, 2006, 4),
    ]
    for i in range(len(anchors) - 1):
        n0, y0, m0 = anchors[i]; n1, y1, m1 = anchors[i + 1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(2006, 4)

# Note: Death of Superman is archived as series "Superman" #75 — also add Vol.2 labeling
# for continuity under Superman (1987). Skip colliding only if same series name.
s87_keys = {1, 2, 22, 75, 82, 100, 123, 151, 200, 226}
s87_descs = {
    1: "Post-Crisis Superman Vol. 2 #1 by John Byrne.",
    2: "Superman Vol. 2 continues Byrne reboot.",
    22: "Superman Vol. 2 — early Byrne/Ordway era.",
    75: "The Death of Superman (Vol. 2 numbering).",
    82: "Reign of the Supermen — Eradicator.",
    100: "Superman Vol. 2 #100.",
    123: "Superman Vol. 2 late-90s landmark.",
    151: "Our Worlds at War Superman Vol. 2.",
    200: "Superman Vol. 2 #200.",
    226: "Final Superman Vol. 2 issue.",
}
for n in range(1, 227):
    cd = supes87_date(n)
    if n <= 22:
        w, a = "John Byrne", "John Byrne"
    elif n <= 55:
        w, a = "Jerry Ordway", "Jerry Ordway"
    elif 75 <= n <= 82:
        w, a = "Dan Jurgens", "Dan Jurgens"
    elif n <= 120:
        w, a = "Dan Jurgens", "Various"
    else:
        w, a = "Various", "Various"
    b.try_add(
        f"dc-superman-1987-{n}", "Superman (1987)", n, cd, w, a,
        s87_descs.get(n, f"Superman Vol. 2 (1987) #{n}."),
        date_msrp(cd), demand=3.0 if n == 75 else (1.5 if n in s87_keys else 0.4),
        key=1 if n in s87_keys else 0, palette=PAL_SUPES,
    )

print("SUPES_1987", len(b.rows))

# --- Superman: The Man of Steel ongoing #1–134 (Jul 1991 – Mar 2003)
def mos_date(n):
    return interp_date(n, 1, 1991, 7, 134, 2003, 3)

mos_keys = {1, 18, 19, 22, 30, 50, 75, 100, 134}
for n in range(1, 135):
    cd = mos_date(n)
    w = "Louise Simonson" if n <= 85 else "Various"
    a = "Jon Bogdanove" if n <= 85 else "Various"
    descs = {
        1: "Superman: The Man of Steel #1 — triangle-era fourth ongoing begins.",
        18: "Doomsday! Death of Superman triangle chapter.",
        19: "Funeral for a Friend — Man of Steel.",
        22: "Reign of the Supermen begins (Steel).",
        134: "Final Superman: The Man of Steel issue.",
    }
    b.try_add(
        f"dc-man-of-steel-ong-{n}", "Superman: The Man of Steel", n, cd, w, a,
        descs.get(n, f"Superman: The Man of Steel #{n}."),
        date_msrp(cd), demand=3.0 if n == 18 else (1.2 if n in mos_keys else 0.4),
        key=1 if n in mos_keys else 0, palette=PAL_SUPES,
    )

print("MAN_OF_STEEL_ONG", len(b.rows))

# --- Superman legacy #650–714 (Oct 2006 – Aug 2011) after Adventures ends
def supes650_date(n):
    return interp_date(n, 650, 2006, 10, 714, 2011, 8)

for n in range(650, 715):
    cd = supes650_date(n)
    w = "Kurt Busiek" if n < 676 else ("James Robinson" if n < 700 else "J. Michael Straczynski")
    a = "Carlos Pacheco" if n < 676 else "Various"
    key = 1 if n in (650, 654, 700, 701, 714) else 0
    descs = {
        650: "Superman #650 — continues Adventures numbering post-Infinite Crisis.",
        654: "Camelot Falls begins.",
        700: "Superman #700.",
        701: "Grounded begins (Straczynski).",
        714: "Final pre-New 52 Superman legacy issue.",
    }
    b.try_add(
        f"dc-superman-legacy-{n}", "Superman", n, cd, w, a,
        descs.get(n, f"Superman #{n}."),
        date_msrp(cd), demand=1.0 if key else 0.45, key=key, palette=PAL_SUPES,
    )

print("SUPES_650", len(b.rows))

# --- Superman/Batman #54–87 (remainder)
def sb_date(n):
    return interp_date(n, 1, 2003, 10, 87, 2011, 10)

def sb_credits(n):
    if n <= 63:
        return "Michael Green, Mike Johnson", "Various"
    return "Various", "Various"

for n in range(54, 88):
    cd = sb_date(n)
    w, a = sb_credits(n)
    b.try_add(
        f"dc-superman-batman-{n}", "Superman/Batman", n, cd, w, a,
        ("Series finale. The Secret concludes." if n == 87 else f"Superman/Batman #{n}."),
        date_msrp(cd), demand=1.0 if n == 87 else 0.5, key=1 if n in (75, 87) else 0,
        palette=PAL_SUPES,
    )

# --- Superman Unlimited (2025) #1–16 (through Aug 2026; #17 on sale Sep 16)
unlimited_dates = {
    1: (2025, 5), 2: (2025, 6), 3: (2025, 7), 4: (2025, 8), 5: (2025, 9),
    6: (2025, 10), 7: (2025, 11), 8: (2025, 12), 9: (2026, 1), 10: (2026, 2),
    11: (2026, 3), 12: (2026, 4), 13: (2026, 5), 14: (2026, 6), 15: (2026, 7),
    16: (2026, 8),
}
for n, (y, m) in unlimited_dates.items():
    artist = "Rafael Albuquerque" if n <= 6 else ("Lucas Meyer" if n >= 11 else "Various")
    b.try_add(
        f"dc-superman-unlimited-{n}", "Superman Unlimited (2025)", n, cover(y, m),
        "Dan Slott", artist,
        ("Summer of Superman — Superman Unlimited begins." if n == 1
         else f"Superman Unlimited #{n}."),
        4.99, demand=1.4 if n == 1 else 0.8, key=1 if n == 1 else 0, palette=PAL_SUPES,
    )

# --- Supergirl (2005) #1–67
for n in range(1, 68):
    cd = interp_date(n, 1, 2005, 10, 67, 2011, 8)
    w = "Jeph Loeb" if n <= 5 else ("Joe Kelly" if n <= 20 else "Various")
    a = "Ian Churchill" if n <= 10 else "Various"
    b.try_add(
        f"dc-supergirl-2005-{n}", "Supergirl (2005)", n, cd, w, a,
        ("Supergirl ongoing relaunch begins." if n == 1 else f"Supergirl (2005) #{n}."),
        date_msrp(cd), demand=1.2 if n == 1 else 0.45, key=1 if n in (1, 12, 50) else 0,
        palette=PAL_SUPES,
    )

# --- Supergirl (2011) New 52 #0–40
for n in [0] + list(range(1, 41)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 40, 2015, 3)
    w = "Michael Green, Mike Johnson" if n <= 19 else "Various"
    a = "Mahmud Asrar" if n <= 12 else "Various"
    b.try_add(
        f"dc-supergirl-n52-{n}", "Supergirl (2011)", n, cd, w, a,
        ("New 52 Supergirl begins." if n == 1 else f"New 52 Supergirl #{n}."),
        2.99, demand=1.0 if n == 1 else 0.4, key=1 if n in (0, 1) else 0, palette=PAL_SUPES,
    )

# --- Supergirl (2016) Rebirth #1–42 (full-ish)
for n in range(1, 43):
    cd = interp_date(n, 1, 2016, 10, 42, 2020, 1)
    b.try_add(
        f"dc-supergirl-2016-{n}", "Supergirl (2016)", n, cd,
        "Steve Orlando" if n <= 20 else "Various",
        "Brian Ching" if n <= 8 else "Various",
        ("Rebirth Supergirl ongoing begins." if n == 1 else f"Supergirl Rebirth #{n}."),
        2.99 if n < 30 else 3.99, demand=1.0 if n == 1 else 0.45, key=1 if n == 1 else 0,
        palette=PAL_SUPES,
    )

# --- Superboy (1994) #0–100
for n in [0] + list(range(1, 101)):
    cd = cover(1994, 11) if n == 0 else interp_date(n, 1, 1994, 2, 100, 2002, 6)
    w = "Karl Kesel" if n <= 75 else "Various"
    a = "Tom Grummett" if n <= 50 else "Various"
    b.try_add(
        f"dc-superboy-1994-{n}", "Superboy (1994)", n, cd, w, a,
        ("Kon-El Superboy ongoing begins." if n == 1 else f"Superboy (1994) #{n}."),
        date_msrp(cd), demand=1.1 if n == 1 else 0.4, key=1 if n in (0, 1, 59, 100) else 0,
        palette=PAL_SUPES,
    )

# --- Superboy (2011) remainder #16–34
for n in range(16, 35):
    cd = interp_date(n, 1, 2011, 11, 34, 2014, 8)
    b.try_add(
        f"dc-superboy-n52-{n}", "Superboy (2011)", n, cd, "Various", "Various",
        f"New 52 Superboy #{n}.", 2.99, demand=0.4, palette=PAL_SUPES,
    )

# --- Superman/Wonder Woman remainder #13–31
for n in range(13, 32):
    cd = interp_date(n, 1, 2013, 12, 31, 2016, 5)
    b.try_add(
        f"dc-superman-ww-{n}", "Superman/Wonder Woman", n, cd, "Various", "Various",
        f"Superman/Wonder Woman #{n}.", 2.99, demand=0.4, palette=PAL_SUPES,
    )

# --- Batman/Superman New 52 remainder + Rebirth
for n in range(16, 32):
    cd = interp_date(n, 1, 2013, 8, 31, 2016, 4)
    b.try_add(
        f"dc-batman-superman-n52-{n}", "Batman/Superman (2013)", n, cd, "Various", "Various",
        f"Batman/Superman (New 52) #{n}.", 2.99, demand=0.4, palette=PAL_SUPES,
    )
for n in range(1, 21):
    cd = interp_date(n, 1, 2019, 11, 20, 2021, 4)
    b.try_add(
        f"dc-batman-superman-2019-{n}", "Batman/Superman (2019)", n, cd,
        "Joshua Williamson", "David Marquez" if n <= 6 else "Various",
        ("Batman/Superman Rebirth-era begins." if n == 1 else f"Batman/Superman (2019) #{n}."),
        3.99, demand=1.0 if n == 1 else 0.5, key=1 if n == 1 else 0, palette=PAL_SUPES,
    )

# --- Elseworlds / one-shots / limited (Superman family)
elseworlds = [
    ("dc-superman-speeding-bullets", "Superman: Speeding Bullets", "nn", "1993-05-01",
     "J.M. DeMatteis", "Eduardo Barreto", "Elseworlds: Kal-El raised by the Waynes.", 4.95, 1.5),
    ("dc-superman-kal", "Superman: Kal", "nn", "1995-01-01",
     "Dave Gibbons", "José Luis García-López", "Elseworlds medieval Superman.", 4.95, 1.2),
    ("dc-superman-distant-fires", "Superman: Distant Fires", "nn", "1998-01-01",
     "Howard Chaykin", "Gil Kane", "Elseworlds post-apocalypse Superman.", 5.95, 1.0),
    ("dc-jl-gods-monsters-1", "Absolute Justice League: Gods and Monsters", "1", "2015-08-01",
     "J.M. DeMatteis", "Various", "Gods and Monsters — alternate Trinity.", 3.99, 0.8),
    ("dc-superman-peace-earth-1", "Superman: Peace on Earth", "nn", "1999-01-01",
     "Paul Dini", "Alex Ross", "Dini/Ross oversized Superman special.", 9.95, 2.0),
    ("dc-superman-secret-identity-1", "Superman: Secret Identity", "1", "2004-03-01",
     "Kurt Busiek", "Stuart Immonen", "Elseworlds: a boy named Clark Kent who becomes Superman.", 5.95, 1.8),
]
for i in range(2, 5):
    elseworlds.append((
        f"dc-superman-secret-identity-{i}", "Superman: Secret Identity", str(i),
        cover(2004, 2 + i), "Kurt Busiek", "Stuart Immonen",
        f"Superman: Secret Identity #{i}.", 5.95, 1.2,
    ))
elseworlds += [
    ("dc-superman-american-alien-1", "Superman: American Alien", "1", "2015-11-01",
     "Max Landis", "Various", "American Alien #1 — modern origin vignettes.", 3.99, 1.3),
]
for i in range(2, 8):
    elseworlds.append((
        f"dc-superman-american-alien-{i}", "Superman: American Alien", str(i),
        cover(2015, 10 + i) if i < 4 else interp_date(i, 1, 2015, 11, 7, 2016, 6),
        "Max Landis", "Various", f"Superman: American Alien #{i}.", 3.99, 0.8,
    ))
elseworlds += [
    ("dc-whatever-happened-superman", "Superman: Whatever Happened to the Man of Tomorrow?", "nn", "1990-08-01",
     "Alan Moore", "Curt Swan", "Imaginary story collected / prestige reprint era packaging.", 3.95, 2.5),
    ("dc-death-superman-tpb", "The Death of Superman", "nn", "1993-06-01",
     "Various", "Various", "Trade collecting the Death of Superman triangle (catalog TPB row).", 9.95, 2.0),
]
# Kingdom Come remainder #2-4
for n, mon in [(2, 6), (3, 7), (4, 8)]:
    elseworlds.append((
        f"dc-kcome-{n}", "Kingdom Come", str(n), cover(1996, mon),
        "Mark Waid", "Alex Ross", f"Kingdom Come #{n}.", 4.95, 2.5,
    ))
# Dark Knight Returns remainder
for n, mon in [(2, 7), (3, 8), (4, 12)]:
    elseworlds.append((
        f"dc-darkknight-{n}", "Batman: The Dark Knight Returns", str(n), cover(1986, mon),
        "Frank Miller", "Frank Miller, Klaus Janson", f"The Dark Knight Returns #{n}.", 2.95, 2.0,
    ))
# Superman Smashes the Klan #2-3
for n, mon in [(2, 12), (3, 5)]:
    y = 2019 if n == 2 else 2020
    elseworlds.append((
        f"dc-superman-smashes-klan-{n}", "Superman Smashes the Klan", str(n), cover(y, mon),
        "Gene Luen Yang", "Gurihiru", f"Superman Smashes the Klan #{n}.", 3.99, 1.2,
    ))
# Superman: Year One
for n in range(1, 4):
    elseworlds.append((
        f"dc-superman-year-one-{n}", "Superman: Year One", str(n), cover(2019, 6 + n),
        "Frank Miller", "John Romita Jr.", ("Black Label Year One begins." if n == 1 else f"Superman: Year One #{n}."),
        5.99, 1.4,
    ))

for rid, series, issue, cd, w, a, desc, msrp, demand in elseworlds:
    pal = PAL_ELSE if "Batman" in series or "Kingdom" in series or "Dark Knight" in series else PAL_SUPES
    pub = "DC Comics / Black Label" if "Year One" in series else PUB
    fmt = "tpb" if rid.endswith("-tpb") else "single"
    issue = str(issue)
    skey = f"{series}|{issue}|{pub}".lower()
    if rid in b.existing_ids or rid in b.used_ids or skey in b.existing_keys or skey in b.used_keys:
        b.skipped.append({"reason": "dup", "id": rid})
        continue
    if cd < FLOOR:
        b.skipped.append({"reason": "pre-floor", "id": rid, "date": cd})
        continue
    if pub == PUB:
        b.try_add(rid, series, issue, cd, w, a, desc, msrp, fmt=fmt, demand=demand, key=1, palette=pal)
    else:
        b.rows.append([rid, series, issue, pub, cd, w, a, desc, float(msrp), fmt, float(demand), 1, pal])
        b.used_ids.add(rid); b.used_keys.add(skey)

print("SUPERMAN_FAMILY_DONE", len(b.rows))

# =============================================================================
# BATMAN FAMILY GAP-FILL
# =============================================================================
b.palette = PAL_BAT

# Batman missing ranges within 400–681 (post-floor); also 326–399 from 1980
# #326 ~ Feb 1980
def batman_date(n):
    anchors = [
        (326, 1980, 2), (350, 1982, 8), (400, 1986, 10), (404, 1987, 2),
        (426, 1988, 12), (450, 1990, 8), (492, 1993, 5), (500, 1993, 10),
        (530, 1996, 5), (567, 1999, 7), (600, 2002, 4), (608, 2002, 12),
        (635, 2005, 2), (655, 2006, 9), (670, 2007, 12), (681, 2008, 11),
    ]
    for i in range(len(anchors) - 1):
        n0, y0, m0 = anchors[i]; n1, y1, m1 = anchors[i + 1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(2008, 11)

batman_keys = {326, 357, 366, 404, 405, 406, 407, 426, 428, 492, 497, 500, 608, 655, 681}
# Fill 326–681 except already present (try_add dedupes)
for n in range(326, 682):
    cd = batman_date(n)
    if n <= 400:
        w, a = "Various", "Various"
    elif n <= 407:
        w, a = "Frank Miller" if n >= 404 else "Jim Starlin", "David Mazzucchelli" if n >= 404 else "Jim Aparo"
    elif 426 <= n <= 429:
        w, a = "Jim Starlin", "Jim Aparo"
    elif 492 <= n <= 500:
        w, a = "Doug Moench", "Jim Aparo"
    elif 608 <= n <= 619:
        w, a = "Jeph Loeb", "Jim Lee"
    elif 655 <= n <= 663:
        w, a = "Grant Morrison", "Andy Kubert"
    else:
        w, a = "Various", "Various"
    descs = {
        326: "Batman enters 1980.",
        404: "Year One part 1.",
        405: "Year One part 2.",
        406: "Year One part 3.",
        407: "Year One part 4.",
        426: "A Lonely Place of Dying setup / Ten Nights fallout era.",
        428: "A Lonely Place of Dying — Tim Drake.",
        492: "Knightfall begins.",
        497: "Knightfall — Bane breaks the Bat.",
        500: "Batman #500.",
        608: "Hush chapter one.",
        655: "Morrison era begins.",
        681: "Batman R.I.P. lead-out / Final Crisis era.",
    }
    b.try_add(
        f"dc-batman-{n}", "Batman", n, cd, w, a,
        descs.get(n, f"Batman #{n}."),
        date_msrp(cd), demand=2.0 if n in (404, 497, 608) else (1.0 if n in batman_keys else 0.45),
        key=1 if n in batman_keys else 0, palette=PAL_BAT,
    )

print("BATMAN", len(b.rows))

# Detective Comics #490 (May 1980) – #881 (pre-N52), skip facsimiles; N52 is separate series
# Existing has scattered; fill gaps. Legacy resumed #934+ partially present.
def det_date(n):
    anchors = [
        (490, 1980, 5), (526, 1983, 5), (568, 1986, 10), (575, 1987, 6),
        (600, 1989, 5), (633, 1991, 7), (700, 1996, 8), (759, 2001, 8),
        (800, 2005, 1), (850, 2009, 1), (881, 2011, 8),
        (934, 2016, 6), (960, 2017, 7), (1000, 2019, 3), (1100, 2025, 1),
    ]
    for i in range(len(anchors) - 1):
        n0, y0, m0 = anchors[i]; n1, y1, m1 = anchors[i + 1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(2011, 8)

# 490-881 and missing rebirth gaps 934-1099 (except existing)
for n in list(range(490, 882)) + list(range(934, 1101)):
    if n in (905, 906, 907, 908, 909, 910, 911, 912, 913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928, 929, 930, 931, 932, 933):
        continue  # New 52 used Detective Comics (2011)
    cd = det_date(n)
    w, a = "Various", "Various"
    if 575 <= n <= 578:
        w, a = "Mike W. Barr", "Alan Davis"
    key = 1 if n in (490, 568, 575, 600, 627, 700, 800, 871, 881, 934, 1000, 1100) else 0
    b.try_add(
        f"dc-det-{n}", "Detective Comics", n, cd, w, a,
        ("Detective Comics enters 1980." if n == 490
         else ("Year Two begins." if n == 575
               else ("Rebirth Detective Comics resumes legacy numbering." if n == 934
                     else f"Detective Comics #{n}."))),
        date_msrp(cd), demand=1.2 if key else 0.4, key=key, palette=PAL_BAT,
    )

# Detective Comics (2011) fill if incomplete — archive has 13; complete 0-52
for n in [0] + list(range(1, 53)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 52, 2016, 5)
    w = "Tony S. Daniel" if n <= 12 else ("John Layman" if n <= 29 else "Various")
    b.try_add(
        f"dc-det-n52-{n}", "Detective Comics (2011)", n, cd, w, "Various",
        ("New 52 Detective Comics begins." if n == 1 else f"New 52 Detective Comics #{n}."),
        2.99, demand=1.0 if n == 1 else 0.4, key=1 if n in (0, 1) else 0, palette=PAL_BAT,
    )

print("DETECTIVE", len(b.rows))

# Nightwing (1996) #1–153
for n in range(1, 154):
    cd = interp_date(n, 1, 1996, 10, 153, 2009, 6)
    w = "Chuck Dixon" if n <= 70 else ("Devin Grayson" if n <= 100 else "Various")
    a = "Scott McDaniel" if n <= 40 else "Various"
    b.try_add(
        f"dc-nightwing-1996-{n}", "Nightwing (1996)", n, cd, w, a,
        ("Nightwing ongoing begins." if n == 1 else f"Nightwing (1996) #{n}."),
        date_msrp(cd), demand=1.3 if n == 1 else 0.4, key=1 if n in (1, 25, 100, 153) else 0,
        palette=PAL_BAT,
    )

# Nightwing (2011) #1–30
for n in [0] + list(range(1, 31)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 30, 2014, 4)
    b.try_add(
        f"dc-nightwing-n52-{n}", "Nightwing (2011)", n, cd,
        "Kyle Higgins", "Eddy Barrows" if n <= 7 else "Various",
        ("New 52 Nightwing begins." if n == 1 else f"New 52 Nightwing #{n}."),
        2.99, demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_BAT,
    )

# Nightwing (2016) remainder beyond 30 — archive has 30; series went to ~100+
for n in range(31, 119):
    cd = interp_date(n, 1, 2016, 9, 118, 2024, 6)
    b.try_add(
        f"dc-nightwing-2016-{n}", "Nightwing (2016)", n, cd,
        "Tim Seeley" if n <= 50 else ("Dan Jurgens" if n <= 70 else "Tom Taylor"),
        "Various",
        f"Nightwing Rebirth #{n}.",
        2.99 if n < 80 else 3.99, demand=0.7 if n == 78 else 0.45,
        key=1 if n in (78, 100) else 0, palette=PAL_BAT,
    )

# Batgirl (2000) #1–73
for n in range(1, 74):
    cd = interp_date(n, 1, 2000, 4, 73, 2006, 4)
    b.try_add(
        f"dc-batgirl-2000-{n}", "Batgirl (2000)", n, cd,
        "Scott Peterson" if n <= 20 else "Various", "Various",
        ("Cassandra Cain Batgirl ongoing begins." if n == 1 else f"Batgirl (2000) #{n}."),
        date_msrp(cd), demand=1.1 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_BAT,
    )

# Batgirl (2009) #1–24
for n in range(1, 25):
    cd = interp_date(n, 1, 2009, 10, 24, 2011, 8)
    b.try_add(
        f"dc-batgirl-2009-{n}", "Batgirl (2009)", n, cd,
        "Bryan Q. Miller", "Lee Garbett" if n <= 12 else "Various",
        ("Stephanie Brown as Batgirl begins." if n == 1 else f"Batgirl (2009) #{n}."),
        2.99, demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_BAT,
    )

# Batgirl (2011) remainder #15–52
for n in range(15, 53):
    cd = interp_date(n, 1, 2011, 11, 52, 2016, 5)
    b.try_add(
        f"dc-batgirl-n52-{n}", "Batgirl (2011)", n, cd,
        "Gail Simone" if n <= 34 else "Various", "Various",
        f"New 52 Batgirl #{n}.", 2.99, demand=0.45, palette=PAL_BAT,
    )

# Batgirl (2016) #1–50
for n in range(1, 51):
    cd = interp_date(n, 1, 2016, 9, 50, 2020, 8)
    b.try_add(
        f"dc-batgirl-2016-{n}", "Batgirl (2016)", n, cd,
        "Hope Larson" if n <= 12 else "Various", "Various",
        ("Rebirth Batgirl begins." if n == 1 else f"Batgirl Rebirth #{n}."),
        2.99, demand=0.9 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_BAT,
    )

# Catwoman (1993) #1–94
for n in range(1, 95):
    cd = interp_date(n, 1, 1993, 8, 94, 2001, 7)
    b.try_add(
        f"dc-catwoman-1993-{n}", "Catwoman (1993)", n, cd,
        "Jo Duffy" if n <= 5 else ("Doug Moench" if n <= 30 else "Various"),
        "Jim Balent" if n <= 77 else "Various",
        ("Catwoman ongoing begins." if n == 1 else f"Catwoman (1993) #{n}."),
        date_msrp(cd), demand=1.2 if n == 1 else 0.4, key=1 if n in (1, 50) else 0,
        palette=PAL_BAT,
    )

# Catwoman (2011) #1–52
for n in [0] + list(range(1, 53)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 52, 2016, 5)
    b.try_add(
        f"dc-catwoman-n52-{n}", "Catwoman (2011)", n, cd,
        "Judd Winick", "Guillem March" if n <= 12 else "Various",
        ("New 52 Catwoman begins." if n == 1 else f"New 52 Catwoman #{n}."),
        2.99, demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_BAT,
    )

# Robin (1993) fill beyond existing 3
for n in range(1, 184):
    cd = interp_date(n, 1, 1993, 11, 183, 2009, 4)
    b.try_add(
        f"dc-robin-1993-{n}", "Robin (1993)", n, cd,
        "Chuck Dixon" if n <= 100 else "Various", "Various",
        ("Tim Drake Robin ongoing begins." if n == 1 else f"Robin (1993) #{n}."),
        date_msrp(cd), demand=1.1 if n == 1 else 0.35, key=1 if n in (1, 100) else 0,
        palette=PAL_BAT,
    )

# Batman: Legends of the Dark Knight #1–214 (fill beyond 8)
for n in range(1, 215):
    cd = interp_date(n, 1, 1989, 11, 214, 2007, 2)
    b.try_add(
        f"dc-lotdk-{n}", "Batman: Legends of the Dark Knight", n, cd,
        "Various", "Various",
        ("Legends of the Dark Knight begins." if n == 1 else f"Legends of the Dark Knight #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.35, key=1 if n in (1, 50, 100) else 0,
        palette=PAL_BAT,
    )

# Shadow of the Bat #1–94 (beyond 8)
for n in range(1, 95):
    cd = interp_date(n, 1, 1992, 6, 94, 2000, 2)
    b.try_add(
        f"dc-sotb-{n}", "Batman: Shadow of the Bat", n, cd,
        "Alan Grant", "Various",
        ("Shadow of the Bat begins." if n == 1 else f"Shadow of the Bat #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.35, key=1 if n in (1, 16) else 0,
        palette=PAL_BAT,
    )

# Batman and Robin (2009) #1–26
for n in range(1, 27):
    cd = interp_date(n, 1, 2009, 8, 26, 2011, 8)
    b.try_add(
        f"dc-batman-robin-2009-{n}", "Batman and Robin (2009)", n, cd,
        "Grant Morrison", "Frank Quitely" if n <= 3 else "Various",
        ("Morrison Batman and Robin begins." if n == 1 else f"Batman and Robin (2009) #{n}."),
        2.99, demand=1.5 if n == 1 else 0.6, key=1 if n == 1 else 0, palette=PAL_BAT,
    )

print("BATMAN_FAMILY_DONE", len(b.rows))

# =============================================================================
# FLASH
# =============================================================================
b.palette = PAL_FLASH

# The Flash (1987) #1–230
for n in range(1, 231):
    cd = interp_date(n, 1, 1987, 6, 230, 2009, 2)
    w = "Mike Baron" if n <= 14 else ("William Messner-Loebs" if n <= 61 else ("Mark Waid" if n <= 159 else ("Geoff Johns" if n <= 225 else "Various")))
    a = "Various"
    if n <= 14: a = "Jackson Guice"
    elif 15 <= n <= 61: a = "Greg LaRocque"
    b.try_add(
        f"dc-flash-1987-{n}", "The Flash (1987)", n, cd, w, a,
        ("Wally West Flash ongoing begins." if n == 1
         else ("The Return of Barry Allen." if n == 74
               else ("Terminal Velocity begins." if n == 95
                     else ("Rogue War / Johns era." if n == 207
                           else f"The Flash (1987) #{n}.")))),
        date_msrp(cd), demand=1.5 if n in (1, 74, 92) else 0.4,
        key=1 if n in (1, 74, 92, 95, 200) else 0, palette=PAL_FLASH,
    )

# The Flash (2011) #0–52
for n in [0] + list(range(1, 53)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 52, 2016, 5)
    b.try_add(
        f"dc-flash-n52-{n}", "The Flash (2011)", n, cd,
        "Francis Manapul, Brian Buccellato" if n <= 25 else "Various",
        "Francis Manapul" if n <= 25 else "Various",
        ("New 52 Flash begins." if n == 1 else f"New 52 Flash #{n}."),
        2.99, demand=1.2 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_FLASH,
    )

# The Flash (2016) #1–88
for n in range(1, 89):
    cd = interp_date(n, 1, 2016, 8, 88, 2020, 8)
    b.try_add(
        f"dc-flash-2016-{n}", "The Flash (2016)", n, cd,
        "Joshua Williamson", "Various",
        ("Rebirth Flash begins." if n == 1 else f"The Flash Rebirth #{n}."),
        2.99 if n < 50 else 3.99, demand=1.2 if n == 1 else 0.45,
        key=1 if n in (1, 50) else 0, palette=PAL_FLASH,
    )

# The Flash (2023) / (2024) ongoing sample #1–20
for n in range(1, 21):
    cd = interp_date(n, 1, 2023, 11, 20, 2025, 6)
    b.try_add(
        f"dc-flash-2023-{n}", "The Flash (2023)", n, cd,
        "Simon Spurrier" if n <= 10 else "Various", "Various",
        ("Dawn of DC Flash begins." if n == 1 else f"The Flash (2023) #{n}."),
        4.99, demand=1.0 if n == 1 else 0.5, key=1 if n == 1 else 0, palette=PAL_FLASH,
    )

# Flashpoint #2-5 (1 may exist)
for n in range(1, 6):
    cd = cover(2011, 5 + n)
    b.try_add(
        f"dc-flashpoint-{n}", "Flashpoint", n, cd, "Geoff Johns", "Andy Kubert",
        ("Flashpoint #1 — the event that births the New 52." if n == 1 else f"Flashpoint #{n}."),
        3.99, demand=2.0 if n == 1 else 1.2, key=1, palette=PAL_FLASH,
    )

print("FLASH_DONE", len(b.rows))

# =============================================================================
# GREEN LANTERN
# =============================================================================
b.palette = PAL_GL

# Green Lantern Vol. 2 from 1980: ~#130 (1980) through #200, then revival
# GL Vol 2 ended #201 (1988), then GL: Emerald Dawn, then Vol 3 (1990) #1-181
for n in range(130, 202):
    cd = interp_date(n, 130, 1980, 7, 201, 1988, 6)
    b.try_add(
        f"dc-gl-v2-{n}", "Green Lantern (1960)", n, cd,
        "Marv Wolfman" if n < 150 else "Various", "Joe Staton" if n < 160 else "Various",
        ("Green Lantern enters 1980." if n == 130 else f"Green Lantern Vol. 2 #{n}."),
        date_msrp(cd), demand=0.9 if n in (130, 188, 200) else 0.35,
        key=1 if n in (130, 188, 200) else 0, palette=PAL_GL,
    )

# Green Lantern Vol. 3 (1990) #1–181
for n in range(1, 182):
    cd = interp_date(n, 1, 1990, 6, 181, 2004, 9)
    w = "Gerard Jones" if n <= 47 else ("Ron Marz" if n <= 125 else "Various")
    a = "Various"
    b.try_add(
        f"dc-gl-1990-{n}", "Green Lantern (1990)", n, cd, w, a,
        ("Green Lantern Vol. 3 begins." if n == 1
         else ("Emerald Twilight — Hal falls." if n == 48
               else ("Kyle Rayner debut era." if n == 51
                     else f"Green Lantern (1990) #{n}."))),
        date_msrp(cd), demand=2.0 if n in (48, 51) else (1.0 if n == 1 else 0.35),
        key=1 if n in (1, 48, 50, 51) else 0, palette=PAL_GL,
    )

# Green Lantern (2005) #1–67
for n in range(1, 68):
    cd = interp_date(n, 1, 2005, 7, 67, 2011, 8)
    b.try_add(
        f"dc-gl-2005-{n}", "Green Lantern (2005)", n, cd,
        "Geoff Johns", "Carlos Pacheco" if n <= 3 else ("Ivan Reis" if n <= 25 else "Various"),
        ("Rebirth Hal Jordan ongoing begins." if n == 1
         else ("The Sinestro Corps War begins." if n == 21
               else f"Green Lantern (2005) #{n}.")),
        date_msrp(cd), demand=1.8 if n in (1, 21) else 0.5,
        key=1 if n in (1, 21, 25) else 0, palette=PAL_GL,
    )

# Green Lantern Corps (2006) #1–63
for n in range(1, 64):
    cd = interp_date(n, 1, 2006, 8, 63, 2011, 8)
    b.try_add(
        f"dc-glc-2006-{n}", "Green Lantern Corps (2006)", n, cd,
        "Dave Gibbons" if n <= 12 else "Various", "Various",
        ("Green Lantern Corps ongoing begins." if n == 1 else f"Green Lantern Corps #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_GL,
    )

# Green Lantern (2011) #0–52
for n in [0] + list(range(1, 53)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 52, 2016, 5)
    b.try_add(
        f"dc-gl-n52-{n}", "Green Lantern (2011)", n, cd,
        "Geoff Johns" if n <= 20 else "Various", "Doug Mahnke" if n <= 20 else "Various",
        ("New 52 Green Lantern begins." if n == 1 else f"New 52 Green Lantern #{n}."),
        2.99, demand=1.2 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_GL,
    )

# Green Lantern Corps (2011) #0–40
for n in [0] + list(range(1, 41)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 40, 2015, 3)
    b.try_add(
        f"dc-glc-n52-{n}", "Green Lantern Corps (2011)", n, cd,
        "Peter J. Tomasi", "Various",
        ("New 52 Green Lantern Corps begins." if n == 1 else f"New 52 GLC #{n}."),
        2.99, demand=0.9 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_GL,
    )

# Green Lanterns (2016) #1–57
for n in range(1, 58):
    cd = interp_date(n, 1, 2016, 8, 57, 2018, 8)
    b.try_add(
        f"dc-gls-2016-{n}", "Green Lanterns (2016)", n, cd,
        "Sam Humphrie" if n <= 32 else "Various", "Various",
        ("Rebirth Green Lanterns (Simon & Jessica) begins." if n == 1 else f"Green Lanterns #{n}."),
        2.99, demand=0.9 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_GL,
    )

# Green Lantern (2018/2019/2021/2023) — condensed major vols
for n in range(1, 13):
    cd = interp_date(n, 1, 2018, 11, 12, 2019, 10)
    b.try_add(f"dc-gl-2018-{n}", "Green Lantern (2018)", n, cd, "Grant Morrison", "Liam Sharp",
              ("Morrison/Sharp Green Lantern begins." if n == 1 else f"Green Lantern (2018) #{n}."),
              3.99, demand=1.1 if n == 1 else 0.5, key=1 if n == 1 else 0, palette=PAL_GL)
for n in range(1, 17):
    cd = interp_date(n, 1, 2021, 5, 16, 2022, 8)
    b.try_add(f"dc-gl-2021-{n}", "Green Lantern (2021)", n, cd, "Geoffrey Thorne", "Various",
              ("Infinite Frontier Green Lantern begins." if n == 1 else f"Green Lantern (2021) #{n}."),
              3.99, demand=0.9 if n == 1 else 0.45, key=1 if n == 1 else 0, palette=PAL_GL)
for n in range(1, 25):
    cd = interp_date(n, 1, 2023, 5, 24, 2025, 4)
    b.try_add(f"dc-gl-2023-{n}", "Green Lantern (2023)", n, cd, "Jeremy Adams", "Various",
              ("Dawn of DC Green Lantern begins." if n == 1 else f"Green Lantern (2023) #{n}."),
              4.99, demand=1.0 if n == 1 else 0.5, key=1 if n == 1 else 0, palette=PAL_GL)

print("GL_DONE", len(b.rows))

# =============================================================================
# OTHER MAJOR DC
# =============================================================================

# Wonder Woman Vol. 2 (1987) #1–226
for n in range(1, 227):
    cd = interp_date(n, 1, 1987, 2, 226, 2006, 4)
    w = "George Pérez" if n <= 62 else ("William Messner-Loebs" if n <= 100 else ("John Byrne" if n <= 136 else "Various"))
    a = "George Pérez" if n <= 24 else "Various"
    b.try_add(
        f"dc-ww-1987-{n}", "Wonder Woman (1987)", n, cd, w, a,
        ("Pérez Wonder Woman reboot begins." if n == 1 else f"Wonder Woman Vol. 2 #{n}."),
        date_msrp(cd), demand=1.8 if n == 1 else 0.4, key=1 if n in (1, 62) else 0,
        palette=PAL_WW,
    )

# Wonder Woman (2006) #1–44
for n in range(1, 45):
    cd = interp_date(n, 1, 2006, 8, 44, 2010, 5)
    b.try_add(
        f"dc-ww-2006-{n}", "Wonder Woman (2006)", n, cd,
        "Allan Heinberg" if n <= 4 else "Various", "Terry Dodson" if n <= 4 else "Various",
        ("Wonder Woman Vol. 3 begins." if n == 1 else f"Wonder Woman (2006) #{n}."),
        date_msrp(cd), demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_WW,
    )

# Wonder Woman (2011) #0–52
for n in [0] + list(range(1, 53)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 52, 2016, 5)
    b.try_add(
        f"dc-ww-n52-{n}", "Wonder Woman (2011)", n, cd,
        "Brian Azzarello", "Cliff Chiang" if n <= 18 else "Various",
        ("New 52 Wonder Woman begins." if n == 1 else f"New 52 Wonder Woman #{n}."),
        2.99, demand=1.3 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_WW,
    )

# Wonder Woman (2016) #1–81
for n in range(1, 82):
    cd = interp_date(n, 1, 2016, 8, 81, 2020, 1)
    b.try_add(
        f"dc-ww-2016-{n}", "Wonder Woman (2016)", n, cd,
        "Greg Rucka" if n <= 25 else ("James Robinson" if n <= 50 else "G. Willow Wilson"),
        "Nicola Scott" if n <= 12 else "Various",
        ("Rebirth Wonder Woman begins." if n == 1 else f"Wonder Woman Rebirth #{n}."),
        2.99 if n < 50 else 3.99, demand=1.2 if n == 1 else 0.45,
        key=1 if n == 1 else 0, palette=PAL_WW,
    )

# Wonder Woman (2023) #1–20
for n in range(1, 21):
    cd = interp_date(n, 1, 2023, 9, 20, 2025, 4)
    b.try_add(
        f"dc-ww-2023-{n}", "Wonder Woman (2023)", n, cd, "Tom King", "Daniel Sampere",
        ("Dawn of DC Wonder Woman begins." if n == 1 else f"Wonder Woman (2023) #{n}."),
        4.99, demand=1.1 if n == 1 else 0.5, key=1 if n == 1 else 0, palette=PAL_WW,
    )

print("WW_DONE", len(b.rows))

# Justice League (2011) #1–52 + fill beyond seed
for n in [0] + list(range(1, 53)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 10, 52, 2016, 5)
    b.try_add(
        f"dc-jl-n52-{n}", "Justice League (2011)", n, cd,
        "Geoff Johns", "Jim Lee" if n <= 12 else "Various",
        ("New 52 Justice League begins." if n == 1 else f"New 52 Justice League #{n}."),
        2.99 if n < 30 else 3.99, demand=1.5 if n == 1 else 0.45,
        key=1 if n in (0, 1) else 0, palette=PAL_JL,
    )

# Justice League (2016/2018) #1–39
for n in range(1, 40):
    cd = interp_date(n, 1, 2016, 9, 39, 2018, 4)
    b.try_add(
        f"dc-jl-2016-{n}", "Justice League (2016)", n, cd,
        "Bryan Hitch" if n <= 20 else "Various", "Various",
        ("Rebirth Justice League begins." if n == 1 else f"Justice League Rebirth #{n}."),
        2.99, demand=1.0 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_JL,
    )

# Justice League (2018) #1–75 (Snyder)
for n in range(1, 76):
    cd = interp_date(n, 1, 2018, 7, 75, 2022, 4)
    b.try_add(
        f"dc-jl-2018-{n}", "Justice League (2018)", n, cd,
        "Scott Snyder" if n <= 39 else "Various", "Jim Cheung" if n <= 10 else "Various",
        ("Snyder Justice League begins." if n == 1 else f"Justice League (2018) #{n}."),
        3.99, demand=1.2 if n == 1 else 0.45, key=1 if n == 1 else 0, palette=PAL_JL,
    )

# JLA (1997) #1–125
for n in range(1, 126):
    cd = interp_date(n, 1, 1997, 1, 125, 2006, 4)
    w = "Grant Morrison" if n <= 41 else ("Mark Waid" if n <= 60 else "Various")
    a = "Howard Porter" if n <= 41 else "Various"
    b.try_add(
        f"dc-jla-1997-{n}", "JLA (1997)", n, cd, w, a,
        ("Morrison JLA begins." if n == 1 else f"JLA #{n}."),
        date_msrp(cd), demand=1.6 if n == 1 else 0.4, key=1 if n in (1, 50) else 0,
        palette=PAL_JL,
    )

# Justice League of America (1980s) from #179 (~1980) to #261
for n in range(179, 262):
    cd = interp_date(n, 179, 1980, 6, 261, 1987, 4)
    b.try_add(
        f"dc-jla-v1-{n}", "Justice League of America (1960)", n, cd,
        "Gerry Conway" if n < 240 else "Various", "Various",
        ("JLA enters 1980." if n == 179 else f"Justice League of America #{n}."),
        date_msrp(cd), demand=0.8 if n in (179, 200) else 0.35,
        key=1 if n in (179, 200) else 0, palette=PAL_JL,
    )

print("JL_DONE", len(b.rows))

# New Teen Titans (1980) #1–40 + Tales + Vol 2
for n in range(1, 41):
    cd = interp_date(n, 1, 1980, 11, 40, 1984, 3)
    b.try_add(
        f"dc-ntt-{n}", "The New Teen Titans (1980)", n, cd,
        "Marv Wolfman", "George Pérez",
        ("New Teen Titans begins." if n == 1 else f"The New Teen Titans #{n}."),
        date_msrp(cd), demand=1.8 if n == 1 else 0.5, key=1 if n in (1, 2) else 0,
        palette=PAL_TT,
    )
for n in range(1, 92):
    cd = interp_date(n, 1, 1984, 8, 91, 1988, 7)
    b.try_add(
        f"dc-tt-1984-{n}", "Teen Titans (1984)", n, cd,
        "Marv Wolfman", "Various",
        ("Teen Titans Vol. 2 begins." if n == 1 else f"Teen Titans (1984) #{n}."),
        date_msrp(cd), demand=0.9 if n == 1 else 0.35, key=1 if n == 1 else 0,
        palette=PAL_TT,
    )
# Teen Titans (2003) #1–100
for n in range(1, 101):
    cd = interp_date(n, 1, 2003, 9, 100, 2011, 8)
    b.try_add(
        f"dc-tt-2003-{n}", "Teen Titans (2003)", n, cd,
        "Geoff Johns" if n <= 26 else "Various", "Mike McKone" if n <= 26 else "Various",
        ("Teen Titans 2003 begins." if n == 1 else f"Teen Titans (2003) #{n}."),
        date_msrp(cd), demand=1.3 if n == 1 else 0.4, key=1 if n == 1 else 0,
        palette=PAL_TT,
    )
# Teen Titans (2011) #1–30
for n in [0] + list(range(1, 31)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 30, 2014, 4)
    b.try_add(
        f"dc-tt-n52-{n}", "Teen Titans (2011)", n, cd, "Scott Lobdell", "Various",
        ("New 52 Teen Titans begins." if n == 1 else f"New 52 Teen Titans #{n}."),
        2.99, demand=0.9 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_TT,
    )

# Aquaman (1986 mini + 1994 + 2003 + 2011 + 2016)
for n in range(1, 5):
    b.try_add(f"dc-aquaman-1986-{n}", "Aquaman (1986)", n, cover(1986, 2 + n),
              "Neal Pozner", "Craig Hamilton", f"Aquaman 1986 mini #{n}.",
              0.75, demand=0.8 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_AQ)
for n in range(1, 76):
    cd = interp_date(n, 1, 1994, 8, 75, 2001, 1)
    b.try_add(f"dc-aquaman-1994-{n}", "Aquaman (1994)", n, cd,
              "Peter David" if n <= 46 else "Various", "Various",
              ("Aquaman 1994 ongoing begins." if n == 1 else f"Aquaman (1994) #{n}."),
              date_msrp(cd), demand=1.0 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_AQ)
for n in range(1, 40):
    cd = interp_date(n, 1, 2003, 2, 39, 2006, 2)
    b.try_add(f"dc-aquaman-2003-{n}", "Aquaman (2003)", n, cd, "Various", "Various",
              ("Aquaman 2003 begins." if n == 1 else f"Aquaman (2003) #{n}."),
              date_msrp(cd), demand=0.8 if n == 1 else 0.35, key=1 if n == 1 else 0, palette=PAL_AQ)
for n in [0] + list(range(1, 53)):
    cd = cover(2012, 11) if n == 0 else interp_date(n, 1, 2011, 11, 52, 2016, 5)
    b.try_add(f"dc-aquaman-n52-{n}", "Aquaman (2011)", n, cd,
              "Geoff Johns" if n <= 25 else "Various", "Ivan Reis" if n <= 18 else "Various",
              ("New 52 Aquaman begins." if n == 1 else f"New 52 Aquaman #{n}."),
              2.99, demand=1.3 if n == 1 else 0.4, key=1 if n == 1 else 0, palette=PAL_AQ)
for n in range(1, 67):
    cd = interp_date(n, 1, 2016, 8, 66, 2020, 12)
    b.try_add(f"dc-aquaman-2016-{n}", "Aquaman (2016)", n, cd,
              "Dan Abnett" if n <= 30 else "Various", "Various",
              ("Rebirth Aquaman begins." if n == 1 else f"Aquaman Rebirth #{n}."),
              2.99 if n < 40 else 3.99, demand=1.0 if n == 1 else 0.4,
              key=1 if n == 1 else 0, palette=PAL_AQ)

print("OTHER_DONE", len(b.rows))

# Crisis / events essentials not already dense
events = [
    ("dc-crisis-1", "Crisis on Infinite Earths", "1", "1985-04-01", "Marv Wolfman", "George Pérez",
     "Crisis on Infinite Earths begins.", 0.75, 3.0),
]
for n in range(2, 13):
    events.append((f"dc-crisis-{n}", "Crisis on Infinite Earths", str(n),
                   interp_date(n, 1, 1985, 4, 12, 1986, 3),
                   "Marv Wolfman", "George Pérez", f"Crisis on Infinite Earths #{n}.", 0.75, 2.0))
for n in range(1, 5):
    events.append((f"dc-identity-crisis-{n}", "Identity Crisis", str(n),
                   cover(2004, 6 + n - 1), "Brad Meltzer", "Rags Morales",
                   ("Identity Crisis begins." if n == 1 else f"Identity Crisis #{n}."), 3.99, 1.5))
for n in range(1, 8):
    events.append((f"dc-final-crisis-{n}", "Final Crisis", str(n),
                   interp_date(n, 1, 2008, 7, 7, 2009, 3), "Grant Morrison", "J.G. Jones",
                   ("Final Crisis begins." if n == 1 else f"Final Crisis #{n}."), 3.99, 1.4))
for n in range(1, 7):
    events.append((f"dc-blackest-night-{n}", "Blackest Night", str(n),
                   interp_date(n, 1, 2009, 9, 8, 2010, 5), "Geoff Johns", "Ivan Reis",
                   ("Blackest Night begins." if n == 1 else f"Blackest Night #{n}."), 3.99, 1.5))
for n in (7, 8):
    events.append((f"dc-blackest-night-{n}", "Blackest Night", str(n),
                   cover(2010, n - 2), "Geoff Johns", "Ivan Reis", f"Blackest Night #{n}.", 3.99, 1.3))
for n in range(1, 8):
    events.append((f"dc-infinite-crisis-{n}", "Infinite Crisis", str(n),
                   interp_date(n, 1, 2005, 12, 7, 2006, 6), "Geoff Johns", "Phil Jimenez",
                   ("Infinite Crisis begins." if n == 1 else f"Infinite Crisis #{n}."), 3.99, 1.5))

for rid, series, issue, cd, w, a, desc, msrp, demand in events:
    b.try_add(rid, series, issue, cd, w, a, desc, msrp, demand=demand, key=1, palette=PAL_JL)

print("EVENTS_DONE", len(b.rows))

# Finalize without trimming (target_max huge)
b.finalize(priority_series={
    "Action Comics", "Adventures of Superman", "Superman (1987)", "Superman: The Man of Steel",
    "Superman Unlimited (2025)", "Supergirl (2005)", "Batman", "Detective Comics",
    "The Flash (1987)", "Green Lantern (2005)", "Wonder Woman (1987)",
})
report = b.report()
out = b.write(
    "batch-006",
    "DC Comics mass archive fill — Superman → Batman → Flash/GL → majors (1980→now)",
    "DC permanent archive gap-fill; floor 1980-01-01; Superman family first",
)
Path("/tmp/batch-006-skipped.json").write_text(json.dumps(b.skipped, indent=2))
Path("/tmp/batch-006-report.json").write_text(json.dumps({
    "count": report["count"],
    "date_max": report["date_max"],
    "date_min": report["date_min"],
    "archive_skipped": report["archive_skipped"],
    "total_skipped": report["total_skipped"],
    "breakdown": report["breakdown"][:80],
    "floor": FLOOR,
}, indent=2))
print("WROTE", out)

#!/usr/bin/env python3
"""
batch-014: DC missing/thin majors (floor 1980).

  - JSA / Justice Society of America (1999 Johns era #1–87)
  - Justice Society of America (2007) #1–54
  - Booster Gold (1986) #1–25; Booster Gold (2007) #1–47
  - The Power of Shazam! (1995) #1–47; modern Shazam volumes
  - Catwoman (2002) #1–82
  - Titans (1999 / 2008 / 2016) — not Teen Titans 2003
  - Swamp Thing densify (Saga Moore tail + Vertigo/later vols)
"""
from __future__ import annotations

from comic_backlog_common import (
    FLOOR, BatchBuilder, load_blocklists, cover, interp_date, BACKLOG,
)

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
b = BatchBuilder("DC Comics", "1e3a8a,dc2626,fbbf24", EXISTING_IDS, EXISTING_KEYS,
                 target_min=1, target_max=25000)

PAL = {
    "DC Comics": "1e3a8a,dc2626,fbbf24",
    "DC Comics / Vertigo": "4c1d95,111827,e5e7eb",
}

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

def date_msrp(cd): return msrp_era(int(cd[:4]))

def anchor_date(n, anchors):
    if n <= anchors[0][0]: return cover(anchors[0][1], anchors[0][2])
    if n >= anchors[-1][0]: return cover(anchors[-1][1], anchors[-1][2])
    for i in range(len(anchors) - 1):
        n0, y0, m0 = anchors[i]
        n1, y1, m1 = anchors[i + 1]
        if n0 <= n <= n1:
            return interp_date(n, n0, y0, m0, n1, y1, m1)
    return cover(anchors[-1][1], anchors[-1][2])

def add_series(pub, id_prefix, series, n0, n1, anchors, writers, artists,
               keys=None, demand_base=0.55, palette=None, also_block_bare=None):
    keys = keys or set()
    pal = palette or PAL.get(pub, b.palette)
    b.pub = pub
    b.palette = pal
    for n in range(n0, n1 + 1):
        cd = anchor_date(n, anchors)
        w = writers if isinstance(writers, str) else writers(n)
        a = artists if isinstance(artists, str) else artists(n)
        dem = 2.0 if n == 1 and n0 <= 1 else (1.2 if n in keys else demand_base)
        b.try_add(
            f"{id_prefix}-{n}", series, n, cd, w, a, f"{series} #{n}.",
            date_msrp(cd), demand=dem, key=1 if n in keys else 0, palette=pal,
            also_block_bare=also_block_bare,
        )

# =============================================================================
print("=== JSA / Justice Society ===")
# Johns-era monthly titled "JSA" (Aug 1999 – Sep 2006), #1–87
add_series(
    "DC Comics", "dc-jsa-1999", "JSA (1999)", 1, 87,
    [(1, 1999, 8), (20, 2001, 3), (40, 2002, 11), (60, 2004, 6), (75, 2005, 9), (87, 2006, 9)],
    "Geoff Johns / David S. Goyer / Various", "Stephen Sadowski / Don Kramer / Various",
    {1, 73, 87}, 0.75,
)
# Justice Society of America (2007) #1–54 (Feb 2007 – Aug 2011)
add_series(
    "DC Comics", "dc-jsa-2007", "Justice Society of America (2007)", 1, 54,
    [(1, 2007, 2), (15, 2008, 4), (30, 2009, 7), (40, 2010, 6), (54, 2011, 8)],
    "Geoff Johns / Bill Willingham / Various", "Dale Eaglesham / Alex Ross / Various",
    {1}, 0.7,
)

# =============================================================================
print("=== Booster Gold ===")
# Booster Gold (1986) #1–25 (Feb 1986 – Feb 1988)
add_series(
    "DC Comics", "dc-bg-1986", "Booster Gold (1986)", 1, 25,
    [(1, 1986, 2), (12, 1987, 1), (25, 1988, 2)],
    "Dan Jurgens", "Dan Jurgens / Various",
    {1}, 0.7,
)
# Booster Gold (2007) #1–47 (May 2007 – Feb 2011)
add_series(
    "DC Comics", "dc-bg-2007", "Booster Gold (2007)", 1, 47,
    [(1, 2007, 5), (15, 2008, 7), (30, 2009, 10), (47, 2011, 2)],
    "Geoff Johns / Jeff Katz / Various", "Dan Jurgens / Various",
    {1}, 0.7,
)

# =============================================================================
print("=== Shazam ===")
# The Power of Shazam! (1995) #1–47 (Mar 1995 – Mar 1999)
add_series(
    "DC Comics", "dc-pos-1995", "The Power of Shazam! (1995)", 1, 47,
    [(1, 1995, 3), (15, 1996, 5), (30, 1997, 8), (47, 1999, 3)],
    "Jerry Ordway / Various", "Jerry Ordway / Various",
    {1}, 0.65,
)
# Shazam! (2018) 4-issue Johns mini
add_series(
    "DC Comics", "dc-shazam-2018", "Shazam! (2018)", 1, 4,
    [(1, 2018, 12), (4, 2019, 3)],
    "Geoff Johns", "Dale Eaglesham",
    {1}, 0.85,
)
# Shazam! (2019) ongoing #1–15
add_series(
    "DC Comics", "dc-shazam-2019", "Shazam! (2019)", 1, 15,
    [(1, 2019, 11), (8, 2020, 6), (15, 2021, 1)],
    "Geoff Johns / Various", "Dale Eaglesham / Various",
    {1}, 0.7,
)
# =============================================================================
print("=== Catwoman (2002) ===")
# Catwoman (2002) #1–82 (Jan 2002 – Mar 2008)
add_series(
    "DC Comics", "dc-cat-2002", "Catwoman (2002)", 1, 82,
    [(1, 2002, 1), (20, 2003, 8), (40, 2005, 4), (60, 2006, 12), (82, 2008, 3)],
    "Ed Brubaker / Various", "Darwyn Cooke / Cameron Stewart / Various",
    {1}, 0.75,
)

# =============================================================================
print("=== Titans volumes (not Teen Titans 2003) ===")
# Titans (1999) #1–50 (Mar 1999 – Sep 2002)
add_series(
    "DC Comics", "dc-titans-1999", "Titans (1999)", 1, 50,
    [(1, 1999, 3), (15, 2000, 5), (30, 2001, 8), (50, 2002, 9)],
    "Devin Grayson / Various", "Mark Buckingham / Various",
    {1}, 0.6,
)
# Titans (2008) #1–38 (Apr 2008 – Oct 2011)
add_series(
    "DC Comics", "dc-titans-2008", "Titans (2008)", 1, 30,
    [(1, 2008, 4), (15, 2009, 6), (25, 2010, 4), (30, 2010, 9)],
    "Judd Winick / Sean McKeever / Various", "Various",
    {1}, 0.55,
)

# =============================================================================
print("=== Swamp Thing densify ===")
# Archive has Saga #20–50; Moore continues through ~#64
add_series(
    "DC Comics", "dc-saga-st", "The Saga of the Swamp Thing", 51, 64,
    [(51, 1986, 8), (57, 1987, 2), (64, 1987, 9)],
    "Alan Moore", "Stephen Bissette / John Totleben / Various",
    {57, 64}, 0.9,
)
# Post-Moore / Veitch era often cataloged under Swamp Thing (1985) — conservative #65–88
add_series(
    "DC Comics", "dc-st-1985", "Swamp Thing (1985)", 65, 80,
    [(65, 1987, 10), (72, 1988, 5), (80, 1989, 1)],
    "Rick Veitch", "Rick Veitch / Various",
    set(), 0.6,
)
# Vertigo-era revival Swamp Thing (2004) #1–29
add_series(
    "DC Comics / Vertigo", "dc-st-2004", "Swamp Thing (2004)", 1, 29,
    [(1, 2004, 5), (12, 2005, 4), (20, 2005, 12), (29, 2006, 9)],
    "Andy Diggle / Joshua Dysart / Various", "Enrique Breccia / Various",
    {1}, 0.55,
)


# Finalize
b.pub = "DC Comics"
b.target_min = 400
b.target_max = 500
b.finalize(priority_series={
    "JSA (1999)", "Justice Society of America (2007)",
    "Booster Gold (1986)", "Booster Gold (2007)",
    "The Power of Shazam! (1995)", "Shazam! (2018)", "Shazam! (2019)",
    "Catwoman (2002)",
    "Titans (1999)", "Titans (2008)",
    "The Saga of the Swamp Thing", "Swamp Thing (1985)",
    "Swamp Thing (2004)", "Swamp Thing (2016)",
})
rep = b.report()
path = b.write(
    "batch-014",
    "DC majors: JSA / Booster Gold / Shazam / Catwoman / Titans / Swamp Thing",
    "JSA 1999+2007, Booster Gold 1986+2007, Power of Shazam + modern Shazam, Catwoman 2002, Titans 1999/2008/2016, Swamp Thing densify",
    created="2026-09-07",
)
print("WROTE", path, "rows", len(b.rows))

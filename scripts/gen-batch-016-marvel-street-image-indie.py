#!/usr/bin/env python3
"""
batch-016: Marvel street-level / team zeros + Image/indie densify (floor 1980).

  - Elektra, Iron Fist, Luke Cage (archive ZERO / near-zero)
  - Winter Soldier, Thunderbolts, Exiles, Young Avengers (ZERO)
  - Hawkeye densify; Defenders densify
  - Image/indie: Black Hammer, Die, Isola, Bitter Root, Farmhand,
    Rat Queens, Wytches densify, Angel (Dark Horse)
"""
from __future__ import annotations

from comic_backlog_common import (
    FLOOR, BatchBuilder, load_blocklists, cover, interp_date, BACKLOG,
)

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
b = BatchBuilder("Marvel Comics", "e30613,111827,f8fafc", EXISTING_IDS, EXISTING_KEYS,
                 target_min=1, target_max=25000)

PAL = {
    "Marvel Comics": "e30613,111827,f8fafc",
    "Image Comics": "f97316,1c1917,fafaf9",
    "Dark Horse Comics": "000000,ef4444,f5f5f4",
    "BOOM! Studios": "0ea5e9,0f172a,f8fafc",
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

print("=== Elektra ===")
add_series("Marvel Comics", "mv-elektra-1996", "Elektra (1996)", 1, 19,
    [(1, 1996, 11), (8, 1997, 6), (19, 1998, 8)],
    "D.G. Chichester / Various", "Joe Quesada / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-elektra-2001", "Elektra (2001)", 1, 35,
    [(1, 2001, 9), (10, 2002, 6), (22, 2003, 6), (35, 2004, 6)],
    "Kevin Smith / Greg Rucka / Various", "Carey Nord / Various", {1}, 0.75)
add_series("Marvel Comics", "mv-elektra-2014", "Elektra (2014)", 1, 11,
    [(1, 2014, 4), (6, 2014, 9), (11, 2015, 2)],
    "W. Haden Blackman / Various", "Michael Del Mundo / Various", {1}, 0.65)
add_series("Marvel Comics", "mv-elektra-2017", "Elektra (2017)", 1, 5,
    [(1, 2017, 4), (5, 2017, 8)],
    "Allyson DeMerce / Various", "Michael Dowling / Various", {1}, 0.6)

print("=== Iron Fist ===")
add_series("Marvel Comics", "mv-iif-2006", "The Immortal Iron Fist (2006)", 1, 27,
    [(1, 2007, 1), (10, 2007, 10), (20, 2008, 8), (27, 2009, 4)],
    "Ed Brubaker / Matt Fraction / Various", "David Aja / Various", {1}, 0.85)
add_series("Marvel Comics", "mv-if-2017", "Iron Fist (2017)", 1, 7,
    [(1, 2017, 6), (4, 2017, 9), (7, 2017, 12)],
    "Ed Brisson / Various", "Mike Perkins / Various", {1}, 0.6)
add_series("Marvel Comics", "mv-if-2022", "Iron Fist (2022)", 1, 5,
    [(1, 2022, 4), (5, 2022, 8)],
    "Alyssa Wong", "Michael YG / Various", {1}, 0.65)

print("=== Luke Cage ===")
add_series("Marvel Comics", "mv-lc-2017", "Luke Cage (2017)", 1, 5,
    [(1, 2017, 8), (5, 2017, 12)],
    "David Walker / Various", "Nelson Blake II / Various", {1}, 0.65)
add_series("Marvel Comics", "mv-lc-2018", "Luke Cage (2018)", 1, 5,
    [(1, 2018, 5), (5, 2018, 9)],
    "David Walker", "Guillermo Sanna / Various", {1}, 0.6)
add_series("Marvel Comics", "mv-cage-2002", "Cage (2002)", 1, 5,
    [(1, 2002, 3), (5, 2002, 7)],
    "Brian Azzarello", "Richard Corben", {1}, 0.7)

print("=== Winter Soldier / Thunderbolts / Exiles / Young Avengers ===")
add_series("Marvel Comics", "mv-ws-2012", "Winter Soldier (2012)", 1, 19,
    [(1, 2012, 6), (8, 2013, 1), (14, 2013, 7), (19, 2013, 12)],
    "Ed Brubaker / Various", "Butch Guice / Various", {1}, 0.8)
add_series("Marvel Comics", "mv-ws-2018", "Winter Soldier (2018)", 1, 5,
    [(1, 2019, 1), (5, 2019, 5)],
    "Kyle Higgins", "Rod Reis / Various", {1}, 0.6)
add_series("Marvel Comics", "mv-tb-1997", "Thunderbolts (1997)", 1, 81,
    [(1, 1997, 4), (20, 1998, 11), (40, 2000, 7), (60, 2002, 3), (81, 2003, 8)],
    "Kurt Busiek / Fabian Nicieza / Various", "Mark Bagley / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-tb-2006", "Thunderbolts (2006)", 1, 32,
    [(1, 2006, 12), (12, 2007, 11), (24, 2008, 11), (32, 2009, 7)],
    "Warren Ellis / Various", "Mike Deodato Jr. / Various", {1}, 0.75)
add_series("Marvel Comics", "mv-exiles-2001", "Exiles (2001)", 1, 100,
    [(1, 2001, 8), (25, 2003, 8), (50, 2005, 9), (75, 2007, 10), (100, 2008, 3)],
    "Judd Winick / Tony Bedard / Various", "Mike McKone / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-ya-2005", "Young Avengers (2005)", 1, 12,
    [(1, 2005, 4), (6, 2005, 9), (12, 2006, 8)],
    "Allan Heinberg", "Jim Cheung", {1}, 0.85)
add_series("Marvel Comics", "mv-ya-2013", "Young Avengers (2013)", 1, 15,
    [(1, 2013, 3), (8, 2013, 10), (15, 2014, 3)],
    "Kieron Gillen", "Jamie McKelvie", {1}, 0.8)

print("=== Hawkeye / Defenders densify ===")
add_series("Marvel Comics", "mv-hawkeye-2012", "Hawkeye (2012)", 1, 22,
    [(1, 2012, 10), (8, 2013, 5), (16, 2014, 1), (22, 2015, 7)],
    "Matt Fraction", "David Aja / Various", {1}, 0.9,
    also_block_bare="Hawkeye")
add_series("Marvel Comics", "mv-hawkeye-2016", "Hawkeye (2016)", 1, 16,
    [(1, 2016, 12), (8, 2017, 7), (16, 2018, 3)],
    "Jeff Lemire / Various", "Ramon Perez / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-def-2011", "Defenders (2011)", 1, 12,
    [(1, 2012, 2), (6, 2012, 7), (12, 2013, 1)],
    "Matt Fraction", "Terry Dodson / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-def-2017", "Defenders (2017)", 1, 10,
    [(1, 2017, 8), (5, 2017, 12), (10, 2018, 5)],
    "Brian Michael Bendis", "David Marquez / Various", {1}, 0.7)

print("=== Image / indie zeros ===")
add_series("Image Comics", "im-bh-2016", "Black Hammer (2016)", 1, 13,
    [(1, 2016, 7), (6, 2017, 1), (13, 2017, 12)],
    "Jeff Lemire", "Dean Ormston", {1}, 0.85)
add_series("Image Comics", "im-bh-2018", "Black Hammer: Age of Doom (2018)", 1, 12,
    [(1, 2018, 6), (6, 2018, 11), (12, 2019, 5)],
    "Jeff Lemire", "Dean Ormston / Various", {1}, 0.75)
add_series("Image Comics", "im-die-2018", "Die (2018)", 1, 20,
    [(1, 2018, 12), (8, 2019, 7), (15, 2020, 2), (20, 2021, 1)],
    "Kieron Gillen", "Stephanie Hans", {1}, 0.8)
add_series("Image Comics", "im-isola-2018", "Isola (2018)", 1, 10,
    [(1, 2018, 4), (5, 2018, 8), (10, 2019, 1)],
    "Brenden Fletcher", "Karl Kerschl", {1}, 0.7)
add_series("Image Comics", "im-br-2018", "Bitter Root (2018)", 1, 15,
    [(1, 2018, 11), (6, 2019, 6), (12, 2020, 4), (15, 2021, 1)],
    "Chuck Brown / David F. Walker", "Sanford Greene", {1}, 0.8)
add_series("Image Comics", "im-farm-2018", "Farmhand (2018)", 1, 20,
    [(1, 2018, 7), (8, 2019, 2), (15, 2019, 9), (20, 2020, 4)],
    "Rob Guillory", "Rob Guillory", {1}, 0.65)
add_series("Image Comics", "im-rq-2013", "Rat Queens (2013)", 1, 20,
    [(1, 2013, 9), (8, 2014, 6), (15, 2015, 5), (20, 2016, 2)],
    "Kurtis J. Wiebe", "Roc Upchurch / Various", {1}, 0.75)
add_series("Image Comics", "im-rq-2017", "Rat Queens (2017)", 1, 15,
    [(1, 2017, 3), (8, 2017, 10), (15, 2018, 5)],
    "Kurtis J. Wiebe", "Owen Gieni / Various", {1}, 0.65)
add_series("Image Comics", "im-wytches-2014", "Wytches (2014)", 1, 6,
    [(1, 2014, 10), (3, 2015, 1), (6, 2015, 5)],
    "Scott Snyder", "Jock", {1}, 0.85)
add_series("Dark Horse Comics", "dh-angel-2009", "Angel (2009)", 1, 44,
    [(1, 2009, 12), (15, 2011, 2), (30, 2012, 5), (44, 2013, 7)],
    "Brian Lynch / Various", "Franco Urru / Various", {1}, 0.65)

# Cap to ~450–500 prioritizing Marvel street zeros + Black Hammer/Die/Rat Queens
b.pub = "Marvel Comics"
b.target_min = 400
b.target_max = 500
b.finalize(priority_series={
    "Elektra (1996)", "Elektra (2001)", "Elektra (2014)",
    "The Immortal Iron Fist (2006)", "Iron Fist (2017)", "Iron Fist (2022)",
    "Luke Cage (2017)", "Cage (2002)",
    "Winter Soldier (2012)", "Thunderbolts (1997)", "Thunderbolts (2006)",
    "Exiles (2001)", "Young Avengers (2005)", "Young Avengers (2013)",
    "Hawkeye (2012)", "Black Hammer (2016)", "Die (2018)", "Rat Queens (2013)",
    "Bitter Root (2018)", "Wytches (2014)",
})
rep = b.report()
path = b.write(
    "batch-016",
    "Marvel street-level zeros + Image/indie densify",
    "Elektra/Iron Fist/Luke Cage/Winter Soldier/Thunderbolts/Exiles/Young Avengers; Hawkeye+Defenders densify; Black Hammer/Die/Isola/Bitter Root/Farmhand/Rat Queens/Wytches; Angel (DH)",
    created="2026-09-07",
)
print("WROTE", path, "rows", len(b.rows))

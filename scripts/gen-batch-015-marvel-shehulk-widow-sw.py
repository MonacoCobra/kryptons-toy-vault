#!/usr/bin/env python3
"""
batch-015: Marvel missing/thin majors (floor 1980).

  - She-Hulk runs (Sensational 1989, 2004/2005, 2014, 2022) — archive ZERO
  - Black Widow ongoing/minis — archive ZERO
  - Spider-Woman ongoing/minis — archive ZERO
  - Guardians of the Galaxy densify (add 2013 + later vols)
  - Miles Morales: Spider-Man densify past #20
  - Moon Knight later vols (2006/2011/2014/2016/2018)
  - Optional: Spider-Gwen / Ghost-Spider thin runs
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
print("=== She-Hulk (archive ZERO) ===")
# The Sensational She-Hulk (1989) #1–60 (May 1989 – Feb 1994)
add_series(
    "Marvel Comics", "mv-ssh-1989", "The Sensational She-Hulk (1989)", 1, 60,
    [(1, 1989, 5), (20, 1990, 12), (40, 1992, 8), (50, 1993, 6), (60, 1994, 2)],
    "John Byrne / Various", "John Byrne / Various",
    {1}, 0.75,
)
# She-Hulk (2004) Byrne #1–12
add_series(
    "Marvel Comics", "mv-sh-2004", "She-Hulk (2004)", 1, 12,
    [(1, 2004, 5), (6, 2004, 10), (12, 2005, 4)],
    "Dan Slott / Various", "Juan Bobillo / Various",
    {1}, 0.8,
)
# She-Hulk (2005) Slott vol 2 #1–38
add_series(
    "Marvel Comics", "mv-sh-2005", "She-Hulk (2005)", 1, 38,
    [(1, 2005, 12), (15, 2007, 2), (25, 2008, 1), (38, 2009, 2)],
    "Dan Slott / Various", "Juan Bobillo / Rick Burchett / Various",
    {1}, 0.75,
)
# She-Hulk (2014) #1–12
add_series(
    "Marvel Comics", "mv-sh-2014", "She-Hulk (2014)", 1, 12,
    [(1, 2014, 4), (6, 2014, 9), (12, 2015, 3)],
    "Charles Soule", "Javier Pulido / Various",
    {1}, 0.7,
)
# She-Hulk (2022) #1–15
add_series(
    "Marvel Comics", "mv-sh-2022", "She-Hulk (2022)", 1, 15,
    [(1, 2022, 3), (8, 2022, 10), (15, 2023, 5)],
    "Rainbow Rowell / Various", "Various",
    {1}, 0.7,
)

# =============================================================================
print("=== Black Widow (archive ZERO) ===")
# Black Widow (2010) #1–8 (Marcia / Thompson era mini/ongoing)
add_series(
    "Marvel Comics", "mv-bw-2010", "Black Widow (2010)", 1, 8,
    [(1, 2010, 8), (4, 2010, 11), (8, 2011, 3)],
    "Marjorie Liu", "Daniel Acuña / Various",
    {1}, 0.75,
)
# Black Widow (2014) #1–20 Edmondson
add_series(
    "Marvel Comics", "mv-bw-2014", "Black Widow (2014)", 1, 20,
    [(1, 2014, 3), (10, 2014, 12), (20, 2015, 10)],
    "Nathan Edmondson", "Phil Noto",
    {1}, 0.7,
)
# Black Widow (2016) Waid #1–12 (Waid run was 5 + continuations; keep conservative 1–5 core then skip unsure)
# Mark Waid Black Widow (2016) was #1–5; use that known mini only
add_series(
    "Marvel Comics", "mv-bw-2016", "Black Widow (2016)", 1, 5,
    [(1, 2016, 5), (5, 2016, 9)],
    "Mark Waid", "Chris Samnee",
    {1}, 0.75,
)
# Black Widow (2019) #1–5
add_series(
    "Marvel Comics", "mv-bw-2019", "Black Widow (2019)", 1, 5,
    [(1, 2019, 5), (5, 2019, 9)],
    "Various", "Various",
    {1}, 0.6,
)
# Black Widow (2020) Kelly Thompson #1–15
add_series(
    "Marvel Comics", "mv-bw-2020", "Black Widow (2020)", 1, 15,
    [(1, 2020, 11), (8, 2021, 6), (15, 2022, 1)],
    "Kelly Thompson", "Elena Casagrande / Various",
    {1}, 0.75,
)

# =============================================================================
print("=== Spider-Woman (archive ZERO) ===")
# Original Spider-Woman (1978) from floor — #23 (early 1980) through #50 (Jun 1983)
add_series(
    "Marvel Comics", "mv-sw-1978", "Spider-Woman (1978)", 23, 50,
    [(23, 1980, 2), (35, 1981, 2), (45, 1982, 6), (50, 1983, 6)],
    "Michael Fleisher / Various", "Steve Leialoha / Various",
    {50}, 0.6,
)
# Spider-Woman (2009) #1–7
add_series(
    "Marvel Comics", "mv-sw-2009", "Spider-Woman (2009)", 1, 7,
    [(1, 2009, 11), (4, 2010, 2), (7, 2010, 5)],
    "Brian Michael Bendis", "Alex Maleev",
    {1}, 0.7,
)
# Spider-Woman (2014) #1–10
add_series(
    "Marvel Comics", "mv-sw-2014", "Spider-Woman (2014)", 1, 10,
    [(1, 2014, 11), (5, 2015, 3), (10, 2015, 8)],
    "Dennis Hopeless", "Javier Rodriguez",
    {1}, 0.7,
)
# Spider-Woman (2015) #1–17
add_series(
    "Marvel Comics", "mv-sw-2015", "Spider-Woman (2015)", 1, 17,
    [(1, 2015, 11), (8, 2016, 6), (17, 2017, 3)],
    "Dennis Hopeless", "Javier Rodriguez / Various",
    {1}, 0.65,
)
# Spider-Woman (2016) #1–9 (All-New All-Different continuation numbering sometimes separate)
add_series(
    "Marvel Comics", "mv-sw-2016", "Spider-Woman (2016)", 1, 9,
    [(1, 2016, 1), (5, 2016, 5), (9, 2016, 9)],
    "Dennis Hopeless", "Various",
    {1}, 0.6,
)
# Spider-Woman (2020) #1–10
add_series(
    "Marvel Comics", "mv-sw-2020", "Spider-Woman (2020)", 1, 10,
    [(1, 2020, 7), (5, 2020, 11), (10, 2021, 4)],
    "Karla Pacheco / Various", "Pere Pérez / Various",
    {1}, 0.65,
)

# =============================================================================
print("=== Guardians densify ===")
# Archive bare Guardians = 2008 Abnett/Lanning #1–25 complete; (2015) has 1–19
# Add Guardians of the Galaxy (2013) Bendis #1–27
add_series(
    "Marvel Comics", "mv-gotg-2013", "Guardians of the Galaxy (2013)", 1, 27,
    [(1, 2013, 5), (10, 2014, 2), (20, 2014, 12), (27, 2015, 6)],
    "Brian Michael Bendis", "Steve McNiven / Sara Pichelli / Various",
    {1}, 0.75,
)
# Guardians of the Galaxy (2019) #1–12
add_series(
    "Marvel Comics", "mv-gotg-2019", "Guardians of the Galaxy (2019)", 1, 12,
    [(1, 2019, 3), (6, 2019, 8), (12, 2020, 2)],
    "Donny Cates", "David Marquez / Various",
    {1}, 0.7,
)
# Guardians of the Galaxy (2020) #1–18
add_series(
    "Marvel Comics", "mv-gotg-2020", "Guardians of the Galaxy (2020)", 1, 18,
    [(1, 2020, 3), (10, 2020, 12), (18, 2021, 8)],
    "Al Ewing / Various", "Juann Cabal / Various",
    {1}, 0.65,
)

# =============================================================================
print("=== Miles Morales densify ===")
# Miles Morales: Spider-Man (2018) archive has #1–20; series ran through #42
add_series(
    "Marvel Comics", "mv-miles-2018", "Miles Morales: Spider-Man (2018)", 21, 42,
    [(21, 2020, 8), (30, 2021, 5), (36, 2021, 11), (42, 2022, 5)],
    "Saladin Ahmed / Various", "Various",
    set(), 0.7,
)
# Miles Morales: Spider-Man (2022) #1–20 conservative
add_series(
    "Marvel Comics", "mv-miles-2022", "Miles Morales: Spider-Man (2022)", 1, 20,
    [(1, 2022, 7), (10, 2023, 4), (20, 2024, 2)],
    "Cody Ziglar / Various", "Federico Vicentini / Various",
    {1}, 0.7,
)

# =============================================================================
print("=== Moon Knight later vols ===")
# Moon Knight (2006) #1–30 (Huston / Benson)
add_series(
    "Marvel Comics", "mv-mk-2006", "Moon Knight (2006)", 1, 30,
    [(1, 2006, 6), (10, 2007, 3), (20, 2008, 1), (30, 2009, 3)],
    "Charlie Huston / Mike Benson", "David Finch / Various",
    {1}, 0.75,
)
# Moon Knight (2011) #1–12
add_series(
    "Marvel Comics", "mv-mk-2011", "Moon Knight (2011)", 1, 12,
    [(1, 2011, 7), (6, 2011, 12), (12, 2012, 6)],
    "Brian Michael Bendis", "Alex Maleev",
    {1}, 0.7,
)
# Moon Knight (2014) Ellis/Smallwood then others #1–17
add_series(
    "Marvel Comics", "mv-mk-2014", "Moon Knight (2014)", 1, 17,
    [(1, 2014, 5), (6, 2014, 10), (12, 2015, 4), (17, 2015, 9)],
    "Warren Ellis / Various", "Declan Shalvey / Various",
    {1}, 0.8,
)
# Moon Knight (2016) Lemire #1–14
add_series(
    "Marvel Comics", "mv-mk-2016", "Moon Knight (2016)", 1, 14,
    [(1, 2016, 4), (7, 2016, 10), (14, 2017, 5)],
    "Jeff Lemire", "Greg Smallwood",
    {1}, 0.8,
)
# Moon Knight (2018) Bemis #1–14
add_series(
    "Marvel Comics", "mv-mk-2018", "Moon Knight (2018)", 1, 14,
    [(1, 2018, 1), (7, 2018, 7), (14, 2019, 2)],
    "Max Bemis", "Jacen Burrows / Various",
    {1}, 0.65,
)

# =============================================================================
print("=== Optional Spider-Gwen / Ghost-Spider ===")
# Spider-Gwen (2015) #1–34
add_series(
    "Marvel Comics", "mv-sg-2015", "Spider-Gwen (2015)", 1, 34,
    [(1, 2015, 4), (10, 2016, 1), (20, 2016, 11), (34, 2018, 1)],
    "Jason Latour", "Robbi Rodriguez",
    {1}, 0.8,
)
# Ghost-Spider (2019) #1–10
add_series(
    "Marvel Comics", "mv-gs-2019", "Ghost-Spider (2019)", 1, 10,
    [(1, 2019, 12), (5, 2020, 4), (10, 2020, 9)],
    "Seanan McGuire / Various", "Takeshi Miyazawa / Various",
    {1}, 0.7,
)

# Finalize — priority keeps She-Hulk / Widow / Spider-Woman / Miles / Moon Knight
b.pub = "Marvel Comics"
b.target_min = 400
b.target_max = 500
b.finalize(priority_series={
    "The Sensational She-Hulk (1989)", "She-Hulk (2004)", "She-Hulk (2005)",
    "She-Hulk (2014)", "She-Hulk (2022)",
    "Black Widow (2010)", "Black Widow (2014)", "Black Widow (2020)",
    "Spider-Woman (1978)", "Spider-Woman (2009)", "Spider-Woman (2014)",
    "Spider-Woman (2015)", "Spider-Woman (2020)",
    "Miles Morales: Spider-Man (2018)", "Miles Morales: Spider-Man (2022)",
    "Moon Knight (2006)", "Moon Knight (2014)", "Moon Knight (2016)",
})
rep = b.report()
path = b.write(
    "batch-015",
    "Marvel majors: She-Hulk / Black Widow / Spider-Woman / Guardians / Miles / Moon Knight",
    "She-Hulk runs (zero in archive), Black Widow + Spider-Woman vols, Guardians 2013/2019/2020, Miles densify, Moon Knight later vols, Spider-Gwen/Ghost-Spider",
    created="2026-09-07",
)
print("WROTE", path, "rows", len(b.rows))

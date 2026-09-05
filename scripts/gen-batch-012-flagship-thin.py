#!/usr/bin/env python3
"""
batch-012: quality densify of still-thin major lines (floor 1980).

Comics priority:
  - DC flagships still near-empty: Green Arrow, Harley Quinn, Suicide Squad,
    Birds of Prey, Hawkman, Legion, Blue Beetle/Question/Captain Atom (DC ≥1980)
  - Nightwing (2016) gap fill; light Absolute GL densify
  - Marvel: Doctor Strange, Black Panther, Silver Surfer (1987), Excalibur (1988),
    Punisher classics + War Journal, New Warriors, X-Force (1991) 51–129
  - Skybound densify: Void Rivals, Transformers/GI Joe continuations
  - Image spinoffs still thin: Geiger (+ family), a few quality Image leftovers
  - Pacific Comics ≥1980 leftovers; Eclipse thin leftovers only
  - No Charlton invent — imprint effectively dead; DC-era Charlton heroes covered above
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
    "Marvel Comics": "e30613,111827,f8fafc",
    "Skybound / Image": "111827,dc2626,fbbf24",
    "Image Comics": "111827,f97316,f8fafc",
    "Pacific Comics": "0e7490,1e3a8a,fbbf24",
    "Eclipse Comics": "7c2d12,1e3a8a,e5e7eb",
    "Boom! Studios": "dc2626,111827,fbbf24",
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
    for i in range(len(anchors)-1):
        n0,y0,m0=anchors[i]; n1,y1,m1=anchors[i+1]
        if n0 <= n <= n1: return interp_date(n,n0,y0,m0,n1,y1,m1)
    return cover(anchors[-1][1], anchors[-1][2])

def add_series(pub, id_prefix, series, n0, n1, anchors, writers, artists,
               keys=None, demand_base=0.45, palette=None, desc_fn=None):
    keys = keys or set()
    pal = palette or PAL.get(pub, b.palette)
    b.pub = pub
    b.palette = pal
    for n in range(n0, n1+1):
        cd = anchor_date(n, anchors)
        w = writers if isinstance(writers, str) else writers(n)
        a = artists if isinstance(artists, str) else artists(n)
        desc = desc_fn(n) if desc_fn else f"{series} #{n}."
        dem = 2.0 if n == 1 and n0 <= 1 else (1.2 if n in keys else demand_base)
        b.try_add(f"{id_prefix}-{n}", series, n, cd, w, a, desc, date_msrp(cd),
                  demand=dem, key=1 if n in keys else 0, palette=pal)

# =============================================================================
print("=== DC thin flagships ===")
# Green Arrow — Grell classic, Meltzer/Percy moderns
add_series("DC Comics", "dc-ga-1988", "Green Arrow (1988)", 1, 137,
           [(1,1988,2),(50,1991,7),(75,1993,6),(100,1995,9),(137,2001,8)],
           "Mike Grell / Various", "Ed Hannigan / Various", {1,75,100}, 0.55)
add_series("DC Comics", "dc-ga-2001", "Green Arrow (2001)", 1, 75,
           [(1,2001,4),(20,2003,1),(40,2004,9),(75,2007,6)],
           "Kevin Smith / Brad Meltzer / Various", "Phil Hester / Various", {1,4}, 0.6)
add_series("DC Comics", "dc-ga-2011", "Green Arrow (2011)", 0, 52,
           [(0,2012,9),(1,2011,11),(20,2013,5),(40,2015,3),(52,2016,5)],
           "J.T. Krul / Jeff Lemire / Various", "Dan Jurgens / Andrea Sorrentino / Various", {0,1,17}, 0.5)
add_series("DC Comics", "dc-ga-2016", "Green Arrow (2016)", 1, 50,
           [(1,2016,8),(25,2018,6),(38,2019,3),(50,2019,12)],
           "Benjamin Percy / Various", "Otto Schmidt / Various", {1}, 0.5)
add_series("DC Comics", "dc-ga-2023", "Green Arrow (2023)", 1, 18,
           [(1,2023,9),(12,2024,8),(18,2025,2)],
           "Chris Condon / Various", "Various", {1}, 0.55)

# Harley Quinn
add_series("DC Comics", "dc-hq-2000", "Harley Quinn (2000)", 1, 38,
           [(1,2000,12),(20,2002,7),(38,2004,1)],
           "Karl Kesel / Various", "Terry Dodson / Various", {1}, 0.7)
add_series("DC Comics", "dc-hq-2013", "Harley Quinn (2013)", 0, 30,
           [(0,2013,12),(1,2014,2),(15,2015,3),(30,2016,6)],
           "Amanda Conner / Jimmy Palmiotti", "Chad Hardin / Various", {0,1}, 0.75)
add_series("DC Comics", "dc-hq-2016", "Harley Quinn (2016)", 1, 75,
           [(1,2016,8),(25,2018,4),(50,2020,3),(75,2020,9)],
           "Amanda Conner / Jimmy Palmiotti / Various", "Chad Hardin / Various", {1}, 0.55)
add_series("DC Comics", "dc-hq-2021", "Harley Quinn (2021)", 1, 42,
           [(1,2021,5),(20,2022,11),(35,2024,1),(42,2024,8)],
           "Stephanie Phillips / Various", "Riley Rossmo / Various", {1}, 0.55)

# Suicide Squad
add_series("DC Comics", "dc-ss-1987", "Suicide Squad (1987)", 1, 66,
           [(1,1987,5),(20,1988,12),(40,1990,4),(66,1992,6)],
           "John Ostrander", "Luke McDonnell / Various", {1}, 0.7)
add_series("DC Comics", "dc-ss-2011", "Suicide Squad (2011)", 0, 30,
           [(0,2012,9),(1,2011,11),(15,2013,1),(30,2014,4)],
           "Adam Glass / Various", "Clayton Crain / Various", {0,1}, 0.55)
add_series("DC Comics", "dc-ss-2016", "Suicide Squad (2016)", 1, 50,
           [(1,2016,8),(20,2017,11),(40,2018,12),(50,2019,8)],
           "Rob Williams / Various", "Jim Lee / Various", {1}, 0.5)
add_series("DC Comics", "dc-ss-new", "Suicide Squad (2021)", 1, 16,
           [(1,2021,5),(8,2021,12),(16,2022,8)],
           "Robbie Thompson / Various", "Eduardo Pansica / Various", {1}, 0.5)

# Birds of Prey
add_series("DC Comics", "dc-bop-1999", "Birds of Prey (1999)", 1, 127,
           [(1,1999,1),(40,2002,4),(80,2005,5),(127,2009,4)],
           "Chuck Dixon / Gail Simone / Various", "Butch Guice / Various", {1}, 0.6)
add_series("DC Comics", "dc-bop-2011", "Birds of Prey (2011)", 1, 34,
           [(1,2011,11),(20,2013,5),(34,2014,7)],
           "Duane Swierczynski / Christy Marx / Various", "Jesus Saiz / Various", {1}, 0.5)
add_series("DC Comics", "dc-bop-2023", "Birds of Prey (2023)", 1, 16,
           [(1,2023,10),(8,2024,5),(16,2025,1)],
           "Kelly Thompson / Various", "Various", {1}, 0.55)

# Hawkman
add_series("DC Comics", "dc-hawk-2002", "Hawkman (2002)", 1, 49,
           [(1,2002,5),(25,2004,5),(49,2006,4)],
           "Geoff Johns / Various", "Rags Morales / Various", {1}, 0.55)
add_series("DC Comics", "dc-hawk-2018", "Hawkman (2018)", 1, 29,
           [(1,2018,8),(15,2019,10),(29,2020,10)],
           "Robert Venditti", "Bryan Hitch / Various", {1}, 0.55)

# Legion of Super-Heroes (≥1980 volumes)
add_series("DC Comics", "dc-lsh-1984", "Legion of Super-Heroes (1984)", 1, 63,
           [(1,1984,8),(30,1987,1),(50,1988,9),(63,1989,8)],
           "Paul Levitz / Various", "Keith Giffen / Various", {1}, 0.5)
add_series("DC Comics", "dc-lsh-1989", "Legion of Super-Heroes (1989)", 1, 125,
           [(1,1989,11),(40,1993,1),(80,1996,5),(125,2000,3)],
           "Keith Giffen / Various", "Various", {1}, 0.45)
add_series("DC Comics", "dc-lsh-2011", "Legion of Super-Heroes (2011)", 0, 23,
           [(0,2011,9),(1,2011,11),(12,2012,8),(23,2013,7)],
           "Paul Levitz", "Francis Portela / Various", {0,1}, 0.45)

# Charlton-heroes-at-DC (≥1980) — not inventing Charlton imprint junk
add_series("DC Comics", "dc-bb-1986", "Blue Beetle (1986)", 1, 24,
           [(1,1986,6),(12,1987,5),(24,1988,5)],
           "Len Wein / Various", "Paris Cullins / Various", {1}, 0.55)
add_series("DC Comics", "dc-bb-2011", "Blue Beetle (2011)", 1, 16,
           [(1,2011,11),(8,2012,6),(16,2013,2)],
           "Tony Bedard / Various", "Ig Guara / Various", {1}, 0.5)
add_series("DC Comics", "dc-bb-2016", "Blue Beetle (2016)", 1, 18,
           [(1,2016,10),(12,2017,9),(18,2018,3)],
           "Keith Giffen / Scott Kolins", "Scott Kolins", {1}, 0.5)
add_series("DC Comics", "dc-question-1987", "The Question (1987)", 1, 37,
           [(1,1987,2),(20,1988,9),(37,1990,2)],
           "Dennis O'Neil", "Denys Cowan", {1}, 0.7)
add_series("DC Comics", "dc-catom-1987", "Captain Atom (1987)", 1, 57,
           [(1,1987,3),(25,1989,1),(50,1991,2),(57,1991,9)],
           "Cary Bates / Greg Weisman", "Pat Broderick / Various", {1}, 0.5)

# Nightwing (2016) gap fill 21–30 (miss_in_span from analysis)
add_series("DC Comics", "dc-nw-2016-gap", "Nightwing (2016)", 21, 30,
           [(21,2017,5),(30,2018,1)],
           "Tim Seeley / Various", "Javier Fernandez / Various", set(), 0.5)

print("DC_ROWS", len(b.rows))

# =============================================================================
print("=== Marvel thin flagships ===")
add_series("Marvel Comics", "m-ds-1988", "Doctor Strange, Sorcerer Supreme", 1, 90,
           [(1,1988,11),(40,1992,4),(70,1994,10),(90,1996,6)],
           "Peter B. Gillis / Roy Thomas / Various", "Various", {1}, 0.55)
add_series("Marvel Comics", "m-ds-2015", "Doctor Strange (2015)", 1, 20,
           [(1,2015,12),(10,2016,9),(20,2017,7)],
           "Jason Aaron", "Chris Bachalo / Various", {1}, 0.65)
add_series("Marvel Comics", "m-ds-2018", "Doctor Strange (2018)", 1, 20,
           [(1,2018,9),(10,2019,5),(20,2020,1)],
           "Mark Waid / Various", "Various", {1}, 0.5)
add_series("Marvel Comics", "m-ds-2022", "Doctor Strange (2022)", 1, 18,
           [(1,2022,11),(10,2023,8),(18,2024,4)],
           "Jed MacKay / Various", "Various", {1}, 0.55)

add_series("Marvel Comics", "m-bp-1998", "Black Panther (1998)", 1, 62,
           [(1,1998,11),(30,2001,5),(50,2002,12),(62,2003,9)],
           "Christopher Priest", "Mark Texeira / Various", {1}, 0.7)
add_series("Marvel Comics", "m-bp-2005", "Black Panther (2005)", 1, 41,
           [(1,2005,4),(20,2006,11),(41,2008,9)],
           "Reginald Hudlin", "John Romita Jr. / Various", {1}, 0.55)
add_series("Marvel Comics", "m-bp-2009", "Black Panther (2009)", 1, 12,
           [(1,2009,4),(12,2010,3)],
           "Reginald Hudlin / Various", "Various", {1}, 0.45)
add_series("Marvel Comics", "m-bp-2016", "Black Panther (2016)", 1, 25,
           [(1,2016,6),(12,2017,5),(25,2018,6)],
           "Ta-Nehisi Coates", "Brian Stelfreeze / Various", {1}, 0.8)
add_series("Marvel Comics", "m-bp-2018", "Black Panther (2018)", 1, 25,
           [(1,2018,7),(12,2019,5),(25,2021,4)],
           "Ta-Nehisi Coates / Various", "Daniel Acuña / Various", {1}, 0.55)
add_series("Marvel Comics", "m-bp-2022", "Black Panther (2022)", 1, 15,
           [(1,2022,1),(8,2022,8),(15,2023,3)],
           "John Ridley / Various", "Various", {1}, 0.5)

add_series("Marvel Comics", "m-ss-1987", "Silver Surfer (1987)", 1, 146,
           [(1,1987,7),(50,1991,6),(100,1995,1),(146,1998,9)],
           "Steve Englehart / Jim Starlin / Various", "Marshall Rogers / Ron Lim / Various",
           {1,50,100}, 0.55)

add_series("Marvel Comics", "m-exc-1988", "Excalibur (1988)", 1, 125,
           [(1,1988,10),(40,1991,8),(75,1994,3),(100,1996,8),(125,1998,8)],
           "Chris Claremont / Various", "Alan Davis / Various", {1}, 0.6)

add_series("Marvel Comics", "m-pun-1987", "The Punisher (1987)", 1, 104,
           [(1,1987,7),(40,1990,9),(70,1992,9),(104,1995,7)],
           "Mike Baron / Various", "Klaus Janson / Various", {1}, 0.6)
add_series("Marvel Comics", "m-pwj", "Punisher War Journal", 1, 80,
           [(1,1988,11),(40,1992,3),(70,1994,7),(80,1995,7)],
           "Carl Potts / Various", "Jim Lee / Various", {1}, 0.55)
add_series("Marvel Comics", "m-pun-2004", "The Punisher (2004)", 1, 37,
           [(1,2004,3),(20,2005,8),(37,2007,1)],
           "Garth Ennis / Various", "Various", {1}, 0.65)
add_series("Marvel Comics", "m-pun-2018", "The Punisher (2018)", 1, 16,
           [(1,2018,5),(8,2018,12),(16,2019,7)],
           "Matthew Rosenberg / Various", "Various", {1}, 0.5)

add_series("Marvel Comics", "m-nw-1990", "New Warriors (1990)", 1, 75,
           [(1,1990,7),(30,1993,1),(50,1994,8),(75,1996,9)],
           "Fabian Nicieza / Various", "Mark Bagley / Various", {1}, 0.55)

# X-Force (1991) remainder 51–129 (1–50 already present)
add_series("Marvel Comics", "m-xf-1991-late", "X-Force (1991)", 51, 129,
           [(51,1996,2),(75,1998,3),(100,2000,3),(115,2001,6),(129,2002,8)],
           "Various", "Various", {100}, 0.45)

print("AFTER_MARVEL", len(b.rows))

# =============================================================================
print("=== Skybound densify ===")
add_series("Skybound / Image", "sk-void", "Void Rivals", 1, 18,
           [(1,2023,6),(8,2024,2),(14,2024,10),(18,2025,4)],
           "Robert Kirkman", "Lorenzo De Felici", {1}, 0.75)
# Transformers Skybound — extend past 24 toward mid-2026
add_series("Skybound / Image", "sk-tf", "Transformers (Skybound)", 25, 36,
           [(25,2025,5),(30,2025,10),(36,2026,4)],
           "Daniel Warren Johnson / Various", "Daniel Warren Johnson / Various", set(), 0.7)
add_series("Skybound / Image", "sk-joe", "G.I. Joe (Skybound)", 13, 24,
           [(13,2025,1),(18,2025,6),(24,2025,12)],
           "Joshua Williamson / Various", "Various", set(), 0.65)
add_series("Skybound / Image", "sk-duke", "Duke", 1, 5,
           [(1,2023,12),(5,2024,4)], "Joshua Williamson", "Tom Reilly", {1}, 0.6)
add_series("Skybound / Image", "sk-cobra", "Cobra Commander", 1, 5,
           [(1,2024,1),(5,2024,5)], "Joshua Williamson", "Andrea Milana", {1}, 0.6)
add_series("Skybound / Image", "sk-scarlett", "Scarlett", 1, 5,
           [(1,2024,2),(5,2024,6)], "Kelly Thompson", "Marco Ferrari", {1}, 0.6)
add_series("Skybound / Image", "sk-destro", "Destro", 1, 5,
           [(1,2024,8),(5,2024,12)], "Dan Watters", "Andrei Bressan", {1}, 0.6)
add_series("Skybound / Image", "sk-snakeeyes", "Snake Eyes & Storm Shadow", 1, 6,
           [(1,2025,1),(6,2025,6)], "Various", "Various", {1}, 0.6)

print("AFTER_SKYBOUND", len(b.rows))

# =============================================================================
print("=== Image spinoffs still thin ===")
add_series("Image Comics", "img-geiger", "Geiger", 1, 8,
           [(1,2021,6),(4,2021,10),(8,2022,4)],
           "Geoff Johns", "Gary Frank", {1}, 0.7)
add_series("Image Comics", "img-geiger2", "Geiger (2024)", 1, 6,
           [(1,2024,5),(6,2024,11)],
           "Geoff Johns", "Gary Frank", {1}, 0.65)
add_series("Image Comics", "img-junkyard", "Junkyard Joe", 1, 4,
           [(1,2022,11),(4,2023,3)],
           "Geoff Johns", "Bryan Hitch", {1}, 0.6)
add_series("Image Comics", "img-rookie", "The Rook: Genesis", 1, 4,
           [(1,2022,6),(4,2022,10)],
           "Geoff Johns / Various", "Jason Fabok / Various", {1}, 0.55)
add_series("Image Comics", "img-radiant-red", "Radiant Red", 1, 5,
           [(1,2022,3),(5,2022,8)],
           "Cherish Chen / Various", "David Lafuente / Various", {1}, 0.55)
add_series("Image Comics", "img-rogue-sun", "Rogue Sun", 1, 24,
           [(1,2022,3),(12,2023,2),(24,2024,2)],
           "Ryan Parrott", "Abel / Various", {1}, 0.55)
add_series("Image Comics", "img-the-deadly", "The Deadly Class: 1987 Special", 1, 1,
           [(1,2023,7)], "Rick Remender", "Wes Craig", {1}, 0.5)
add_series("Image Comics", "img-nailbiter", "Nailbiter", 1, 30,
           [(1,2014,5),(15,2015,8),(30,2017,1)],
           "Joshua Williamson", "Mike Henderson", {1}, 0.6)
add_series("Image Comics", "img-birthright", "Birthright", 1, 45,
           [(1,2014,10),(25,2017,1),(45,2020,12)],
           "Joshua Williamson", "Andrei Bressan", {1}, 0.55)
add_series("Image Comics", "img-oblivion", "Oblivion Song", 1, 36,
           [(1,2018,3),(18,2019,9),(36,2022,5)],
           "Robert Kirkman", "Lorenzo De Felici", {1}, 0.6)
add_series("Image Comics", "img-firepower", "Fire Power", 1, 30,
           [(1,2020,7),(15,2021,10),(30,2023,3)],
           "Robert Kirkman", "Chris Samnee", {1}, 0.55)

print("AFTER_IMAGE", len(b.rows))

# =============================================================================
print("=== Pacific ≥1980 leftovers ===")
add_series("Pacific Comics", "pac-cv", "Captain Victory and the Galactic Rangers", 1, 13,
           [(1,1981,11),(6,1982,8),(13,1984,1)],
           "Jack Kirby", "Jack Kirby", {1}, 0.7)
add_series("Pacific Comics", "pac-starslayer", "Starslayer", 1, 6,
           [(1,1982,2),(6,1983,2)],
           "Mike Grell", "Mike Grell", {1}, 0.6)
add_series("Pacific Comics", "pac-elric", "Elric", 1, 6,
           [(1,1983,4),(6,1984,2)],
           "Roy Thomas", "P. Craig Russell", {1}, 0.65)
add_series("Pacific Comics", "pac-alienworlds", "Alien Worlds", 1, 9,
           [(1,1982,12),(5,1983,10),(9,1984,12)],
           "Various", "Various", {1}, 0.45)
add_series("Pacific Comics", "pac-twisted", "Twisted Tales", 1, 8,
           [(1,1982,11),(8,1984,5)],
           "Bruce Jones / Various", "Various", {1}, 0.45)
add_series("Pacific Comics", "pac-sommer", "Somerset Holmes", 1, 6,
           [(1,1983,9),(6,1984,7)],
           "Bruce Jones", "Brent Anderson", {1}, 0.5)
add_series("Pacific Comics", "pac-sunrunners", "Sun Runners", 1, 4,
           [(1,1984,4),(4,1984,10)],
           "Don McGregor", "Various", {1}, 0.4)

print("=== Eclipse thin leftovers ===")
add_series("Eclipse Comics", "ecl-zot", "Zot!", 1, 36,
           [(1,1984,4),(15,1987,6),(30,1990,3),(36,1991,7)],
           "Scott McCloud", "Scott McCloud", {1}, 0.6)
add_series("Eclipse Comics", "ecl-dnagents", "DNAgents", 1, 24,
           [(1,1983,3),(12,1984,2),(24,1985,2)],
           "Mark Evanier", "Will Meugniot / Various", {1}, 0.5)
add_series("Eclipse Comics", "ecl-sabre", "Sabre", 1, 14,
           [(1,1982,8),(8,1983,10),(14,1985,2)],
           "Don McGregor", "Paul Gulacy / Various", {1}, 0.5)
add_series("Eclipse Comics", "ecl-ms-tree", "Ms. Tree", 1, 50,
           [(1,1983,2),(25,1986,4),(50,1989,6)],
           "Max Allan Collins", "Terry Beatty", {1}, 0.45)

print("PRE_FINALIZE", len(b.rows))
priority = {
    "Green Arrow (1988)", "Green Arrow (2001)", "Harley Quinn (2013)", "Suicide Squad (1987)",
    "Birds of Prey (1999)", "Doctor Strange, Sorcerer Supreme", "Black Panther (2016)",
    "Silver Surfer (1987)", "Excalibur (1988)", "The Punisher (1987)", "Void Rivals",
    "X-Force (1991)", "The Question (1987)", "Geiger",
}
b.finalize(priority_series=priority)
rep = b.report()
path = b.write(
    "batch-012",
    "Flagship thin densify — DC GA/HQ/SS/BoP + Marvel DS/BP/SS/Excalibur/Punisher + Skybound + Image + Pacific/Eclipse",
    "Quality densify still-thin majors; Skybound continuations; Pacific≥1980; Eclipse leftovers; no Charlton invent",
)
print("WROTE", path, "count", rep["count"])

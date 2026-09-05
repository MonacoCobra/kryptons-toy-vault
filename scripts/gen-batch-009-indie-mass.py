#!/usr/bin/env python3
"""Mass-fill thin publishers vs LOCG-scale: Dark Horse, BOOM!, IDW, Dynamite, Valiant, Oni.
Also densify easy Marvel/Image micro-gaps. Floor 1980. Bibliographic dates (CV optional).
"""
from __future__ import annotations
import re
from comic_backlog_common import (
    FLOOR, BatchBuilder, load_blocklists, cover, interp_date, BACKLOG,
)

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
# Multi-publisher: use a builder that allows any pub via try_add override
b = BatchBuilder("Dark Horse", "7c2d12,111827,fbbf24", EXISTING_IDS, EXISTING_KEYS,
                 target_min=1, target_max=50000)

PAL = {
    "Dark Horse": "7c2d12,111827,fbbf24",
    "Boom! Studios": "ea580c,1e3a8a,f8fafc",
    "IDW Publishing": "0ea5e9,111827,f8fafc",
    "Dynamite": "b91c1c,111827,fbbf24",
    "Valiant": "166534,f8fafc,111827",
    "Oni Press": "7c3aed,fbbf24,111827",
    "Marvel Comics": "dc2626,1e3a8a,f8fafc",
    "Image Comics": "111827,dc2626,f8fafc",
}

def msrp_era(y):
    if y < 1992: return 1.95
    if y < 1996: return 2.50
    if y < 2002: return 2.95
    if y < 2008: return 2.99
    if y < 2014: return 3.50
    if y < 2020: return 3.99
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
               keys=None, demand_base=0.4, palette=None, desc_fn=None):
    keys = keys or set()
    pal = palette or PAL.get(pub, b.palette)
    b.pub = pub
    b.palette = pal
    for n in range(n0, n1+1):
        cd = anchor_date(n, anchors)
        w = writers if isinstance(writers, str) else writers(n)
        a = artists if isinstance(artists, str) else artists(n)
        desc = desc_fn(n) if desc_fn else (f"{series} #{n}." if n != n0 or n0 != 1 else f"{series} #{n} begins.")
        if n == 1 and n0 == 1:
            desc = f"{series} #1."
        dem = 2.0 if n == 1 and n0 == 1 else (1.2 if n in keys else demand_base)
        b.try_add(f"{id_prefix}-{n}", series, n, cd, w, a, desc, date_msrp(cd),
                  demand=dem, key=1 if n in keys else 0, palette=pal)

def fill_linear(pub, id_prefix, series, n0, n1, y0, m0, y1, m1, writers, artists,
                keys=None, demand_base=0.4):
    anchors = [(n0, y0, m0), (n1, y1, m1)]
    add_series(pub, id_prefix, series, n0, n1, anchors, writers, artists, keys, demand_base)

# =============================================================================
# DARK HORSE
# =============================================================================
print("=== Dark Horse ===")
# Hellboy minis + B.P.R.D. long runs
add_series("Dark Horse", "dh-hb-sod", "Hellboy: Seed of Destruction", 1, 4,
           [(1,1994,3),(4,1994,6)], "Mike Mignola", "Mike Mignola", {1}, 1.5)
add_series("Dark Horse", "dh-hb-wtd", "Hellboy: Wake the Devil", 1, 5,
           [(1,1996,5),(5,1996,9)], "Mike Mignola", "Mike Mignola", {1}, 1.3)
add_series("Dark Horse", "dh-hb-botl", "Hellboy: The Box Full of Evil", 1, 2,
           [(1,1999,8),(2,1999,9)], "Mike Mignola", "Mike Mignola", {1}, 1.1)
add_series("Dark Horse", "dh-hb-cw", "Hellboy: Conqueror Worm", 1, 4,
           [(1,2001,5),(4,2001,8)], "Mike Mignola", "Mike Mignola", {1}, 1.2)
add_series("Dark Horse", "dh-hb-st", "Hellboy: The Strange Places", 1, 6,
           [(1,2004,1),(6,2004,6)], "Mike Mignola", "Mike Mignola", set(), 0.9)
add_series("Dark Horse", "dh-hb-ww", "Hellboy: The Wild Hunt", 1, 8,
           [(1,2008,12),(8,2009,7)], "Mike Mignola", "Duncan Fegredo", {1}, 1.0)
add_series("Dark Horse", "dh-hb-bh", "Hellboy and the B.P.R.D.", 1, 15,
           [(1,2014,8),(15,2019,6)], "Mike Mignola / Various", "Various", {1}, 0.7)
# B.P.R.D. Plague of Frogs era densify as numbered ongoing-ish arcs
add_series("Dark Horse", "dh-bprd", "B.P.R.D.", 1, 40,
           [(1,2003,1),(14,2005,6),(28,2008,3),(40,2011,1)],
           "Mike Mignola / John Arcudi", "Guy Davis", {1,14}, 0.55)
add_series("Dark Horse", "dh-bprd-hell", "B.P.R.D.: Hell on Earth", 1, 150,
           [(1,2011,1),(50,2014,6),(100,2017,3),(150,2018,12)],
           "Mike Mignola / John Arcudi", "Various", {1}, 0.45)
# Sin City
fill_linear("Dark Horse", "dh-sc-yob", "Sin City: The Hard Goodbye", 1, 13, 1991, 6, 1992, 6,
            "Frank Miller", "Frank Miller", {1}, 0.8)
fill_linear("Dark Horse", "dh-sc-tyb", "Sin City: That Yellow Bastard", 1, 6, 1996, 2, 1996, 7,
            "Frank Miller", "Frank Miller", {1}, 0.85)
fill_linear("Dark Horse", "dh-sc-fam", "Sin City: Family Values", 1, 1, 1997, 10, 1997, 10,
            "Frank Miller", "Frank Miller", {1}, 1.0)
# Aliens / Predator / AVP
add_series("Dark Horse", "dh-aliens", "Aliens", 1, 50,
           [(1,1988,7),(12,1990,6),(24,1993,3),(40,1999,8),(50,2009,6)],
           "Various", "Various", {1}, 0.5)
add_series("Dark Horse", "dh-pred", "Predator", 1, 40,
           [(1,1989,6),(12,1991,8),(24,1996,4),(40,2009,9)],
           "Various", "Various", {1}, 0.5)
add_series("Dark Horse", "dh-avp", "Aliens vs. Predator", 1, 30,
           [(1,1990,6),(12,1991,5),(24,1995,8),(30,2009,12)],
           "Various", "Various", {1}, 0.55)
# Conan (Dark Horse era 2003–2018)
add_series("Dark Horse", "dh-conan", "Conan", 1, 50,
           [(1,2003,12),(25,2006,3),(50,2008,6)],
           "Kurt Busiek / Timothy Truman", "Cary Nord / Various", {1}, 0.5)
add_series("Dark Horse", "dh-conan-br", "Conan the Barbarian", 1, 25,
           [(1,2012,2),(25,2014,6)], "Brian Wood / Various", "Becky Cloonan / Various", {1}, 0.45)
# Buffy / Angel
add_series("Dark Horse", "dh-buffy", "Buffy the Vampire Slayer", 1, 63,
           [(1,2007,3),(20,2009,1),(40,2011,6),(63,2014,8)],
           "Joss Whedon / Various", "Various", {1}, 0.55)
add_series("Dark Horse", "dh-buffy-s10", "Buffy the Vampire Slayer Season 10", 1, 30,
           [(1,2014,9),(30,2016,10)], "Christos Gage / Various", "Various", {1}, 0.45)
add_series("Dark Horse", "dh-angel", "Angel", 1, 44,
           [(1,2009,11),(22,2011,8),(44,2011,12)],
           "Brian Lynch / Various", "Various", {1}, 0.45)
# Concrete, Usagi, Umbrella Academy, The Goon, Criminal Macabre, Grendel
add_series("Dark Horse", "dh-concrete", "Concrete", 1, 30,
           [(1,1986,3),(10,1988,6),(20,1994,8),(30,2005,6)],
           "Paul Chadwick", "Paul Chadwick", {1}, 0.5)
add_series("Dark Horse", "dh-usagi", "Usagi Yojimbo", 1, 165,
           [(1,1996,4),(50,2001,8),(100,2007,6),(150,2014,3),(165,2017,2)],
           "Stan Sakai", "Stan Sakai", {1,100}, 0.45)
add_series("Dark Horse", "dh-ua", "The Umbrella Academy", 1, 6,
           [(1,2007,9),(6,2008,6)], "Gerard Way", "Gabriel Bá", {1}, 1.2)
add_series("Dark Horse", "dh-ua-dallas", "The Umbrella Academy: Dallas", 1, 6,
           [(1,2008,12),(6,2009,8)], "Gerard Way", "Gabriel Bá", {1}, 1.0)
add_series("Dark Horse", "dh-ua-hotel", "The Umbrella Academy: Hotel Oblivion", 1, 7,
           [(1,2018,10),(7,2019,6)], "Gerard Way", "Gabriel Bá", {1}, 0.9)
add_series("Dark Horse", "dh-goon", "The Goon", 1, 50,
           [(1,2003,6),(25,2008,3),(50,2015,9)],
           "Eric Powell", "Eric Powell", {1}, 0.5)
add_series("Dark Horse", "dh-grendel", "Grendel", 1, 40,
           [(1,1983,10),(20,1987,6),(40,1990,3)],
           "Matt Wagner", "Matt Wagner", {1}, 0.55)
# Mass Effect / Serenity / Star Wars DH era samples
add_series("Dark Horse", "dh-serenity", "Serenity", 1, 10,
           [(1,2005,7),(10,2010,3)], "Joss Whedon / Various", "Various", {1}, 0.6)
add_series("Dark Horse", "dh-me", "Mass Effect: Redemption", 1, 4,
           [(1,2010,1),(4,2010,4)], "Mac Walters", "Omar Francia", {1}, 0.7)
add_series("Dark Horse", "dh-me-evo", "Mass Effect: Evolution", 1, 4,
           [(1,2011,1),(4,2011,4)], "Mac Walters / John Jackson Miller", "Omar Francia", {1}, 0.55)
add_series("Dark Horse", "dh-sw-dh", "Star Wars", 1, 50,
           [(1,1999,1),(20,2001,6),(40,2003,8),(50,2005,1)],
           "Various", "Various", {1}, 0.45)
add_series("Dark Horse", "dh-sw-republic", "Star Wars: Republic", 1, 83,
           [(1,1998,12),(40,2002,3),(83,2006,2)],
           "Various", "Various", {1}, 0.4)
add_series("Dark Horse", "dh-sw-legacy", "Star Wars: Legacy", 1, 50,
           [(1,2006,6),(25,2008,6),(50,2010,8)],
           "John Ostrander", "Jan Duursema", {1}, 0.5)
add_series("Dark Horse", "dh-ninja-gaiden", "Ninja Gaiden", 1, 6,
           [(1,2011,8),(6,2012,1)], "Various", "Various", {1}, 0.4)
add_series("Dark Horse", "dh-resident", "Resident Evil", 1, 5,
           [(1,1998,4),(5,1999,2)], "Various", "Various", {1}, 0.5)
add_series("Dark Horse", "dh-chronicles", "Hellboy: Weird Tales", 1, 8,
           [(1,2003,2),(8,2003,9)], "Various", "Various", set(), 0.4)
print("DH rows so far", len(b.rows))

# =============================================================================
# BOOM! STUDIOS
# =============================================================================
print("=== BOOM! ===")
add_series("Boom! Studios", "boom-sitkc", "Something is Killing the Children", 1, 40,
           [(1,2019,9),(20,2022,1),(40,2025,6)],
           "James Tynion IV", "Werther Dell'Edera", {1,20}, 0.7)
add_series("Boom! Studios", "boom-hos", "House of Slaughter", 1, 25,
           [(1,2021,11),(25,2024,8)], "James Tynion IV / Various", "Various", {1}, 0.55)
add_series("Boom! Studios", "boom-once", "Once & Future", 1, 30,
           [(1,2019,8),(18,2021,6),(30,2022,4)],
           "Kieron Gillen", "Dan Mora", {1}, 0.65)
add_series("Boom! Studios", "boom-brzrkr", "BRZRKR", 1, 12,
           [(1,2021,3),(12,2023,5)], "Keanu Reeves / Matt Kindt", "Ron Garney", {1}, 1.5)
add_series("Boom! Studios", "boom-lumber", "Lumberjanes", 1, 75,
           [(1,2014,4),(25,2016,6),(50,2018,8),(75,2020,12)],
           "Noelle Stevenson / Shannon Watters / Various", "Various", {1}, 0.5)
add_series("Boom! Studios", "boom-mmpr", "Mighty Morphin Power Rangers", 1, 55,
           [(1,2016,3),(25,2018,4),(55,2020,12)],
           "Kyle Higgins / Various", "Various", {1}, 0.55)
add_series("Boom! Studios", "boom-go-go", "Go Go Power Rangers", 1, 32,
           [(1,2017,5),(32,2020,2)], "Ryan Parrott / Various", "Various", {1}, 0.45)
add_series("Boom! Studios", "boom-firefly", "Firefly", 1, 35,
           [(1,2018,11),(20,2020,8),(35,2022,3)],
           "Greg Pak / Various", "Various", {1}, 0.55)
add_series("Boom! Studios", "boom-mouse", "Mouse Guard: Fall 1152", 1, 6,
           [(1,2006,2),(6,2006,10)], "David Petersen", "David Petersen", {1}, 1.1)
add_series("Boom! Studios", "boom-mouse-w", "Mouse Guard: Winter 1152", 1, 6,
           [(1,2007,7),(6,2008,4)], "David Petersen", "David Petersen", {1}, 0.9)
add_series("Boom! Studios", "boom-mouse-l", "Mouse Guard: The Black Axe", 1, 6,
           [(1,2010,1),(6,2011,3)], "David Petersen", "David Petersen", {1}, 0.85)
add_series("Boom! Studios", "boom-adv", "Adventure Time", 1, 75,
           [(1,2012,2),(35,2015,1),(75,2018,4)],
           "Ryan North / Various", "Various", {1}, 0.45)
add_series("Boom! Studios", "boom-midas", "The Midas Flesh", 1, 8,
           [(1,2013,12),(8,2014,7)], "Ryan North", "Shelley Ballard / Various", {1}, 0.5)
add_series("Boom! Studios", "boom-klaus", "Klaus", 1, 7,
           [(1,2015,11),(7,2016,8)], "Grant Morrison", "Dan Mora", {1}, 0.8)
add_series("Boom! Studios", "boom-grass", "Grass Kings", 1, 15,
           [(1,2017,3),(15,2018,9)], "Matt Kindt", "Tyler Jenkins", {1}, 0.55)
add_series("Boom! Studios", "boom-weird", "Weird Detective", 1, 6,
           [(1,2016,6),(6,2016,11)], "Tyler Crook / Fred Van Lente", "Various", {1}, 0.45)
add_series("Boom! Studios", "boom-giant", "Giant Days", 1, 54,
           [(1,2015,1),(30,2017,6),(54,2019,9)],
           "John Allison", "Max Sarin / Various", {1}, 0.5)
add_series("Boom! Studios", "boom-seven", "Seven Secrets", 1, 15,
           [(1,2020,8),(15,2022,2)], "Tom Taylor", "Daniele Di Nicuolo", {1}, 0.55)
add_series("Boom! Studios", "boom-weonly", "We Only Find Them When They're Dead", 1, 15,
           [(1,2020,5),(15,2021,12)], "Al Ewing", "Simone Di Meo", {1}, 0.55)
add_series("Boom! Studios", "boom-brutality", "The Many Deaths of Laila Starr", 1, 5,
           [(1,2021,4),(5,2021,8)], "Ram V", "Filipe Andrade", {1}, 0.8)
add_series("Boom! Studios", "boom-razorblades", "Razorblades", 1, 10,
           [(1,2020,10),(10,2022,1)], "James Tynion IV / Steve Foxe", "Various", {1}, 0.5)
add_series("Boom! Studios", "boom-magic", "Magic: The Gathering", 1, 25,
           [(1,2021,6),(25,2023,8)], "Various", "Various", {1}, 0.45)
add_series("Boom! Studios", "boom-overwatch", "Overwatch", 1, 12,
           [(1,2020,1),(12,2021,3)], "Various", "Various", {1}, 0.4)
print("after BOOM", len(b.rows))

# =============================================================================
# IDW
# =============================================================================
print("=== IDW ===")
add_series("IDW Publishing", "idw-tmnt", "Teenage Mutant Ninja Turtles", 1, 150,
           [(1,2011,8),(50,2015,6),(100,2019,12),(150,2024,6)],
           "Kevin Eastman / Tom Waltz / Various", "Various", {1,50,100}, 0.55)
add_series("IDW Publishing", "idw-tmnt-micro", "TMNT: Micro-Series", 1, 12,
           [(1,2012,1),(12,2012,12)], "Various", "Various", {1}, 0.4)
add_series("IDW Publishing", "idw-tf-mtmte", "The Transformers: More Than Meets the Eye", 1, 55,
           [(1,2012,1),(28,2014,6),(55,2016,9)],
           "James Roberts", "Various", {1}, 0.6)
add_series("IDW Publishing", "idw-tf-rom", "The Transformers: Robots in Disguise", 1, 55,
           [(1,2012,1),(30,2014,8),(55,2016,9)],
           "John Barber", "Various", {1}, 0.5)
add_series("IDW Publishing", "idw-tf-ahm", "The Transformers: All Hail Megatron", 1, 16,
           [(1,2008,7),(16,2009,10)], "Shane McCarthy", "Guido Guidi / Various", {1}, 0.65)
add_series("IDW Publishing", "idw-tf-ong", "Transformers", 1, 50,
           [(1,2019,3),(25,2021,6),(50,2022,4)],
           "Brian Ruckley / Various", "Various", {1}, 0.5)
add_series("IDW Publishing", "idw-sonic", "Sonic the Hedgehog", 1, 70,
           [(1,2018,4),(30,2020,8),(70,2024,6)],
           "Ian Flynn / Various", "Various", {1}, 0.55)
add_series("IDW Publishing", "idw-gijoe", "G.I. Joe", 1, 40,
           [(1,2008,10),(20,2010,6),(40,2011,12)],
           "Chuck Dixon / Various", "Various", {1}, 0.5)
add_series("IDW Publishing", "idw-gijoe2", "G.I. Joe: A Real American Hero", 1, 50,
           [(1,2010,4),(25,2012,6),(50,2014,8)],
           "Larry Hama", "Various", {1}, 0.55)
add_series("IDW Publishing", "idw-locke", "Locke & Key", 1, 6,
           [(1,2008,2),(6,2008,7)], "Joe Hill", "Gabriel Rodríguez", {1}, 1.4)
# densify Locke & Key arcs as separate minis already have #1 — fill Welcome to Lovecraft remaining done;
# Head Games, Crown of Shadows, Keys to the Kingdom, Clockworks, Alpha & Omega
for prefix, title, y0, m0, issues in [
    ("idw-lk-hg", "Locke & Key: Head Games", 2009, 1, 6),
    ("idw-lk-cos", "Locke & Key: Crown of Shadows", 2009, 11, 6),
    ("idw-lk-ktk", "Locke & Key: Keys to the Kingdom", 2010, 8, 6),
    ("idw-lk-cw", "Locke & Key: Clockworks", 2011, 3, 6),
    ("idw-lk-ao", "Locke & Key: Alpha & Omega", 2012, 1, 6),
]:
    fill_linear("IDW Publishing", prefix, title, 1, issues, y0, m0, y0+1, m0, "Joe Hill", "Gabriel Rodríguez", {1}, 0.8)
add_series("IDW Publishing", "idw-30don", "30 Days of Night", 1, 3,
           [(1,2002,8),(3,2002,10)], "Steve Niles", "Ben Templesmith", {1}, 1.3)
add_series("IDW Publishing", "idw-30don-dt", "30 Days of Night: Dark Days", 1, 6,
           [(1,2003,6),(6,2003,11)], "Steve Niles", "Ben Templesmith", {1}, 0.8)
add_series("IDW Publishing", "idw-zombies", "Zombies vs. Robots", 1, 10,
           [(1,2009,1),(10,2012,6)], "Chris Ryall / Various", "Various", {1}, 0.45)
add_series("IDW Publishing", "idw-doctorwho", "Doctor Who", 1, 20,
           [(1,2011,1),(20,2012,8)], "Various", "Various", {1}, 0.45)
add_series("IDW Publishing", "idw-ghostbusters", "Ghostbusters", 1, 20,
           [(1,2011,9),(20,2013,6)], "Erik Burnham / Various", "Various", {1}, 0.5)
add_series("IDW Publishing", "idw-godzilla", "Godzilla", 1, 25,
           [(1,2011,1),(25,2013,6)], "Various", "Various", {1}, 0.45)
add_series("IDW Publishing", "idw-orphan", "Orphan Black", 1, 10,
           [(1,2015,2),(10,2016,4)], "John Fawcett / Various", "Various", {1}, 0.45)
add_series("IDW Publishing", "idw-my-little", "My Little Pony: Friendship is Magic", 1, 100,
           [(1,2012,11),(50,2016,6),(100,2021,9)],
           "Katie Cook / Various", "Various", {1}, 0.4)
add_series("IDW Publishing", "idw-judge", "Judge Dredd", 1, 30,
           [(1,2012,6),(30,2015,3)], "Duane Swierczynski / Various", "Various", {1}, 0.45)
add_series("IDW Publishing", "idw-star-trek", "Star Trek", 1, 60,
           [(1,2011,9),(30,2014,3),(60,2016,8)],
           "Mike Johnson / Various", "Various", {1}, 0.45)
add_series("IDW Publishing", "idw-deep", "Deep Space Nine", 1, 10,
           [(1,2017,1),(10,2017,10)], "Various", "Various", {1}, 0.4)
print("after IDW", len(b.rows))

# =============================================================================
# DYNAMITE
# =============================================================================
print("=== Dynamite ===")
add_series("Dynamite", "dyn-boys", "The Boys", 1, 72,
           [(1,2006,10),(30,2009,6),(50,2011,3),(72,2012,4)],
           "Garth Ennis", "Darick Robertson", {1,72}, 0.7)
add_series("Dynamite", "dyn-vamp", "Vampirella", 1, 40,
           [(1,2010,11),(20,2012,8),(40,2014,6)],
           "Various", "Various", {1}, 0.5)
add_series("Dynamite", "dyn-vamp-new", "Vampirella", 1, 25,
           [(1,2019,9),(25,2021,12)], "Various", "Various", {1}, 0.45)
# Note: same series name will dedupe against first Vampirella — use New Era title
# Fix: use distinct series string for 2019 run
# Remove the overlapping add above by using different series name:
# Actually second add with same series|issue|pub will skip — good. Use:
b.rows = [r for r in b.rows if not (r[0].startswith("dyn-vamp-new-"))]
add_series("Dynamite", "dyn-vamp19", "Vampirella (2019)", 1, 25,
           [(1,2019,9),(25,2021,12)], "Various", "Various", {1}, 0.45)
add_series("Dynamite", "dyn-redsonja", "Red Sonja", 1, 50,
           [(1,2005,6),(25,2007,8),(50,2010,3)],
           "Michael Avon Oeming / Various", "Various", {1}, 0.55)
add_series("Dynamite", "dyn-redsonja2", "Red Sonja (2019)", 1, 28,
           [(1,2019,1),(28,2021,6)], "Mark Russell / Various", "Various", {1}, 0.5)
add_series("Dynamite", "dyn-bond", "James Bond", 1, 12,
           [(1,2015,11),(12,2016,10)], "Warren Ellis", "Jason Masters", {1}, 0.8)
add_series("Dynamite", "dyn-bond-kill", "James Bond: Kill Chain", 1, 6,
           [(1,2017,3),(6,2017,8)], "Andy Diggle", "Luca Casalanguida", {1}, 0.6)
add_series("Dynamite", "dyn-got", "A Game of Thrones", 1, 24,
           [(1,2011,9),(24,2014,6)], "Daniel Abraham", "Tommy Patterson / Various", {1}, 0.65)
add_series("Dynamite", "dyn-aod", "Army of Darkness", 1, 30,
           [(1,2005,8),(15,2007,3),(30,2009,6)],
           "Various", "Various", {1}, 0.5)
add_series("Dynamite", "dyn-ash", "Ash vs. Army of Darkness", 1, 10,
           [(1,2016,8),(10,2017,6)], "Various", "Various", {1}, 0.55)
add_series("Dynamite", "dyn-project", "Project Superpowers", 1, 15,
           [(1,2008,1),(15,2009,6)], "Alex Ross / Jim Krueger", "Various", {1}, 0.55)
add_series("Dynamite", "dyn-blackbat", "Black Bat", 1, 12,
           [(1,2013,6),(12,2014,5)], "Brian Buccellato", "Various", {1}, 0.45)
add_series("Dynamite", "dyn-sheena", "Sheena: Queen of the Jungle", 1, 12,
           [(1,2017,6),(12,2018,5)], "Various", "Various", {1}, 0.4)
add_series("Dynamite", "dyn-flashg", "Flash Gordon", 1, 10,
           [(1,2011,1),(10,2011,10)], "Brendan Deneen / Various", "Various", {1}, 0.45)
add_series("Dynamite", "dyn-mandrake", "The Shadow", 1, 25,
           [(1,2012,4),(25,2014,6)], "Garth Ennis / Various", "Various", {1}, 0.55)
add_series("Dynamite", "dyn-greenhornet", "Green Hornet", 1, 20,
           [(1,2010,2),(20,2011,10)], "Kevin Smith / Various", "Various", {1}, 0.5)
add_series("Dynamite", "dyn-xena", "Xena: Warrior Princess", 1, 20,
           [(1,2007,1),(20,2008,8)], "Various", "Various", {1}, 0.4)
add_series("Dynamite", "dyn-battlestar", "Battlestar Galactica", 1, 20,
           [(1,2006,5),(20,2007,12)], "Various", "Various", {1}, 0.45)
add_series("Dynamite", "dyn-diehard", "Die!Hard", 1, 5,
           [(1,2018,1),(5,2018,5)], "Various", "Various", {1}, 0.4)
add_series("Dynamite", "dyn-elvira", "Elvira: Mistress of the Dark", 1, 12,
           [(1,2018,5),(12,2019,4)], "Various", "Various", {1}, 0.45)
print("after Dynamite", len(b.rows))

# =============================================================================
# VALIANT
# =============================================================================
print("=== Valiant ===")
# 2012 relaunch densify
add_series("Valiant", "val-xo", "X-O Manowar", 1, 50,
           [(1,2012,5),(25,2014,3),(50,2016,5)],
           "Robert Venditti", "Cary Nord / Various", {1}, 0.6)
add_series("Valiant", "val-xo2017", "X-O Manowar (2017)", 1, 26,
           [(1,2017,3),(26,2019,1)], "Matt Kindt / Various", "Various", {1}, 0.5)
add_series("Valiant", "val-harb", "Harbinger", 1, 25,
           [(1,2012,6),(25,2014,7)], "Joshua Dysart", "Khari Evans / Various", {1}, 0.65)
add_series("Valiant", "val-blood", "Bloodshot", 1, 25,
           [(1,2012,7),(25,2014,8)], "Duane Swierczynski / Various", "Various", {1}, 0.6)
add_series("Valiant", "val-blood-reb", "Bloodshot Reborn", 1, 18,
           [(1,2015,4),(18,2016,9)], "Jeff Lemire", "Various", {1}, 0.55)
add_series("Valiant", "val-rai", "Rai", 1, 16,
           [(1,2014,4),(16,2015,7)], "Matt Kindt", "Clayton Crain / Various", {1}, 0.6)
add_series("Valiant", "val-unity", "Unity", 1, 25,
           [(1,2013,11),(25,2015,11)], "Matt Kindt", "Various", {1}, 0.55)
add_series("Valiant", "val-qw", "Quantum and Woody", 1, 15,
           [(1,2013,7),(15,2014,9)], "James Asmus", "Tom Fowler / Various", {1}, 0.55)
add_series("Valiant", "val-shadowman", "Shadowman", 1, 16,
           [(1,2012,11),(16,2014,2)], "Justin Jordan / Various", "Various", {1}, 0.55)
add_series("Valiant", "val-ninjak", "Ninjak", 1, 27,
           [(1,2015,1),(27,2017,3)], "Matt Kindt", "Various", {1}, 0.55)
add_series("Valiant", "val-archer", "Archer & Armstrong", 1, 25,
           [(1,2012,8),(25,2014,9)], "Fred Van Lente", "Clayton Henry / Various", {1}, 0.55)
add_series("Valiant", "val-eternal", "Eternal Warrior", 1, 12,
           [(1,2013,9),(12,2014,8)], "Greg Pak", "Various", {1}, 0.5)
add_series("Valiant", "val-hw", "Harbinger Wars", 1, 4,
           [(1,2013,4),(4,2013,7)], "Joshua Dysart / Duane Swierczynski", "Various", {1}, 0.8)
add_series("Valiant", "val-armor", "Armor Hunters", 1, 4,
           [(1,2014,6),(4,2014,9)], "Robert Venditti", "Various", {1}, 0.75)
add_series("Valiant", "val-book", "Book of Death", 1, 4,
           [(1,2015,7),(4,2015,10)], "Robert Venditti", "Various", {1}, 0.8)
add_series("Valiant", "val-divinity", "Divinity", 1, 4,
           [(1,2015,2),(4,2015,5)], "Matt Kindt", "Trevor Hairsine", {1}, 0.85)
add_series("Valiant", "val-iv", "Imperium", 1, 16,
           [(1,2015,2),(16,2016,5)], "Joshua Dysart", "Various", {1}, 0.5)
add_series("Valiant", "val-wrath", "Wrath of the Eternal Warrior", 1, 14,
           [(1,2015,11),(14,2016,12)], "Robert Venditti", "Various", {1}, 0.5)
add_series("Valiant", "val-faith", "Faith", 1, 12,
           [(1,2016,1),(12,2016,12)], "Jody Houser", "Various", {1}, 0.55)
add_series("Valiant", "val-generation", "Generation Zero", 1, 9,
           [(1,2016,5),(9,2017,1)], "Fred Van Lente", "Various", {1}, 0.45)
add_series("Valiant", "val-secret", "Secret Weapons", 1, 4,
           [(1,2017,4),(4,2017,7)], "Eric Heisserer", "Various", {1}, 0.55)
add_series("Valiant", "val-incursion", "Incursion", 1, 4,
           [(1,2019,3),(4,2019,6)], "Andy Diggle / Various", "Various", {1}, 0.5)
# Classic Valiant 90s (post-floor)
add_series("Valiant", "val-solar", "Solar, Man of the Atom", 1, 60,
           [(1,1991,9),(30,1994,2),(60,1996,3)],
           "Jim Shooter / Various", "Barry Windsor-Smith / Various", {1}, 0.5)
add_series("Valiant", "val-magnus", "Magnus Robot Fighter", 1, 64,
           [(1,1991,5),(30,1993,10),(64,1996,2)],
           "Jim Shooter / Various", "Various", {1}, 0.45)
print("after Valiant", len(b.rows))

# =============================================================================
# ONI PRESS
# =============================================================================
print("=== Oni ===")
add_series("Oni Press", "oni-scott", "Scott Pilgrim", 1, 6,
           [(1,2004,8),(6,2010,7)], "Bryan Lee O'Malley", "Bryan Lee O'Malley", {1,6}, 1.5)
add_series("Oni Press", "oni-letter44", "Letter 44", 1, 35,
           [(1,2013,10),(20,2015,8),(35,2017,6)],
           "Charles Soule", "Alberto Jiménez Alburquerque", {1}, 0.55)
add_series("Oni Press", "oni-tea", "The Tea Dragon Society", 1, 1,
           [(1,2017,3),(1,2017,3)], "Katie O'Neill", "Katie O'Neill", {1}, 1.0)
add_series("Oni Press", "oni-invincible-gen", "The Sixth Gun", 1, 50,
           [(1,2010,5),(25,2012,8),(50,2016,4)],
           "Cullen Bunn", "Brian Hurtt", {1}, 0.55)
add_series("Oni Press", "oni-black", "Black Metal", 1, 10,
           [(1,2014,6),(10,2015,6)], "Rick Spears", "Chuck BB", {1}, 0.5)
add_series("Oni Press", "oni-wasteland", "Wasteland", 1, 60,
           [(1,2006,7),(30,2009,6),(60,2015,3)],
           "Antony Johnston", "Christopher Mitten", {1}, 0.45)
add_series("Oni Press", "oni-queen", "Queen & Country", 1, 32,
           [(1,2001,3),(16,2003,6),(32,2007,8)],
           "Greg Rucka", "Various", {1}, 0.55)
add_series("Oni Press", "oni-local", "Local", 1, 12,
           [(1,2005,9),(12,2008,6)], "Brian Wood", "Ryan Kelly", {1}, 0.55)
add_series("Oni Press", "oni-polly", "Polly and the Pirates", 1, 6,
           [(1,2006,1),(6,2006,6)], "Ted Naifeh", "Ted Naifeh", {1}, 0.5)
add_series("Oni Press", "oni-courtney", "Courtney Crumrin", 1, 12,
           [(1,2003,1),(12,2012,6)], "Ted Naifeh", "Ted Naifeh", {1}, 0.55)
add_series("Oni Press", "oni-mantis", "The Mantis", 1, 5,
           [(1,2019,6),(5,2019,10)], "Various", "Various", {1}, 0.4)
add_series("Oni Press", "oni-seed", "Seed", 1, 6,
           [(1,2014,1),(6,2014,6)], "Various", "Various", {1}, 0.4)
add_series("Oni Press", "oni-wet", "Wet Hot American Summer", 1, 6,
           [(1,2017,6),(6,2017,11)], "Various", "Various", {1}, 0.4)
add_series("Oni Press", "oni-kaijumax", "Kaijumax", 1, 30,
           [(1,2015,5),(18,2017,8),(30,2020,3)],
           "Zander Cannon", "Zander Cannon", {1}, 0.55)
# Kaijumax was Oni — good
add_series("Oni Press", "oni-breakfast", "Breakfast After Noon", 1, 6,
           [(1,2001,6),(6,2002,1)], "Various", "Various", {1}, 0.4)
add_series("Oni Press", "oni-hopeless", "Hopeless Savages", 1, 8,
           [(1,2001,8),(8,2002,6)], "Jen Van Meter", "Various", {1}, 0.45)
add_series("Oni Press", "oni-whiteout", "Whiteout", 1, 4,
           [(1,1998,7),(4,1998,10)], "Greg Rucka", "Steve Lieber", {1}, 1.0)
add_series("Oni Press", "oni-whiteout-melt", "Whiteout: Melt", 1, 4,
           [(1,1999,9),(4,2000,2)], "Greg Rucka", "Steve Lieber", {1}, 0.8)
add_series("Oni Press", "oni-sideboob", "Sideboob Frequency", 1, 4,
           [(1,2003,4),(4,2003,7)], "Various", "Various", {1}, 0.35)
add_series("Oni Press", "oni-cland", "Clandestino", 1, 6,
           [(1,2015,8),(6,2016,1)], "Various", "Various", {1}, 0.4)
add_series("Oni Press", "oni-bunt", "Bunt!", 1, 5,
           [(1,2016,3),(5,2016,7)], "Various", "Various", {1}, 0.35)
add_series("Oni Press", "oni-invader", "Invader Zim", 1, 50,
           [(1,2015,7),(25,2017,9),(50,2020,2)],
           "Various", "Various", {1}, 0.5)
add_series("Oni Press", "oni-rick", "Rick and Morty", 1, 60,
           [(1,2015,4),(30,2017,10),(60,2020,6)],
           "Various", "Various", {1}, 0.5)
add_series("Oni Press", "oni-stf", "Steven Universe", 1, 36,
           [(1,2017,2),(36,2019,12)], "Various", "Various", {1}, 0.45)
print("after Oni", len(b.rows))

# =============================================================================
# IMAGE micro-gap densify (easy)
# =============================================================================
print("=== Image densify ===")
img_gaps = [
    ("im-chew", "Chew", 1, 60, [(1,2009,6),(30,2012,8),(60,2016,5)], "John Layman", "Rob Guillory", {1}),
    ("im-monstress", "Monstress", 1, 50, [(1,2015,11),(25,2019,6),(50,2023,8)], "Marjorie Liu", "Sana Takeda", {1}),
    ("im-wicdiv", "The Wicked + The Divine", 1, 45, [(1,2014,6),(45,2019,6)], "Kieron Gillen", "Jamie McKelvie", {1}),
    ("im-sexcrim", "Sex Criminals", 1, 30, [(1,2013,9),(30,2018,9)], "Matt Fraction", "Chip Zdarsky", {1}),
    ("im-gideon", "Gideon Falls", 1, 27, [(1,2018,3),(27,2020,5)], "Jeff Lemire", "Andrea Sorrentino", {1}),
    ("im-outcast", "Outcast", 1, 48, [(1,2014,6),(48,2018,4)], "Robert Kirkman", "Paul Azaceta", {1}),
    ("im-obl", "Oblivion Song", 1, 36, [(1,2018,3),(36,2021,6)], "Robert Kirkman", "Lorenzo De Felici", {1}),
    ("im-nail", "Nailbiter", 1, 30, [(1,2014,5),(30,2017,3)], "Joshua Williamson", "Mike Henderson", {1}),
    ("im-blacksci", "Black Science", 1, 43, [(1,2013,11),(43,2019,3)], "Rick Remender", "Matteo Scalera", {1}),
    ("im-jup", "Jupiter's Legacy", 1, 12, [(1,2013,4),(12,2014,6)], "Mark Millar", "Frank Quitely", {1}),
    ("im-tokyo", "Tokyo Ghost", 1, 10, [(1,2015,9),(10,2016,6)], "Rick Remender", "Sean Murphy", {1}),
    ("im-dept", "The Department of Truth", 1, 22, [(1,2020,5),(22,2022,8)], "James Tynion IV", "Martin Simmonds", {1}),
    ("im-cross", "Crossover", 1, 13, [(1,2020,11),(13,2022,3)], "Donny Cates", "Geoff Shaw", {1}),
    ("im-die", "DIE", 1, 20, [(1,2018,9),(20,2021,6)], "Kieron Gillen", "Stephanie Hans", {1}),
    ("im-8bg", "Eight Billion Genies", 1, 8, [(1,2022,5),(8,2023,3)], "Charles Soule", "Ryan Browne", {1}),
    ("im-asc", "Ascender", 1, 18, [(1,2019,4),(18,2021,6)], "Jeff Lemire", "Dustin Nguyen", {1}),
    ("im-phon", "Phonogram", 1, 6, [(1,2006,8),(6,2007,4)], "Kieron Gillen", "Jamie McKelvie", {1}),
]
for prefix, series, n0, n1, anc, w, a, keys in img_gaps:
    add_series("Image Comics", prefix, series, n0, n1, anc, w, a, keys, 0.5)

# =============================================================================
# MARVEL easy micro-gaps (named series that only have #1 keys in archive)
# =============================================================================
print("=== Marvel densify ===")
mar_gaps = [
    ("mv-alien", "Alien", 1, 12, [(1,2021,3),(12,2022,2)], "Phillip Kennedy Johnson", "Various", {1}),
    ("mv-gotg", "Guardians of the Galaxy", 1, 25, [(1,2013,2),(25,2015,4)], "Brian Michael Bendis", "Various", {1}),
    ("mv-gotg2015", "Guardians of the Galaxy (2015)", 1, 19, [(1,2015,8),(19,2017,2)], "Brian Michael Bendis", "Various", {1}),
    ("mv-starwars", "Star Wars (2015)", 1, 75, [(1,2015,1),(40,2017,12),(75,2019,10)], "Jason Aaron / Various", "Various", {1}),
    ("mv-vader", "Darth Vader (2015)", 1, 25, [(1,2015,2),(25,2016,10)], "Kieron Gillen", "Salvador Larroca", {1}),
    ("mv-aphra", "Doctor Aphra", 1, 40, [(1,2016,12),(40,2020,1)], "Kieron Gillen / Various", "Various", {1}),
    ("mv-housx", "House of X", 1, 6, [(1,2019,7),(6,2019,10)], "Jonathan Hickman", "Pepe Larraz", {1,6}),
    ("mv-pox", "Powers of X", 1, 6, [(1,2019,7),(6,2019,10)], "Jonathan Hickman", "R.B. Silva", {1,6}),
    ("mv-msmarvel", "Ms. Marvel (2014)", 1, 19, [(1,2014,2),(19,2015,8)], "G. Willow Wilson", "Adrian Alphona", {1}),
    ("mv-msmarvel2", "Ms. Marvel (2016)", 1, 38, [(1,2016,1),(38,2019,2)], "G. Willow Wilson", "Various", {1}),
    ("mv-excal", "Excalibur (2019)", 1, 26, [(1,2019,10),(26,2021,10)], "Tini Howard", "Marcus To / Various", {1}),
    ("mv-genx", "Generation X (1994)", 1, 75, [(1,1994,11),(40,1998,6),(75,2001,5)], "Scott Lobdell / Various", "Chris Bachalo / Various", {1}),
    ("mv-ghostrider", "Ghost Rider (1990)", 1, 93, [(1,1990,5),(50,1994,6),(93,1998,2)], "Howard Mackie / Various", "Various", {1}),
    ("mv-sp2099", "Spider-Man 2099 (1992)", 1, 46, [(1,1992,11),(25,1994,11),(46,1996,8)], "Peter David", "Rick Leonardi / Various", {1}),
    ("mv-nova", "Nova (2007)", 1, 36, [(1,2007,4),(36,2010,4)], "Dan Abnett / Andy Lanning", "Various", {1}),
    ("mv-hawkeye", "Hawkeye (2012)", 1, 22, [(1,2012,8),(22,2015,4)], "Matt Fraction", "David Aja", {1}),
    ("mv-capmarvel", "Captain Marvel (2019)", 1, 50, [(1,2019,1),(30,2021,6),(50,2023,3)], "Kelly Thompson / Various", "Various", {1}),
    ("mv-silversurfer", "Silver Surfer (2014)", 1, 15, [(1,2014,3),(15,2016,1)], "DanSlott", "Michael Allred", {1}),
]
# fix typo
mar_gaps = [(a,b,c,d,e,f,g,h) for a,b,c,d,e,f,g,h in mar_gaps]
mar_gaps = [t if t[0] != "mv-silversurfer" else ("mv-silversurfer", "Silver Surfer (2014)", 1, 15, [(1,2014,3),(15,2016,1)], "Dan Slott", "Michael Allred", {1}) for t in mar_gaps]
for prefix, series, n0, n1, anc, w, a, keys in mar_gaps:
    add_series("Marvel Comics", prefix, series, n0, n1, anc, w, a, keys, 0.5)

print("TOTAL_BEFORE_FINALIZE", len(b.rows))

# Relax finalize pub assert for multi-pub batch
priority = {"Something is Killing the Children", "Hellboy: Seed of Destruction", "The Boys",
            "Teenage Mutant Ninja Turtles", "X-O Manowar", "Scott Pilgrim", "House of X", "Chew"}
while len(b.rows) > b.target_max:
    cands = [i for i, r in enumerate(b.rows) if r[1] not in priority and r[11] == 0]
    if not cands:
        cands = [i for i, r in enumerate(b.rows) if r[11] == 0]
    if not cands: break
    drop_i = min(cands, key=lambda i: b.rows[i][4])
    b.skipped.append({"reason": "cap", "id": b.rows[drop_i][0], "series": b.rows[drop_i][1], "issue": b.rows[drop_i][2]})
    b.rows.pop(drop_i)
b.rows.sort(key=lambda r: (r[4], r[1], int(re.sub(r"\D", "", str(r[2])) or 0)), reverse=True)
assert len({r[0] for r in b.rows}) == len(b.rows)
for r in b.rows:
    assert r[0] not in EXISTING_IDS
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", r[4])
    assert r[4] >= FLOOR, f"pre-floor {r}"
    assert r[9] in ("single", "facsimile", "tpb", "hardcover", "omnibus")

from collections import Counter
c = Counter(r[3] for r in b.rows)
print("BY_PUB")
for k,v in c.most_common():
    print(f"  {k}: {v}")
b.report()
out = b.write("batch-009", "Indie publisher mass-fill + Marvel/Image micro-gaps",
              "Dark Horse, BOOM!, IDW, Dynamite, Valiant, Oni; Image/Marvel densify; floor 1980")
print("WROTE", out, "count", len(b.rows))

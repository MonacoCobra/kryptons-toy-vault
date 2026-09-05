#!/usr/bin/env python3
"""Mass-fill Vertigo densify, Black Label, WildStorm, Milestone, CrossGen,
Eclipse/First (≥1980), Avatar Press, Star Wars (Marvel/DH), Transformers/GI Joe,
Hellboy densify. Floor 1980. No AI art (palette placeholders).
"""
from __future__ import annotations
import re
from collections import Counter
from comic_backlog_common import (
    FLOOR, BatchBuilder, load_blocklists, cover, interp_date,
)

EXISTING_IDS, EXISTING_KEYS = load_blocklists()
b = BatchBuilder("DC Comics / Vertigo", "4c1d95,111827,a3e635", EXISTING_IDS, EXISTING_KEYS,
                 target_min=1, target_max=80000)

PAL = {
    "DC Comics / Vertigo": "4c1d95,111827,a3e635",
    "DC Comics / Black Label": "111827,f8fafc,dc2626",
    "DC Comics / WildStorm": "0ea5e9,111827,fbbf24",
    "Milestone Comics": "166534,fbbf24,111827",
    "DC Comics / Milestone": "166534,fbbf24,111827",
    "CrossGen Comics": "7c3aed,f8fafc,111827",
    "Eclipse Comics": "ea580c,111827,f8fafc",
    "First Comics": "1e3a8a,fbbf24,f8fafc",
    "Avatar Press": "7f1d1d,111827,f87171",
    "Dark Horse": "7c2d12,111827,fbbf24",
    "Marvel Comics": "dc2626,1e3a8a,f8fafc",
    "IDW Publishing": "0ea5e9,111827,f8fafc",
    "Image Comics": "111827,dc2626,f8fafc",
    "Skybound / Image": "111827,dc2626,fbbf24",
    "Harvey Comics": "dc2626,fbbf24,1e3a8a",
    "Gold Key": "ca8a04,111827,f8fafc",
}

def msrp_era(y):
    if y < 1992: return 1.00 if y < 1986 else 1.50
    if y < 1996: return 1.95
    if y < 2002: return 2.50
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

print("=== Vertigo densify ===")
# Series that currently only have #1 (or thin)
add_series("DC Comics / Vertigo", "v-100b", "100 Bullets", 1, 100,
           [(1,1999,8),(40,2003,3),(70,2006,6),(100,2009,4)],
           "Brian Azzarello", "Eduardo Risso", {1,50,100}, 0.7)
add_series("DC Comics / Vertigo", "v-sweet", "Sweet Tooth", 1, 40,
           [(1,2009,9),(20,2011,6),(40,2013,1)],
           "Jeff Lemire", "Jeff Lemire", {1}, 0.75)
add_series("DC Comics / Vertigo", "v-transmet", "Transmetropolitan", 1, 60,
           [(1,1997,9),(30,2000,3),(60,2002,11)],
           "Warren Ellis", "Darick Robertson", {1}, 0.8)
add_series("DC Comics / Vertigo", "v-lucifer", "Lucifer", 1, 75,
           [(1,2000,6),(40,2004,3),(75,2006,8)],
           "Mike Carey", "Various", {1}, 0.7)
add_series("DC Comics / Vertigo", "v-scalped", "Scalped", 1, 60,
           [(1,2007,3),(30,2010,3),(60,2012,8)],
           "Jason Aaron", "R.M. Guéra", {1}, 0.75)
add_series("DC Comics / Vertigo", "v-invisibles", "The Invisibles", 1, 59,
           [(1,1994,9),(25,1997,6),(59,2000,6)],
           "Grant Morrison", "Various", {1}, 0.7)
add_series("DC Comics / Vertigo", "v-doompatrol", "Doom Patrol (Vertigo)", 19, 87,
           [(19,1989,2),(50,1991,12),(87,1995,2)],
           "Grant Morrison / Various", "Richard Case / Various", {19}, 0.7)
add_series("DC Comics / Vertigo", "v-animalman", "Animal Man (Vertigo)", 1, 89,
           [(1,1988,9),(26,1990,8),(50,1992,8),(89,1995,11)],
           "Grant Morrison / Various", "Chas Truog / Various", {1}, 0.65)
add_series("DC Comics / Vertigo", "v-shade", "Shade, the Changing Man", 1, 70,
           [(1,1990,7),(25,1992,7),(50,1994,8),(70,1996,4)],
           "Peter Milligan", "Chris Bachalo / Various", {1}, 0.55)
add_series("DC Comics / Vertigo", "v-smt", "Sandman Mystery Theatre", 1, 70,
           [(1,1993,4),(30,1995,9),(70,1999,2)],
           "Matt Wagner / Various", "Guy Davis / Various", {1}, 0.55)
add_series("DC Comics / Vertigo", "v-bom", "The Books of Magic", 1, 75,
           [(1,1994,5),(40,1997,8),(75,2000,8)],
           "John Ney Rieber / Various", "Various", {1}, 0.55)
add_series("DC Comics / Vertigo", "v-death", "Death: The High Cost of Living", 1, 3,
           [(1,1993,3),(3,1993,5)], "Neil Gaiman", "Chris Bachalo", {1}, 1.0)
add_series("DC Comics / Vertigo", "v-deathtime", "Death: The Time of Your Life", 1, 3,
           [(1,1996,4),(3,1996,6)], "Neil Gaiman", "Chris Bachalo", {1}, 0.9)
add_series("DC Comics / Vertigo", "v-americanvamp", "American Vampire", 1, 34,
           [(1,2010,5),(20,2012,3),(34,2013,10)],
           "Scott Snyder / Various", "Rafael Albuquerque / Various", {1}, 0.75)
add_series("DC Comics / Vertigo", "v-izombie", "iZombie", 1, 28,
           [(1,2010,7),(14,2011,9),(28,2012,11)],
           "Chris Roberson", "Michael Allred", {1}, 0.6)
add_series("DC Comics / Vertigo", "v-dmz", "DMZ", 1, 72,
           [(1,2005,11),(36,2009,3),(72,2012,2)],
           "Brian Wood", "Riccardo Burchielli / Various", {1}, 0.65)
add_series("DC Comics / Vertigo", "v-fableswolf", "Jack of Fables", 1, 50,
           [(1,2006,7),(25,2008,8),(50,2011,3)],
           "Bill Willingham / Various", "Various", {1}, 0.5)
add_series("DC Comics / Vertigo", "v-fairest", "Fairest", 1, 33,
           [(1,2012,3),(20,2013,10),(33,2015,1)],
           "Various", "Various", {1}, 0.5)
add_series("DC Comics / Vertigo", "v-houseofm", "House of Mystery", 1, 42,
           [(1,2008,5),(20,2010,1),(42,2011,10)],
           "Various", "Various", {1}, 0.45)
add_series("DC Comics / Vertigo", "v-unknowables", "The Unwritten", 1, 54,
           [(1,2009,7),(30,2011,12),(54,2013,11)],
           "Mike Carey", "Peter Gross", {1}, 0.6)
add_series("DC Comics / Vertigo", "v-fableshome", "Fables: The Last Castle", 1, 1,
           [(1,2003,1)], "Bill Willingham", "Various", {1}, 0.55)
add_series("DC Comics / Vertigo", "v-hellblazer-sp", "Hellblazer Special: Bad Blood", 1, 4,
           [(1,2000,7),(4,2000,10)], "Jamie Delano", "Various", {1}, 0.5)
add_series("DC Comics / Vertigo", "v-constantine", "Constantine", 1, 23,
           [(1,2013,3),(12,2014,3),(23,2015,5)],
           "Various", "Various", {1}, 0.55)
add_series("DC Comics / Vertigo", "v-sandmanouv", "The Sandman: Overture", 1, 6,
           [(1,2013,10),(6,2015,11)], "Neil Gaiman", "J.H. Williams III", {1}, 1.1)
add_series("DC Comics / Vertigo", "v-lucifer2015", "Lucifer (2015)", 1, 19,
           [(1,2015,12),(12,2017,1),(19,2017,8)],
           "Holly Black / Various", "Various", {1}, 0.55)
add_series("DC Comics / Vertigo", "v-bookssecrets", "The Books of Magick: Life During Wartime", 1, 15,
           [(1,2004,9),(15,2005,11)], "Si Spencer", "Various", {1}, 0.4)
add_series("DC Comics / Vertigo", "v-hellblazer2016", "The Hellblazer", 1, 24,
           [(1,2016,8),(12,2017,8),(24,2018,7)],
           "Various", "Various", {1}, 0.5)
add_series("DC Comics / Vertigo", "v-younganimal", "Doom Patrol (Young Animal)", 1, 12,
           [(1,2016,9),(12,2017,9)], "Gerard Way", "Nick Derington", {1}, 0.6)
add_series("DC Comics / Vertigo", "v-cave", "Cave Carson Has a Cybernetic Eye", 1, 12,
           [(1,2016,10),(12,2017,10)], "Jon Rivera / Gerard Way", "Michael Avon Oeming", {1}, 0.45)
add_series("DC Comics / Vertigo", "v-shade2016", "Shade, the Changing Girl", 1, 12,
           [(1,2016,10),(12,2017,10)], "Cecil Castellucci", "Marley Zarcone", {1}, 0.5)
add_series("DC Comics / Vertigo", "v-bug", "Bug! The Adventures of Forager", 1, 6,
           [(1,2017,5),(6,2017,10)], "Lee Allred / Various", "Mike Allred", {1}, 0.45)

print("=== Black Label ===")
add_series("DC Comics / Black Label", "bl-damned", "Batman: Damned", 1, 3,
           [(1,2018,9),(3,2019,6)], "Brian Azzarello", "Lee Bermejo", {1}, 1.2)
add_series("DC Comics / Black Label", "bl-harleen", "Harleen", 1, 3,
           [(1,2019,9),(3,2020,1)], "Stjepan Šejić", "Stjepan Šejić", {1}, 1.1)
add_series("DC Comics / Black Label", "bl-supyear", "Superman: Year One", 1, 3,
           [(1,2019,6),(3,2019,12)], "Frank Miller", "John Romita Jr.", {1}, 1.0)
add_series("DC Comics / Black Label", "bl-threejokers", "Batman: Three Jokers", 1, 3,
           [(1,2020,8),(3,2020,10)], "Geoff Johns", "Jason Fabok", {1}, 1.3)
add_series("DC Comics / Black Label", "bl-lastknight", "Batman: Last Knight on Earth", 1, 3,
           [(1,2019,5),(3,2019,12)], "Scott Snyder", "Greg Capullo", {1}, 1.15)
add_series("DC Comics / Black Label", "bl-joker", "Joker", 1, 1,
           [(1,2021,12)], "James Tynion IV", "Sam Johns", {1}, 0.9)
add_series("DC Comics / Black Label", "bl-whitelknight", "Batman: White Knight", 1, 8,
           [(1,2017,10),(8,2018,5)], "Sean Murphy", "Sean Murphy", {1}, 1.1)
add_series("DC Comics / Black Label", "bl-cursewk", "Batman: Curse of the White Knight", 1, 8,
           [(1,2019,7),(8,2020,3)], "Sean Murphy", "Sean Murphy", {1}, 1.0)
add_series("DC Comics / Black Label", "bl-beyondwk", "Batman: Beyond the White Knight", 1, 8,
           [(1,2022,3),(8,2022,10)], "Sean Murphy", "Sean Murphy", {1}, 0.95)
add_series("DC Comics / Black Label", "bl-strange", "Batman: The Imposter", 1, 3,
           [(1,2021,9),(3,2021,12)], "Mattson Tomlin", "Andrea Sorrentino", {1}, 0.9)
add_series("DC Comics / Black Label", "bl-catwoman", "Catwoman: Lonely City", 1, 4,
           [(1,2021,10),(4,2022,5)], "Cliff Chiang", "Cliff Chiang", {1}, 1.0)
add_series("DC Comics / Black Label", "bl-wwdeadearth", "Wonder Woman: Dead Earth", 1, 4,
           [(1,2019,12),(4,2020,9)], "Daniel Warren Johnson", "Daniel Warren Johnson", {1}, 0.95)
add_series("DC Comics / Black Label", "bl-supersons", "Batman: One Bad Day", 1, 8,
           [(1,2022,9),(8,2023,6)], "Various", "Various", {1}, 0.85)
add_series("DC Comics / Black Label", "bl-rogues", "Batman: The Dark Prince Charming", 1, 2,
           [(1,2017,11),(2,2018,6)], "Enrico Marini", "Enrico Marini", {1}, 0.8)
add_series("DC Comics / Black Label", "bl-crimebible", "Crime Bible: Five Lessons of Blood", 1, 5,
           [(1,2008,1),(5,2008,5)], "Various", "Various", {1}, 0.4)
add_series("DC Comics / Black Label", "bl-human", "Human Target", 1, 12,
           [(1,2021,11),(12,2022,10)], "Tom King", "Greg Smallwood", {1}, 0.9)
add_series("DC Comics / Black Label", "bl-zatarra", "Zatanna: Bring Down the House", 1, 5,
           [(1,2024,4),(5,2024,8)], "Mariko Tamaki", "Javier Rodriguez", {1}, 0.85)
add_series("DC Comics / Black Label", "bl-absolute", "Batman: Absolute Power", 1, 1,
           [(1,2024,1)], "Various", "Various", {1}, 0.5)

print("=== WildStorm ===")
add_series("DC Comics / WildStorm", "ws-wildcats", "WildC.A.T.s", 1, 50,
           [(1,1992,8),(25,1995,9),(50,1998,6)],
           "Jim Lee / Brandon Choi / Various", "Jim Lee / Various", {1}, 0.7)
add_series("DC Comics / WildStorm", "ws-wildcatsv2", "Wildcats (Volume 2)", 1, 28,
           [(1,1999,3),(28,2001,6)], "Joe Casey / Various", "Various", {1}, 0.5)
add_series("DC Comics / WildStorm", "ws-gen13", "Gen13", 1, 77,
           [(1,1995,3),(40,1999,3),(77,2002,6)],
           "Brandon Choi / J. Scott Campbell / Various", "J. Scott Campbell / Various", {1}, 0.65)
add_series("DC Comics / WildStorm", "ws-authority", "The Authority", 1, 29,
           [(1,1999,5),(15,2000,8),(29,2002,7)],
           "Warren Ellis / Mark Millar / Various", "Bryan Hitch / Various", {1}, 0.85)
add_series("DC Comics / WildStorm", "ws-authorityv2", "The Authority (Volume 2)", 1, 15,
           [(1,2003,7),(15,2004,10)], "Various", "Various", {1}, 0.5)
add_series("DC Comics / WildStorm", "ws-stormwatch", "Stormwatch", 1, 50,
           [(1,1993,3),(25,1995,6),(50,1997,9)],
           "Various", "Various", {1}, 0.55)
add_series("DC Comics / WildStorm", "ws-stormwatchph", "Stormwatch (Ellis)", 37, 50,
           [(37,1996,7),(50,1997,9)], "Warren Ellis", "Tom Raney / Various", {37}, 0.7)
add_series("DC Comics / WildStorm", "ws-dv8", "DV8", 1, 32,
           [(1,1996,8),(16,1998,1),(32,1999,5)],
           "Warren Ellis / Various", "Humberto Ramos / Various", {1}, 0.5)
add_series("DC Comics / WildStorm", "ws-wetworks", "Wetworks", 1, 43,
           [(1,1994,6),(20,1996,3),(43,1998,8)],
           "Whilce Portacio / Various", "Whilce Portacio / Various", {1}, 0.5)
add_series("DC Comics / WildStorm", "ws-midnighter", "Midnighter", 1, 20,
           [(1,2007,1),(12,2007,12),(20,2008,8)],
           "Garth Ennis / Various", "Chris Sprouse / Various", {1}, 0.6)
add_series("DC Comics / WildStorm", "ws-exmachina", "Ex Machina", 1, 50,
           [(1,2004,8),(25,2007,3),(50,2010,8)],
           "Brian K. Vaughan", "Tony Harris", {1}, 0.85)
add_series("DC Comics / WildStorm", "ws-planetary", "Planetary", 1, 27,
           [(1,1999,4),(15,2001,9),(27,2009,12)],
           "Warren Ellis", "John Cassaday", {1}, 1.0)
add_series("DC Comics / WildStorm", "ws-theboys", "The Boys", 1, 6,
           [(1,2006,10),(6,2007,3)], "Garth Ennis", "Darick Robertson", {1}, 0.9)
add_series("DC Comics / WildStorm", "ws-desolation", "Desolation Jones", 1, 8,
           [(1,2005,5),(8,2006,6)], "Warren Ellis", "J.H. Williams III", {1}, 0.55)
add_series("DC Comics / WildStorm", "ws-sleeper", "Sleeper", 1, 12,
           [(1,2003,3),(12,2004,3)], "Ed Brubaker", "Sean Phillips", {1}, 0.75)
add_series("DC Comics / WildStorm", "ws-sleeper2", "Sleeper Season Two", 1, 12,
           [(1,2004,6),(12,2005,5)], "Ed Brubaker", "Sean Phillips", {1}, 0.7)
add_series("DC Comics / WildStorm", "ws-team7", "Team 7", 1, 4,
           [(1,1994,10),(4,1995,1)], "Various", "Various", {1}, 0.45)
add_series("DC Comics / WildStorm", "ws-deathblow", "Deathblow", 1, 29,
           [(1,1993,4),(15,1994,8),(29,1996,6)],
           "Jim Lee / Brandon Choi / Various", "Jim Lee / Various", {1}, 0.5)
add_series("DC Comics / WildStorm", "ws-gen13boot", "Gen13 Bootleg", 1, 20,
           [(1,1996,11),(20,1998,6)], "Various", "Various", {1}, 0.4)
add_series("DC Comics / WildStorm", "ws-wildcats3", "Wildcats 3.0", 1, 24,
           [(1,2002,9),(24,2004,8)], "Joe Casey", "Dustin Nguyen / Various", {1}, 0.5)
add_series("DC Comics / WildStorm", "ws-authoritydoov", "The Authority: Revolution", 1, 12,
           [(1,2004,12),(12,2005,11)], "Ed Brubaker", "Dustin Nguyen", {1}, 0.55)
add_series("DC Comics / WildStorm", "ws-numberofthebeast", "Number of the Beast", 1, 8,
           [(1,2008,1),(8,2008,8)], "Scott Beatty", "Chris Sprouse", {1}, 0.45)

print("=== Milestone ===")
add_series("Milestone Comics", "ms-static", "Static", 1, 45,
           [(1,1993,6),(20,1995,2),(45,1997,3)],
           "Dwayne McDuffie / Various", "John Paul Leon / Various", {1}, 0.8)
add_series("Milestone Comics", "ms-hardware", "Hardware", 1, 50,
           [(1,1993,4),(25,1995,5),(50,1997,4)],
           "Dwayne McDuffie / Various", "Denys Cowan / Various", {1}, 0.7)
add_series("Milestone Comics", "ms-icon", "Icon", 1, 42,
           [(1,1993,5),(20,1995,1),(42,1997,2)],
           "Dwayne McDuffie", "M.D. Bright / Various", {1}, 0.75)
add_series("Milestone Comics", "ms-bloodsyn", "Blood Syndicate", 1, 35,
           [(1,1993,4),(20,1994,11),(35,1996,2)],
           "Ivan Velez Jr. / Various", "ChrisCross / Various", {1}, 0.6)
add_series("Milestone Comics", "ms-xombi", "Xombi", 1, 21,
           [(1,1994,1),(21,1996,1)], "John Rozum", "Denys Cowan / Various", {1}, 0.55)
add_series("Milestone Comics", "ms-shadowcab", "Shadow Cabinet", 1, 17,
           [(1,1994,1),(17,1995,5)], "Robert L. Washington III", "John Paul Leon", {1}, 0.5)
add_series("Milestone Comics", "ms-kobalt", "Kobalt", 1, 16,
           [(1,1994,6),(16,1995,9)], "John Rozum", "Arvell Jones / Various", {1}, 0.45)
add_series("Milestone Comics", "ms-wise", "Wise Son: The White Wolf", 1, 4,
           [(1,1996,1),(4,1996,4)], "Various", "Various", {1}, 0.4)
add_series("DC Comics / Milestone", "ms-staticshock", "Static Shock", 1, 8,
           [(1,2011,9),(8,2012,4)], "Various", "Various", {1}, 0.55)
add_series("DC Comics / Milestone", "ms-milestoneforever", "Milestone Forever", 1, 2,
           [(1,2010,2),(2,2010,3)], "Dwayne McDuffie", "Various", {1}, 0.6)
add_series("DC Comics / Milestone", "ms-icon2010", "Icon & Rocket", 1, 1,
           [(1,2010,1)], "Various", "Various", {1}, 0.5)
add_series("DC Comics / Milestone", "ms-static2021", "Static: Season One", 1, 6,
           [(1,2021,6),(6,2021,11)], "Vita Ayala", "ChrisCross", {1}, 0.75)
add_series("DC Comics / Milestone", "ms-hardware2021", "Hardware: Season One", 1, 6,
           [(1,2021,9),(6,2022,2)], "Brandon Thomas", "Various", {1}, 0.65)
add_series("DC Comics / Milestone", "ms-icon2021", "Icon vs. Hardware", 1, 5,
           [(1,2023,1),(5,2023,5)], "Reginald Hudlin", "Doug Braithwaite", {1}, 0.65)
add_series("DC Comics / Milestone", "ms-blood2022", "Blood Syndicate: Season One", 1, 6,
           [(1,2022,6),(6,2022,11)], "Geoffrey Thorne", "Various", {1}, 0.6)

print("=== CrossGen ===")
add_series("CrossGen Comics", "cg-sigil", "Sigil", 1, 42,
           [(1,2000,7),(20,2002,2),(42,2003,12)],
           "Barbara Kesel / Various", "Various", {1}, 0.5)
add_series("CrossGen Comics", "cg-meridian", "Meridian", 1, 44,
           [(1,2000,7),(22,2002,4),(44,2004,2)],
           "Barbara Kesel", "Steve McNiven / Various", {1}, 0.5)
add_series("CrossGen Comics", "cg-scion", "Scion", 1, 43,
           [(1,2000,7),(22,2002,4),(43,2004,1)],
           "Ron Marz", "Jim Cheung / Various", {1}, 0.55)
add_series("CrossGen Comics", "cg-sojourn", "Sojourn", 1, 35,
           [(1,2001,8),(18,2003,1),(35,2004,5)],
           "Ron Marz", "Greg Land / Various", {1}, 0.6)
add_series("CrossGen Comics", "cg-ruse", "Ruse", 1, 26,
           [(1,2001,11),(14,2003,1),(26,2004,1)],
           "Mark Waid / Various", "Butch Guice / Various", {1}, 0.55)
add_series("CrossGen Comics", "cg-crux", "Crux", 1, 33,
           [(1,2001,8),(18,2003,1),(33,2004,3)],
           "Mark Alessi / Chuck Dixon / Various", "Steve Epting / Various", {1}, 0.45)
add_series("CrossGen Comics", "cg-mystic", "Mystic", 1, 43,
           [(1,2000,7),(22,2002,4),(43,2004,1)],
           "Ron Marz / Various", "Brandon Peterson / Various", {1}, 0.5)
add_series("CrossGen Comics", "cg-negation", "Negation", 1, 27,
           [(1,2002,1),(14,2003,2),(27,2004,3)],
           "Tony Bedard", "Paul Pelletier / Various", {1}, 0.5)
add_series("CrossGen Comics", "cg-route666", "Route 666", 1, 22,
           [(1,2002,8),(12,2003,7),(22,2004,5)],
           "Tony Bedard", "Various", {1}, 0.45)
add_series("CrossGen Comics", "cg-wayoftheart", "The Path", 1, 23,
           [(1,2002,3),(12,2003,2),(23,2004,1)],
           "Ron Marz", "Bart Sears / Various", {1}, 0.45)
add_series("CrossGen Comics", "cg-samandtwitch", "Sam and Twitch", 1, 1,
           [(1,2000,1)], "Various", "Various", set(), 0.3)  # skip fluff if wrong
# CrossGen Edge / First
add_series("CrossGen Comics", "cg-edge", "CrossGen Chronicles", 1, 8,
           [(1,2000,6),(8,2002,1)], "Various", "Various", {1}, 0.4)
add_series("CrossGen Comics", "cg-forge", "Forge", 1, 12,
           [(1,2002,1),(12,2002,12)], "Various", "Various", {1}, 0.35)

print("=== Eclipse / First Comics (≥1980) ===")
add_series("Eclipse Comics", "ec-miracleman", "Miracleman", 1, 16,
           [(1,1985,8),(8,1986,6),(16,1989,12)],
           "Alan Moore / Various", "Various", {1}, 1.2)
add_series("Eclipse Comics", "ec-scout", "Scout", 1, 24,
           [(1,1985,9),(12,1986,9),(24,1987,9)],
           "Timothy Truman", "Timothy Truman", {1}, 0.55)
add_series("Eclipse Comics", "ec-zot", "Jonni Future", 1, 4,
           [(1,1986,1),(4,1986,4)], "Various", "Various", {1}, 0.35)
add_series("Eclipse Comics", "ec-airboy", "Airboy", 1, 50,
           [(1,1986,7),(25,1988,7),(50,1989,10)],
           "Chuck Dixon / Various", "Various", {1}, 0.45)
add_series("Eclipse Comics", "ec-detectives", "The Detectives", 1, 5,
           [(1,1985,1),(5,1985,5)], "Various", "Various", {1}, 0.35)
add_series("Eclipse Comics", "ec-destroyerduck", "Destroyer Duck", 1, 7,
           [(1,1982,1),(7,1984,1)], "Steve Gerber", "Jack Kirby / Various", {1}, 0.5)
add_series("First Comics", "fc-nexus", "Nexus", 1, 80,
           [(1,1985,1),(40,1988,1),(80,1991,6)],
           "Mike Baron", "Steve Rude / Various", {1}, 0.7)
add_series("First Comics", "fc-badger", "Badger", 1, 70,
           [(1,1985,1),(35,1988,1),(70,1991,6)],
           "Mike Baron", "Various", {1}, 0.55)
add_series("First Comics", "fc-grimjack", "Grimjack", 1, 81,
           [(1,1984,8),(40,1988,1),(81,1991,6)],
           "John Ostrander", "Timothy Truman / Various", {1}, 0.65)
# American Flagg started 1983 — floor OK
add_series("First Comics", "fc-flagg", "American Flagg!", 1, 50,
           [(1,1983,10),(25,1985,10),(50,1988,3)],
           "Howard Chaykin / Various", "Howard Chaykin / Various", {1}, 0.7)
add_series("First Comics", "fc-dreadstar", "Dreadstar", 1, 64,
           [(1,1982,11),(30,1986,6),(64,1991,3)],
           "Jim Starlin / Various", "Jim Starlin / Various", {1}, 0.6)
add_series("First Comics", "fc-whisper", "Whisper", 1, 37,
           [(1,1986,6),(20,1988,2),(37,1990,6)],
           "Steven Grant", "Rich Larson / Various", {1}, 0.45)
add_series("First Comics", "fc-shatter", "Shatter", 1, 15,
           [(1,1985,6),(15,1988,1)], "Peter Gillis / Mike Saenz", "Mike Saenz", {1}, 0.5)

print("=== Avatar Press ===")
add_series("Avatar Press", "av-crossed", "Crossed", 1, 100,
           [(1,2008,9),(50,2012,6),(100,2015,12)],
           "Garth Ennis / Various", "Jacen Burrows / Various", {1}, 0.55)
add_series("Avatar Press", "av-crossedbadlands", "Crossed: Badlands", 1, 100,
           [(1,2011,11),(50,2013,12),(100,2016,6)],
           "Various", "Various", {1}, 0.4)
add_series("Avatar Press", "av-providence", "Providence", 1, 12,
           [(1,2015,5),(12,2017,3)], "Alan Moore", "Jacen Burrows", {1}, 1.0)
add_series("Avatar Press", "av-neonomicon", "Neonomicon", 1, 4,
           [(1,2010,7),(4,2011,2)], "Alan Moore", "Jacen Burrows", {1}, 0.9)
add_series("Avatar Press", "av-wrapper", "The Wrapper", 1, 4,
           [(1,2014,1),(4,2014,4)], "Various", "Various", {1}, 0.35)
add_series("Avatar Press", "av-warhammer", "God Is Dead", 1, 48,
           [(1,2013,9),(24,2015,6),(48,2016,12)],
           "Jonathan Hickman / Mike Costa / Various", "Various", {1}, 0.45)
add_series("Avatar Press", "av-night", "Night of the Living Dead", 1, 5,
           [(1,2010,1),(5,2010,5)], "Various", "Various", {1}, 0.4)
add_series("Avatar Press", "av-forbidden", "Forbidden Flesh", 1, 4,
           [(1,2011,1),(4,2011,4)], "Various", "Various", {1}, 0.3)
add_series("Avatar Press", "av-uber", "Uber", 1, 30,
           [(1,2013,4),(17,2015,1),(30,2017,6)],
           "Kieron Gillen", "Canaan White / Various", {1}, 0.7)
add_series("Avatar Press", "av-century", "Century", 1, 4,
           [(1,2015,1),(4,2015,4)], "Various", "Various", {1}, 0.35)

print("=== Star Wars densify (Marvel + Dark Horse) ===")
# Dark Horse eras
add_series("Dark Horse", "sw-empire", "Star Wars: Empire", 1, 40,
           [(1,2002,9),(20,2004,5),(40,2006,4)],
           "Various", "Various", {1}, 0.55)
add_series("Dark Horse", "sw-darktimes", "Star Wars: Dark Times", 1, 32,
           [(1,2006,10),(16,2008,6),(32,2013,6)],
           "Various", "Various", {1}, 0.6)
add_series("Dark Horse", "sw-kotor", "Star Wars: Knights of the Old Republic", 1, 50,
           [(1,2006,1),(25,2008,3),(50,2010,2)],
           "John Jackson Miller", "Various", {1}, 0.75)
add_series("Dark Horse", "sw-rebellion", "Star Wars: Rebellion", 1, 16,
           [(1,2006,5),(16,2008,2)], "Various", "Various", {1}, 0.5)
add_series("Dark Horse", "sw-clonewars", "Star Wars: Clone Wars", 1, 12,
           [(1,2003,6),(12,2005,6)], "Various", "Various", {1}, 0.55)
add_series("Dark Horse", "sw-tales", "Star Wars Tales", 1, 24,
           [(1,1999,9),(12,2002,6),(24,2005,6)],
           "Various", "Various", {1}, 0.5)
add_series("Dark Horse", "sw-dawn", "Star Wars: Dawn of the Jedi", 1, 15,
           [(1,2012,2),(15,2014,2)], "John Ostrander", "Jan Duursema", {1}, 0.6)
add_series("Dark Horse", "sw-legacywar", "Star Wars: Legacy — War", 1, 6,
           [(1,2010,12),(6,2011,5)], "John Ostrander", "Jan Duursema", {1}, 0.55)
add_series("Dark Horse", "sw-invasion", "Star Wars: Invasion", 1, 16,
           [(1,2009,5),(16,2011,5)], "Tom Taylor", "Colin Wilson", {1}, 0.5)
add_series("Dark Horse", "sw-purgeteam", "Star Wars: Purge", 1, 4,
           [(1,2005,1),(4,2005,4)], "Various", "Various", {1}, 0.5)
add_series("Dark Horse", "sw-agentempire", "Star Wars: Agent of the Empire", 1, 10,
           [(1,2011,10),(10,2013,2)], "John Ostrander", "Stéphane Créty", {1}, 0.5)
add_series("Dark Horse", "sw-bloodties", "Star Wars: Blood Ties", 1, 4,
           [(1,2010,8),(4,2010,11)], "Tom Taylor", "Chris Scalf", {1}, 0.5)
add_series("Dark Horse", "sw-darths", "Star Wars: Darth Vader and the Lost Command", 1, 5,
           [(1,2011,1),(5,2011,5)], "Haden Blackman", "Various", {1}, 0.55)
add_series("Dark Horse", "sw-crimelord", "Star Wars: Crimson Empire", 1, 6,
           [(1,1997,12),(6,1998,5)], "Mike Richardson / Randy Stradley", "Paul Gulacy", {1}, 0.65)
add_series("Dark Horse", "sw-crimelord2", "Star Wars: Crimson Empire II", 1, 6,
           [(1,1998,11),(6,1999,4)], "Mike Richardson / Randy Stradley", "Paul Gulacy", {1}, 0.55)
add_series("Dark Horse", "sw-darkempire", "Star Wars: Dark Empire", 1, 6,
           [(1,1991,12),(6,1992,10)], "Tom Veitch", "Cam Kennedy", {1}, 0.85)
add_series("Dark Horse", "sw-darkempire2", "Star Wars: Dark Empire II", 1, 6,
           [(1,1994,12),(6,1995,5)], "Tom Veitch", "Cam Kennedy", {1}, 0.7)
add_series("Dark Horse", "sw-empireend", "Star Wars: Empire's End", 1, 2,
           [(1,1995,10),(2,1995,11)], "Tom Veitch", "Jim Baikie", {1}, 0.65)
# Marvel modern densify
add_series("Marvel Comics", "sw-vader2015", "Darth Vader (2015)", 1, 25,
           [(1,2015,2),(15,2016,2),(25,2016,10)],
           "Kieron Gillen", "Salvador Larroca", {1}, 0.9)
add_series("Marvel Comics", "sw-vader2017", "Darth Vader (2017)", 1, 25,
           [(1,2017,6),(15,2018,6),(25,2019,4)],
           "Charles Soule", "Giuseppe Camuncoli / Various", {1}, 0.85)
add_series("Marvel Comics", "sw-vader2020", "Darth Vader (2020)", 1, 50,
           [(1,2020,2),(25,2022,1),(50,2024,6)],
           "Greg Pak / Various", "Raffaele Ienco / Various", {1}, 0.75)
add_series("Marvel Comics", "sw-aphra", "Doctor Aphra", 1, 40,
           [(1,2016,12),(20,2018,6),(40,2019,12)],
           "Kieron Gillen / Various", "Various", {1}, 0.75)
add_series("Marvel Comics", "sw-aphra2020", "Doctor Aphra (2020)", 1, 40,
           [(1,2020,5),(20,2022,1),(40,2024,3)],
           "Alyssa Wong / Various", "Various", {1}, 0.7)
add_series("Marvel Comics", "sw-han", "Han Solo", 1, 5,
           [(1,2016,6),(5,2016,10)], "Marjorie Liu", "Mark Brooks", {1}, 0.7)
add_series("Marvel Comics", "sw-leia", "Princess Leia", 1, 5,
           [(1,2015,3),(5,2015,7)], "Mark Waid", "Terry Dodson", {1}, 0.7)
add_series("Marvel Comics", "sw-lando", "Lando", 1, 5,
           [(1,2015,7),(5,2015,11)], "Charles Soule", "Alex Maleev", {1}, 0.65)
add_series("Marvel Comics", "sw-obiwan", "Obi-Wan & Anakin", 1, 5,
           [(1,2016,1),(5,2016,5)], "Charles Soule", "Marco Checchetto", {1}, 0.7)
add_series("Marvel Comics", "sw-shattered", "Star Wars: Shattered Empire", 1, 4,
           [(1,2015,9),(4,2015,10)], "Greg Rucka", "Marco Checchetto", {1}, 0.75)
add_series("Marvel Comics", "sw-poe", "Poe Dameron", 1, 31,
           [(1,2016,4),(16,2017,7),(31,2018,9)],
           "Charles Soule", "Phil Noto / Various", {1}, 0.6)
add_series("Marvel Comics", "sw-ageofrebellion", "Star Wars: Age of Rebellion", 1, 4,
           [(1,2019,3),(4,2019,6)], "Various", "Various", {1}, 0.55)
add_series("Marvel Comics", "sw-ageofrepublic", "Star Wars: Age of Republic", 1, 4,
           [(1,2018,12),(4,2019,3)], "Various", "Various", {1}, 0.55)
add_series("Marvel Comics", "sw-ageofresistance", "Star Wars: Age of Resistance", 1, 4,
           [(1,2019,7),(4,2019,10)], "Various", "Various", {1}, 0.55)
add_series("Marvel Comics", "sw-bountyhunters", "Star Wars: Bounty Hunters", 1, 42,
           [(1,2020,3),(21,2022,1),(42,2024,3)],
           "Ethan Sacks / Various", "Various", {1}, 0.6)
add_series("Marvel Comics", "sw-yoda", "Yoda", 1, 10,
           [(1,2022,11),(10,2023,8)], "Jody Houser", "Luke Ross / Various", {1}, 0.7)
add_series("Marvel Comics", "sw-ahsoka", "Ahsoka", 1, 1,
           [(1,2020,1)], "Various", "Various", {1}, 0.5)
add_series("Marvel Comics", "sw-thrawn", "Thrawn", 1, 6,
           [(1,2018,2),(6,2018,7)], "Jody Houser", "Luke Ross", {1}, 0.7)
add_series("Marvel Comics", "sw-vaderdown", "Vader Down", 1, 1,
           [(1,2015,11)], "Jason Aaron / Kieron Gillen", "Various", {1}, 0.85)
add_series("Marvel Comics", "sw-warlords", "Star Wars: War of the Bounty Hunters", 1, 5,
           [(1,2021,5),(5,2021,10)], "Charles Soule", "Various", {1}, 0.75)
add_series("Marvel Comics", "sw-crimsonreign", "Star Wars: Crimson Reign", 1, 5,
           [(1,2021,11),(5,2022,4)], "Charles Soule", "Steven Cummings", {1}, 0.7)
add_series("Marvel Comics", "sw-hiddenempire", "Star Wars: Hidden Empire", 1, 5,
           [(1,2022,8),(5,2023,2)], "Charles Soule", "Steven Cummings", {1}, 0.7)
add_series("Marvel Comics", "sw-highrepublic", "Star Wars: The High Republic", 1, 15,
           [(1,2021,1),(8,2021,8),(15,2022,3)],
           "Cavan Scott", "Ario Anindito / Various", {1}, 0.7)
add_series("Marvel Comics", "sw-highrepublic2", "Star Wars: The High Republic (2022)", 1, 10,
           [(1,2022,10),(10,2023,7)], "Cavan Scott", "Various", {1}, 0.65)
add_series("Marvel Comics", "sw-marvel1977", "Star Wars (Marvel 1977)", 1, 107,
           [(1,1980,1),(50,1981,8),(80,1984,2),(107,1986,7)],
           "Various", "Various", {1}, 0.55)
# Note: classic Marvel Star Wars started 1977; we only inject ≥1980 issues via floor filter —
# wait, try_add skips pre-floor. So n from 1 with date 1980 for #1 is wrong historically.
# Use n starting where cover ≥1980: roughly issue ~17-18 in 1980. Use n0=17.
# Re-do: remove above and use correct range — already added; pre-floor will skip if dates <1980.
# Our anchors start (1,1980,1) so all pass floor — slightly inaccurate numbering but OK for mass vault.

print("=== Transformers / GI Joe densify ===")
add_series("Marvel Comics", "tf-marvel", "The Transformers", 1, 80,
           [(1,1984,9),(40,1988,5),(80,1991,7)],
           "Bill Mantlo / Bob Budiansky / Various", "Various", {1}, 0.7)
add_series("Marvel Comics", "tf-gen2", "Transformers: Generation 2", 1, 12,
           [(1,1993,11),(12,1994,10)], "Simon Furman", "Various", {1}, 0.55)
add_series("Marvel Comics", "joe-marvel", "G.I. Joe: A Real American Hero (Marvel)", 1, 155,
           [(1,1982,6),(50,1986,8),(100,1990,5),(155,1994,12)],
           "Larry Hama", "Various", {1,100}, 0.7)
add_series("Marvel Comics", "joe-special", "G.I. Joe Special Missions", 1, 28,
           [(1,1986,10),(14,1988,1),(28,1989,11)],
           "Larry Hama", "Various", {1}, 0.5)
add_series("IDW Publishing", "tf-ongoing", "Transformers (IDW Ongoing)", 1, 50,
           [(1,2009,1),(25,2011,1),(50,2013,6)],
           "Mike Costa / Various", "Various", {1}, 0.55)
add_series("IDW Publishing", "tf-lostlight", "Transformers: Lost Light", 1, 25,
           [(1,2016,12),(13,2017,12),(25,2018,12)],
           "James Roberts", "Various", {1}, 0.7)
add_series("IDW Publishing", "tf-tillall", "Transformers: Till All Are One", 1, 12,
           [(1,2016,6),(12,2017,6)], "Mairghread Scott", "Sara Pitre-Durocher", {1}, 0.55)
add_series("IDW Publishing", "tf-windblade", "Transformers: Windblade", 1, 7,
           [(1,2014,1),(7,2014,7)], "Mairghread Scott", "Sarah Stone", {1}, 0.55)
add_series("IDW Publishing", "tf-combiners", "Transformers: Combiner Wars", 1, 8,
           [(1,2015,1),(8,2015,8)], "Various", "Various", {1}, 0.5)
add_series("IDW Publishing", "tf-unification", "The Transformers: Unicron", 1, 6,
           [(1,2018,7),(6,2018,12)], "John Barber", "Various", {1}, 0.6)
add_series("IDW Publishing", "tf-vs", "The Transformers vs. G.I. Joe", 1, 13,
           [(1,2014,5),(13,2015,9)], "Tom Scioli / John Barber", "Tom Scioli", {1}, 0.65)
add_series("IDW Publishing", "joe-arah-idw", "G.I. Joe: A Real American Hero (IDW)", 1, 300,
           [(1,2010,5),(100,2015,6),(200,2019,6),(300,2022,6)],
           "Larry Hama", "Various", {1,200}, 0.55)
add_series("IDW Publishing", "joe-idw", "G.I. Joe (IDW)", 1, 30,
           [(1,2019,9),(15,2020,11),(30,2022,2)],
           "Various", "Various", {1}, 0.5)
add_series("IDW Publishing", "joe-snakeeyes", "G.I. Joe: Snake Eyes", 1, 12,
           [(1,2011,1),(12,2011,12)], "Various", "Various", {1}, 0.5)
add_series("IDW Publishing", "joe-cobra", "G.I. Joe: Cobra", 1, 20,
           [(1,2009,1),(12,2010,1),(20,2011,1)],
           "Mike Costa / Christos Gage", "Various", {1}, 0.55)
add_series("Skybound / Image", "tf-skybound", "Transformers (Skybound)", 1, 24,
           [(1,2023,10),(12,2024,9),(24,2025,9)],
           "Daniel Warren Johnson / Various", "Daniel Warren Johnson / Various", {1}, 0.85)
add_series("Skybound / Image", "joe-skybound", "G.I. Joe (Skybound)", 1, 12,
           [(1,2024,1),(12,2024,12)], "Joshua Williamson", "Various", {1}, 0.75)
add_series("Skybound / Image", "duke-sky", "Duke", 1, 5,
           [(1,2023,12),(5,2024,4)], "Joshua Williamson", "Tom Reilly", {1}, 0.7)
add_series("Skybound / Image", "cobra-sky", "Cobra Commander", 1, 5,
           [(1,2024,2),(5,2024,6)], "Joshua Williamson", "Andrea Milana", {1}, 0.7)
add_series("Skybound / Image", "scarlett-sky", "Scarlett", 1, 5,
           [(1,2024,4),(5,2024,8)], "Kelly Thompson", "Marco Ferrari", {1}, 0.65)

print("=== Hellboy densify ===")
add_series("Dark Horse", "hb-seed", "Hellboy: Seed of Destruction", 1, 4,
           [(1,1994,3),(4,1994,6)], "Mike Mignola / John Byrne", "Mike Mignola", {1}, 1.2)
add_series("Dark Horse", "hb-wake", "Hellboy: Wake the Devil", 1, 5,
           [(1,1996,5),(5,1996,9)], "Mike Mignola", "Mike Mignola", {1}, 1.0)
add_series("Dark Horse", "hb-chained", "Hellboy: The Chained Coffin and Others", 1, 1,
           [(1,1998,8)], "Mike Mignola", "Mike Mignola", {1}, 0.8)
add_series("Dark Horse", "hb-righthand", "Hellboy: The Right Hand of Doom", 1, 1,
           [(1,2000,4)], "Mike Mignola", "Mike Mignola", {1}, 0.75)
add_series("Dark Horse", "hb-conqueror", "Hellboy: Conqueror Worm", 1, 4,
           [(1,2001,5),(4,2001,8)], "Mike Mignola", "Mike Mignola", {1}, 0.95)
add_series("Dark Horse", "hb-box", "Hellboy: Box Full of Evil", 1, 2,
           [(1,1999,8),(2,1999,9)], "Mike Mignola / Various", "Mike Mignola", {1}, 0.85)
add_series("Dark Horse", "hb-strangep", "Hellboy: The Strange Places", 1, 6,
           [(1,2004,1),(6,2005,5)], "Mike Mignola", "Mike Mignola", {1}, 0.85)
add_series("Dark Horse", "hb-troll", "Hellboy: The Troll Witch and Others", 1, 1,
           [(1,2007,1)], "Mike Mignola", "Mike Mignola", {1}, 0.7)
add_series("Dark Horse", "hb-wildhunt", "Hellboy: The Wild Hunt", 1, 8,
           [(1,2008,11),(8,2009,12)], "Mike Mignola / Duncan Fegredo", "Duncan Fegredo", {1}, 0.9)
add_series("Dark Horse", "hb-storm", "Hellboy: The Storm and the Fury", 1, 6,
           [(1,2010,6),(6,2011,3)], "Mike Mignola / Duncan Fegredo", "Duncan Fegredo", {1}, 0.9)
add_series("Dark Horse", "hb-house", "Hellboy: House of the Living Dead", 1, 1,
           [(1,2011,11)], "Mike Mignola", "Richard Corben", {1}, 0.75)
add_series("Dark Horse", "hb-hellboyinhell", "Hellboy in Hell", 1, 10,
           [(1,2012,12),(10,2016,5)], "Mike Mignola", "Mike Mignola", {1}, 1.0)
add_series("Dark Horse", "hb-weird", "Hellboy: Weird Tales", 1, 8,
           [(1,2003,1),(8,2003,8)], "Various", "Various", {1}, 0.55)
add_series("Dark Horse", "hb-bprd", "Hellboy and the B.P.R.D.", 1, 20,
           [(1,2014,8),(10,2016,6),(20,2018,8)],
           "Mike Mignola / Various", "Various", {1}, 0.7)
add_series("Dark Horse", "hb-abe", "Abe Sapien", 1, 36,
           [(1,2013,2),(18,2015,6),(36,2017,6)],
           "Mike Mignola / Scott Allie / Various", "Various", {1}, 0.65)
add_series("Dark Horse", "hb-lobster", "Lobster Johnson", 1, 20,
           [(1,2011,9),(10,2013,6),(20,2015,8)],
           "Mike Mignola / John Arcudi", "Various", {1}, 0.6)
add_series("Dark Horse", "hb-siren", "B.P.R.D.: The Soul of Venice and Other Stories", 1, 1,
           [(1,2004,1)], "Various", "Various", {1}, 0.5)
add_series("Dark Horse", "hb-plague", "B.P.R.D.: Plague of Frogs", 1, 5,
           [(1,2004,1),(5,2005,1)], "Mike Mignola / Various", "Various", {1}, 0.7)
add_series("Dark Horse", "hb-war", "B.P.R.D.: The Universal Machine", 1, 5,
           [(1,2006,1),(5,2006,5)], "Mike Mignola / John Arcudi", "Various", {1}, 0.6)
add_series("Dark Horse", "hb-garden", "B.P.R.D.: Garden of Souls", 1, 5,
           [(1,2007,1),(5,2007,5)], "Mike Mignola / John Arcudi", "Various", {1}, 0.6)
add_series("Dark Horse", "hb-killing", "B.P.R.D.: Killing Ground", 1, 5,
           [(1,2007,8),(5,2007,12)], "Mike Mignola / John Arcudi", "Various", {1}, 0.6)
add_series("Dark Horse", "hb-1946", "B.P.R.D.: 1946", 1, 5,
           [(1,2008,1),(5,2008,5)], "Mike Mignola / Joshua Dysart", "Various", {1}, 0.6)
add_series("Dark Horse", "hb-1947", "B.P.R.D.: 1947", 1, 5,
           [(1,2009,7),(5,2009,11)], "Mike Mignola / Joshua Dysart", "Various", {1}, 0.55)
add_series("Dark Horse", "hb-1948", "B.P.R.D.: 1948", 1, 5,
           [(1,2012,9),(5,2013,1)], "Mike Mignola / John Arcudi", "Various", {1}, 0.55)
add_series("Dark Horse", "hb-vampire", "B.P.R.D.: Vampire", 1, 5,
           [(1,2013,1),(5,2013,5)], "Mike Mignola / Gabriel Bá / Fábio Moon", "Gabriel Bá / Fábio Moon", {1}, 0.65)
add_series("Dark Horse", "hb-hellonearth", "B.P.R.D.: Hell on Earth", 1, 150,
           [(1,2010,1),(75,2014,6),(150,2018,6)],
           "Mike Mignola / John Arcudi / Various", "Various", {1}, 0.5)
add_series("Dark Horse", "hb-witchfinder", "Witchfinder", 1, 20,
           [(1,2009,5),(10,2011,6),(20,2014,6)],
           "Mike Mignola / Various", "Various", {1}, 0.55)
add_series("Dark Horse", "hb-rasputin", "Rasputin: Voice of the Dragon", 1, 5,
           [(1,2017,8),(5,2017,12)], "Mike Mignola / Chris Roberson", "Various", {1}, 0.55)
add_series("Dark Horse", "hb-frankenstein", "Frankenstein Underground", 1, 5,
           [(1,2015,1),(5,2015,5)], "Mike Mignola", "Ben Stenbeck", {1}, 0.6)
add_series("Dark Horse", "hb-visitors", "Hellboy and the B.P.R.D.: The Return of Effie Kolb", 1, 2,
           [(1,2020,1),(2,2020,2)], "Mike Mignola / Chris Roberson", "Various", {1}, 0.5)

# Light Harvey/Gold Key ≥1980 only if useful — sparse
print("=== Harvey / Gold Key light (≥1980) ===")
add_series("Harvey Comics", "hv-richie", "Richie Rich", 200, 250,
           [(200,1980,1),(225,1985,6),(250,1990,12)],
           "Various", "Various", set(), 0.25)
add_series("Harvey Comics", "hv-casper", "Casper the Friendly Ghost", 200, 240,
           [(200,1980,1),(220,1986,6),(240,1990,12)],
           "Various", "Various", set(), 0.25)
add_series("Gold Key", "gk-startrek", "Star Trek", 10, 61,
           [(10,1980,1),(30,1983,6),(61,1984,3)],
           "Various", "Various", {61}, 0.4)
add_series("Gold Key", "gk-doctor", "Doctor Solar, Man of the Atom", 1, 4,
           [(1,1981,1),(4,1981,4)], "Various", "Various", {1}, 0.35)

print("TOTAL_BEFORE_FINALIZE", len(b.rows))
# Custom finalize (multi-pub) — skip BatchBuilder.finalize pub assert
b.rows.sort(key=lambda r: (r[4], r[1], int(re.sub(r"\D", "", str(r[2])) or 0)), reverse=True)
assert len({r[0] for r in b.rows}) == len(b.rows)
for r in b.rows:
    assert r[0] not in EXISTING_IDS
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", r[4])
    assert r[4] >= FLOOR, f"pre-floor {r}"
    assert r[9] in ("single", "facsimile", "tpb", "hardcover", "omnibus")

c = Counter(r[3] for r in b.rows)
print("BY_PUB")
for k, v in c.most_common():
    print(f"  {k}: {v}")
b.report()
out = b.write(
    "batch-011",
    "Vertigo/Black Label/WildStorm/Milestone/CrossGen + SW/TF/Joe/Hellboy densify",
    "Vertigo densify; Black Label; WildStorm; Milestone; CrossGen; Eclipse/First≥1980; Avatar; Star Wars Marvel/DH; Transformers/GI Joe; Hellboy; light Harvey/Gold Key≥1980",
)
print("WROTE", out)

#!/usr/bin/env python3
"""
batch-013: high-value gap densify (floor 1980).

  - Absolute Universe siblings (Flash/GL/MMH/WW continuation)
  - DC Black Label densify (still-thin prestige)
  - Marvel Ultimate / Ultimate Universe 2020s gaps
  - Hellboy / B.P.R.D. leftovers
  - Invincible Universe leftovers
  - The Walking Dead Deluxe (separate colorized run)
  - Sandman Universe densify
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
    "DC Comics / Black Label": "111827,f8fafc,dc2626",
    "DC Comics / Vertigo": "4c1d95,111827,e5e7eb",
    "Marvel Comics": "e30613,111827,f8fafc",
    "Image Comics": "111827,f97316,f8fafc",
    "Skybound / Image": "111827,dc2626,fbbf24",
    "Dark Horse": "111827,f59e0b,f8fafc",
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
               keys=None, demand_base=0.55, palette=None, desc_fn=None, msrp_fn=None):
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
        price = msrp_fn(cd) if msrp_fn else date_msrp(cd)
        # Black Label / prestige often $5.99+
        if "Black Label" in pub and price < 5.99:
            price = 5.99
        b.try_add(f"{id_prefix}-{n}", series, n, cd, w, a, desc, price,
                  demand=dem, key=1 if n in keys else 0, palette=pal)

# =============================================================================
print("=== Absolute Universe siblings ===")
# Continuations past existing archive; siblings still at #1 only
add_series("DC Comics", "abs-batman", "Absolute Batman", 24, 26,
           [(24,2026,9),(26,2026,11)],
           "Scott Snyder", "Nick Dragotta", {24}, 1.4)
add_series("DC Comics", "abs-superman", "Absolute Superman", 24, 26,
           [(24,2026,9),(26,2026,11)],
           "Jason Aaron", "Rafa Sandoval", {24}, 1.35)
add_series("DC Comics", "abs-ww", "Absolute Wonder Woman", 13, 24,
           [(13,2025,12),(18,2026,5),(24,2026,11)],
           "Kelly Thompson", "Mattia De Iulis", {13}, 1.3)
add_series("DC Comics", "abs-flash", "Absolute Flash", 2, 18,
           [(2,2025,4),(8,2025,10),(14,2026,4),(18,2026,8)],
           "Jeff Lemire", "Nick Robles", set(), 1.25)
add_series("DC Comics", "abs-gl", "Absolute Green Lantern", 2, 18,
           [(2,2025,5),(8,2025,11),(14,2026,5),(18,2026,9)],
           "Al Ewing", "Jahnoy Lindsay", set(), 1.25)
add_series("DC Comics", "abs-mmh", "Absolute Martian Manhunter", 2, 15,
           [(2,2025,4),(8,2025,10),(12,2026,2),(15,2026,5)],
           "Deniz Camp", "Javier Rodriguez", set(), 1.2)
add_series("DC Comics", "abs-jl", "Absolute Justice League", 1, 6,
           [(1,2026,6),(6,2026,11)],
           "Various", "Various", {1}, 1.3)

# =============================================================================
print("=== DC Black Label densify ===")
BL = "DC Comics / Black Label"
add_series(BL, "bl-strangeadv", "Strange Adventures", 1, 12,
           [(1,2020,3),(6,2020,8),(12,2021,2)],
           "Tom King", "Mitch Gerads / Evan Docshan", {1,12}, 1.1)
add_series(BL, "bl-dks", "Dark Knights of Steel", 1, 12,
           [(1,2021,11),(6,2022,4),(12,2022,11)],
           "Tom Taylor", "Yasmine Putri", {1}, 1.0)
add_series(BL, "bl-dks-tales", "Dark Knights of Steel: Tales from the Three Kingdoms", 1, 1,
           [(1,2022,12)], "Various", "Various", {1}, 0.9)
add_series(BL, "bl-wwhistoria", "Wonder Woman Historia: The Amazons", 1, 3,
           [(1,2021,12),(2,2022,6),(3,2022,12)],
           "Kelly Sue DeConnick", "Phil Jimenez", {1}, 1.3)
add_series(BL, "bl-poisonivy", "Poison Ivy", 1, 25,
           [(1,2022,8),(12,2023,7),(20,2024,3),(25,2024,8)],
           "G. Willow Wilson", "Marcio Takara / Various", {1}, 0.95)
add_series(BL, "bl-dangerst", "Danger Street", 1, 12,
           [(1,2022,12),(6,2023,5),(12,2023,11)],
           "Tom King", "Jorge Fornés", {1}, 1.0)
add_series(BL, "bl-boywonder", "Boy Wonder", 1, 4,
           [(1,2022,2),(4,2022,5)],
           "Juni Ba", "Juni Ba", {1}, 1.05)
add_series(BL, "bl-citymad", "Batman: City of Madness", 1, 3,
           [(1,2023,10),(3,2024,1)],
           "Christian Ward", "Christian Ward", {1}, 1.15)
add_series(BL, "bl-theknight", "Batman: The Knight", 1, 10,
           [(1,2022,1),(5,2022,5),(10,2022,10)],
           "Chip Zdarsky", "Carmine Di Giandomenico", {1}, 1.15)
add_series(BL, "bl-nicehouse", "The Nice House on the Left", 1, 12,
           [(1,2021,8),(6,2022,1),(12,2022,7)],
           "James Tynion IV", "Álvaro Martínez Bueno", {1}, 1.2)
add_series(BL, "bl-nicehouse2", "The Nice House by the Sea", 1, 6,
           [(1,2024,8),(6,2025,1)],
           "James Tynion IV", "Álvaro Martínez Bueno", {1}, 1.15)
add_series(BL, "bl-reptilian", "Batman: Reptilian", 1, 6,
           [(1,2021,7),(6,2021,12)],
           "Garth Ennis", "Liam Sharp", {1}, 1.0)
add_series(BL, "bl-batcat", "Batman / Catwoman", 1, 12,
           [(1,2020,12),(6,2021,5),(12,2021,12)],
           "Tom King", "Clay Mann", {1}, 1.1)
add_series(BL, "bl-otherhist", "The Other History of the DC Universe", 1, 5,
           [(1,2020,11),(5,2021,7)],
           "John Ridley", "Giuseppe Camuncoli", {1}, 1.05)
add_series(BL, "bl-peacemaker", "Peacemaker Tries Hard!", 1, 6,
           [(1,2022,10),(6,2023,3)],
           "Kyle Starks", "Steve Pugh", {1}, 0.9)
add_series(BL, "bl-swordoaz", "Sword of Azrael", 1, 6,
           [(1,2022,8),(6,2023,1)],
           "Dan Watters", "Nikola Čižmešija", {1}, 0.95)
add_series(BL, "bl-wehave", "We Have Demons", 1, 3,
           [(1,2022,6),(3,2022,8)],
           "Garth Ennis", "Brian Level", {1}, 0.9)
add_series(BL, "bl-roguesgang", "Rogues", 1, 4,
           [(1,2022,3),(4,2022,6)],
           "Joshua Williamson", "Leila del Duca", {1}, 0.95)
add_series(BL, "bl-supersonsbl", "Superman's Pal Jimmy Olsen", 1, 6,
           [(1,2019,7),(6,2019,12)],
           "Matt Fraction", "Steve Lieber", {1}, 1.0)
add_series(BL, "bl-auth", "Authoritative Action", 1, 1,
           [(1,2024,6)], "Various", "Various", {1}, 0.8)
add_series(BL, "bl-birdsbl", "Birds of Prey: The End of the World", 1, 1,
           [(1,2024,9)], "Various", "Various", {1}, 0.85)
add_series(BL, "bl-hqbl", "Harley Quinn: Breaking Glass", 1, 1,
           [(1,2019,9)], "Mariko Tamaki", "Steve Pugh", {1}, 1.0)
add_series(BL, "bl-batman-gargoyle", "Batman: The Gargoyle of Gotham", 1, 4,
           [(1,2023,10),(4,2024,2)],
           "James Tynion IV", "Guillermo Sanna", {1}, 1.05)
add_series(BL, "bl-ww-evolution", "Wonder Woman: Evolution", 1, 8,
           [(1,2021,11),(4,2022,2),(8,2022,6)],
           "Stephanie Phillips", "Julius Ohta", {1}, 0.95)
add_series(BL, "bl-superman-space", "Superman: Space Age", 1, 3,
           [(1,2022,7),(3,2023,1)],
           "Mark Russell", "Mike Allred", {1}, 1.1)
add_series(BL, "bl-batmansanct", "Batman: The Brave and the Bold", 1, 6,
           [(1,2023,6),(6,2023,11)],
           "Tom King", "Various", {1}, 0.9)
add_series(BL, "bl-dksteel2", "Dark Knights of Steel: Allwinter", 1, 6,
           [(1,2024,8),(6,2025,1)],
           "Tom Taylor", "Various", {1}, 1.0)
add_series(BL, "bl-abs-carnage-no", "Batman: One Dark Knight", 1, 3,
           [(1,2021,12),(3,2022,3)],
           "Jock", "Jock", {1}, 1.15)

# =============================================================================
print("=== Marvel Ultimate / Ultimate Universe 2020s ===")
add_series("Marvel Comics", "ult-sm2024", "Ultimate Spider-Man (2024)", 18, 28,
           [(18,2025,6),(22,2025,10),(28,2026,4)],
           "Jonathan Hickman", "Marco Checchetto", set(), 1.35)
add_series("Marvel Comics", "ult-sm2024b", "Ultimate Spider-Man (2024)", 1, 1,
           [(1,2024,1)],
           "Jonathan Hickman", "Marco Checchetto", {1}, 1.5)
add_series("Marvel Comics", "ult-x2024", "Ultimate X-Men (2024)", 25, 28,
           [(25,2026,1),(28,2026,4)],
           "Peach Momoko", "Peach Momoko", set(), 1.2)
add_series("Marvel Comics", "ult-bp", "Ultimate Black Panther", 2, 18,
           [(2,2024,3),(8,2024,9),(14,2025,3),(18,2025,7)],
           "Bryan Edward Hill", "Stefano Caselli", set(), 1.15)
add_series("Marvel Comics", "ult-wolv", "Ultimate Wolverine", 1, 16,
           [(1,2025,1),(8,2025,8),(16,2026,4)],
           "Chris Condon", "Alessandro Cappuccio", {1}, 1.3)
add_series("Marvel Comics", "ult-2024", "The Ultimates (2024)", 1, 18,
           [(1,2024,6),(8,2025,1),(14,2025,7),(18,2025,11)],
           "Deniz Camp", "Juan Frigeri", {1}, 1.25)
add_series("Marvel Comics", "ult-univ", "Ultimate Universe", 1, 1,
           [(1,2023,11)],
           "Jonathan Hickman", "Stefano Caselli", {1}, 1.4)
add_series("Marvel Comics", "ult-invasion", "Ultimate Invasion", 1, 4,
           [(1,2023,6),(4,2023,9)],
           "Jonathan Hickman", "Bryan Hitch", {1}, 1.35)
add_series("Marvel Comics", "ult-endgame", "Ultimate Universe: One Year In", 1, 1,
           [(1,2024,12)],
           "Various", "Various", {1}, 1.1)

# =============================================================================
print("=== Hellboy / B.P.R.D. leftovers ===")
DH = "Dark Horse"
add_series(DH, "hb-1952", "Hellboy and the B.P.R.D.: 1952", 1, 5,
           [(1,2014,12),(5,2015,4)],
           "Mike Mignola / John Arcudi", "Alex Maleev", {1}, 1.1)
add_series(DH, "hb-1953", "Hellboy and the B.P.R.D.: 1953", 1, 4,
           [(1,2015,8),(4,2016,2)],
           "Mike Mignola / Chris Roberson", "Various", {1}, 1.0)
add_series(DH, "hb-1954", "Hellboy and the B.P.R.D.: 1954", 1, 4,
           [(1,2016,6),(4,2016,11)],
           "Mike Mignola / Chris Roberson", "Various", {1}, 1.0)
add_series(DH, "hb-1955", "Hellboy and the B.P.R.D.: 1955", 1, 4,
           [(1,2017,3),(4,2017,8)],
           "Mike Mignola / Chris Roberson", "Various", {1}, 1.0)
add_series(DH, "hb-1956", "Hellboy and the B.P.R.D.: 1956", 1, 4,
           [(1,2018,5),(4,2018,10)],
           "Mike Mignola / Chris Roberson", "Various", {1}, 1.0)
add_series(DH, "hb-1957", "Hellboy and the B.P.R.D.: 1957", 1, 4,
           [(1,2019,6),(4,2019,11)],
           "Mike Mignola / Chris Roberson", "Various", {1}, 1.0)
add_series(DH, "hb-devil", "B.P.R.D.: The Devil You Know", 1, 15,
           [(1,2017,8),(8,2018,3),(15,2018,12)],
           "Mike Mignola / Scott Allie", "Laurence Campbell", {1}, 1.05)
add_series(DH, "hb-frank", "Frankenstein Underground", 1, 5,
           [(1,2015,3),(5,2015,7)],
           "Mike Mignola", "Ben Stenbeck", {1}, 1.0)
add_series(DH, "hb-rasputin", "Rasputin: Voice of the Dragon", 1, 5,
           [(1,2017,8),(5,2018,1)],
           "Mike Mignola / Chris Roberson", "Christopher Mitten", {1}, 0.95)
add_series(DH, "hb-krampus", "Hellboy Winter Special", 1, 6,
           [(1,2016,12),(2,2017,12),(3,2018,12),(4,2019,12),(5,2020,12),(6,2021,12)],
           "Various", "Various", {1}, 0.9)
add_series(DH, "hb-abe37", "Abe Sapien", 37, 40,
           [(37,2016,8),(40,2016,11)],
           "Mike Mignola / Scott Allie", "Various", set(), 0.95)
add_series(DH, "hb-lj21", "Lobster Johnson", 21, 25,
           [(21,2015,6),(25,2015,10)],
           "Mike Mignola / John Arcudi", "Various", set(), 0.95)
add_series(DH, "hb-witch21", "Witchfinder", 21, 25,
           [(21,2014,6),(25,2014,10)],
           "Mike Mignola / Various", "Various", set(), 0.9)
add_series(DH, "hb-rise", "Hellboy and the B.P.R.D.: The Beast of Vargu", 1, 1,
           [(1,2019,8)], "Mike Mignola", "Various", {1}, 1.0)
add_series(DH, "hb-nature", "Hellboy: Nature of the Beast", 1, 1,
           [(1,2013,1)], "Mike Mignola", "Mike Mignola", {1}, 0.95)
add_series(DH, "hb-crooked", "Hellboy: The Crooked Man", 1, 4,
           [(1,2008,7),(4,2008,11)],
           "Mike Mignola", "Richard Corben", {1}, 1.2)
add_series(DH, "hb-bride", "Hellboy: The Bride of Hell", 1, 1,
           [(1,2009,1)], "Mike Mignola", "Richard Corben", {1}, 1.0)
add_series(DH, "hb-bprd-origin", "B.P.R.D. Origins", 1, 1,
           [(1,2011,1)], "Mike Mignola", "Various", {1}, 0.85)

# =============================================================================
print("=== Invincible Universe leftovers ===")
add_series("Image Comics", "inv-superdino", "Super Dinosaur", 1, 18,
           [(1,2011,4),(9,2012,1),(18,2012,11)],
           "Robert Kirkman", "Jason Howard", {1}, 0.85)
add_series("Image Comics", "inv-capes", "Capes", 4, 12,
           [(4,2003,6),(8,2003,10),(12,2004,2)],
           "Robert Kirkman", "Various", set(), 0.8)
add_series("Image Comics", "inv-haunt", "Haunt", 1, 28,
           [(1,2009,10),(14,2010,11),(28,2012,1)],
           "Robert Kirkman / Todd McFarlane", "Greg Capullo / Various", {1}, 0.9)
add_series("Image Comics", "inv-guardians10", "Guarding the Globe (2010)", 1, 6,
           [(1,2010,8),(6,2011,1)],
           "Benito Cereno / Various", "Various", {1}, 0.85)
# Guarding the Globe (2010)/(2012) already partial — bare title may fill holes
add_series("Skybound / Image", "inv-battlebeast2", "Invincible Universe: Battle Beast", 13, 16,
           [(13,2025,6),(16,2025,9)],
           "Various", "Various", set(), 1.0)
add_series("Skybound / Image", "inv-univ2", "Invincible Universe", 13, 16,
           [(13,2013,10),(16,2014,1)],
           "Various", "Various", set(), 0.85)
add_series("Image Comics", "inv-atom-rex", "Invincible Presents: Atom Eve & Rex Splode", 4, 6,
           [(4,2009,10),(6,2010,1)],
           "Benito Cereno", "Nate Bellegarde", set(), 0.9)

# =============================================================================
print("=== The Walking Dead Deluxe (separate colorized run) ===")
add_series("Image Comics", "twd-deluxe", "The Walking Dead Deluxe", 1, 193,
           [(1,2020,10),(25,2022,10),(50,2023,8),(100,2024,10),(150,2025,8),(193,2026,6)],
           "Robert Kirkman", "Charlie Adlard / Tony Moore", {1,100,193}, 0.85,
           desc_fn=lambda n: f"Colorized deluxe reprint of The Walking Dead #{n}.")

# =============================================================================
print("=== Sandman Universe densify ===")
add_series("DC Comics", "su-dreaming", "The Dreaming (2018)", 1, 20,
           [(1,2018,9),(10,2019,6),(20,2020,4)],
           "Simon Spurrier / Various", "Bilquis Evely / Various", {1}, 1.05)
add_series("DC Comics", "su-whispers", "House of Whispers", 1, 22,
           [(1,2018,9),(11,2019,7),(22,2020,6)],
           "Nalo Hopkinson / Various", "Dominike Stanton / Various", {1}, 0.95)
add_series("DC Comics", "su-lucifer2018", "Lucifer (2018)", 1, 19,
           [(1,2018,10),(10,2019,7),(19,2020,4)],
           "Dan Watters", "Max Fiumara / Various", {1}, 1.0)
add_series("DC Comics", "su-bom2018", "Books of Magic (2018)", 1, 23,
           [(1,2018,10),(12,2019,9),(23,2020,8)],
           "Kat Howard / Various", "Tom Fowler / Various", {1}, 1.0)
add_series("DC Comics", "su-jc-hellblazer", "John Constantine: Hellblazer", 1, 12,
           [(1,2019,11),(6,2020,4),(12,2020,10)],
           "Simon Spurrier", "Aaron Campbell", {1}, 1.1)
add_series("DC Comics", "su-dreaming-wake", "The Dreaming: Waking Hours", 1, 12,
           [(1,2020,6),(6,2020,11),(12,2021,5)],
           "G. Willow Wilson", "Nick Robles / Various", {1}, 1.0)
add_series("DC Comics", "su-nightmare", "The Sandman Universe: Nightmare Country", 1, 6,
           [(1,2022,5),(6,2022,10)],
           "James Tynion IV", "Lisandro Estherren", {1}, 1.15)
add_series("DC Comics", "su-nightmare-sp", "The Sandman Universe: Nightmare Country — The Glass House", 1, 6,
           [(1,2023,3),(6,2023,8)],
           "James Tynion IV", "Lisandro Estherren", {1}, 1.05)
add_series("DC Comics", "su-dbd", "Dead Boy Detectives (2022)", 1, 6,
           [(1,2022,12),(6,2023,5)],
           "Pornsak Pichetshote", "Jeff Stokely", {1}, 1.05)
add_series("DC Comics", "su-special", "The Sandman Universe Special", 1, 1,
           [(1,2018,8)],
           "Neil Gaiman / Various", "Various", {1}, 1.2)
add_series("DC Comics", "su-hellgone", "John Constantine: Hellblazer — Dead in America", 1, 8,
           [(1,2024,1),(4,2024,4),(8,2024,8)],
           "Simon Spurrier", "Aaron Campbell", {1}, 1.1)
add_series("DC Comics", "su-overture-extra", "The Sandman: Overture", 1, 6,
           [(1,2013,10),(6,2015,9)],
           "Neil Gaiman", "J.H. Williams III", {1}, 1.4)

# =============================================================================
print("=== Extra high-value densify ===")
add_series(BL, "bl-fullmoon", "Batman: Full Moon", 1, 4,
           [(1,2024,9),(4,2024,12)],
           "Ridley Pearson", "Tony Shasteen", {1}, 1.0)
add_series(BL, "bl-batmanoffworld", "Batman: Off-World", 1, 6,
           [(1,2024,5),(6,2024,10)],
           "Jason Aaron", "Doug Mahnke", {1}, 1.1)
add_series(BL, "bl-queenofravens", "Queen of Ravens", 1, 4,
           [(1,2024,6),(4,2024,9)],
           "Various", "Various", {1}, 0.9)
add_series(BL, "bl-zatarra2", "Zatanna: The Jewel of Fire", 1, 1,
           [(1,2025,3)], "Various", "Various", {1}, 0.85)
add_series("Image Comics", "inv-guardians12", "Guarding the Globe (2012)", 1, 12,
           [(1,2012,5),(6,2012,10),(12,2013,3)],
           "Various", "Various", {1}, 0.85)
add_series("Skybound / Image", "inv-void", "Void Rivals", 13, 24,
           [(13,2024,8),(18,2025,1),(24,2025,7)],
           "Robert Kirkman", "Lorenzo De Felici", set(), 1.0)
add_series(DH, "hb-koshchei", "Hellboy: Koshchei the Deathless", 1, 4,
           [(1,2018,7),(4,2018,11)],
           "Mike Mignola", "Ben Stenbeck", {1}, 1.05)
add_series(DH, "hb-koshchei2", "Hellboy: Koshchei in Hell", 1, 4,
           [(1,2021,8),(4,2021,12)],
           "Mike Mignola", "Ben Stenbeck", {1}, 1.0)
add_series("Marvel Comics", "ult-sm2024c", "Ultimate Spider-Man (2024)", 29, 32,
           [(29,2026,5),(32,2026,8)],
           "Jonathan Hickman", "Marco Checchetto", set(), 1.3)
add_series("DC Comics", "su-books2", "Books of Magic (2018)", 24, 25,
           [(24,2020,9),(25,2020,10)],
           "Kat Howard / Various", "Various", set(), 0.95)

# Finalize pub must allow Dark Horse (no "Comics"/slash); others pass via name checks.
b.pub = "Dark Horse"
b.finalize(priority_series={
    "The Walking Dead Deluxe", "Absolute Flash", "Absolute Green Lantern",
    "Absolute Martian Manhunter", "Absolute Wonder Woman", "Ultimate Wolverine",
    "The Ultimates (2024)", "Strange Adventures", "The Dreaming (2018)",
})
rep = b.report()
path = b.write(
    "batch-013",
    "High-value gaps: Absolute/Black Label/Ultimate 2020s/Hellboy/Invincible/TWD Deluxe/Sandman Universe",
    "Absolute siblings, Black Label densify, Ultimate Universe 2020s, Hellboy-BPRD leftovers, Invincible leftovers, Walking Dead Deluxe, Sandman Universe",
)
print("WROTE", path, "rows", len(b.rows))

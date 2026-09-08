#!/usr/bin/env python3
"""
batch-017: Marvel Dawn of X / recent majors + DC zeros + Image Energon/indie (floor 1980).

  Marvel: Unbeatable Squirrel Girl, Ms. Marvel (2019), Eternals (2021),
          Hellions, Children of the Atom, X-Corp, Betsy Braddock: Captain Britain,
          Cable (2020), Wolverine (2024), X-Force (2024) densify,
          Absolute Carnage / King in Black densify + Sword Masters
  DC: Batgirls, Justice League Incarnate, Dark Crisis on Infinite Earths,
      Absolute Power (2024), Outsiders (2023), New Gods (2024), The Penguin (2023),
      Dark Nights Metal/Death Metal adjacent densify
  Image: Minor Threats, Energon Universe Specials, Transformers/GI Joe/Void Rivals densify
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
    "DC Comics": "0476c2,0a0a0a,f8fafc",
    "Image Comics": "f97316,1c1917,fafaf9",
    "Skybound / Image Comics": "f97316,1c1917,fafaf9",
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

print("=== Marvel Dawn of X / street majors ===")
add_series("Marvel Comics", "mv-usg-2015", "The Unbeatable Squirrel Girl (2015)", 1, 50,
    [(1, 2015, 10), (12, 2016, 9), (25, 2017, 10), (38, 2018, 11), (50, 2019, 11)],
    "Ryan North", "Erica Henderson / Derek Charm / Various", {1, 50}, 0.75)
add_series("Marvel Comics", "mv-msm-2019", "Ms. Marvel (2019)", 1, 38,
    [(1, 2019, 5), (10, 2020, 2), (20, 2020, 12), (30, 2021, 10), (38, 2022, 4)],
    "Saladin Ahmed / Various", "Minkyu Jung / Various", {1}, 0.8)
add_series("Marvel Comics", "mv-eternals-2021", "Eternals (2021)", 1, 12,
    [(1, 2021, 1), (6, 2021, 6), (12, 2022, 1)],
    "Kieron Gillen", "Esad Ribic / Various", {1}, 0.85)
add_series("Marvel Comics", "mv-hellions-2020", "Hellions (2020)", 1, 18,
    [(1, 2020, 5), (6, 2020, 10), (12, 2021, 4), (18, 2021, 10)],
    "Zeb Wells", "Stephen Segovia / Various", {1}, 0.75)
add_series("Marvel Comics", "mv-cota-2021", "Children of the Atom (2021)", 1, 6,
    [(1, 2021, 5), (3, 2021, 7), (6, 2021, 10)],
    "Vita Ayala", "Bernard Chang / Various", {1}, 0.65)
add_series("Marvel Comics", "mv-xcorp-2021", "X-Corp (2021)", 1, 5,
    [(1, 2021, 7), (3, 2021, 9), (5, 2021, 11)],
    "Tini Howard", "Alberto Foche / Various", {1}, 0.65)
add_series("Marvel Comics", "mv-betsy-cb-2021", "Betsy Braddock: Captain Britain (2023)", 1, 5,
    [(1, 2023, 4), (3, 2023, 6), (5, 2023, 8)],
    "Tini Howard", "Ben Harvey / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-cable-2020", "Cable (2020)", 1, 12,
    [(1, 2020, 5), (4, 2020, 8), (8, 2020, 12), (12, 2021, 4)],
    "Gerry Duggan", "Phil Noto / Various", {1}, 0.75)
add_series("Marvel Comics", "mv-wolv-2024", "Wolverine (2024)", 1, 20,
    [(1, 2024, 9), (6, 2025, 2), (12, 2025, 8), (20, 2026, 4)],
    "Saladin Ahmed / Various", "Martin Coccolo / Various", {1}, 0.85)
add_series("Marvel Comics", "mv-xf-2024", "X-Force (2024)", 1, 18,
    [(1, 2024, 9), (6, 2025, 2), (12, 2025, 8), (18, 2026, 2)],
    "Geoffrey Thorne / Various", "Benjamin Dewey / Various", {1}, 0.75)
add_series("Marvel Comics", "mv-sword-masters-2020", "Sword Masters (2020)", 1, 5,
    [(1, 2020, 1), (3, 2020, 3), (5, 2020, 5)],
    "Murewa Ayodele / Various", "Dotun Akande / Various", {1}, 0.55)

print("=== Absolute Carnage / King in Black densify ===")
# Main minis already present; add key related one-shots / short runs as titled series densify
add_series("Marvel Comics", "mv-ac-am-2019", "Absolute Carnage: Avengers (2019)", 1, 3,
    [(1, 2019, 10), (2, 2019, 11), (3, 2019, 12)],
    "Cullen Bunn", "Ibrahim Moustafa / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-ac-immortal-2019", "Absolute Carnage: Immortal Hulk (2019)", 1, 1,
    [(1, 2019, 11)],
    "Al Ewing", "Ryan Ottley", {1}, 0.75)
add_series("Marvel Comics", "mv-ac-weapon-2019", "Absolute Carnage: Weapon Plus (2019)", 1, 1,
    [(1, 2019, 12)],
    "Donny Cates", "Ibrahem Sallam", {1}, 0.7)
add_series("Marvel Comics", "mv-kib-namor-2021", "King in Black: Namor (2021)", 1, 5,
    [(1, 2021, 2), (3, 2021, 4), (5, 2021, 6)],
    "Kurt Busiek", "Benjamin Dewey / Various", {1}, 0.65)
add_series("Marvel Comics", "mv-kib-blackknight-2021", "King in Black: Black Knight (2021)", 1, 1,
    [(1, 2021, 4)],
    "Simon Spurrier", "Sergio Davila", {1}, 0.6)
add_series("Marvel Comics", "mv-kib-ironman-2021", "King in Black: Iron Man / Doom (2021)", 1, 1,
    [(1, 2021, 3)],
    "Christopher Cantwell", "Angel Unzueta", {1}, 0.65)

print("=== DC zeros / events ===")
add_series("DC Comics", "dc-batgirls-2021", "Batgirls (2021)", 1, 19,
    [(1, 2021, 12), (6, 2022, 5), (12, 2022, 11), (19, 2023, 6)],
    "Becky Cloonan / Michael W. Conrad", "Jorge Corona / Various", {1}, 0.8)
add_series("DC Comics", "dc-jli-2021", "Justice League Incarnate (2021)", 1, 5,
    [(1, 2021, 12), (3, 2022, 2), (5, 2022, 4)],
    "Brian Michael Bendis / Joshua Williamson", "Andrei Bressan / Various", {1}, 0.85)
add_series("DC Comics", "dc-darkcrisis-2022", "Dark Crisis on Infinite Earths (2022)", 1, 7,
    [(1, 2022, 7), (3, 2022, 9), (5, 2022, 11), (7, 2023, 1)],
    "Joshua Williamson", "Daniel Sampere / Various", {1, 7}, 0.9)
add_series("DC Comics", "dc-abspow-2024", "Absolute Power (2024)", 1, 4,
    [(1, 2024, 7), (2, 2024, 8), (3, 2024, 9), (4, 2024, 10)],
    "Mark Waid", "Dan Mora / Various", {1}, 0.9)
add_series("DC Comics", "dc-outsiders-2023", "Outsiders (2023)", 1, 11,
    [(1, 2023, 11), (4, 2024, 2), (8, 2024, 6), (11, 2024, 9)],
    "Jackson Lanzing / Collin Kelly", "Robert Carey / Various", {1}, 0.7)
add_series("DC Comics", "dc-newgods-2024", "New Gods (2024)", 1, 6,
    [(1, 2024, 12), (3, 2025, 2), (6, 2025, 5)],
    "Ram V", "Evan Cagle / Various", {1}, 0.8)
add_series("DC Comics", "dc-penguin-2023", "The Penguin (2023)", 1, 12,
    [(1, 2023, 10), (4, 2024, 1), (8, 2024, 5), (12, 2024, 9)],
    "Tom King", "Rafael Albuquerque / Various", {1}, 0.85)
# Metal/Death Metal adjacent densify (mains mostly present)
add_series("DC Comics", "dc-darkdays-2017", "Dark Days: The Forge (2017)", 1, 1,
    [(1, 2017, 8)],
    "Scott Snyder / James Tynion IV", "Jim Lee / Various", {1}, 0.85)
add_series("DC Comics", "dc-darkdays-cast-2017", "Dark Days: The Casting (2017)", 1, 1,
    [(1, 2017, 9)],
    "Scott Snyder / James Tynion IV", "Jim Lee / Various", {1}, 0.85)
add_series("DC Comics", "dc-metal-reddeath-2017", "Batman: The Red Death (2017)", 1, 1,
    [(1, 2017, 11)],
    "Joshua Williamson", "Carmine Di Giandomenico", {1}, 0.8)
add_series("DC Comics", "dc-metal-murder-2017", "Batman: The Murder Machine (2017)", 1, 1,
    [(1, 2017, 11)],
    "James Tynion IV", "Ricardo Federici", {1}, 0.8)
add_series("DC Comics", "dc-metal-dawnbreaker-2017", "Batman: The Dawnbreaker (2017)", 1, 1,
    [(1, 2017, 12)],
    "Sam Johns", "Ivan Reis", {1}, 0.8)
add_series("DC Comics", "dc-metal-drowned-2017", "Batman: The Drowned (2017)", 1, 1,
    [(1, 2017, 12)],
    "Dan Abnett", "Philip Tan", {1}, 0.75)
add_series("DC Comics", "dc-metal-merciless-2017", "Batman: The Merciless (2017)", 1, 1,
    [(1, 2018, 1)],
    "Peter J. Tomasi", "Francis Manapul", {1}, 0.75)
add_series("DC Comics", "dc-metal-devastator-2017", "Batman: The Devastator (2017)", 1, 1,
    [(1, 2018, 1)],
    "Frank Tieri", "Tony S. Daniel", {1}, 0.75)
add_series("DC Comics", "dc-metal-who-laughs-2017", "The Batman Who Laughs (2018)", 1, 1,
    [(1, 2018, 1)],
    "James Tynion IV", "Riley Rossmo", {1}, 0.9)
add_series("DC Comics", "dc-dm-rise-2020", "Dark Nights: Death Metal - Rise of the New God (2020)", 1, 1,
    [(1, 2020, 11)],
    "James Tynion IV", "Juan Gedeon", {1}, 0.7)
add_series("DC Comics", "dc-dm-multiverse-2020", "Dark Nights: Death Metal - Multiverse's End (2020)", 1, 1,
    [(1, 2020, 10)],
    "James Tynion IV", "Juan Gedeon", {1}, 0.7)
add_series("DC Comics", "dc-dm-legion-2020", "Dark Nights: Death Metal - The Last 52: War of the Multiverses (2020)", 1, 1,
    [(1, 2021, 1)],
    "Various", "Various", {1}, 0.65)

print("=== Image / Energon / indie ===")
add_series("Image Comics", "im-minor-threats-2022", "Minor Threats (2022)", 1, 4,
    [(1, 2022, 9), (2, 2022, 10), (3, 2022, 11), (4, 2022, 12)],
    "Patton Oswalt / Jordan Blum", "Scott Hepburn", {1}, 0.85)
add_series("Image Comics", "im-minor-threats-ft-2023", "Minor Threats: The Fastest Kill in the West (2023)", 1, 1,
    [(1, 2023, 10)],
    "Patton Oswalt / Jordan Blum", "Scott Hepburn", {1}, 0.75)
add_series("Image Comics", "im-minor-threats-mw-2024", "Minor Threats: The Man with the Metal Face (2024)", 1, 1,
    [(1, 2024, 5)],
    "Patton Oswalt / Jordan Blum", "Scott Hepburn", {1}, 0.75)
add_series("Image Comics", "im-eu-special-2024", "Energon Universe Special (2024)", 1, 1,
    [(1, 2024, 5)],
    "Various", "Various", {1}, 0.8)
add_series("Image Comics", "im-eu-special-2025", "Energon Universe 2025 Special (2025)", 1, 1,
    [(1, 2025, 5)],
    "Various", "Various", {1}, 0.75)
# densify ongoing Energon titles beyond current archive tip
add_series("Image Comics", "im-tf-sky-2023", "Transformers (Skybound)", 37, 48,
    [(37, 2025, 9), (42, 2026, 2), (48, 2026, 8)],
    "Daniel Warren Johnson / Various", "Jorge Corona / Various", set(), 0.85,
    also_block_bare="Transformers (Skybound)")
add_series("Image Comics", "im-gij-sky-2024", "G.I. Joe (Skybound)", 25, 36,
    [(25, 2025, 9), (30, 2026, 2), (36, 2026, 8)],
    "Joshua Williamson / Various", "Andrea Milana / Various", set(), 0.8)
add_series("Image Comics", "im-vr-2023", "Void Rivals", 25, 32,
    [(25, 2025, 9), (28, 2026, 1), (32, 2026, 5)],
    "Robert Kirkman / Various", "Lorenzo De Felici / Various", set(), 0.8)


print("=== Extra Marvel Dawn of X zeros ===")
add_series("Marvel Comics", "mv-legionx-2022", "Legion of X (2022)", 1, 10,
    [(1, 2022, 7), (5, 2022, 11), (10, 2023, 4)],
    "Si Spurrier", "Jan Bazaldua / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-knightsx-2022", "Knights of X (2022)", 1, 5,
    [(1, 2022, 6), (3, 2022, 8), (5, 2022, 10)],
    "Tini Howard", "Bob Quinn / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-xmenred-2022", "X-Men Red (2022)", 1, 18,
    [(1, 2022, 6), (6, 2022, 11), (12, 2023, 5), (18, 2023, 11)],
    "Al Ewing", "Stefano Caselli / Various", {1}, 0.8)
add_series("Marvel Comics", "mv-sabretooth-2022", "Sabretooth (2022)", 1, 5,
    [(1, 2022, 6), (3, 2022, 8), (5, 2022, 10)],
    "Victor LaValle", "Leonard Kirk / Various", {1}, 0.75)
add_series("Marvel Comics", "mv-marauders-2022", "Marauders (2022)", 1, 12,
    [(1, 2022, 6), (6, 2022, 11), (12, 2023, 5)],
    "Steve Orlando", "Eleonora Carlini / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-trial-magneto-2021", "Trial of Magneto (2021)", 1, 5,
    [(1, 2021, 10), (3, 2021, 12), (5, 2022, 2)],
    "Leah Williams", "Lucas Werneck / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-sword-2020", "S.W.O.R.D. (2020)", 1, 11,
    [(1, 2020, 12), (4, 2021, 3), (8, 2021, 7), (11, 2021, 10)],
    "Al Ewing", "Valerio Schiti / Various", {1}, 0.75)
add_series("Marvel Comics", "mv-wayofx-2021", "Way of X (2021)", 1, 5,
    [(1, 2021, 6), (3, 2021, 8), (5, 2021, 10)],
    "Si Spurrier", "Bob Quinn / Various", {1}, 0.7)
add_series("Marvel Comics", "mv-inferno-2021", "Inferno (2021)", 1, 4,
    [(1, 2021, 11), (2, 2021, 12), (3, 2022, 1), (4, 2022, 2)],
    "Jonathan Hickman", "Valerio Schiti / Various", {1}, 0.85)

print("=== Extra DC zeros ===")
add_series("DC Comics", "dc-titans-2023", "Titans (2023)", 1, 16,
    [(1, 2023, 7), (6, 2023, 12), (12, 2024, 6), (16, 2024, 10)],
    "Tom Taylor / Various", "Nicola Scott / Various", {1}, 0.8)
add_series("DC Comics", "dc-powergirl-2023", "Power Girl (2023)", 1, 12,
    [(1, 2023, 9), (4, 2023, 12), (8, 2024, 4), (12, 2024, 8)],
    "Leah Williams", "Eduardo Pansica / Various", {1}, 0.7)
add_series("DC Comics", "dc-bluebeetle-2023", "Blue Beetle (2023)", 1, 8,
    [(1, 2023, 11), (4, 2024, 2), (8, 2024, 6)],
    "Josh Trujillo", "Adriana Melo / Various", {1}, 0.65)
add_series("DC Comics", "dc-shazam-2023", "Shazam! (2023)", 1, 12,
    [(1, 2023, 5), (4, 2023, 8), (8, 2023, 12), (12, 2024, 4)],
    "Mark Waid / Various", "Dan Mora / Various", {1}, 0.75)
add_series("DC Comics", "dc-nw-2016-cont", "Nightwing (2016)", 119, 140,
    [(119, 2024, 6), (128, 2025, 3), (140, 2026, 3)],
    "Tom Taylor / Various", "Bruno Redondo / Various", set(), 0.8,
    also_block_bare="Nightwing")

print("=== Extra Image zeros ===")
add_series("Image Comics", "im-nicehouse-2021", "The Nice House on the Lake (2021)", 1, 12,
    [(1, 2021, 12), (4, 2022, 3), (8, 2022, 7), (12, 2022, 11)],
    "James Tynion IV", "Alvaro Martinez Bueno", {1}, 0.9)
add_series("Image Comics", "im-nicehouse2-2024", "The Nice House by the Sea (2024)", 1, 6,
    [(1, 2024, 8), (3, 2024, 10), (6, 2025, 1)],
    "James Tynion IV", "Alvaro Martinez Bueno", {1}, 0.85)

# Cap ~400–500
b.pub = "Marvel Comics"
b.target_min = 400
b.target_max = 500
b.finalize(priority_series={
    "The Unbeatable Squirrel Girl (2015)", "Ms. Marvel (2019)", "Eternals (2021)",
    "Hellions (2020)", "Children of the Atom (2021)", "X-Corp (2021)",
    "Betsy Braddock: Captain Britain (2023)", "Cable (2020)",
    "Wolverine (2024)", "X-Force (2024)",
    "X-Men Red (2022)", "S.W.O.R.D. (2020)", "Legion of X (2022)", "Inferno (2021)",
    "Batgirls (2021)", "Dark Crisis on Infinite Earths (2022)", "Absolute Power (2024)",
    "Outsiders (2023)", "The Penguin (2023)", "Justice League Incarnate (2021)",
    "Titans (2023)", "Nightwing (2016)",
    "Minor Threats (2022)", "New Gods (2024)", "The Nice House on the Lake (2021)",
})
rep = b.report()
path = b.write(
    "batch-017",
    "Marvel Dawn of X / DC zeros / Image Energon densify",
    "Squirrel Girl/Ms Marvel 2019/Eternals/Hellions/CoTA/X-Corp/Betsy/Cable/Wolverine 2024/X-Force densify; Batgirls/Dark Crisis/Absolute Power/Outsiders/Penguin/New Gods/JL Incarnate; Minor Threats + Energon densify",
    created="2026-09-08",
)
print("WROTE", path, "rows", len(b.rows))

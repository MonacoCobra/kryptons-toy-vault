#!/usr/bin/env python3
"""Generate bbts_wave7_data.json — BBTS AF brand expansion wave 7."""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).with_name("bbts_wave7_data.json")

def R(suf, name, sub, date, demand, msrp=None):
    row = [suf, name, sub, date, float(demand)]
    if msrp is not None:
        row.append(float(msrp))
    return row

def dates(y, m, n, step=1):
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}-01")
        m += step
        while m > 12:
            m -= 12
            y += 1
    return out

def add(data, key, prefix, items, y, m, step, default_msrp):
    ds = dates(y, m, len(items), step)
    rows = []
    for i, it in enumerate(items):
        if len(it) == 4:
            name, sub, demand, msrp = it
        else:
            name, sub, demand = it
            msrp = default_msrp
        rows.append(R(f"{prefix}-{i+1:02d}", name, sub, max(ds[i], "1980-01-01"), demand, msrp))
    data[key] = rows

data: dict[str, list] = {}

# ========== NEW (12) ==========
add(data, "generationtoy", "gt", [
    ("Gravity Builder", "Combiner", 1.45, 180), ("Giant", "Gravity Builder limb", 1.3, 55),
    ("Crusher", "Gravity Builder limb", 1.25, 55), ("Tanker", "Gravity Builder limb", 1.25, 55),
    ("Excavator", "Gravity Builder limb", 1.25, 55), ("Mixer", "Gravity Builder limb", 1.2, 55),
    ("Truck", "Gravity Builder limb", 1.2, 55), ("Gravity Destroyer", "Special", 1.5, 200),
    ("Sea King", "Combiner", 1.4, 170), ("Sea King A", "Sea King limb", 1.2, 50),
    ("Sea King B", "Sea King limb", 1.2, 50), ("Sea King C", "Sea King limb", 1.2, 50),
    ("Sea King D", "Sea King limb", 1.2, 50), ("Sea King E", "Sea King limb", 1.15, 50),
    ("Sea King F", "Sea King limb", 1.15, 50), ("Monster King", "Combiner", 1.45, 185),
    ("Monster A", "Monster King limb", 1.25, 55), ("Monster B", "Monster King limb", 1.25, 55),
    ("Monster C", "Monster King limb", 1.2, 55), ("Monster D", "Monster King limb", 1.2, 55),
    ("Monster E", "Monster King limb", 1.2, 55), ("Guardian", "Solo", 1.35, 90),
    ("Guardian Black", "Special", 1.4, 95), ("Guardian Clear", "Special", 1.35, 100),
    ("Air Robot", "Solo", 1.3, 85), ("Air Robot Spec Ops", "Special", 1.35, 90),
    ("Tank Engine", "Solo", 1.3, 80), ("Trainbot Leader", "Solo", 1.35, 95),
    ("Trainbot A", "Train set", 1.2, 60), ("Trainbot B", "Train set", 1.2, 60),
    ("Trainbot C", "Train set", 1.15, 60), ("Trainbot D", "Train set", 1.15, 60),
    ("Trainbot E", "Train set", 1.15, 60), ("Gravity Builder Metallic", "Special", 1.5, 220),
    ("Gravity Builder Desert", "Special", 1.45, 190), ("City Commander", "Solo", 1.3, 88),
    ("City Defender", "Solo", 1.25, 82), ("City Scout", "Solo", 1.2, 75),
    ("Sea King Metallic", "Special", 1.45, 190), ("Monster King Metallic", "Special", 1.45, 200),
    ("Gravity Builder Mini", "Mini", 1.2, 40), ("Guardian Mini", "Mini", 1.15, 35),
    ("Air Robot Mini", "Mini", 1.15, 35), ("Combiner Upgrade Pack", "Special", 1.25, 45),
    ("Gravity Builder Ghost", "Special", 1.4, 195),
], 2016, 3, 2, 90)

add(data, "zeta", "zt", [
    ("ZA-01 Blitzwing", "ZA Series", 1.5, 160), ("ZA-02 Astrotrain", "ZA Series", 1.45, 150),
    ("ZA-03 Octane", "ZA Series", 1.35, 120), ("ZA-04 Hotlink", "ZA Series", 1.3, 110),
    ("ZA-05 Bitstream", "ZA Series", 1.3, 110), ("ZA-06 Scramble", "ZA Series", 1.25, 100),
    ("ZA-07 Reflector", "ZA Series", 1.4, 140), ("ZA-08 Spectro", "ZA Series", 1.25, 55),
    ("ZA-09 Spyglass", "ZA Series", 1.25, 55), ("ZA-10 Viewfinder", "ZA Series", 1.25, 55),
    ("ZB-01 Optimus", "ZB Series", 1.55, 180), ("ZB-02 Megatron", "ZB Series", 1.55, 180),
    ("ZB-03 Starscream", "ZB Series", 1.45, 150), ("ZB-04 Soundwave", "ZB Series", 1.5, 160),
    ("ZB-05 Shockwave", "ZB Series", 1.45, 155), ("ZB-06 Jazz", "ZB Series", 1.35, 130),
    ("ZB-07 Prowl", "ZB Series", 1.35, 130), ("ZB-08 Ironhide", "ZB Series", 1.35, 135),
    ("ZB-09 Ratchet", "ZB Series", 1.3, 125), ("ZB-10 Bumblebee", "ZB Series", 1.4, 120),
    ("ZC-01 Superion A", "Combiner", 1.35, 90), ("ZC-02 Superion B", "Combiner", 1.3, 85),
    ("ZC-03 Superion C", "Combiner", 1.3, 85), ("ZC-04 Superion D", "Combiner", 1.3, 85),
    ("ZC-05 Superion E", "Combiner", 1.3, 85), ("ZC-06 Superion Complete", "Combiner", 1.55, 380),
    ("ZD-01 Menasor A", "Combiner", 1.35, 90), ("ZD-02 Menasor B", "Combiner", 1.3, 85),
    ("ZD-03 Menasor C", "Combiner", 1.3, 85), ("ZD-04 Menasor D", "Combiner", 1.3, 85),
    ("ZD-05 Menasor E", "Combiner", 1.3, 85), ("ZD-06 Menasor Complete", "Combiner", 1.55, 380),
    ("ZE-01 Grimlock", "ZE Series", 1.5, 170), ("ZE-02 Slag", "ZE Series", 1.3, 100),
    ("ZE-03 Snarl", "ZE Series", 1.3, 100), ("ZE-04 Sludge", "ZE Series", 1.25, 95),
    ("ZE-05 Swoop", "ZE Series", 1.3, 100), ("ZS Blitzwing Black", "Special", 1.5, 175),
    ("ZS Optimus Chrome", "Special", 1.55, 200), ("ZS Megatron Chrome", "Special", 1.55, 200),
    ("ZS Starscream Ghost", "Special", 1.45, 165), ("ZS Soundwave Blue", "Special", 1.45, 170),
    ("ZM Mini Optimus", "Mini", 1.25, 45), ("ZM Mini Megatron", "Mini", 1.25, 45),
    ("ZM Mini Starscream", "Mini", 1.2, 40),
], 2017, 1, 2, 120)

# Mech Fans / ToyWolf / Evolution — patterned series
for key, prefix, y, brand in [
    ("mechfans", "mf", 2018, "MF"),
    ("toywolf", "tw", 2017, "W"),
    ("evolutiontoy", "et", 2016, "ET"),
]:
    items = []
    solos = ["Commander", "Warrior", "Scout", "Medic", "Heavy", "Flyer", "Seeker Red",
             "Seeker Blue", "Seeker Purple", "Cassette Cat", "Cassette Bird", "Cassette Dog",
             "Dinobot King", "Dinobot A", "Dinobot B", "Dinobot C", "Dinobot D", "City Bot",
             "Triple Changer", "Insecticon A", "Insecticon B", "Insecticon C"]
    for i, n in enumerate(solos):
        items.append((f"{brand}-{i+1:02d} {n}", "Series", 1.25 + (i % 6) * 0.04, 70 + (i % 8) * 5))
    for limb in ["A", "B", "C", "D", "E"]:
        items.append((f"{brand} Combiner {limb}", "Combiner", 1.25, 80))
    items.append((f"{brand} Combiner Complete", "Combiner", 1.5, 350))
    for n, sub, d, p in [
        (f"{brand} Commander Chrome", "Special", 1.45, 120),
        (f"{brand} Warrior Desert", "Special", 1.3, 90),
        (f"{brand} Scout Night", "Special", 1.25, 80),
        (f"{brand} Dinobot King Metallic", "Special", 1.5, 160),
        (f"{brand} City Bot Black", "Special", 1.35, 110),
        (f"{brand} Triple Changer Ghost", "Special", 1.4, 140),
        (f"{brand} Mini Commander", "Mini", 1.2, 40),
        (f"{brand} Mini Warrior", "Mini", 1.15, 38),
        (f"{brand} Mini Flyer", "Mini", 1.15, 38),
        (f"{brand} Cassette Pack", "Special", 1.3, 55),
        (f"{brand} Combiner Upgrade", "Special", 1.25, 45),
        (f"{brand} Flyer Spec Ops", "Special", 1.3, 95),
    ]:
        items.append((n, sub, d, p))
    add(data, key, prefix, items, y, 2, 2, 90)

# Star Ace
add(data, "starace", "sa", [
    ("Harry Potter", "Sorcerer's Stone", 1.4), ("Harry Potter", "Prisoner of Azkaban", 1.45),
    ("Harry Potter", "Goblet of Fire", 1.4), ("Harry Potter", "Order of the Phoenix", 1.4),
    ("Hermione Granger", "Sorcerer's Stone", 1.4), ("Hermione Granger", "Prisoner of Azkaban", 1.4),
    ("Ron Weasley", "Sorcerer's Stone", 1.35), ("Ron Weasley", "Prisoner of Azkaban", 1.35),
    ("Albus Dumbledore", "Half-Blood Prince", 1.5), ("Severus Snape", "Deathly Hallows", 1.5),
    ("Lord Voldemort", "Deathly Hallows", 1.55), ("Bellatrix Lestrange", "Deathly Hallows", 1.45),
    ("Draco Malfoy", "Half-Blood Prince", 1.35), ("Rubeus Hagrid", "Sorcerer's Stone", 1.4),
    ("Minerva McGonagall", "Order of the Phoenix", 1.35), ("Sirius Black", "Prisoner of Azkaban", 1.45),
    ("Remus Lupin", "Prisoner of Azkaban", 1.4), ("James Dean", "Rebel Without a Cause", 1.4),
    ("James Dean", "Giant", 1.35), ("Bruce Lee", "Enter the Dragon", 1.55),
    ("Bruce Lee", "Game of Death", 1.5), ("Bruce Lee", "Fist of Fury", 1.45),
    ("Clint Eastwood", "Dirty Harry", 1.5), ("Clint Eastwood", "The Good the Bad and the Ugly", 1.5),
    ("Rocky Balboa", "Rocky", 1.45), ("Apollo Creed", "Rocky", 1.4), ("Ivan Drago", "Rocky IV", 1.45),
    ("Frankenstein", "Universal Monsters", 1.4), ("Dracula", "Universal Monsters", 1.4),
    ("Wolf Man", "Universal Monsters", 1.35), ("Mummy", "Universal Monsters", 1.35),
    ("Creature from the Black Lagoon", "Universal Monsters", 1.4), ("Invisible Man", "Universal Monsters", 1.35),
    ("Godzilla", "1954", 1.5), ("King Kong", "1933", 1.45),
    ("Ray Harryhausen Skeleton", "Jason and the Argonauts", 1.4), ("Talos", "Jason and the Argonauts", 1.4),
    ("Medusa", "Clash of the Titans", 1.4), ("Wonder Woman", "1984", 1.4),
    ("Steve Trevor", "Wonder Woman", 1.3), ("Harry Potter Quidditch", "Prisoner of Azkaban", 1.45),
    ("Dobby", "Chamber of Secrets", 1.35), ("Dementor", "Prisoner of Azkaban", 1.4),
    ("Death Eater", "Order of the Phoenix", 1.3), ("Elvis Presley", "Aloha from Hawaii", 1.4),
], 2015, 3, 2, 280)

# EXO-6
add(data, "exo6", "exo", [
    ("Kirk", "TOS", 1.5), ("Spock", "TOS", 1.55), ("McCoy", "TOS", 1.4), ("Scotty", "TOS", 1.4),
    ("Uhura", "TOS", 1.4), ("Sulu", "TOS", 1.35), ("Chekov", "TOS", 1.35), ("Chapel", "TOS", 1.3),
    ("Rand", "TOS", 1.25), ("Khan", "Space Seed", 1.5), ("Kor", "Errand of Mercy", 1.35),
    ("Kang", "Day of the Dove", 1.35), ("Koloth", "Trouble with Tribbles", 1.3),
    ("Gorn Captain", "Arena", 1.4), ("Andorian", "TOS", 1.3), ("Picard", "TNG", 1.55),
    ("Riker", "TNG", 1.45), ("Data", "TNG", 1.5), ("Worf", "TNG", 1.45), ("Troi", "TNG", 1.35),
    ("Crusher", "TNG", 1.35), ("La Forge", "TNG", 1.4), ("Yar", "TNG", 1.3), ("Q", "TNG", 1.5),
    ("Locutus", "Best of Both Worlds", 1.55), ("Borg Drone", "TNG", 1.4), ("Sisko", "DS9", 1.45),
    ("Kira", "DS9", 1.4), ("Odo", "DS9", 1.4), ("Dax", "DS9", 1.35), ("O'Brien", "DS9", 1.35),
    ("Bashir", "DS9", 1.3), ("Quark", "DS9", 1.35), ("Garak", "DS9", 1.4), ("Dukat", "DS9", 1.4),
    ("Janeway", "Voyager", 1.45), ("Chakotay", "Voyager", 1.35), ("Seven of Nine", "Voyager", 1.5),
    ("Tuvok", "Voyager", 1.35), ("Archer", "Enterprise", 1.35), ("T'Pol", "Enterprise", 1.4),
], 2021, 1, 1, 245)

# Blitzway
add(data, "blitzway", "bw", [
    ("Michael Jackson", "Thriller", 1.55), ("Michael Jackson", "Smooth Criminal", 1.5),
    ("Michael Jackson", "Billie Jean", 1.5), ("Michael Jackson", "Bad", 1.45),
    ("Bruce Lee", "Enter the Dragon", 1.55), ("Bruce Lee", "Way of the Dragon", 1.5),
    ("Bruce Lee", "Fist of Fury", 1.45), ("Chaplin", "The Tramp", 1.4),
    ("Chaplin", "Modern Times", 1.4), ("Chaplin", "City Lights", 1.35),
    ("Superb Scale Joker", "1989 Batman", 1.55), ("Superb Scale Batman", "1989 Batman", 1.55),
    ("Superb Scale Penguin", "Batman Returns", 1.45), ("Superb Scale Catwoman", "Batman Returns", 1.5),
    ("Superb Scale Joker", "1989 Deluxe", 1.6), ("Superb Scale Batman", "1989 Deluxe", 1.6),
    ("Ghostbusters Venkman", "1984", 1.45), ("Ghostbusters Spengler", "1984", 1.45),
    ("Ghostbusters Stantz", "1984", 1.45), ("Ghostbusters Zeddemore", "1984", 1.4),
    ("Ghostbusters Stay Puft", "Deluxe", 1.5), ("Mars Attacks Martian", "Standard", 1.4),
    ("Mars Attacks Martian", "Ambassador", 1.4), ("Mars Attacks Soldier", "Invasion", 1.3),
    ("Ultraman", "Type A", 1.45), ("Ultraman", "Type B", 1.4), ("Ultraman", "Type C", 1.4),
    ("Ultraseven", "Ultraman", 1.4), ("Ultraman Ace", "Ultraman", 1.35),
    ("Zetton", "Ultraman", 1.35), ("Alien Baltan", "Ultraman", 1.35),
    ("Carbotix Getter 1", "Getter Robo", 1.5), ("Carbotix Getter 2", "Getter Robo", 1.4),
    ("Carbotix Getter 3", "Getter Robo", 1.4), ("Carbotix Shin Getter", "Getter Robo", 1.55),
    ("Figure Complex Mazinger Z", "Mazinger", 1.45), ("Figure Complex Great Mazinger", "Mazinger", 1.4),
    ("Figure Complex Aphrodite A", "Mazinger", 1.3), ("Figure Complex Boss Borot", "Mazinger", 1.25),
    ("Superb Scale Joker", "Mime", 1.5),
], 2018, 4, 2, 320)

# Toynami
add(data, "toynami", "tn", [
    ("Rick Hunter", "Veritech Pilot", 1.4, 28), ("Lisa Hayes", "SDF-1 Bridge", 1.35, 28),
    ("Max Sterling", "Veritech Pilot", 1.4, 28), ("Miriya Sterling", "Quadrono Pilot", 1.4, 28),
    ("Roy Fokker", "Skull Squadron", 1.45, 28), ("Claudia Grant", "SDF-1 Bridge", 1.3, 28),
    ("Lynn Minmei", "Civilian", 1.35, 28), ("Breetai", "Zentraedi", 1.4, 28),
    ("Exedore", "Zentraedi", 1.3, 28), ("Khyron", "Zentraedi", 1.4, 28),
    ("Azonia", "Zentraedi", 1.35, 28), ("VF-1J Rick", "Robotech VF", 1.5, 55),
    ("VF-1S Roy", "Robotech VF", 1.5, 55), ("VF-1A Max", "Robotech VF", 1.45, 55),
    ("VF-1A Hikaru", "Macross VF", 1.5, 55), ("VF-1S Roy Focker", "Macross VF", 1.5, 55),
    ("VF-1J Max", "Macross VF", 1.45, 55), ("VF-1A Kakizaki", "Macross VF", 1.35, 55),
    ("Destroid Tomahawk", "Robotech", 1.35, 55), ("Destroid Defender", "Robotech", 1.3, 55),
    ("Destroid Spartan", "Robotech", 1.3, 55), ("Destroid Phalanx", "Robotech", 1.25, 55),
    ("Destroid Monster", "Robotech", 1.4, 55), ("Battlepod Regult", "Zentraedi", 1.35, 45),
    ("Officer's Pod Glaug", "Zentraedi", 1.4, 50), ("Queadluun-Rau", "Zentraedi", 1.45, 55),
    ("Scott Bernard", "New Generation", 1.35, 28), ("Rook Bartley", "New Generation", 1.3, 28),
    ("Rand", "New Generation", 1.25, 28), ("Annie LaBelle", "New Generation", 1.2, 28),
    ("Lancer", "New Generation", 1.3, 28), ("Marlene", "New Generation", 1.25, 28),
    ("VF-1J Super Valkyrie", "Macross VF", 1.55, 65), ("VF-1S Strike Valkyrie", "Macross VF", 1.55, 65),
    ("VF-1A GBP Armor", "Macross VF", 1.5, 60), ("VF-1D Trainer", "Macross VF", 1.35, 55),
    ("VF-1A Low Viz", "Special", 1.4, 60), ("VF-1J Stealth", "Special", 1.4, 60),
    ("Rick Hunter Dress", "Special", 1.3, 30), ("Max Sterling Wedding", "Special", 1.35, 30),
    ("Miriya Wedding", "Special", 1.35, 30), ("Breetai Micronized", "Special", 1.3, 30),
    ("Khyron Throne", "Special", 1.35, 35), ("VF-1J Clear", "Special", 1.4, 65),
    ("SDF-1 Bridge Set", "Display AF", 1.3, 40),
], 2005, 6, 3, 40)

# Creative Beast
dinos = [
    ("Tyrannosaurus rex", "Tyrannosaur Series", 1.55), ("Daspletosaurus", "Tyrannosaur Series", 1.4),
    ("Gorgosaurus", "Tyrannosaur Series", 1.4), ("Albertosaurus", "Tyrannosaur Series", 1.35),
    ("Tarbosaurus", "Tyrannosaur Series", 1.35), ("Alioramus", "Tyrannosaur Series", 1.3),
    ("Qianzhousaurus", "Tyrannosaur Series", 1.3), ("Dryptosaurus", "Tyrannosaur Series", 1.25),
    ("Velociraptor mongoliensis", "Raptor Series", 1.5), ("Velociraptor osmolskae", "Raptor Series", 1.4),
    ("Deinonychus", "Raptor Series", 1.5), ("Utahraptor", "Raptor Series", 1.45),
    ("Achillobator", "Raptor Series", 1.35), ("Dromaeosaurus", "Raptor Series", 1.3),
    ("Atrociraptor", "Raptor Series", 1.35), ("Pyroraptor", "Raptor Series", 1.35),
    ("Bambiraptor", "Raptor Series", 1.25), ("Saurornitholestes", "Raptor Series", 1.25),
    ("Ceratosaurus", "Theropod", 1.35), ("Carnotaurus", "Theropod", 1.4),
    ("Allosaurus", "Theropod", 1.4), ("Spinosaurus", "Theropod", 1.5),
    ("Baryonyx", "Theropod", 1.35), ("Suchomimus", "Theropod", 1.3),
    ("Dilophosaurus", "Theropod", 1.4), ("Triceratops", "Ceratopsian Series", 1.45),
    ("Styracosaurus", "Ceratopsian Series", 1.35), ("Pachyrhinosaurus", "Ceratopsian Series", 1.35),
    ("Einiosaurus", "Ceratopsian Series", 1.3), ("Nasutoceratops", "Ceratopsian Series", 1.3),
    ("Medusaceratops", "Ceratopsian Series", 1.25), ("Diabloceratops", "Ceratopsian Series", 1.3),
    ("Kosmoceratops", "Ceratopsian Series", 1.3), ("Pentaceratops", "Ceratopsian Series", 1.3),
    ("Centrosaurus", "Ceratopsian Series", 1.25), ("Chasmosaurus", "Ceratopsian Series", 1.25),
    ("Stegosaurus", "Thyreophoran", 1.4), ("Ankylosaurus", "Thyreophoran", 1.4),
    ("Nodosaurus", "Thyreophoran", 1.25), ("Kentrosaurus", "Thyreophoran", 1.3),
    ("Parasaurolophus", "Hadrosaur", 1.35), ("Corythosaurus", "Hadrosaur", 1.3),
    ("Edmontosaurus", "Hadrosaur", 1.3), ("Lambeosaurus", "Hadrosaur", 1.25),
    ("Iguanodon", "Ornithopod", 1.3), ("Dryosaurus", "Ornithopod", 1.2),
    ("Gallimimus", "Ornithomimid", 1.3), ("Struthiomimus", "Ornithomimid", 1.25),
    ("Oviraptor", "Oviraptorosaur", 1.35), ("Citipati", "Oviraptorosaur", 1.3),
]
add(data, "creativebeast", "cb", dinos, 2018, 1, 1, 55)

# Alert Line
al = [
    ("WWII German Sniper", "Elite Series", 1.35), ("WWII German Panzer Crew", "Elite Series", 1.3),
    ("WWII German Infantry", "Elite Series", 1.3), ("WWII US Ranger", "Elite Series", 1.4),
    ("WWII US Airborne", "Elite Series", 1.4), ("WWII US Marine", "Pacific", 1.4),
    ("WWII US Navy Corpsman", "Pacific", 1.35), ("WWII Soviet Infantry", "Eastern Front", 1.35),
    ("WWII Soviet Sniper", "Eastern Front", 1.4), ("WWII British SAS", "Elite Series", 1.4),
    ("WWII British Commando", "Elite Series", 1.35), ("WWII Japanese Infantry", "Pacific", 1.3),
    ("WWII Japanese Officer", "Pacific", 1.3), ("Vietnam US MACV-SOG", "Modern", 1.45),
    ("Vietnam US Marine", "Modern", 1.4), ("Vietnam NVA Regular", "Modern", 1.3),
    ("Vietnam VC Guerrilla", "Modern", 1.3), ("Modern US Delta", "Modern", 1.45),
    ("Modern US SEAL", "Modern", 1.45), ("Modern US Ranger", "Modern", 1.4),
    ("Modern Russian Spetsnaz", "Modern", 1.4), ("Modern British SAS", "Modern", 1.4),
    ("Modern German KSK", "Modern", 1.35), ("WWII German Fallschirmjager", "Elite Series", 1.4),
    ("WWII German Waffen-SS", "Elite Series", 1.35), ("WWII US Tank Crew", "Elite Series", 1.3),
    ("WWII Soviet Tank Crew", "Eastern Front", 1.3), ("WWII British Para", "Elite Series", 1.35),
    ("WWII French Resistance", "Elite Series", 1.25), ("Modern PMC Operator", "Modern", 1.35),
    ("Modern SWAT Breacher", "Modern", 1.3), ("Modern FBI HRT", "Modern", 1.35),
    ("WWII Nurse", "Support", 1.25), ("WWII Medic US", "Support", 1.3),
    ("WWII German Medic", "Support", 1.25), ("Vietnam Tunnel Rat", "Modern", 1.35),
    ("Modern US Marine Force Recon", "Modern", 1.4), ("Modern Israeli Shayetet", "Modern", 1.35),
    ("WWII German Afrika Korps", "Desert", 1.35), ("WWII British Desert Rat", "Desert", 1.35),
]
add(data, "alertline", "al", al, 2016, 5, 2, 165)

# Snail Shell
ss = [
    ("Bunny Girl Frontline", "Original", 1.4), ("Bunny Girl Frontline Black", "Original", 1.4),
    ("Assassin", "Original", 1.35), ("Assassin White", "Original", 1.35),
    ("Tactical Girl A", "Original", 1.3), ("Tactical Girl B", "Original", 1.3),
    ("Tactical Girl C", "Original", 1.25), ("Cyber Nurse", "Original", 1.35),
    ("Cyber Nurse Black", "Original", 1.35), ("Maid Armor", "Original", 1.4),
    ("Maid Armor Black", "Original", 1.4), ("Knight Armor", "Original", 1.35),
    ("Knight Armor Crimson", "Original", 1.35), ("School Combat A", "Original", 1.3),
    ("School Combat B", "Original", 1.3), ("Idol Combat", "Original", 1.35),
    ("Idol Combat Stage", "Special", 1.4), ("Ninja Girl", "Original", 1.35),
    ("Ninja Girl Shadow", "Special", 1.4), ("Mecha Pilot A", "Original", 1.3),
    ("Mecha Pilot B", "Original", 1.3), ("Mecha Pilot C", "Original", 1.25),
    ("Body Suit White", "Original", 1.25), ("Body Suit Black", "Original", 1.25),
    ("Body Suit Red", "Original", 1.25), ("Swim Combat", "Original", 1.3),
    ("Winter Tactical", "Original", 1.3), ("Desert Tactical", "Original", 1.3),
    ("Urban Tactical", "Original", 1.3), ("Bunny Girl Deluxe", "Special", 1.45),
    ("Assassin Deluxe", "Special", 1.4), ("Maid Armor Deluxe", "Special", 1.45),
    ("Knight Deluxe", "Special", 1.4), ("Ninja Deluxe", "Special", 1.4),
    ("Cyber Nurse Deluxe", "Special", 1.4), ("Tactical Clear", "Special", 1.3),
    ("Mecha Pilot Clear", "Special", 1.3), ("Body Suit Clear", "Special", 1.25),
    ("Limited Anniversary", "Special", 1.5), ("Limited Winter Festival", "Special", 1.45),
]
add(data, "snailshell", "ss", ss, 2020, 3, 1, 68)

# ========== DENSIFY ==========
add(data, "bandai", "bn7", [
    ("RX-78-2 Gundam", "Robot Spirits ver. A.N.I.M.E.", 1.45, 65),
    ("MS-06S Zaku II", "Robot Spirits ver. A.N.I.M.E.", 1.4, 65),
    ("MS-07B Gouf", "Robot Spirits ver. A.N.I.M.E.", 1.35, 60),
    ("MS-09 Dom", "Robot Spirits ver. A.N.I.M.E.", 1.3, 60),
    ("RX-77 Guncannon", "Robot Spirits ver. A.N.I.M.E.", 1.3, 60),
    ("RX-75 Guntank", "Robot Spirits ver. A.N.I.M.E.", 1.2, 55),
    ("RGM-79 GM", "Robot Spirits ver. A.N.I.M.E.", 1.25, 55),
    ("MSM-07 Z'Gok", "Robot Spirits ver. A.N.I.M.E.", 1.3, 60),
    ("MS-14A Gelgoog", "Robot Spirits ver. A.N.I.M.E.", 1.35, 65),
    ("MSN-02 Zeong", "Robot Spirits ver. A.N.I.M.E.", 1.4, 75),
    ("RX-78GP01 Zephyranthes", "Robot Spirits", 1.4, 70),
    ("RX-78GP01Fb Full Burnern", "Robot Spirits", 1.45, 75),
    ("RX-78GP02A Physalis", "Robot Spirits", 1.4, 70),
    ("MSZ-006 Zeta Gundam", "Robot Spirits", 1.5, 75),
    ("MSN-00100 Hyaku Shiki", "Robot Spirits", 1.4, 70),
    ("RX-178 Gundam Mk-II Titans", "Robot Spirits", 1.4, 70),
    ("RX-178 Gundam Mk-II AEUG", "Robot Spirits", 1.4, 70),
    ("RX-93 Nu Gundam", "Robot Spirits", 1.55, 80),
    ("MSN-04 Sazabi", "Robot Spirits", 1.5, 80),
    ("RX-0 Unicorn Gundam", "Robot Spirits", 1.55, 85),
    ("RX-0 Unicorn Banshee", "Robot Spirits", 1.5, 85),
    ("RX-0 Full Armor Unicorn", "Robot Spirits", 1.55, 95),
    ("MSN-06S Sinanju", "Robot Spirits", 1.45, 80),
    ("ASW-G-08 Barbatos", "Robot Spirits", 1.45, 70),
    ("ASW-G-08 Barbatos Lupus", "Robot Spirits", 1.45, 75),
    ("ASW-G-08 Barbatos Lupus Rex", "Robot Spirits", 1.5, 80),
    ("GN-001 Gundam Exia", "Robot Spirits", 1.45, 70),
    ("GN-0000 00 Gundam", "Robot Spirits", 1.45, 75),
    ("GNT-0000 00 Qan[T]", "Robot Spirits", 1.5, 80),
    ("XXXG-00W0 Wing Zero EW", "Robot Spirits", 1.5, 80),
    ("XXXG-01D Deathscythe Hell EW", "Robot Spirits", 1.4, 70),
    ("XXXG-01S Shenlong EW", "Robot Spirits", 1.35, 65),
    ("XXXG-01H Heavyarms EW", "Robot Spirits", 1.35, 65),
    ("XXXG-01W Wing Gundam EW", "Robot Spirits", 1.4, 70),
    ("Gundam Universe RX-78-2", "Gundam Universe", 1.35, 25),
    ("Gundam Universe Char Zaku II", "Gundam Universe", 1.35, 25),
    ("Gundam Universe Unicorn", "Gundam Universe", 1.4, 25),
    ("Gundam Universe Barbatos", "Gundam Universe", 1.35, 25),
    ("Gundam Universe Exia", "Gundam Universe", 1.35, 25),
    ("Gundam Universe Wing Zero", "Gundam Universe", 1.4, 25),
    ("Gundam Universe Nu Gundam", "Gundam Universe", 1.4, 25),
    ("Gundam Universe Sazabi", "Gundam Universe", 1.4, 25),
    ("Gundam Universe Zaku II", "Gundam Universe", 1.25, 22),
    ("Gundam Universe GM", "Gundam Universe", 1.2, 22),
    ("Gundam Universe Gouf", "Gundam Universe", 1.25, 22),
    ("Robot Spirits Destiny Gundam", "Robot Spirits", 1.4, 70),
    ("Robot Spirits Freedom Gundam", "Robot Spirits", 1.45, 75),
    ("Robot Spirits Strike Gundam", "Robot Spirits", 1.4, 70),
    ("Robot Spirits Impulse Gundam", "Robot Spirits", 1.35, 65),
    ("Robot Spirits Providence Gundam", "Robot Spirits", 1.35, 70),
    ("Robot Spirits Infinite Justice", "Robot Spirits", 1.4, 75),
    ("Robot Spirits Strike Freedom", "Robot Spirits", 1.5, 80),
    ("Robot Spirits Wing Zero Custom", "Robot Spirits", 1.45, 75),
    ("Robot Spirits Tallgeese", "Robot Spirits", 1.35, 65),
    ("Robot Spirits Epyon", "Robot Spirits", 1.4, 70),
], 2014, 2, 2, 65)

add(data, "figma", "fg7", [
    ("Link", "Twilight Princess", 1.5), ("Zelda", "Twilight Princess", 1.45),
    ("Ganondorf", "Twilight Princess", 1.5), ("Link", "Breath of the Wild", 1.55),
    ("Zelda", "Breath of the Wild", 1.45), ("Link", "Tears of the Kingdom", 1.55),
    ("Samus Aran", "Metroid Dread", 1.5), ("Samus Aran", "Zero Suit", 1.45),
    ("Ridley", "Metroid", 1.4), ("Cloud Strife", "Final Fantasy VII", 1.55),
    ("Tifa Lockhart", "Final Fantasy VII", 1.5), ("Sephiroth", "Final Fantasy VII", 1.55),
    ("Aerith Gainsborough", "Final Fantasy VII", 1.45), ("Yuffie Kisaragi", "Final Fantasy VII", 1.35),
    ("2B", "Nier Automata", 1.55), ("9S", "Nier Automata", 1.45), ("A2", "Nier Automata", 1.45),
    ("Joker", "Persona 5", 1.5), ("Crow", "Persona 5", 1.4), ("Violet", "Persona 5", 1.4),
    ("Kasumi Yoshizawa", "Persona 5", 1.4), ("Makoto Niijima", "Persona 5", 1.35),
    ("Saber", "Fate/stay night", 1.5), ("Saber Alter", "Fate/stay night", 1.5),
    ("Archer", "Fate/stay night", 1.4), ("Rider", "Fate/stay night", 1.4),
    ("Lancer", "Fate/stay night", 1.35), ("Gilgamesh", "Fate/stay night", 1.45),
    ("Kirito", "Sword Art Online", 1.4), ("Asuna", "Sword Art Online", 1.45),
    ("Tanjiro Kamado", "Demon Slayer", 1.5), ("Nezuko Kamado", "Demon Slayer", 1.5),
    ("Zenitsu Agatsuma", "Demon Slayer", 1.4), ("Inosuke Hashibira", "Demon Slayer", 1.4),
    ("Giyu Tomioka", "Demon Slayer", 1.4), ("Shinobu Kocho", "Demon Slayer", 1.45),
    ("Daki", "Demon Slayer", 1.35), ("Gyutaro", "Demon Slayer", 1.35),
    ("Spider-Man", "Across the Spider-Verse", 1.5), ("Miles Morales", "Spider-Verse", 1.5),
    ("Batman", "Ninja Batman", 1.45), ("Joker", "Ninja Batman", 1.4),
    ("Harley Quinn", "Ninja Batman", 1.4), ("Deathstroke", "Ninja Batman", 1.35),
    ("Mario", "Super Mario", 1.4), ("Luigi", "Super Mario", 1.35),
    ("Yoshi", "Super Mario", 1.3), ("Bowser", "Super Mario", 1.4),
    ("Pikachu", "Pokemon", 1.4), ("Lucario", "Pokemon", 1.35),
    ("Dante", "Devil May Cry", 1.45), ("Vergil", "Devil May Cry", 1.45),
    ("Lady", "Devil May Cry", 1.35), ("Nero", "Devil May Cry", 1.4),
    ("Mikey", "Tokyo Revengers", 1.35), ("Draken", "Tokyo Revengers", 1.3),
], 2015, 1, 2, 75)

add(data, "beastkingdom", "bk7", [
    ("Iron Man Mark LXXXV", "DAH Endgame", 1.5), ("Iron Man Mark L", "DAH Infinity War", 1.45),
    ("Captain America", "DAH Endgame", 1.45), ("Thor", "DAH Endgame", 1.45),
    ("Black Widow", "DAH Endgame", 1.4), ("Hawkeye", "DAH Endgame", 1.35),
    ("Hulk", "DAH Endgame", 1.4), ("War Machine", "DAH Endgame", 1.4),
    ("Scarlet Witch", "DAH Multiverse", 1.45), ("Doctor Strange", "DAH Multiverse", 1.45),
    ("Spider-Man Integrated", "DAH No Way Home", 1.5), ("Green Goblin", "DAH No Way Home", 1.45),
    ("Doctor Octopus", "DAH No Way Home", 1.45), ("Batman", "DAH The Batman", 1.5),
    ("Batman", "DAH Justice League", 1.45), ("Superman", "DAH Justice League", 1.45),
    ("Wonder Woman", "DAH Justice League", 1.45), ("Aquaman", "DAH Justice League", 1.4),
    ("Cyborg", "DAH Justice League", 1.35), ("Flash", "DAH Justice League", 1.4),
    ("Joker", "DAH 2019", 1.5), ("Harley Quinn", "DAH Birds of Prey", 1.45),
    ("Batman", "DAH Dark Knight", 1.5), ("Joker", "DAH Dark Knight", 1.55),
    ("Bane", "DAH Dark Knight Rises", 1.4), ("Catwoman", "DAH Dark Knight Rises", 1.4),
    ("Deadpool", "DAH Deadpool 2", 1.5), ("Wolverine", "DAH Deadpool & Wolverine", 1.55),
    ("Deadpool", "DAH Deadpool & Wolverine", 1.5), ("Venom", "DAH Venom", 1.45),
    ("Carnage", "DAH Venom 2", 1.45), ("Superman", "DAH Black Suit", 1.5),
    ("Batman", "DAH Hush", 1.45), ("Superman", "DAH Hush", 1.45),
    ("Batman", "DAH Ascending Knight", 1.4), ("Iron Man Mark III", "DAH Classic", 1.45),
    ("Iron Man Mark XLII", "DAH Iron Man 3", 1.4), ("Thanos", "DAH Infinity War", 1.55),
    ("Ebony Maw", "DAH Infinity War", 1.35), ("Cull Obsidian", "DAH Infinity War", 1.3),
    ("Corvus Glaive", "DAH Infinity War", 1.3), ("Proxima Midnight", "DAH Infinity War", 1.3),
    ("Batman", "DAH Killing Joke", 1.45), ("Joker", "DAH Killing Joke", 1.5),
    ("Batgirl", "DAH Batgirl", 1.4), ("Nightwing", "DAH Nightwing", 1.4),
    ("Robin", "DAH Damian", 1.35), ("Red Hood", "DAH Under the Red Hood", 1.45),
    ("Deathstroke", "DAH Deathstroke", 1.4), ("Green Lantern", "DAH Hal Jordan", 1.4),
], 2018, 6, 1, 125)

add(data, "enterbay", "eb7", [
    ("Michael Jordan", "Away Red", 1.55), ("Michael Jordan", "Home White", 1.55),
    ("Michael Jordan", "Road Black", 1.5), ("Michael Jordan", "All-Star", 1.5),
    ("Michael Jordan", "Rookie", 1.5), ("Kobe Bryant", "Lakers Home", 1.55),
    ("Kobe Bryant", "Lakers Away", 1.5), ("Kobe Bryant", "All-Star", 1.5),
    ("LeBron James", "Lakers", 1.5), ("LeBron James", "Cavaliers", 1.45),
    ("Stephen Curry", "Warriors", 1.45), ("Kevin Durant", "Warriors", 1.4),
    ("Shaquille O'Neal", "Lakers", 1.45), ("Magic Johnson", "Lakers", 1.4),
    ("Larry Bird", "Celtics", 1.4), ("Bruce Lee", "Enter the Dragon", 1.55),
    ("Bruce Lee", "Game of Death", 1.5), ("Bruce Lee", "Fist of Fury", 1.5),
    ("Bruce Lee", "Way of the Dragon", 1.5), ("Bruce Lee", "Jeet Kune Do", 1.45),
    ("Muhammad Ali", "Boxing", 1.5), ("Mike Tyson", "Boxing", 1.45),
    ("Rocky Balboa", "Rocky", 1.45), ("Apollo Creed", "Rocky", 1.4),
    ("Ivan Drago", "Rocky IV", 1.4), ("Elvis Presley", "'68 Comeback", 1.45),
    ("Elvis Presley", "Aloha from Hawaii", 1.45), ("Elvis Presley", "Vegas", 1.4),
    ("James Dean", "Rebel", 1.4), ("Marlon Brando", "Godfather", 1.45),
    ("Al Pacino", "Scarface", 1.5), ("Robert De Niro", "Taxi Driver", 1.45),
    ("Batman", "1989", 1.5), ("Joker", "1989", 1.55),
    ("Batman", "Dark Knight", 1.5), ("Joker", "Dark Knight", 1.55),
    ("Superman", "1978", 1.45), ("Superman", "Black Suit", 1.45),
    ("Iron Man Mark III", "Iron Man", 1.5), ("Iron Man Mark VII", "Avengers", 1.45),
    ("Captain America", "First Avenger", 1.4), ("Wolverine", "X-Men", 1.5),
    ("Deadpool", "Movie", 1.5), ("Spider-Man", "Amazing", 1.45), ("Venom", "Movie", 1.45),
], 2012, 3, 2, 280)

ht = [
    ("Iron Man Mark LXXXV", "Endgame", 1.55), ("Iron Man Mark L", "Infinity War", 1.5),
    ("Iron Man Mark III", "Diecast", 1.55), ("Iron Man Mark IV", "Diecast", 1.5),
    ("Iron Man Mark V", "Suitcase", 1.5), ("Iron Man Mark VI", "Diecast", 1.45),
    ("Iron Man Mark VII", "Avengers", 1.5), ("Iron Man Mark XLII", "Iron Man 3", 1.5),
    ("Iron Man Mark XLIII", "Age of Ultron", 1.45), ("Iron Man Mark XLIV Hulkbuster", "Age of Ultron", 1.55),
    ("War Machine Mark VI", "Endgame", 1.45), ("War Machine Mark IV", "Infinity War", 1.4),
    ("Captain America", "Endgame", 1.5), ("Captain America", "Infinity War", 1.45),
    ("Thor", "Endgame", 1.45), ("Thor", "Love and Thunder", 1.45),
    ("Black Widow", "Endgame", 1.4), ("Hawkeye", "Endgame", 1.35), ("Hulk", "Endgame", 1.45),
    ("Scarlet Witch", "Multiverse of Madness", 1.5), ("Doctor Strange", "Multiverse of Madness", 1.5),
    ("Spider-Man", "No Way Home Integrated", 1.55), ("Spider-Man", "No Way Home Black & Gold", 1.5),
    ("Green Goblin", "No Way Home", 1.5), ("Doctor Octopus", "No Way Home", 1.5),
    ("Venom", "Let There Be Carnage", 1.5), ("Carnage", "Let There Be Carnage", 1.5),
    ("Batman", "The Batman", 1.55), ("Batman", "Batfleck Justice League", 1.5),
    ("Superman", "Black Suit Zack Snyder", 1.5), ("Wonder Woman", "1984", 1.45),
    ("Aquaman", "Lost Kingdom", 1.4), ("Joker", "Joaquin Phoenix", 1.55),
    ("Harley Quinn", "Birds of Prey", 1.45), ("Deadpool", "Deadpool 2", 1.5),
    ("Wolverine", "Deadpool & Wolverine", 1.55), ("Deadpool", "Deadpool & Wolverine", 1.5),
    ("Darth Vader", "Rogue One", 1.55), ("Darth Vader", "Return of the Jedi", 1.55),
    ("Luke Skywalker", "Return of the Jedi", 1.5), ("Luke Skywalker", "Bespin", 1.5),
    ("Han Solo", "A New Hope", 1.45), ("Princess Leia", "A New Hope", 1.45),
    ("Boba Fett", "Return of the Jedi", 1.55), ("Boba Fett", "The Mandalorian", 1.55),
    ("The Mandalorian", "Beskar Armor", 1.55), ("Grogu", "The Mandalorian", 1.5),
    ("Din Djarin", "Darksaber", 1.5), ("Ahsoka Tano", "The Mandalorian", 1.5),
    ("Bo-Katan Kryze", "The Mandalorian", 1.4), ("Kylo Ren", "Rise of Skywalker", 1.45),
    ("Rey", "Rise of Skywalker", 1.45), ("Stormtrooper", "Mandalorian", 1.35),
    ("Scout Trooper", "Mandalorian", 1.35), ("Dark Trooper", "Mandalorian", 1.45),
]
add(data, "hottoys", "ht7", ht, 2018, 1, 1, 350)

tz = [
    ("Optimus Prime", "DLX Rise of the Beasts", 1.5, 200), ("Megatron", "DLX Rise of the Beasts", 1.5, 200),
    ("Optimus Primal", "DLX Rise of the Beasts", 1.45, 200), ("Bumblebee", "DLX Rise of the Beasts", 1.4, 180),
    ("Arcee", "DLX Rise of the Beasts", 1.35, 170), ("Mirage", "DLX Rise of the Beasts", 1.35, 170),
    ("Optimus Prime", "DLX Bumblebee Movie", 1.5, 200), ("Bumblebee", "DLX Bumblebee Movie", 1.45, 180),
    ("Optimus Prime", "DLX The Last Knight", 1.45, 190), ("Megatron", "DLX The Last Knight", 1.45, 190),
    ("Optimus Prime", "DLX Age of Extinction", 1.45, 190), ("Lockdown", "DLX Age of Extinction", 1.4, 180),
    ("Grimlock", "DLX Age of Extinction", 1.5, 220), ("Ultra Magnus", "DLX Age of Extinction", 1.4, 180),
    ("FigZero Batman", "The Batman", 1.5, 160), ("FigZero Catwoman", "The Batman", 1.45, 150),
    ("FigZero Riddler", "The Batman", 1.4, 140), ("FigZero Penguin", "The Batman", 1.35, 140),
    ("FigZero Guts", "Berserk Black Swordsman", 1.55, 180), ("FigZero Guts", "Berserk Berserker Armor", 1.55, 200),
    ("FigZero Griffith", "Berserk", 1.5, 170), ("FigZero Casca", "Berserk", 1.4, 150),
    ("FigZero Zodd", "Berserk", 1.45, 180), ("FigZero Eren Yeager", "Attack on Titan", 1.45, 150),
    ("FigZero Mikasa Ackerman", "Attack on Titan", 1.45, 150), ("FigZero Levi Ackerman", "Attack on Titan", 1.5, 160),
    ("FigZero Armored Titan", "Attack on Titan", 1.45, 200), ("FigZero Attack Titan", "Attack on Titan", 1.5, 220),
    ("FigZero Colossal Titan", "Attack on Titan", 1.45, 250), ("DLX Geralt", "The Witcher", 1.5, 180),
    ("DLX Ciri", "The Witcher", 1.45, 170), ("DLX Yennefer", "The Witcher", 1.45, 170),
    ("FigZero Robocop", "Robocop", 1.5, 160), ("FigZero ED-209", "Robocop", 1.45, 200),
    ("FigZero Robocop", "Battle Damaged", 1.45, 165), ("FigZero Judge Dredd", "Dredd", 1.45, 150),
    ("FigZero Jason Voorhees", "Friday the 13th", 1.4, 140), ("FigZero Michael Myers", "Halloween", 1.4, 140),
    ("FigZero Deathstroke", "Injustice", 1.4, 140), ("FigZero Batman", "Injustice", 1.4, 140),
    ("FigZero Superman", "Injustice", 1.4, 140), ("FigZero Wonder Woman", "Injustice", 1.35, 135),
    ("DLX Soundwave", "Transformers", 1.5, 200), ("DLX Starscream", "Transformers", 1.45, 180),
    ("DLX Shockwave", "Transformers", 1.45, 180), ("DLX Jazz", "Transformers", 1.4, 170),
    ("DLX Ironhide", "Transformers", 1.4, 170), ("DLX Ratchet", "Transformers", 1.35, 165),
    ("FigZero Spike Spiegel", "Cowboy Bebop", 1.5, 160), ("FigZero Faye Valentine", "Cowboy Bebop", 1.45, 150),
    ("FigZero Jet Black", "Cowboy Bebop", 1.4, 145), ("FigZero Ein", "Cowboy Bebop", 1.3, 80),
    ("FigZero Vicious", "Cowboy Bebop", 1.4, 145), ("FigZero Batmobile Batman", "The Batman", 1.5, 180),
    ("DLX Optimus Prime", "Transformers ROTB Metallic", 1.55, 220),
]
add(data, "threezero", "tz7", tz, 2019, 2, 1, 160)

vv = [(n, "Action Force", 1.2 + (i % 5) * 0.05, 24.99) for i, n in enumerate([
    "Sergeant Pathfinder", "Coldsnap", "Shadow", "Quartermaster", "Desert Infantry",
    "Urban Infantry", "Jungle Infantry", "Arctic Infantry", "Night Ops", "Breacher",
    "Sniper", "Medic", "Heavy Gunner", "Radioman", "Scout", "Engineer", "Pilot",
    "Tank Commander", "Martial Artist", "Ninja", "Mercenary A", "Mercenary B",
    "Mercenary C", "Enemy Officer", "Enemy Trooper A", "Enemy Trooper B",
    "Enemy Trooper C", "Enemy Heavy", "Enemy Sniper", "Civilian Photojournalist",
    "Civilian Scientist", "Zombie Trooper", "Zombie Civilian", "Robot Trooper",
    "Robot Officer", "Action Force Viper", "Action Force Cobra-type", "Action Force Baroness-type",
    "Action Force Destro-type", "Action Force Storm Shadow-type", "Action Force Snake Eyes-type",
    "Action Force Scarlett-type", "Action Force Roadblock-type", "Action Force Duke-type",
    "Action Force Flint-type", "Action Force Lady Jaye-type", "Action Force Shipwreck-type",
    "Action Force Alpine-type", "Action Force Spirit-type", "Action Force Quick Kick-type",
])]
add(data, "valaverse", "vv7", vv, 2020, 4, 1, 24.99)

pdna = [
    ("He-Man", "Filmation", 1.5), ("Skeletor", "Filmation", 1.55), ("Battle Cat", "Filmation", 1.4),
    ("Panthor", "Filmation", 1.4), ("Man-At-Arms", "Filmation", 1.35), ("Teela", "Filmation", 1.4),
    ("Evil-Lyn", "Filmation", 1.4), ("Beast Man", "Filmation", 1.35), ("Mer-Man", "Filmation", 1.3),
    ("Trap Jaw", "Filmation", 1.35), ("Tri-Klops", "Filmation", 1.3), ("Orko", "Filmation", 1.35),
    ("Sorceress", "Filmation", 1.35), ("King Randor", "Filmation", 1.3), ("Queen Marlena", "Filmation", 1.25),
    ("Fisto", "Filmation", 1.25), ("Stratos", "Filmation", 1.25), ("Zodac", "Filmation", 1.25),
    ("Whiplash", "Filmation", 1.25), ("Clawful", "Filmation", 1.25), ("Jitsu", "Filmation", 1.25),
    ("Webstor", "Filmation", 1.2), ("Kobra Khan", "Filmation", 1.25), ("Modulok", "Filmation", 1.3),
    ("Sy-Klone", "Filmation", 1.25), ("Roboto", "Filmation", 1.3), ("Moss Man", "Filmation", 1.25),
    ("Mekaneck", "Filmation", 1.2), ("Ram Man", "Filmation", 1.25), ("Spikor", "Filmation", 1.25),
    ("Stinkor", "Filmation", 1.3), ("Two-Bad", "Filmation", 1.3), ("Hordak", "Filmation", 1.45),
    ("She-Ra", "Filmation", 1.5), ("Catra", "Filmation", 1.45), ("Scorpia", "Filmation", 1.35),
    ("Imp", "Filmation", 1.25), ("Horde Trooper", "Filmation", 1.2), ("Grizzlor", "Filmation", 1.25),
    ("Leech", "Filmation", 1.25), ("Mantenna", "Filmation", 1.25), ("Modulok Deluxe", "Special", 1.35),
    ("He-Man Battle Damaged", "Special", 1.45), ("Skeletor Throne", "Special", 1.55),
    ("Battle Cat Soft Goods", "Special", 1.45),
]
add(data, "premiumdna", "pd7", pdna, 2021, 6, 1, 55)

ar = [(n, s, d) for n, s, d in [
    ("Lancer", "1:18", 1.3), ("Scout", "1:18", 1.25), ("Heavy", "1:18", 1.3), ("Medic", "1:18", 1.2),
    ("Sniper", "1:18", 1.3), ("Breacher", "1:18", 1.25), ("Pilot", "1:18", 1.25), ("Officer", "1:18", 1.3),
    ("Civilian A", "1:18", 1.15), ("Civilian B", "1:18", 1.15), ("Enemy Trooper", "1:18", 1.25),
    ("Enemy Heavy", "1:18", 1.25), ("Enemy Sniper", "1:18", 1.25), ("Mech Pilot", "1:18", 1.35),
    ("Mech Frame A", "1:18", 1.4), ("Mech Frame B", "1:18", 1.4), ("Mech Frame C", "1:18", 1.35),
    ("Vehicle Driver", "1:18", 1.2), ("Desert Lancer", "Special", 1.3), ("Arctic Scout", "Special", 1.25),
    ("Urban Heavy", "Special", 1.3), ("Night Ops Sniper", "Special", 1.35), ("Jungle Breacher", "Special", 1.25),
    ("Coastal Medic", "Special", 1.2), ("Sandstorm Officer", "Special", 1.3), ("Ashfall Pilot", "Special", 1.3),
    ("Rust Belt Civilian", "Special", 1.15), ("Wasteland Enemy", "Special", 1.25),
    ("Acid Rain Trooper Clear", "Special", 1.3), ("Mech Frame Clear", "Special", 1.4),
    ("Lancer Soft Goods", "Special", 1.35), ("Scout Soft Goods", "Special", 1.3),
    ("Heavy Soft Goods", "Special", 1.35), ("Enemy Soft Goods", "Special", 1.3),
    ("Mech Pilot Deluxe", "Special", 1.4), ("Officer Deluxe", "Special", 1.35),
    ("Sniper Deluxe", "Special", 1.35), ("Breacher Deluxe", "Special", 1.3),
    ("Vehicle Crew Set", "Special", 1.3), ("Squad Pack Alpha", "Special", 1.4),
    ("Squad Pack Bravo", "Special", 1.4), ("Squad Pack Enemy", "Special", 1.35),
    ("Mech Duo Pack", "Special", 1.45), ("Desert Squad", "Special", 1.35), ("Arctic Squad", "Special", 1.35),
]]
add(data, "acidrain", "ar7", ar, 2017, 5, 2, 35)

fh = [
    ("Sir Gideon Heavensbrand", "Mythic Legions", 1.4), ("Lady Avarona", "Mythic Legions", 1.35),
    ("Orc Soldier", "Mythic Legions", 1.3), ("Orc Archer", "Mythic Legions", 1.25),
    ("Skeleton Warrior", "Mythic Legions", 1.3), ("Skeleton Archer", "Mythic Legions", 1.25),
    ("Goblin Legion Builder", "Mythic Legions", 1.3), ("Dwarf Warrior", "Mythic Legions", 1.35),
    ("Elf Ranger", "Mythic Legions", 1.35), ("Knight of the Order", "Mythic Legions", 1.35),
    ("Knight Black", "Mythic Legions", 1.35), ("Knight Gold", "Mythic Legions", 1.4),
    ("Necronominus", "Mythic Legions", 1.5), ("Illythia", "Mythic Legions", 1.45),
    ("Arethyr", "Mythic Legions", 1.45), ("Attila Leossyr", "Mythic Legions", 1.4),
    ("Thord", "Mythic Legions", 1.35), ("Bog Goblin", "Mythic Legions", 1.25),
    ("Deluxe Legion Builder Skeleton", "Mythic Legions", 1.35), ("Deluxe Legion Builder Orc", "Mythic Legions", 1.35),
    ("Cosmic Legions Hvalkatar", "Cosmic Legions", 1.4), ("Cosmic Legions T.U.5.C.C. Trooper", "Cosmic Legions", 1.35),
    ("Cosmic Legions Sphexxian", "Cosmic Legions", 1.35), ("Cosmic Legions Slygor", "Cosmic Legions", 1.3),
    ("Cosmic Legions Vorgus", "Cosmic Legions", 1.35), ("Cosmic Legions Thraxxon", "Cosmic Legions", 1.35),
    ("Cosmic Legions Traedorion", "Cosmic Legions", 1.4), ("Cosmic Legions Deluxe Trooper", "Cosmic Legions", 1.4),
    ("Figura Obscura Headless Horseman", "Figura Obscura", 1.55), ("Figura Obscura Krampus", "Figura Obscura", 1.55),
    ("Figura Obscura Father Christmas", "Figura Obscura", 1.45), ("Figura Obscura Frankenstein", "Figura Obscura", 1.5),
    ("Figura Obscura Bride of Frankenstein", "Figura Obscura", 1.5), ("Figura Obscura Phantom of the Opera", "Figura Obscura", 1.45),
    ("Figura Obscura Hunchback", "Figura Obscura", 1.4), ("Figura Obscura Dracula", "Figura Obscura", 1.5),
    ("Figura Obscura Wolfman", "Figura Obscura", 1.45), ("Figura Obscura Mummy", "Figura Obscura", 1.4),
    ("Figura Obscura Creature", "Figura Obscura", 1.4), ("Mythic Legions Sir Godfrey", "Mythic Legions", 1.35),
    ("Mythic Legions Lady Jeannette", "Mythic Legions", 1.3), ("Mythic Legions Barbarian", "Mythic Legions", 1.3),
    ("Mythic Legions Sorceress", "Mythic Legions", 1.35), ("Mythic Legions Demon", "Mythic Legions", 1.4),
    ("Mythic Legions Angel", "Mythic Legions", 1.4), ("Mythic Legions Undead Knight", "Mythic Legions", 1.35),
    ("Mythic Legions Plague Doctor", "Mythic Legions", 1.4), ("Mythic Legions Executioner", "Mythic Legions", 1.35),
    ("Mythic Legions Court Jester", "Mythic Legions", 1.3), ("Mythic Legions Pirate Captain", "Mythic Legions", 1.35),
    ("Mythic Legions Pirate Crew", "Mythic Legions", 1.25), ("Mythic Legions Sea Hag", "Mythic Legions", 1.35),
    ("Mythic Legions Minotaur", "Mythic Legions", 1.4), ("Mythic Legions Centaur", "Mythic Legions", 1.4),
    ("Mythic Legions Gargoyle", "Mythic Legions", 1.35),
]
add(data, "fourhorsemen", "fh7", fh, 2018, 3, 1, 48)

jada = [
    ("Ryu", "Street Fighter", 1.45), ("Ken", "Street Fighter", 1.4), ("Chun-Li", "Street Fighter", 1.5),
    ("Guile", "Street Fighter", 1.35), ("Blanka", "Street Fighter", 1.35), ("Dhalsim", "Street Fighter", 1.3),
    ("E. Honda", "Street Fighter", 1.25), ("Zangief", "Street Fighter", 1.35), ("M. Bison", "Street Fighter", 1.45),
    ("Vega", "Street Fighter", 1.4), ("Balrog", "Street Fighter", 1.3), ("Sagat", "Street Fighter", 1.4),
    ("Cammy", "Street Fighter", 1.45), ("Akuma", "Street Fighter", 1.5), ("Juri", "Street Fighter", 1.4),
    ("Luke", "Street Fighter", 1.35), ("Jamie", "Street Fighter", 1.3), ("Kimberly", "Street Fighter", 1.3),
    ("Manon", "Street Fighter", 1.3), ("Marisa", "Street Fighter", 1.3), ("JP", "Street Fighter", 1.3),
    ("Lily", "Street Fighter", 1.25), ("Dee Jay", "Street Fighter", 1.25), ("Honda Deluxe", "Street Fighter", 1.3),
    ("Nano Metalfigs Batman", "DC", 1.2, 16.99), ("Nano Metalfigs Superman", "DC", 1.2, 16.99),
    ("Nano Metalfigs Wonder Woman", "DC", 1.2, 16.99), ("Nano Metalfigs Flash", "DC", 1.15, 16.99),
    ("Nano Metalfigs Joker", "DC", 1.25, 16.99), ("Nano Metalfigs Harley", "DC", 1.25, 16.99),
    ("Universal Monsters Frankenstein", "Universal", 1.35), ("Universal Monsters Dracula", "Universal", 1.35),
    ("Universal Monsters Wolf Man", "Universal", 1.3), ("Universal Monsters Mummy", "Universal", 1.3),
    ("Universal Monsters Creature", "Universal", 1.35), ("Universal Monsters Bride", "Universal", 1.35),
    ("Universal Monsters Invisible Man", "Universal", 1.3), ("Universal Monsters Phantom", "Universal", 1.3),
    ("Street Fighter Ryu Chase", "Special", 1.5), ("Street Fighter Chun-Li Chase", "Special", 1.5),
    ("Street Fighter Akuma Chase", "Special", 1.55), ("Street Fighter Cammy Chase", "Special", 1.45),
    ("Universal Monsters Glow", "Special", 1.4), ("DC Nano Chase Pack", "Special", 1.25, 16.99),
    ("Street Fighter Guile Deluxe", "Special", 1.4),
]
add(data, "jada", "jd7", jada, 2021, 2, 1, 24.99)

jakks = [
    ("Sonic", "Sonic Movie 2", 1.4), ("Tails", "Sonic Movie 2", 1.35), ("Knuckles", "Sonic Movie 2", 1.4),
    ("Robotnik", "Sonic Movie 2", 1.35), ("Sonic", "Sonic Movie 3", 1.45), ("Shadow", "Sonic Movie 3", 1.5),
    ("Sonic Classic", "2.5-inch", 1.3), ("Tails Classic", "2.5-inch", 1.25), ("Knuckles Classic", "2.5-inch", 1.25),
    ("Amy Classic", "2.5-inch", 1.25), ("Shadow Classic", "2.5-inch", 1.35), ("Silver Classic", "2.5-inch", 1.25),
    ("Metal Sonic", "2.5-inch", 1.35), ("Eggman", "2.5-inch", 1.3), ("Sonic 4-inch", "Modern", 1.35),
    ("Tails 4-inch", "Modern", 1.3), ("Knuckles 4-inch", "Modern", 1.3), ("Shadow 4-inch", "Modern", 1.4),
    ("Amy 4-inch", "Modern", 1.3), ("Rouge 4-inch", "Modern", 1.3), ("Vector 4-inch", "Modern", 1.2),
    ("Espio 4-inch", "Modern", 1.2), ("Charmy 4-inch", "Modern", 1.15), ("Omega 4-inch", "Modern", 1.25),
    ("Super Sonic", "Modern", 1.45), ("Hyper Sonic", "Special", 1.4),
    ("He-Man Primal Age", "MotU Primal Age", 1.35), ("Skeletor Primal Age", "MotU Primal Age", 1.4),
    ("Beast Man Primal Age", "MotU Primal Age", 1.3), ("Teela Primal Age", "MotU Primal Age", 1.3),
    ("Mer-Man Primal Age", "MotU Primal Age", 1.25), ("Trap Jaw Primal Age", "MotU Primal Age", 1.3),
    ("Mario", "Nintendo", 1.35), ("Luigi", "Nintendo", 1.3), ("Yoshi", "Nintendo", 1.3),
    ("Bowser", "Nintendo", 1.35), ("Peach", "Nintendo", 1.3), ("Toad", "Nintendo", 1.2),
    ("Link", "Nintendo", 1.4), ("Zelda", "Nintendo", 1.35), ("Samus", "Nintendo", 1.4),
    ("Kirby", "Nintendo", 1.3), ("Donkey Kong", "Nintendo", 1.3), ("Diddy Kong", "Nintendo", 1.25),
    ("Pikachu", "Nintendo", 1.35), ("Pokemon Trainer", "Nintendo", 1.25),
    ("Sonic Super Sized", "Special", 1.4), ("Shadow Super Sized", "Special", 1.45),
    ("Knuckles Super Sized", "Special", 1.35), ("Eggman Deluxe", "Special", 1.35),
]
add(data, "jakks", "jk7", jakks, 2019, 5, 1, 14.99)

tb = [
    ("Spider-Man", "Series 1", 1.5), ("Green Goblin", "Series 1", 1.45), ("Doctor Octopus", "Series 1", 1.4),
    ("Venom", "Series 1", 1.5), ("Carnage", "Series 2", 1.45), ("Hobgoblin", "Series 2", 1.35),
    ("Black Cat", "Series 2", 1.4), ("Punisher", "Series 2", 1.4), ("Daredevil", "Series 3", 1.45),
    ("Elektra", "Series 3", 1.4), ("Kingpin", "Series 3", 1.4), ("Bullseye", "Series 3", 1.35),
    ("Wolverine", "Series 4", 1.55), ("Cyclops", "Series 4", 1.4), ("Jean Grey", "Series 4", 1.4),
    ("Storm", "Series 4", 1.45), ("Magneto", "Series 5", 1.5), ("Professor X", "Series 5", 1.35),
    ("Beast", "Series 5", 1.4), ("Nightcrawler", "Series 5", 1.45), ("Rogue", "Series 6", 1.5),
    ("Gambit", "Series 6", 1.5), ("Sabretooth", "Series 6", 1.4), ("Jubilee", "Series 6", 1.35),
    ("Iceman", "Series 7", 1.35), ("Angel", "Series 7", 1.3), ("Colossus", "Series 7", 1.35),
    ("Kitty Pryde", "Series 7", 1.35), ("Cable", "Series 8", 1.45), ("Deadpool", "Series 8", 1.5),
    ("Bishop", "Series 8", 1.35), ("Psylocke", "Series 8", 1.4), ("Captain America", "Series 9", 1.45),
    ("Iron Man", "Series 9", 1.45), ("Thor", "Series 9", 1.45), ("Hulk", "Series 9", 1.4),
    ("Black Panther", "Series 10", 1.45), ("Falcon", "Series 10", 1.3), ("Winter Soldier", "Series 10", 1.4),
    ("Hawkeye", "Series 10", 1.3), ("Doctor Strange", "Series 11", 1.4), ("Scarlet Witch", "Series 11", 1.4),
    ("Vision", "Series 11", 1.35), ("Quicksilver", "Series 11", 1.3), ("Silver Surfer", "Series 12", 1.45),
    ("Galactus", "Build-A-Figure", 1.5), ("Thanos", "Series 12", 1.5), ("Adam Warlock", "Series 12", 1.4),
    ("Ghost Rider", "Series 13", 1.45), ("Blade", "Series 13", 1.4), ("Morbius", "Series 13", 1.35),
    ("Werewolf by Night", "Series 13", 1.3), ("Spider-Man Black Suit", "Special", 1.55),
    ("Wolverine Brown Suit", "Special", 1.55), ("Apocalypse", "Build-A-Figure", 1.5),
]
add(data, "toybiz", "tb7", tb, 2002, 2, 1, 8.99)

kenner = [
    ("Superman", "Super Powers", 1.5), ("Batman", "Super Powers", 1.5), ("Robin", "Super Powers", 1.4),
    ("Wonder Woman", "Super Powers", 1.45), ("Aquaman", "Super Powers", 1.35), ("Flash", "Super Powers", 1.4),
    ("Green Lantern", "Super Powers", 1.45), ("Hawkman", "Super Powers", 1.35), ("Green Arrow", "Super Powers", 1.35),
    ("Firestorm", "Super Powers", 1.3), ("Red Tornado", "Super Powers", 1.3), ("Martian Manhunter", "Super Powers", 1.4),
    ("Joker", "Super Powers", 1.5), ("Penguin", "Super Powers", 1.4), ("Riddler", "Super Powers", 1.4),
    ("Catwoman", "Super Powers", 1.45), ("Lex Luthor", "Super Powers", 1.45), ("Brainiac", "Super Powers", 1.4),
    ("Darkseid", "Super Powers", 1.55), ("Kalibak", "Super Powers", 1.35), ("Steppenwolf", "Super Powers", 1.3),
    ("Parademon", "Super Powers", 1.25), ("Desaad", "Super Powers", 1.3), ("Mr. Freeze", "Super Powers", 1.4),
    ("Two-Face", "Super Powers", 1.35), ("Scarecrow", "Super Powers", 1.3), ("Solomon Grundy", "Super Powers", 1.35),
    ("Golden Pharaoh", "Super Powers", 1.25), ("Samurai", "Super Powers", 1.25), ("Cyclotron", "Super Powers", 1.2),
    ("Orion", "Super Powers", 1.4), ("Lightray", "Super Powers", 1.3), ("Mantis", "Super Powers", 1.25),
    ("Metron", "Super Powers", 1.3), ("Batman", "Dark Knight Collection", 1.45), ("Joker", "Dark Knight Collection", 1.45),
    ("Batman", "Batman Returns", 1.4), ("Penguin", "Batman Returns", 1.4), ("Catwoman", "Batman Returns", 1.45),
    ("Batman", "Batman Forever", 1.35), ("Robin", "Batman Forever", 1.3), ("Riddler", "Batman Forever", 1.35),
    ("Two-Face", "Batman Forever", 1.3), ("Batman", "Batman & Robin", 1.3), ("Mr. Freeze", "Batman & Robin", 1.35),
    ("Poison Ivy", "Batman & Robin", 1.35), ("Bane", "Batman & Robin", 1.3), ("Batgirl", "Batman & Robin", 1.3),
    ("Tyr", "Super Powers", 1.2), ("Cyano", "Super Powers", 1.2),
]
add(data, "kenner", "kn7", kenner, 1984, 5, 2, 5.99)

OUT.write_text(json.dumps(data, indent=2) + "\n")
total = sum(len(v) for v in data.values())
print({k: len(v) for k, v in data.items()})
print("TOTAL", total)
assert 800 <= total <= 1500, total

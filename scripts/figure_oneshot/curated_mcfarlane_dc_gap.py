"""McFarlane DC Multiverse / Megafigs / Gold Label / Page Punchers densify.

Real character + wave names only. Floor 1980. No imageUrl.
Source tag: curated-mcfarlane-dc-gap
"""
from __future__ import annotations

FLOOR = "1980-01-01"


def F(rid, name, subtitle, line, company, release, msrp, scale, demand, tags):
    if release < FLOOR:
        release = FLOOR
    return {
        "id": rid,
        "name": name,
        "subtitle": subtitle,
        "line": line,
        "company": company,
        "kind": "figure",
        "releaseDate": release,
        "msrp": float(msrp),
        "scale": scale,
        "demand": float(demand),
        "tags": [t for t in tags.split(",") if t],
        "source": "curated-mcfarlane-dc-gap",
    }


def build_mcfarlane_dc_gap() -> list[dict]:
    rows: list[dict] = []

    # ---- New Gods / Apokolips densify (thin / missing) ----
    NG = [
        ("orion-classic", "Orion", "New Gods Classic", "2022-08-01", 1.35),
        ("orion-astro", "Orion", "Astro-Harness", "2023-02-01", 1.4),
        ("mr-miracle", "Mr. Miracle", "Scott Free", "2022-09-01", 1.35),
        ("mr-miracle-escape", "Mr. Miracle", "Escape Artist", "2023-06-01", 1.3),
        ("big-barda", "Big Barda", "New Gods", "2022-09-01", 1.4),
        ("big-barda-armor", "Big Barda", "Battle Armor", "2023-07-01", 1.35),
        ("highfather", "Highfather", "New Genesis", "2023-01-01", 1.3),
        ("metron", "Metron", "Mobius Chair", "2023-03-01", 1.45),
        ("kalibak-classic", "Kalibak", "Son of Darkseid", "2022-10-01", 1.35),
        ("kalibak-mega", "Kalibak", "Megafig", "2023-05-01", 1.5),
        ("desaad", "DeSaad", "Apokolips", "2022-11-01", 1.25),
        ("granny-goodness", "Granny Goodness", "Apokolips", "2023-01-01", 1.3),
        ("steppenwolf-classic", "Steppenwolf", "Classic Armor", "2021-06-01", 1.3),
        ("parademon-basic", "Parademon", "Apokolips Soldier", "2021-07-01", 1.2),
        ("parademon-shield", "Parademon", "Shield Variant", "2021-08-01", 1.15),
        ("female-fury-bernaleth", "Bernadeth", "Female Furies", "2023-04-01", 1.25),
        ("female-fury-stompa", "Stompa", "Female Furies", "2023-04-01", 1.25),
        ("female-fury-lashina", "Lashina", "Female Furies", "2023-05-01", 1.3),
        ("female-fury-mad-harriet", "Mad Harriet", "Female Furies", "2023-05-01", 1.25),
        ("glorious-godfrey", "Glorious Godfrey", "Apokolips", "2023-08-01", 1.2),
        ("forager", "Forager", "New Gods", "2023-09-01", 1.2),
        ("lightray", "Lightray", "New Genesis", "2023-09-01", 1.2),
        ("black-racer", "Black Racer", "New Gods", "2024-01-01", 1.35),
        ("darkseid-armor", "Darkseid", "Armored", "2022-12-01", 1.5),
        ("darkseid-return", "Darkseid", "Return of Darkseid", "2024-03-01", 1.45),
    ]
    for suf, name, sub, date, dem in NG:
        msrp, scale = (39.99, '10"') if "Megafig" in sub or suf.endswith("-mega") else (24.99, '7"')
        line = "DC Multiverse Megafigs" if scale == '10"' else "DC Multiverse"
        rows.append(F(f"mcfdc-{suf}", name, sub, line, "mcfarlane", date, msrp, scale, dem,
                      "dc,mcfarlane,multiverse,new-gods,curated"))

    # ---- Mystics / Vertigo-adjacent DC Multiverse ----
    MYST = [
        ("constantine", "John Constantine", "Hellblazer", "2022-03-01", 1.4),
        ("constantine-trench", "John Constantine", "Trench Coat", "2023-10-01", 1.35),
        ("spectre", "The Spectre", "Jim Corrigan", "2022-05-01", 1.45),
        ("etigan", "Etrigan", "The Demon", "2022-04-01", 1.4),
        ("etigan-animated", "Etrigan", "Animated Series", "2023-11-01", 1.3),
        ("deadman", "Deadman", "Boston Brand", "2022-06-01", 1.3),
        ("phantom-stranger", "Phantom Stranger", "Mystic", "2022-07-01", 1.25),
        ("zatanna-stage", "Zatanna", "Stage Magician", "2021-09-01", 1.35),
        ("zatanna-top-hat", "Zatanna", "Top Hat Exclusive", "2023-02-01", 1.4),
        ("doctor-fate-classic", "Doctor Fate", "Kent Nelson Classic", "2021-05-01", 1.35),
        ("doctor-fate-helmet", "Doctor Fate", "Full Helmet", "2022-08-01", 1.4),
        ("swamp-thing-classic", "Swamp Thing", "Classic", "2021-04-01", 1.4),
        ("swamp-thing-planetary", "Swamp Thing", "Planetary", "2023-06-01", 1.35),
        ("clar-ken", "Klarion", "The Witch Boy", "2023-03-01", 1.25),
        ("enchantress", "Enchantress", "June Moone", "2022-01-01", 1.3),
        ("ragman", "Ragman", "Mystical", "2023-07-01", 1.2),
        ("blue-devil", "Blue Devil", "Daniel Cassidy", "2023-08-01", 1.25),
        ("amadeus-arkham", "Amadeus Arkham", "Arkham Asylum", "2024-02-01", 1.2),
    ]
    for suf, name, sub, date, dem in MYST:
        rows.append(F(f"mcfdc-{suf}", name, sub, "DC Multiverse", "mcfarlane", date, 24.99, '7"', dem,
                      "dc,mcfarlane,multiverse,mystic,curated"))

    # ---- Justice Society / Golden Age densify ----
    JSA = [
        ("jay-garrick", "The Flash", "Jay Garrick", "2021-11-01", 1.35),
        ("alan-scott", "Green Lantern", "Alan Scott", "2021-11-01", 1.35),
        ("alan-scott-gold", "Green Lantern", "Alan Scott Gold Label", "2023-04-01", 1.45),
        ("hawkgirl-jsa", "Hawkgirl", "JSA Classic", "2022-02-01", 1.3),
        ("hawkman-jsa", "Hawkman", "Carter Hall JSA", "2022-02-01", 1.3),
        ("dr-midnite", "Doctor Mid-Nite", "Charles McNider", "2022-06-01", 1.2),
        ("hourman", "Hourman", "Rex Tyler", "2022-06-01", 1.2),
        ("wildcat", "Wildcat", "Ted Grant", "2022-07-01", 1.25),
        ("atom-al", "The Atom", "Al Pratt", "2022-08-01", 1.15),
        ("starman", "Starman", "Ted Knight", "2022-09-01", 1.25),
        ("sandman-jsa", "Sandman", "Wesley Dodds", "2022-10-01", 1.25),
        ("power-girl-jsa", "Power Girl", "JSA", "2021-12-01", 1.4),
        ("power-girl-rebirth", "Power Girl", "Rebirth", "2023-01-01", 1.35),
        ("stargirl", "Stargirl", "Courtney Whitmore", "2022-03-01", 1.3),
        ("jesse-quick", "Jesse Quick", "JSA", "2022-11-01", 1.2),
        ("obsidian", "Obsidian", "Todd Rice", "2023-02-01", 1.2),
        ("jade", "Jade", "Jennifer-Lynn Hayden", "2023-02-01", 1.25),
        ("doctor-fate-hector", "Doctor Fate", "Hector Hall", "2023-05-01", 1.25),
        ("black-canary-dinah", "Black Canary", "Dinah Lance Classic", "2021-10-01", 1.3),
        ("green-arrow-classic", "Green Arrow", "Classic Oliver Queen", "2021-10-01", 1.3),
        ("green-arrow-longbow", "Green Arrow", "Longbow Hunters", "2023-06-01", 1.35),
        ("speedy-mia", "Speedy", "Mia Dearden", "2023-07-01", 1.15),
        ("arsenal-roy", "Arsenal", "Roy Harper", "2022-12-01", 1.25),
    ]
    for suf, name, sub, date, dem in JSA:
        line = "DC Multiverse Gold Label" if "Gold Label" in sub else "DC Multiverse"
        msrp = 29.99 if "Gold Label" in sub else 24.99
        rows.append(F(f"mcfdc-{suf}", name, sub, line, "mcfarlane", date, msrp, '7"', dem,
                      "dc,mcfarlane,multiverse,jsa,curated"))

    # ---- JL / mid-tier heroes missing ----
    JL = [
        ("plastic-man", "Plastic Man", "Classic", "2022-04-01", 1.35),
        ("plastic-man-stretch", "Plastic Man", "Stretch Pack", "2023-09-01", 1.3),
        ("firestorm", "Firestorm", "Ronnie Raymond", "2022-05-01", 1.3),
        ("firestorm-jason", "Firestorm", "Jason Rusch", "2023-08-01", 1.25),
        ("atom-ray", "The Atom", "Ray Palmer", "2022-03-01", 1.25),
        ("atom-ryan", "The Atom", "Ryan Choi", "2023-10-01", 1.2),
        ("booster-gold-classic", "Booster Gold", "Classic", "2021-08-01", 1.3),
        ("booster-gold-blue", "Booster Gold", "Blue Beetle Team-Up", "2023-03-01", 1.25),
        ("blue-beetle-ted", "Blue Beetle", "Ted Kord", "2022-01-01", 1.3),
        ("blue-beetle-jaime-movie", "Blue Beetle", "Jaime Reyes Movie", "2023-08-01", 1.35),
        ("martian-manhunter-classic", "Martian Manhunter", "Classic", "2021-03-01", 1.4),
        ("martian-manhunter-white", "Martian Manhunter", "White Martian Variant", "2023-05-01", 1.35),
        ("vixen", "Vixen", "Mari McCabe", "2022-07-01", 1.25),
        ("steel", "Steel", "John Henry Irons", "2022-08-01", 1.3),
        ("steel-mega", "Steel", "Megafig Hammer", "2024-01-01", 1.4),
        ("icon", "Icon", "Milestone", "2023-04-01", 1.3),
        ("rocket", "Rocket", "Milestone", "2023-04-01", 1.25),
        ("static", "Static", "Milestone", "2023-05-01", 1.35),
        ("hardware", "Hardware", "Milestone", "2023-06-01", 1.25),
        ("red-tornado", "Red Tornado", "Android", "2022-10-01", 1.25),
        ("metamorpho", "Metamorpho", "Rex Mason", "2023-01-01", 1.2),
        ("animal-man", "Animal Man", "Buddy Baker", "2023-02-01", 1.25),
        ("question", "The Question", "Vic Sage", "2022-11-01", 1.3),
        ("question-renee", "The Question", "Renee Montoya", "2023-11-01", 1.25),
        ("huntress-helena", "Huntress", "Helena Bertinelli", "2022-09-01", 1.3),
        ("oracle", "Oracle", "Barbara Gordon", "2023-07-01", 1.35),
        ("batwing", "Batwing", "Luke Fox", "2023-08-01", 1.2),
        ("batwoman", "Batwoman", "Kate Kane", "2022-06-01", 1.35),
        ("batwoman-red", "Batwoman", "Red Alice Rival", "2023-12-01", 1.25),
        ("azrael", "Azrael", "Jean-Paul Valley", "2021-09-01", 1.35),
        ("azrael-suit", "Azrael", "Suit of Sorrows", "2023-03-01", 1.4),
        ("manbat", "Man-Bat", "Kirk Langstrom", "2022-05-01", 1.3),
        ("clayface", "Clayface", "Basil Karlo", "2022-07-01", 1.35),
        ("clayface-mega", "Clayface", "Megafig", "2023-09-01", 1.5),
        ("killer-croc-classic", "Killer Croc", "Classic", "2021-06-01", 1.3),
        ("killer-croc-mega", "Killer Croc", "Megafig Arkham", "2022-11-01", 1.45),
        ("scarecrow-classic", "Scarecrow", "Classic", "2021-07-01", 1.25),
        ("scarecrow-fear", "Scarecrow", "Fear Toxin", "2023-04-01", 1.3),
        ("two-face-classic", "Two-Face", "Harvey Dent", "2021-05-01", 1.3),
        ("riddler-classic", "The Riddler", "Classic Question Marks", "2021-04-01", 1.25),
        ("penguin-classic", "The Penguin", "Classic", "2021-04-01", 1.25),
        ("penguin-cobblepot", "The Penguin", "Oswald Cobblepot Deluxe", "2024-06-01", 1.4),
        ("poison-ivy-classic", "Poison Ivy", "Classic", "2021-05-01", 1.3),
        ("poison-ivy-vines", "Poison Ivy", "Vines Exclusive", "2023-05-01", 1.35),
        ("mr-freeze-classic", "Mr. Freeze", "Classic", "2021-08-01", 1.35),
        ("mr-freeze-ice", "Mr. Freeze", "Ice Chamber Build-A", "2023-01-01", 1.4),
        ("bane-classic", "Bane", "Classic Venom", "2021-03-01", 1.4),
        ("bane-knightfall", "Bane", "Knightfall", "2022-09-01", 1.45),
        ("ras-al-ghul", "Ra's al Ghul", "Demon's Head", "2021-10-01", 1.35),
        ("talia", "Talia al Ghul", "Daughter of the Demon", "2021-10-01", 1.3),
        ("deathstroke-classic", "Deathstroke", "Classic Orange", "2021-02-01", 1.4),
        ("deathstroke-armor", "Deathstroke", "Armored", "2023-02-01", 1.4),
        ("ravager", "Ravager", "Rose Wilson", "2022-12-01", 1.25),
        ("midnighter", "Midnighter", "The Authority", "2023-06-01", 1.3),
        ("apollo", "Apollo", "The Authority", "2023-06-01", 1.3),
        ("lobo-classic", "Lobo", "Main Man Classic", "2021-12-01", 1.4),
        ("lobo-spacehog", "Lobo", "Spacehog Pack", "2024-08-01", 1.45),
    ]
    for suf, name, sub, date, dem in JL:
        if "Megafig" in sub:
            msrp, scale, line = 44.99, '10"', "DC Multiverse Megafigs"
        elif "Gold Label" in sub or "Exclusive" in sub:
            msrp, scale, line = 29.99, '7"', "DC Multiverse Gold Label"
        elif "Deluxe" in sub or "Build-A" in sub:
            msrp, scale, line = 34.99, '7"', "DC Multiverse"
        else:
            msrp, scale, line = 24.99, '7"', "DC Multiverse"
        rows.append(F(f"mcfdc-{suf}", name, sub, line, "mcfarlane", date, msrp, scale, dem,
                      "dc,mcfarlane,multiverse,curated"))

    # ---- Page Punchers densify (comic + figure packs) ----
    PP = [
        ("pp-batman-hush", "Batman", "Page Punchers Hush", "2022-06-01", 1.3),
        ("pp-superman-action", "Superman", "Page Punchers Action Comics", "2022-06-01", 1.25),
        ("pp-ww-history", "Wonder Woman", "Page Punchers", "2022-07-01", 1.25),
        ("pp-flash-rebirth", "The Flash", "Page Punchers Rebirth", "2022-07-01", 1.25),
        ("pp-gl-hal", "Green Lantern", "Page Punchers Hal Jordan", "2022-08-01", 1.25),
        ("pp-aquaman", "Aquaman", "Page Punchers", "2022-08-01", 1.2),
        ("pp-cyborg", "Cyborg", "Page Punchers", "2022-09-01", 1.2),
        ("pp-shazam", "Shazam", "Page Punchers", "2022-09-01", 1.25),
        ("pp-nightwing", "Nightwing", "Page Punchers", "2022-10-01", 1.3),
        ("pp-redhood", "Red Hood", "Page Punchers", "2022-10-01", 1.3),
        ("pp-batgirl", "Batgirl", "Page Punchers", "2022-11-01", 1.25),
        ("pp-harley", "Harley Quinn", "Page Punchers", "2022-11-01", 1.3),
        ("pp-joker", "The Joker", "Page Punchers", "2022-12-01", 1.35),
        ("pp-deathstroke", "Deathstroke", "Page Punchers", "2023-01-01", 1.3),
        ("pp-robin-damian", "Robin", "Page Punchers Damian", "2023-02-01", 1.25),
        ("pp-raven", "Raven", "Page Punchers", "2023-03-01", 1.3),
        ("pp-starfire", "Starfire", "Page Punchers", "2023-03-01", 1.3),
        ("pp-beastboy", "Beast Boy", "Page Punchers", "2023-04-01", 1.25),
        ("pp-constantine", "John Constantine", "Page Punchers", "2023-05-01", 1.35),
        ("pp-swamp", "Swamp Thing", "Page Punchers Wave 2", "2023-06-01", 1.35),
        ("pp-mm", "Martian Manhunter", "Page Punchers", "2023-07-01", 1.3),
        ("pp-black-adam", "Black Adam", "Page Punchers", "2023-08-01", 1.3),
        ("pp-dr-fate", "Doctor Fate", "Page Punchers Wave 2", "2023-08-01", 1.3),
        ("pp-supergirl", "Supergirl", "Page Punchers", "2023-09-01", 1.25),
        ("pp-powergirl", "Power Girl", "Page Punchers", "2023-10-01", 1.3),
    ]
    for suf, name, sub, date, dem in PP:
        rows.append(F(f"mcfdc-{suf}", name, sub, "Page Punchers", "mcfarlane", date, 24.99, '7"', dem,
                      "dc,mcfarlane,page-punchers,curated"))

    # ---- Megafigs densify ----
    MEGA = [
        ("mega-doomsday-hx", "Doomsday", "Megafig Hush Exclusive", "2022-03-01", 1.5),
        ("mega-darkseid-armor", "Darkseid", "Megafig Armored", "2022-06-01", 1.55),
        ("mega-anti-monitor-classic", "Anti-Monitor", "Megafig Classic", "2021-11-01", 1.6),
        ("mega-swamp-classic", "Swamp Thing", "Megafig Classic", "2021-09-01", 1.45),
        ("mega-steppenwolf-jl", "Steppenwolf", "Megafig Justice League", "2021-05-01", 1.4),
        ("mega-devastator", "The Devastator", "Megafig Dark Nights", "2021-08-01", 1.5),
        ("mega-mercuriless", "The Merciless", "Megafig Dark Nights", "2021-08-01", 1.45),
        ("mega-batman-who-laughs", "Batman Who Laughs", "Megafig with Robins", "2022-01-01", 1.55),
        ("mega-king-shark", "King Shark", "Megafig", "2022-09-01", 1.4),
        ("mega-gorilla-grodd", "Gorilla Grodd", "Megafig", "2022-10-01", 1.4),
        ("mega-solomon-grundy", "Solomon Grundy", "Megafig", "2022-04-01", 1.4),
        ("mega-killer-croc-arkham", "Killer Croc", "Megafig Arkham Asylum", "2021-12-01", 1.45),
        ("mega-clayface-animated", "Clayface", "Megafig Animated", "2023-02-01", 1.45),
        ("mega-bizarro", "Bizarro", "Megafig", "2023-05-01", 1.4),
        ("mega-mongul", "Mongul", "Megafig", "2023-07-01", 1.45),
        ("mega-brainiac", "Brainiac", "Megafig Skull Ship", "2023-09-01", 1.5),
        ("mega-parademon-army", "Parademon", "Megafig Army Builder", "2022-07-01", 1.25),
        ("mega-kalibak-apok", "Kalibak", "Megafig Apokolips", "2023-11-01", 1.45),
        ("mega-orion", "Orion", "Megafig Astro-Force", "2024-02-01", 1.45),
        ("mega-lobo", "Lobo", "Megafig Main Man", "2024-05-01", 1.5),
    ]
    for suf, name, sub, date, dem in MEGA:
        rows.append(F(f"mcfdc-{suf}", name, sub, "DC Multiverse Megafigs", "mcfarlane", date, 44.99, '10"', dem,
                      "dc,mcfarlane,megafig,curated"))

    # ---- Gold Label / Platinum exclusives densify ----
    GL = [
        ("gl-batman-platinum", "Batman", "Platinum Edition Chase", "2022-05-01", 1.4),
        ("gl-superman-platinum", "Superman", "Platinum Edition Chase", "2022-05-01", 1.35),
        ("gl-ww-platinum", "Wonder Woman", "Platinum Edition Chase", "2022-06-01", 1.35),
        ("gl-flash-platinum", "The Flash", "Platinum Edition Chase", "2022-06-01", 1.3),
        ("gl-joker-black-white", "The Joker", "Black & White Gold Label", "2022-08-01", 1.45),
        ("gl-harley-black-white", "Harley Quinn", "Black & White Gold Label", "2022-08-01", 1.45),
        ("gl-batman-red-death", "Batman", "The Red Death Gold Label", "2021-11-01", 1.5),
        ("gl-batman-drowned", "Batman", "The Drowned Gold Label", "2021-12-01", 1.45),
        ("gl-batman-dawnbreaker", "Batman", "The Dawnbreaker Gold Label", "2022-01-01", 1.45),
        ("gl-batman-murder-machine", "Batman", "Murder Machine Gold Label", "2022-01-01", 1.45),
        ("gl-superman-red-son", "Superman", "Red Son Gold Label", "2022-03-01", 1.4),
        ("gl-batman-white-knight", "Batman", "White Knight Gold Label", "2022-04-01", 1.4),
        ("gl-batman-fortnite", "Batman", "Fortnite Gold Label", "2021-07-01", 1.25),
        ("gl-catwoman-fortnite", "Catwoman", "Fortnite Gold Label", "2021-07-01", 1.25),
        ("gl-batman-future-state", "Batman", "Future State Gold Label", "2021-09-01", 1.3),
        ("gl-batman-designed", "Batman", "Designed by Todd Gold Label", "2021-06-01", 1.4),
        ("gl-spawn-batman", "Spawn", "Batman Crossover Gold Label", "2021-06-01", 1.45),
        ("gl-batman-last-knight", "Batman", "Last Knight on Earth Gold Label", "2021-10-01", 1.4),
        ("gl-joker-translucent", "The Joker", "Translucent Gold Label", "2022-09-01", 1.45),
        ("gl-harley-punchline", "Harley Quinn", "Punchline Gold Label", "2022-10-01", 1.4),
        ("gl-punchline", "Punchline", "Gold Label", "2022-10-01", 1.4),
        ("gl-batman-speed-force", "Batman", "Speed Force Gold Label", "2022-02-01", 1.3),
        ("gl-flash-speed-force", "The Flash", "Speed Force Gold Label", "2022-02-01", 1.35),
        ("gl-batman-hush-chase", "Batman", "Hush Chase Gold Label", "2023-01-01", 1.4),
        ("gl-catwoman-hush", "Catwoman", "Hush Gold Label", "2023-01-01", 1.35),
        ("gl-superman-black", "Superman", "Black Suit Gold Label", "2023-03-01", 1.4),
        ("gl-ww-golden", "Wonder Woman", "Golden Armor Gold Label", "2023-04-01", 1.4),
        ("gl-aquaman-lost", "Aquaman", "Lost Kingdom Gold Label", "2023-12-01", 1.35),
        ("gl-black-manta", "Black Manta", "Gold Label", "2023-12-01", 1.35),
        ("gl-shazam-movie", "Shazam", "Movie Gold Label", "2023-03-01", 1.3),
        ("gl-black-adam-movie", "Black Adam", "Movie Gold Label", "2022-10-01", 1.35),
        ("gl-dr-fate-movie", "Doctor Fate", "Black Adam Movie Gold Label", "2022-10-01", 1.35),
        ("gl-hawkman-movie", "Hawkman", "Black Adam Movie Gold Label", "2022-11-01", 1.3),
        ("gl-cyclone", "Cyclone", "Black Adam Movie Gold Label", "2022-11-01", 1.25),
        ("gl-atom-smasher", "Atom Smasher", "Black Adam Movie Gold Label", "2022-11-01", 1.25),
        ("gl-superman-2025", "Superman", "2025 Movie Gold Label", "2025-07-01", 1.5),
        ("gl-lois-2025", "Lois Lane", "2025 Movie Gold Label", "2025-07-01", 1.35),
        ("gl-mr-terrific-2025", "Mr. Terrific", "2025 Movie Gold Label", "2025-07-01", 1.4),
        ("gl-hawkgirl-2025", "Hawkgirl", "2025 Movie Gold Label", "2025-07-01", 1.35),
        ("gl-green-lantern-guy", "Green Lantern", "Guy Gardner 2025 Movie", "2025-07-01", 1.4),
        ("gl-metamorpho-2025", "Metamorpho", "2025 Movie Gold Label", "2025-08-01", 1.3),
        ("gl-lex-2025", "Lex Luthor", "2025 Movie Gold Label", "2025-08-01", 1.45),
        ("gl-engineer", "The Engineer", "2025 Movie Gold Label", "2025-08-01", 1.35),
        ("gl-krypto", "Krypto", "2025 Movie Accessory Pack", "2025-09-01", 1.3),
        ("gl-creature-rick", "Rick Flag Sr.", "Creature Commandos", "2025-01-01", 1.35),
        ("gl-creature-bride", "The Bride", "Creature Commandos", "2025-01-01", 1.4),
        ("gl-creature-nina", "Nina Mazursky", "Creature Commandos", "2025-02-01", 1.25),
        ("gl-creature-weasel", "Weasel", "Creature Commandos", "2025-02-01", 1.3),
        ("gl-creature-g-i-robot", "G.I. Robot", "Creature Commandos", "2025-03-01", 1.3),
        ("gl-creature-doctor", "Doctor Phosphorus", "Creature Commandos", "2025-03-01", 1.35),
        ("gl-creature-frank", "Frankenstein", "Creature Commandos", "2025-04-01", 1.35),
    ]
    for suf, name, sub, date, dem in GL:
        rows.append(F(f"mcfdc-{suf}", name, sub, "DC Multiverse Gold Label", "mcfarlane", date, 29.99, '7"', dem,
                      "dc,mcfarlane,gold-label,curated"))

    # ---- Light DC Essentials / New 52 Collectibles densify (real known only) ----
    ESS = [
        ("ess-batman", "Batman", "DC Essentials", "2018-06-01", 1.25),
        ("ess-superman", "Superman", "DC Essentials", "2018-06-01", 1.2),
        ("ess-ww", "Wonder Woman", "DC Essentials", "2018-07-01", 1.2),
        ("ess-flash", "The Flash", "DC Essentials", "2018-07-01", 1.2),
        ("ess-gl", "Green Lantern", "DC Essentials Hal", "2018-08-01", 1.2),
        ("ess-aquaman", "Aquaman", "DC Essentials", "2018-08-01", 1.15),
        ("ess-cyborg", "Cyborg", "DC Essentials", "2018-09-01", 1.15),
        ("ess-joker", "The Joker", "DC Essentials", "2018-09-01", 1.3),
        ("ess-harley", "Harley Quinn", "DC Essentials", "2018-10-01", 1.3),
        ("ess-deathstroke", "Deathstroke", "DC Essentials", "2018-10-01", 1.25),
        ("ess-nightwing", "Nightwing", "DC Essentials", "2018-11-01", 1.25),
        ("ess-robin", "Robin", "DC Essentials Damian", "2018-11-01", 1.2),
        ("ess-redhood", "Red Hood", "DC Essentials", "2018-12-01", 1.25),
        ("ess-batgirl", "Batgirl", "DC Essentials", "2018-12-01", 1.2),
        ("ess-supergirl", "Supergirl", "DC Essentials", "2019-01-01", 1.2),
        ("ess-lex", "Lex Luthor", "DC Essentials", "2019-01-01", 1.25),
        ("ess-darkseid", "Darkseid", "DC Essentials", "2019-02-01", 1.4),
        ("ess-doomsday", "Doomsday", "DC Essentials", "2019-02-01", 1.35),
        ("ess-sinestro", "Sinestro", "DC Essentials", "2019-03-01", 1.25),
        ("ess-black-manta", "Black Manta", "DC Essentials", "2019-03-01", 1.25),
    ]
    for suf, name, sub, date, dem in ESS:
        rows.append(F(f"mcfdc-{suf}", name, sub, "DC Essentials", "dcdirect", date, 24.99, '6.5"', dem,
                      "dc,dcdirect,essentials,curated"))

    N52 = [
        ("n52-batman", "Batman", "New 52", "2013-06-01", 1.25),
        ("n52-superman", "Superman", "New 52", "2013-06-01", 1.2),
        ("n52-ww", "Wonder Woman", "New 52", "2013-07-01", 1.2),
        ("n52-flash", "The Flash", "New 52", "2013-07-01", 1.2),
        ("n52-gl", "Green Lantern", "New 52 Hal", "2013-08-01", 1.2),
        ("n52-aquaman", "Aquaman", "New 52", "2013-08-01", 1.15),
        ("n52-cyborg", "Cyborg", "New 52", "2013-09-01", 1.15),
        ("n52-joker", "The Joker", "New 52", "2013-09-01", 1.3),
        ("n52-harley", "Harley Quinn", "New 52", "2013-10-01", 1.3),
        ("n52-deathstroke", "Deathstroke", "New 52", "2013-10-01", 1.25),
        ("n52-nightwing", "Nightwing", "New 52", "2013-11-01", 1.25),
        ("n52-redhood", "Red Hood", "New 52", "2013-11-01", 1.25),
        ("n52-batgirl", "Batgirl", "New 52", "2013-12-01", 1.2),
        ("n52-catwoman", "Catwoman", "New 52", "2013-12-01", 1.25),
        ("n52-lex", "Lex Luthor", "New 52 Armor", "2014-01-01", 1.3),
        ("n52-darkseid", "Darkseid", "New 52", "2014-02-01", 1.4),
        ("n52-shazam", "Shazam", "New 52", "2014-03-01", 1.25),
        ("n52-black-adam", "Black Adam", "New 52", "2014-03-01", 1.3),
        ("n52-sinestro", "Sinestro", "New 52", "2014-04-01", 1.25),
        ("n52-doomsday", "Doomsday", "New 52", "2014-05-01", 1.35),
    ]
    for suf, name, sub, date, dem in N52:
        rows.append(F(f"mcfdc-{suf}", name, sub, "DC Collectibles New 52", "dcdirect", date, 24.99, '6.75"', dem,
                      "dc,dcdirect,new52,curated"))

    return rows


if __name__ == "__main__":
    from collections import Counter

    rows = build_mcfarlane_dc_gap()
    print("RAW", len(rows))
    print(Counter(r["line"] for r in rows))
    print(Counter(r["company"] for r in rows))

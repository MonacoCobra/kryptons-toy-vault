"""Real Mattel DC Universe Classics fills missing from oneshot.

Source: Wikipedia "DC Universe Classics" wave tables (verified 2026-09).
Only characters absent from current archive by name+line key.
Floor 1980. No imageUrl / no AI art.
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
        "source": "curated-dcuc-real-fill",
    }


def build_dcuc_real_fill() -> list[dict]:
    rows: list[dict] = []
    # (suffix, name, subtitle, date, demand) — real retail DCUC waves
    DCUC = [
        # Wave 1 Metamorpho CnC — Metamorpho may exist under wrong wave; add CnC SKU
        ("metamorpho-cnc-w1", "Metamorpho", "Collect & Connect Wave 1", "2008-01-01", 1.45),
        # Wave 2 Grodd — Black Manta missing as DCUC
        ("black-manta-w2", "Black Manta", "Wave 2", "2008-03-01", 1.4),
        ("firestorm-ronnie-w2", "Firestorm", "Ronnie Raymond Wave 2", "2008-03-01", 1.35),
        ("superman-red-w2", "Superman", "Superman Red Wave 2", "2008-03-01", 1.3),
        ("superman-blue-w2", "Superman", "Superman Blue Wave 2", "2008-03-01", 1.3),
        ("harley-w2", "Harley Quinn", "Wave 2", "2008-03-01", 1.55),
        # Wave 4 Despero
        ("despero-cnc-w4", "Despero", "Collect & Connect Wave 4", "2008-09-01", 1.55),
        ("ares-w4", "Ares", "Wave 4", "2008-09-01", 1.4),
        ("artemis-w4", "Artemis", "Wave 4 Variant", "2008-09-01", 1.35),
        ("captain-atom-w4", "Captain Atom", "Wave 4", "2008-09-01", 1.35),
        ("captain-atom-kc-w4", "Captain Atom", "Kingdom Come Wave 4", "2008-09-01", 1.4),
        ("cyborg-sp-w4", "Cyborg", "Super Powers Arm Wave 4", "2008-09-01", 1.35),
        # Wave 5 Walmart Metallo
        ("amazo-w5", "Amazo", "Wave 5 Walmart", "2008-11-01", 1.4),
        ("atom-ray-w5", "The Atom", "Ray Palmer Wave 5", "2008-11-01", 1.3),
        ("eradicator-w5", "Eradicator", "Wave 5 Walmart", "2008-11-01", 1.35),
        # Wave 6 Kalibak
        ("kalibak-cnc-w6", "Kalibak", "Collect & Connect Wave 6", "2009-01-01", 1.5),
        ("dr-impossible-w6", "Doctor Impossible", "Wave 6 Variant", "2009-01-01", 1.25),
        ("hawkman-w6", "Hawkman", "Wave 6", "2009-01-01", 1.4),
        ("killer-moth-w6", "Killer Moth", "Wave 6", "2009-01-01", 1.2),
        ("shazam-w6", "Shazam", "Wave 6", "2009-01-01", 1.4),
        # Wave 7 Atom Smasher
        ("atom-smasher-cnc-w7", "Atom Smasher", "Collect & Connect Wave 7", "2009-03-01", 1.5),
        ("kid-flash-w7", "Kid Flash", "Wally West Wave 7", "2009-03-01", 1.35),
        ("blue-beetle-ted-w7", "Blue Beetle", "Ted Kord Wave 7", "2009-03-01", 1.4),
        ("captain-cold-w7", "Captain Cold", "Wave 7", "2009-03-01", 1.3),
        ("aquaman-ocean-w7", "Aquaman", "Ocean Warrior Wave 7", "2009-03-01", 1.3),
        # Wave 8 Giganta
        ("giganta-cnc-w8", "Giganta", "Collect & Connect Wave 8", "2009-05-01", 1.5),
        ("commander-steel-w8", "Commander Steel", "Wave 8", "2009-05-01", 1.25),
        ("mister-terrific-w8", "Mister Terrific", "Wave 8", "2009-05-01", 1.3),
        ("vigilante-w8", "Vigilante", "Wave 8", "2009-05-01", 1.25),
        ("parademon-comic-w8", "Parademon", "Comics Wave 8", "2009-05-01", 1.3),
        ("parademon-sp-w8", "Parademon", "Super Powers Wave 8", "2009-05-01", 1.3),
        ("gentleman-ghost-w8", "Gentleman Ghost", "Wave 8", "2009-05-01", 1.35),
        ("dr-fate-hector-w8", "Doctor Fate", "Hector Hall Wave 8", "2009-05-01", 1.35),
        # Wave 9 Chemo
        ("chemo-cnc-w9", "Chemo", "Collect & Connect Wave 9", "2009-08-01", 1.55),
        ("wildcat-black-w9", "Wildcat", "Black Costume Wave 9", "2009-08-01", 1.3),
        ("wildcat-blue-w9", "Wildcat", "Blue Costume Wave 9", "2009-08-01", 1.3),
        ("deadshot-w9", "Deadshot", "Wave 9", "2009-08-01", 1.4),
        ("mantis-comic-w9", "Mantis", "Comics Wave 9", "2009-08-01", 1.25),
        ("mantis-sp-w9", "Mantis", "Super Powers Wave 9", "2009-08-01", 1.25),
        # Wave 10 Imperiex Walmart
        ("robotman-w10", "Robotman", "Wave 10 Walmart", "2009-10-01", 1.3),
        ("forager-w10", "Forager", "Wave 10 Walmart", "2009-10-01", 1.25),
        # Wave 11 Kilowog
        ("katma-tui-w11", "Katma Tui", "Wave 11", "2009-12-01", 1.35),
        ("shark-w11", "Shark", "Wave 11", "2009-12-01", 1.25),
        ("question-w11", "The Question", "Wave 11", "2009-12-01", 1.45),
        ("gl-john-w11", "Green Lantern", "John Stewart Wave 11", "2009-12-01", 1.4),
        ("steppenwolf-comic-w11", "Steppenwolf", "Comics Wave 11", "2009-12-01", 1.35),
        ("steppenwolf-sp-w11", "Steppenwolf", "Super Powers Wave 11", "2009-12-01", 1.35),
        # Wave 12 Darkseid
        ("copperhead-w12", "Copperhead", "Wave 12", "2010-02-01", 1.3),
        ("dr-midnite-w12", "Doctor Mid-Nite", "Wave 12", "2010-02-01", 1.25),
        ("iron-metalmen-w12", "Iron", "Metal Men Wave 12", "2010-02-01", 1.2),
        # Wave 13 Trigon
        ("negative-man-w13", "Negative Man", "Wave 13", "2010-04-01", 1.35),
        ("negative-man-unbandaged-w13", "Negative Man", "Unbandaged Wave 13", "2010-04-01", 1.35),
        ("cyclotron-w13", "Cyclotron", "Wave 13", "2010-04-01", 1.3),
        ("blue-devil-w13", "Blue Devil", "Wave 13", "2010-04-01", 1.3),
        ("donna-troy-w13", "Donna Troy", "Wave 13", "2010-04-01", 1.35),
        ("blue-beetle-jaime-w13", "Blue Beetle", "Jaime Reyes Wave 13", "2010-04-01", 1.35),
        # Wave 14 Ultra-Humanite Walmart
        ("kamandi-w14", "Kamandi", "Wave 14 Walmart", "2010-06-01", 1.35),
        ("obsidian-w14", "Obsidian", "Wave 14 Walmart", "2010-06-01", 1.3),
        ("tyr-w14", "Tyr", "Wave 14 Walmart", "2010-06-01", 1.25),
        ("gold-metalmen-w14", "Gold", "Metal Men Wave 14", "2010-06-01", 1.2),
        ("hourman-rex-w14", "Hourman", "Rex Tyler Wave 14", "2010-06-01", 1.3),
        # Wave 15 Validus
        ("validus-cnc-w15", "Validus", "Collect & Connect Wave 15", "2010-10-01", 1.55),
        ("golden-pharaoh-w15", "Golden Pharaoh", "Wave 15", "2010-10-01", 1.3),
        ("omac-w15", "OMAC", "Wave 15", "2010-10-01", 1.35),
        ("jemm-w15", "Jemm", "Son of Saturn Wave 15", "2010-10-01", 1.3),
        ("starman-ted-w15", "Starman", "Ted Knight Wave 15", "2010-10-01", 1.35),
        ("starman-jack-w15", "Starman", "Jack Knight Wave 15", "2010-10-01", 1.4),
        # Wave 16 Bane
        ("jonah-hex-w16", "Jonah Hex", "Wave 16", "2010-12-01", 1.4),
        ("creeper-w16", "The Creeper", "Wave 16", "2010-12-01", 1.35),
        ("mercury-metalmen-w16", "Mercury", "Metal Men Wave 16", "2010-12-01", 1.2),
        ("batman-azrael-w16", "Batman", "Jean-Paul Valley Wave 16", "2010-12-01", 1.4),
        ("robin-dick-w16", "Robin", "Dick Grayson Wave 16", "2010-12-01", 1.35),
        # Wave 17 Anti-Monitor (Blackest Night)
        ("antimonitor-cnc-w17", "Anti-Monitor", "Collect & Connect Wave 17", "2011-02-01", 1.7),
        ("ww-star-sapphire-w17", "Wonder Woman", "Star Sapphire Wave 17", "2011-02-01", 1.45),
        ("scarecrow-sinestro-w17", "Scarecrow", "Sinestro Corps Wave 17", "2011-02-01", 1.35),
        ("flash-blue-lantern-w17", "The Flash", "Blue Lantern Wave 17", "2011-02-01", 1.4),
        ("atom-indigo-w17", "The Atom", "Indigo Tribe Wave 17", "2011-02-01", 1.3),
        ("lex-orange-w17", "Lex Luthor", "Orange Lantern Wave 17", "2011-02-01", 1.4),
        ("hal-black-lantern-w17", "Green Lantern", "Black Lantern Hal Wave 17", "2011-02-01", 1.45),
        ("hal-white-lantern-w17", "Green Lantern", "White Lantern Hal Wave 17", "2011-02-01", 1.5),
        # Wave 18 Apache Chief
        ("apache-chief-cnc-w18", "Apache Chief", "Collect & Connect Wave 18", "2011-05-01", 1.5),
        ("black-vulcan-w18", "Black Vulcan", "Wave 18", "2011-05-01", 1.3),
        ("el-dorado-w18", "El Dorado", "Wave 18", "2011-05-01", 1.3),
        ("toyman-w18", "Toyman", "Wave 18", "2011-05-01", 1.25),
        ("captain-boomerang-w18", "Captain Boomerang", "Wave 18", "2011-05-01", 1.3),
        ("samurai-w18", "Samurai", "Wave 18", "2011-05-01", 1.3),
        ("bronze-tiger-w18", "Bronze Tiger", "Wave 18", "2011-05-01", 1.35),
        # Wave 19 S.T.R.I.P.E.
        ("stripe-cnc-w19", "S.T.R.I.P.E.", "Collect & Connect Wave 19", "2011-08-01", 1.5),
        ("sandman-wesley-w19", "Sandman", "Wesley Dodds Wave 19", "2011-08-01", 1.35),
        ("atom-al-pratt-w19", "The Atom", "Al Pratt Wave 19", "2011-08-01", 1.25),
        ("stargirl-w19", "Stargirl", "Wave 19", "2011-08-01", 1.35),
        ("lord-naga-w19", "Lord Naga", "Wave 19", "2011-08-01", 1.2),
        ("hawkman-golden-w19", "Hawkman", "Golden Age Wave 19", "2011-08-01", 1.35),
        ("magog-w19", "Magog", "Wave 19", "2011-08-01", 1.4),
        # Wave 20 Nekron
        ("hawk-w20", "Hawk", "Wave 20", "2011-11-01", 1.3),
        ("dove-w20", "Dove", "Dawn Granger Wave 20", "2011-11-01", 1.3),
        ("red-arrow-w20", "Red Arrow", "Wave 20", "2011-11-01", 1.3),
        ("green-arrow-bd-w20", "Green Arrow", "Brightest Day Wave 20", "2011-11-01", 1.35),
        ("flash-white-lantern-w20", "The Flash", "White Lantern Wave 20", "2011-11-01", 1.4),
        ("reverse-flash-w20", "Reverse-Flash", "Wave 20", "2011-11-01", 1.45),
        # Exclusives / All-Stars / packs (real releases)
        ("lightray-tru", "Lightray", "TRU New Gods Pack", "2008-11-01", 1.3),
        ("abin-sur-tru", "Abin Sur", "TRU Green Lantern Pack", "2008-11-01", 1.35),
        ("adam-strange-matty", "Adam Strange", "Matty Space Heroes", "2009-01-01", 1.35),
        ("starfire-matty", "Starfire", "Matty Space Heroes", "2009-01-01", 1.4),
        ("ultraman-matty", "Ultraman", "Matty Earth-3", "2009-06-01", 1.4),
        ("alexander-luthor-matty", "Alexander Luthor", "Matty Earth-3", "2009-06-01", 1.3),
        ("animal-man-matty", "Animal Man", "Matty Jungle", "2009-12-01", 1.35),
        ("bwana-beast-matty", "B'wana Beast", "Matty Jungle", "2009-12-01", 1.25),
        ("plastic-man-sdcc", "Plastic Man", "SDCC 2010 Exclusive", "2010-07-01", 1.55),
        ("swamp-thing-sdcc", "Swamp Thing", "SDCC 2011 Exclusive", "2011-07-01", 1.55),
        ("guy-gardner-wm", "Green Lantern", "Guy Gardner Walmart 5-Pack", "2010-09-01", 1.35),
        ("tomar-re-wm", "Tomar-Re", "Walmart 5-Pack", "2010-09-01", 1.3),
        ("owlman-csa", "Owlman", "Crime Syndicate Walmart", "2011-07-01", 1.4),
        ("superwoman-csa", "Superwoman", "Crime Syndicate Walmart", "2011-07-01", 1.35),
        ("johnny-quick-csa", "Johnny Quick", "Crime Syndicate Walmart", "2011-07-01", 1.3),
        ("power-ring-csa", "Power Ring", "Crime Syndicate Walmart", "2011-07-01", 1.3),
        # Legion 12-pack (Matty)
        ("legion-cosmic-boy", "Cosmic Boy", "Legion 12-Pack Matty", "2011-09-01", 1.3),
        ("legion-lightning-lad", "Lightning Lad", "Legion 12-Pack Matty", "2011-09-01", 1.3),
        ("legion-saturn-girl", "Saturn Girl", "Legion 12-Pack Matty", "2011-09-01", 1.3),
        ("legion-brainiac5", "Brainiac 5", "Legion 12-Pack Matty", "2011-09-01", 1.35),
        ("legion-chameleon-boy", "Chameleon Boy", "Legion 12-Pack Matty", "2011-09-01", 1.25),
        ("legion-ultra-boy", "Ultra Boy", "Legion 12-Pack Matty", "2011-09-01", 1.3),
        ("legion-karate-kid", "Karate Kid", "Legion 12-Pack Matty", "2011-09-01", 1.25),
        ("legion-wildfire", "Wildfire", "Legion 12-Pack Matty", "2011-09-01", 1.3),
        ("legion-matter-eater", "Matter-Eater Lad", "Legion 12-Pack Matty", "2011-09-01", 1.2),
        ("legion-timber-wolf", "Timber Wolf", "Legion 12-Pack Matty", "2011-09-01", 1.3),
        ("legion-colossal-boy", "Colossal Boy", "Legion 12-Pack Matty", "2011-09-01", 1.25),
        # Club Infinite Earths select missing
        ("cie-metron", "Metron", "Club Infinite Earths", "2012-06-01", 1.5),
        ("cie-atrocitus", "Atrocitus", "Club Infinite Earths", "2012-06-01", 1.45),
        ("cie-jay-garrick", "The Flash", "Jay Garrick Club Infinite Earths", "2012-05-01", 1.4),
        ("cie-rocket-red", "Rocket Red", "Club Infinite Earths Oversized", "2012-07-01", 1.4),
        ("cie-mirror-master", "Mirror Master", "Club Infinite Earths", "2012-08-01", 1.35),
        ("cie-black-mask", "Black Mask", "Club Infinite Earths", "2012-09-01", 1.35),
        ("cie-uncle-sam", "Uncle Sam", "Club Infinite Earths", "2012-11-01", 1.3),
        ("cie-elasti-girl", "Elasti-Girl", "Club Infinite Earths Oversized", "2012-10-01", 1.35),
        ("cie-saint-walker", "Saint Walker", "Club Infinite Earths 2013", "2013-01-01", 1.35),
        ("cie-phantom-stranger", "Phantom Stranger", "Club Infinite Earths 2013", "2013-02-01", 1.3),
        ("cie-elongated-man", "Elongated Man", "Club Infinite Earths 2013", "2013-03-01", 1.3),
        ("cie-larfleeze", "Larfleeze", "Club Infinite Earths 2013", "2013-04-01", 1.45),
        ("cie-mallah", "Monsieur Mallah", "Club Infinite Earths Exclusive", "2013-04-01", 1.4),
        ("cie-wally-west", "The Flash", "Wally West Club Infinite Earths", "2013-05-01", 1.4),
        ("cie-red-hood", "Red Hood", "Club Infinite Earths 2013", "2013-06-01", 1.45),
        ("cie-captain-marvel-jr", "Captain Marvel Jr.", "Club Infinite Earths 2013", "2013-07-01", 1.3),
        ("cie-fire", "Fire", "Club Infinite Earths 2013", "2013-08-01", 1.25),
        ("cie-huntress", "Huntress", "Helena Bertinelli Club Infinite Earths", "2013-09-01", 1.35),
        ("cie-ice", "Ice", "Club Infinite Earths 2014", "2014-06-01", 1.25),
        ("cie-damian", "Robin", "Damian Wayne Club Infinite Earths", "2014-12-01", 1.4),
        ("cie-doomsday-unleashed", "Doomsday", "Doomsday Unleashed Final Figure", "2015-01-01", 1.6),
    ]
    for suf, name, sub, date, dem in DCUC:
        rows.append(
            F(
                f"dcucf-{suf}",
                name,
                sub,
                "DC Universe Classics",
                "mattel",
                date,
                12.99,
                '6"',
                dem,
                "dc,dcuc,mattel,curated,real-fill",
            )
        )
    return rows


if __name__ == "__main__":
    from collections import Counter

    rows = build_dcuc_real_fill()
    print("RAW", len(rows))
    print(Counter(r["line"] for r in rows))

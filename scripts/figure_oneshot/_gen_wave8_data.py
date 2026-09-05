#!/usr/bin/env python3
"""Generate bbts_wave8_data.json — BBTS AF brand expansion wave 8."""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).with_name("bbts_wave8_data.json")

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
# Asmus Toys — LOTR / Hobbit / Witcher 1:6
add(data, "asmus", "as", [
    ("Aragorn", "Fellowship", 1.55), ("Legolas", "Fellowship", 1.5), ("Gimli", "Fellowship", 1.45),
    ("Frodo", "Fellowship", 1.45), ("Samwise", "Fellowship", 1.4), ("Gandalf the Grey", "Fellowship", 1.55),
    ("Gandalf the White", "Return of the King", 1.55), ("Boromir", "Fellowship", 1.45),
    ("Merry", "Fellowship", 1.3), ("Pippin", "Fellowship", 1.3), ("Arwen", "Fellowship", 1.4),
    ("Elrond", "Fellowship", 1.35), ("Galadriel", "Fellowship", 1.4), ("Saruman", "Two Towers", 1.5),
    ("Gollum", "Two Towers", 1.5), ("Smeagol", "Two Towers", 1.45), ("Faramir", "Two Towers", 1.35),
    ("Eowyn", "Two Towers", 1.45), ("Theoden", "Two Towers", 1.4), ("Eomer", "Two Towers", 1.35),
    ("Denethor", "Return of the King", 1.3), ("King of the Dead", "Return of the King", 1.4),
    ("Witch-king", "Return of the King", 1.55), ("Mouth of Sauron", "Return of the King", 1.35),
    ("Lurtz", "Fellowship", 1.45), ("Uruk-Hai", "Two Towers", 1.3), ("Orc Overseer", "Fellowship", 1.25),
    ("Bilbo Baggins", "Hobbit", 1.4), ("Thorin Oakenshield", "Hobbit", 1.5), ("Balin", "Hobbit", 1.3),
    ("Dwalin", "Hobbit", 1.3), ("Kili", "Hobbit", 1.35), ("Fili", "Hobbit", 1.35),
    ("Smaug", "Hobbit Deluxe", 1.55, 450), ("Azog", "Hobbit", 1.45), ("Bolg", "Hobbit", 1.4),
    ("Tauriel", "Hobbit", 1.4), ("Thranduil", "Hobbit", 1.45), ("Bard the Bowman", "Hobbit", 1.35),
    ("Geralt of Rivia", "Witcher", 1.55), ("Ciri", "Witcher", 1.5), ("Yennefer", "Witcher", 1.5),
    ("Triss Merigold", "Witcher", 1.4), ("Eredin", "Witcher", 1.4), ("Vesemir", "Witcher", 1.35),
], 2014, 2, 2, 280)

# HeroCross — Hybrid Metal Figuration / TF AF
add(data, "herocross", "hx", [
    ("HMF Optimus Prime", "Hybrid Metal", 1.55, 180), ("HMF Megatron", "Hybrid Metal", 1.55, 180),
    ("HMF Bumblebee", "Hybrid Metal", 1.5, 150), ("HMF Starscream", "Hybrid Metal", 1.45, 150),
    ("HMF Soundwave", "Hybrid Metal", 1.5, 160), ("HMF Ironhide", "Hybrid Metal", 1.4, 145),
    ("HMF Jazz", "Hybrid Metal", 1.4, 140), ("HMF Ratchet", "Hybrid Metal", 1.35, 140),
    ("HMF Grimlock", "Hybrid Metal", 1.55, 200), ("HMF Shockwave", "Hybrid Metal", 1.45, 155),
    ("HMF Hot Rod", "Hybrid Metal", 1.4, 145), ("HMF Ultra Magnus", "Hybrid Metal", 1.5, 190),
    ("HMF Galvatron", "Hybrid Metal", 1.5, 185), ("HMF Rodimus", "Hybrid Metal", 1.45, 170),
    ("HMF Devastator", "Hybrid Metal Combiner", 1.55, 380), ("HMF Superion", "Hybrid Metal Combiner", 1.5, 360),
    ("HMF Menasor", "Hybrid Metal Combiner", 1.5, 360), ("HMF Predaking", "Hybrid Metal Combiner", 1.55, 400),
    ("HMF Optimus Prime Black", "Special", 1.5, 200), ("HMF Megatron Chrome", "Special", 1.5, 200),
    ("HMF Bumblebee Gold", "Special", 1.45, 170), ("HMF Starscream Ghost", "Special", 1.45, 165),
    ("HMF Soundwave Blue", "Special", 1.45, 175), ("HMF Grimlock Metallic", "Special", 1.55, 220),
    ("HMF Optimus Movie", "Movie", 1.5, 190), ("HMF Bumblebee Movie", "Movie", 1.45, 160),
    ("HMF Megatron Movie", "Movie", 1.5, 190), ("HMF Barricade", "Movie", 1.35, 140),
    ("HMF Ironhide Movie", "Movie", 1.4, 150), ("HMF Ratchet Movie", "Movie", 1.35, 145),
    ("HMF Sideswipe", "Movie", 1.35, 140), ("HMF Lockdown", "Movie", 1.4, 155),
    ("HMF Drift", "Movie", 1.35, 145), ("HMF Hound", "Movie", 1.3, 140),
    ("HMF Mini Optimus", "Mini", 1.25, 55), ("HMF Mini Megatron", "Mini", 1.25, 55),
    ("HMF Mini Bumblebee", "Mini", 1.2, 50), ("HMF Mini Starscream", "Mini", 1.2, 50),
    ("HMF Optimus Clear", "Special", 1.45, 195), ("HMF Devastator Limb Pack", "Combiner", 1.3, 80),
    ("HMF Superion Limb Pack", "Combiner", 1.3, 80), ("HMF Upgrade Kit", "Special", 1.25, 45),
    ("HMF Soundwave Cassettes", "Special", 1.4, 90), ("HMF Reflector Set", "Special", 1.35, 120),
    ("HMF Dinobot Pack", "Special", 1.45, 250),
], 2015, 3, 2, 150)

# Fans Hobby — 3P Masterpiece TF
add(data, "fanshobby", "fhb", [
    ("MB-01 Athena", "Master Builder", 1.5, 220), ("MB-02 Power Baser", "Master Builder", 1.45, 200),
    ("MB-03 Quakewave", "Master Builder", 1.4, 180), ("MB-04 War Giant", "Master Builder", 1.55, 280),
    ("MB-05 God Feather", "Master Builder", 1.5, 240), ("MB-06 Jet", "Master Builder", 1.4, 170),
    ("MB-07 Blue", "Master Builder", 1.35, 160), ("MB-08 Red", "Master Builder", 1.35, 160),
    ("MB-09 Yellow", "Master Builder", 1.35, 160), ("MB-10 Purple", "Master Builder", 1.35, 160),
    ("MB-11 Green", "Master Builder", 1.3, 155), ("MB-12 Black", "Master Builder", 1.4, 175),
    ("MB-13 Commander", "Master Builder", 1.5, 230), ("MB-14 Warrior", "Master Builder", 1.4, 180),
    ("MB-15 Scout", "Master Builder", 1.35, 150), ("MB-16 Medic", "Master Builder", 1.3, 145),
    ("MB-17 Heavy", "Master Builder", 1.4, 185), ("MB-18 Flyer", "Master Builder", 1.4, 175),
    ("MB-19 Triple", "Master Builder", 1.45, 200), ("MB-20 City", "Master Builder", 1.5, 250),
    ("MB Athena Chrome", "Special", 1.55, 250), ("MB Power Baser Desert", "Special", 1.45, 210),
    ("MB Quakewave Ghost", "Special", 1.4, 195), ("MB War Giant Metallic", "Special", 1.55, 300),
    ("MB God Feather Clear", "Special", 1.5, 260), ("MB Commander Black", "Special", 1.5, 245),
    ("MB Combiner A", "Combiner", 1.35, 90), ("MB Combiner B", "Combiner", 1.3, 85),
    ("MB Combiner C", "Combiner", 1.3, 85), ("MB Combiner D", "Combiner", 1.3, 85),
    ("MB Combiner E", "Combiner", 1.3, 85), ("MB Combiner Complete", "Combiner", 1.55, 400),
    ("MB Mini Athena", "Mini", 1.25, 50), ("MB Mini Commander", "Mini", 1.25, 50),
    ("MB Mini Warrior", "Mini", 1.2, 45), ("MB Upgrade Pack", "Special", 1.25, 55),
    ("MB Cassette Pack", "Special", 1.3, 60), ("MB City Fortress", "Special", 1.5, 320),
    ("MB Triple Changer Ghost", "Special", 1.45, 220), ("MB Flyer Spec Ops", "Special", 1.4, 190),
    ("MB Scout Night", "Special", 1.3, 160), ("MB Heavy Chrome", "Special", 1.45, 200),
    ("MB Medic Desert", "Special", 1.3, 155), ("MB Warrior Metallic", "Special", 1.4, 195),
    ("MB Athena Clear", "Special", 1.5, 240),
], 2016, 4, 2, 180)

# FansProject — 3P TF classic
add(data, "fansproject", "fp", [
    ("Causality Warbot", "Causality", 1.45, 160), ("Causality Broadside", "Causality", 1.4, 150),
    ("Causality Quake", "Causality", 1.35, 140), ("Causality Trailer", "Causality", 1.4, 155),
    ("Causality Jet", "Causality", 1.4, 145), ("Causality Tank", "Causality", 1.35, 140),
    ("Function X1", "Function X", 1.45, 170), ("Function X2", "Function X", 1.4, 160),
    ("Function X3", "Function X", 1.4, 160), ("Function X4", "Function X", 1.35, 150),
    ("Function X5", "Function X", 1.35, 150), ("Function X Complete", "Function X", 1.55, 380),
    ("Convobat", "Named", 1.5, 180), ("Carmine", "Named", 1.4, 150),
    ("Explorer", "Named", 1.35, 140), ("Smart Robin", "Named", 1.4, 145),
    ("Seacon A", "Seacon", 1.35, 90), ("Seacon B", "Seacon", 1.3, 85),
    ("Seacon C", "Seacon", 1.3, 85), ("Seacon D", "Seacon", 1.3, 85),
    ("Seacon E", "Seacon", 1.3, 85), ("Seacon F", "Seacon", 1.3, 85),
    ("Seacon Complete", "Seacon", 1.55, 420), ("Crossfire", "Named", 1.4, 155),
    ("Empress", "Named", 1.45, 170), ("Ironhide Homage", "Named", 1.4, 160),
    ("Ratchet Homage", "Named", 1.35, 155), ("Prowl Homage", "Named", 1.4, 150),
    ("Jazz Homage", "Named", 1.4, 150), ("Mirage Homage", "Named", 1.35, 145),
    ("Causality Chrome", "Special", 1.5, 190), ("Function X Ghost", "Special", 1.45, 180),
    ("Convobat Clear", "Special", 1.5, 200), ("Seacon Metallic", "Special", 1.5, 450),
    ("Mini Causality", "Mini", 1.25, 45), ("Mini Convobat", "Mini", 1.25, 45),
    ("Mini Function", "Mini", 1.2, 40), ("Upgrade Pack A", "Special", 1.25, 50),
    ("Upgrade Pack B", "Special", 1.25, 50), ("Causality Desert", "Special", 1.4, 165),
    ("Explorer Night", "Special", 1.35, 150), ("Crossfire Spec Ops", "Special", 1.4, 165),
    ("Empress Chrome", "Special", 1.45, 185), ("Ironhide Homage Black", "Special", 1.4, 170),
    ("Jazz Homage Gold", "Special", 1.4, 165),
], 2014, 5, 2, 150)

# TransArt Toys — 3P Beast / combiner
add(data, "transart", "ta", [
    ("BWM-01 Lion", "Beast Wars Metal", 1.5, 140), ("BWM-02 Tiger", "Beast Wars Metal", 1.45, 130),
    ("BWM-03 Panther", "Beast Wars Metal", 1.4, 125), ("BWM-04 Cheetah", "Beast Wars Metal", 1.45, 130),
    ("BWM-05 Wolf", "Beast Wars Metal", 1.4, 120), ("BWM-06 Eagle", "Beast Wars Metal", 1.45, 135),
    ("BWM-07 Raptor", "Beast Wars Metal", 1.5, 145), ("BWM-08 Gorilla", "Beast Wars Metal", 1.5, 150),
    ("BWM-09 Rhino", "Beast Wars Metal", 1.4, 130), ("BWM-10 Scorpion", "Beast Wars Metal", 1.4, 125),
    ("BWM-11 Snake", "Beast Wars Metal", 1.35, 120), ("BWM-12 Rat", "Beast Wars Metal", 1.3, 110),
    ("TA Combiner A", "Combiner", 1.35, 85), ("TA Combiner B", "Combiner", 1.3, 80),
    ("TA Combiner C", "Combiner", 1.3, 80), ("TA Combiner D", "Combiner", 1.3, 80),
    ("TA Combiner E", "Combiner", 1.3, 80), ("TA Combiner Complete", "Combiner", 1.55, 360),
    ("BWM Lion Chrome", "Special", 1.55, 170), ("BWM Tiger Desert", "Special", 1.45, 145),
    ("BWM Panther Night", "Special", 1.4, 140), ("BWM Cheetah Ghost", "Special", 1.45, 145),
    ("BWM Wolf Metallic", "Special", 1.4, 135), ("BWM Eagle Clear", "Special", 1.45, 150),
    ("BWM Raptor Spec Ops", "Special", 1.5, 160), ("BWM Gorilla Black", "Special", 1.5, 165),
    ("TA Mini Lion", "Mini", 1.25, 40), ("TA Mini Tiger", "Mini", 1.2, 38),
    ("TA Mini Eagle", "Mini", 1.2, 38), ("TA Mini Raptor", "Mini", 1.25, 40),
    ("BWM Upgrade Pack", "Special", 1.25, 45), ("TA Combiner Upgrade", "Special", 1.25, 50),
    ("BWM Dinobot King", "Special", 1.55, 180), ("BWM Insecticon A", "Series", 1.3, 100),
    ("BWM Insecticon B", "Series", 1.3, 100), ("BWM Insecticon C", "Series", 1.25, 95),
    ("BWM Triple Changer", "Series", 1.45, 160), ("BWM City Bot", "Series", 1.4, 150),
    ("BWM Seeker Red", "Series", 1.35, 120), ("BWM Seeker Blue", "Series", 1.35, 120),
    ("BWM Seeker Purple", "Series", 1.35, 120), ("BWM Cassette Cat", "Series", 1.3, 70),
    ("BWM Cassette Bird", "Series", 1.3, 70), ("BWM Cassette Dog", "Series", 1.25, 70),
    ("BWM Lion Clear", "Special", 1.5, 155),
], 2017, 2, 2, 130)

# BingoToys — 3P TF
add(data, "bingotoys", "bt", [
    ("BT-01 Commander", "Series", 1.45, 110), ("BT-02 Warrior", "Series", 1.4, 100),
    ("BT-03 Scout", "Series", 1.35, 90), ("BT-04 Medic", "Series", 1.3, 85),
    ("BT-05 Heavy", "Series", 1.4, 105), ("BT-06 Flyer", "Series", 1.4, 100),
    ("BT-07 Seeker Red", "Series", 1.35, 95), ("BT-08 Seeker Blue", "Series", 1.35, 95),
    ("BT-09 Seeker Purple", "Series", 1.35, 95), ("BT-10 Cassette Cat", "Series", 1.3, 55),
    ("BT-11 Cassette Bird", "Series", 1.3, 55), ("BT-12 Cassette Dog", "Series", 1.25, 55),
    ("BT-13 Dinobot King", "Series", 1.5, 140), ("BT-14 Dinobot A", "Series", 1.3, 80),
    ("BT-15 Dinobot B", "Series", 1.3, 80), ("BT-16 Dinobot C", "Series", 1.25, 75),
    ("BT-17 Dinobot D", "Series", 1.25, 75), ("BT-18 City Bot", "Series", 1.4, 120),
    ("BT-19 Triple Changer", "Series", 1.45, 130), ("BT-20 Insecticon A", "Series", 1.3, 70),
    ("BT Combiner A", "Combiner", 1.3, 75), ("BT Combiner B", "Combiner", 1.25, 70),
    ("BT Combiner C", "Combiner", 1.25, 70), ("BT Combiner D", "Combiner", 1.25, 70),
    ("BT Combiner E", "Combiner", 1.25, 70), ("BT Combiner Complete", "Combiner", 1.5, 320),
    ("BT Commander Chrome", "Special", 1.5, 140), ("BT Warrior Desert", "Special", 1.35, 110),
    ("BT Scout Night", "Special", 1.3, 95), ("BT Dinobot King Metallic", "Special", 1.55, 160),
    ("BT City Bot Black", "Special", 1.4, 130), ("BT Triple Changer Ghost", "Special", 1.45, 145),
    ("BT Mini Commander", "Mini", 1.2, 35), ("BT Mini Warrior", "Mini", 1.15, 32),
    ("BT Mini Flyer", "Mini", 1.15, 32), ("BT Cassette Pack", "Special", 1.3, 50),
    ("BT Combiner Upgrade", "Special", 1.25, 40), ("BT Flyer Spec Ops", "Special", 1.35, 110),
    ("BT Heavy Chrome", "Special", 1.4, 120), ("BT Medic Clear", "Special", 1.3, 95),
    ("BT Seeker Ghost", "Special", 1.35, 105), ("BT Insecticon Pack", "Special", 1.35, 180),
    ("BT Commander Clear", "Special", 1.45, 135), ("BT Warrior Metallic", "Special", 1.4, 115),
    ("BT Scout Spec Ops", "Special", 1.3, 100),
], 2018, 1, 2, 95)

# Heatboys — 3P TF / mecha
add(data, "heatboys", "hb", [
    ("HB001 Metal Dragon", "Series", 1.5, 160), ("HB002 Metal Tiger", "Series", 1.45, 140),
    ("HB003 Metal Eagle", "Series", 1.45, 145), ("HB004 Metal Wolf", "Series", 1.4, 130),
    ("HB005 Metal Lion", "Series", 1.5, 155), ("HB006 Metal Snake", "Series", 1.35, 120),
    ("HB007 Metal Rhino", "Series", 1.4, 135), ("HB008 Metal Gorilla", "Series", 1.45, 150),
    ("HB009 Metal Raptor", "Series", 1.5, 155), ("HB010 Metal Scorpion", "Series", 1.4, 125),
    ("HB011 Commander", "Series", 1.5, 170), ("HB012 Warrior", "Series", 1.4, 140),
    ("HB013 Scout", "Series", 1.35, 120), ("HB014 Medic", "Series", 1.3, 115),
    ("HB015 Heavy", "Series", 1.4, 145), ("HB016 Flyer", "Series", 1.4, 140),
    ("HB Combiner A", "Combiner", 1.35, 90), ("HB Combiner B", "Combiner", 1.3, 85),
    ("HB Combiner C", "Combiner", 1.3, 85), ("HB Combiner D", "Combiner", 1.3, 85),
    ("HB Combiner E", "Combiner", 1.3, 85), ("HB Combiner Complete", "Combiner", 1.55, 380),
    ("HB Metal Dragon Chrome", "Special", 1.55, 190), ("HB Metal Tiger Desert", "Special", 1.45, 155),
    ("HB Metal Eagle Ghost", "Special", 1.45, 160), ("HB Metal Lion Metallic", "Special", 1.5, 175),
    ("HB Commander Black", "Special", 1.5, 185), ("HB Warrior Clear", "Special", 1.4, 155),
    ("HB Mini Dragon", "Mini", 1.25, 45), ("HB Mini Tiger", "Mini", 1.2, 40),
    ("HB Mini Eagle", "Mini", 1.2, 40), ("HB Upgrade Pack", "Special", 1.25, 50),
    ("HB Triple Changer", "Series", 1.45, 165), ("HB City Bot", "Series", 1.4, 150),
    ("HB Seeker Red", "Series", 1.35, 125), ("HB Seeker Blue", "Series", 1.35, 125),
    ("HB Seeker Purple", "Series", 1.35, 125), ("HB Cassette Pack", "Special", 1.3, 55),
    ("HB Dinobot King", "Series", 1.5, 170), ("HB Insecticon Pack", "Special", 1.35, 200),
    ("HB Metal Dragon Clear", "Special", 1.5, 180), ("HB Flyer Spec Ops", "Special", 1.4, 155),
    ("HB Heavy Chrome", "Special", 1.45, 160), ("HB Scout Night", "Special", 1.3, 130),
    ("HB Medic Desert", "Special", 1.3, 125),
], 2019, 3, 2, 140)

# CCS Toys — Mortal Kombat / anime AF 1/6 & 1/12
add(data, "ccstoys", "ccs", [
    ("Scorpion", "Mortal Kombat 1/6", 1.55, 280), ("Sub-Zero", "Mortal Kombat 1/6", 1.55, 280),
    ("Raiden", "Mortal Kombat 1/6", 1.5, 270), ("Liu Kang", "Mortal Kombat 1/6", 1.5, 270),
    ("Kitana", "Mortal Kombat 1/6", 1.45, 260), ("Mileena", "Mortal Kombat 1/6", 1.45, 260),
    ("Johnny Cage", "Mortal Kombat 1/6", 1.4, 250), ("Sonya Blade", "Mortal Kombat 1/6", 1.4, 250),
    ("Kano", "Mortal Kombat 1/6", 1.35, 240), ("Jax", "Mortal Kombat 1/6", 1.4, 250),
    ("Shang Tsung", "Mortal Kombat 1/6", 1.5, 270), ("Shao Kahn", "Mortal Kombat 1/6", 1.55, 300),
    ("Scorpion", "Mortal Kombat 1/12", 1.5, 95), ("Sub-Zero", "Mortal Kombat 1/12", 1.5, 95),
    ("Raiden", "Mortal Kombat 1/12", 1.45, 90), ("Liu Kang", "Mortal Kombat 1/12", 1.45, 90),
    ("Kitana", "Mortal Kombat 1/12", 1.4, 85), ("Mileena", "Mortal Kombat 1/12", 1.4, 85),
    ("Noob Saibot", "Mortal Kombat 1/6", 1.5, 280), ("Smoke", "Mortal Kombat 1/6", 1.45, 270),
    ("Reptile", "Mortal Kombat 1/6", 1.4, 260), ("Ermac", "Mortal Kombat 1/6", 1.4, 260),
    ("Scorpion Klassic", "Special", 1.55, 300), ("Sub-Zero Klassic", "Special", 1.55, 300),
    ("Scorpion Inferno", "Special", 1.5, 290), ("Sub-Zero Cryomancer", "Special", 1.5, 290),
    ("Raiden Dark", "Special", 1.5, 285), ("Liu Kang Fire God", "Special", 1.55, 295),
    ("Kitana Assassin", "Special", 1.45, 275), ("Mileena Tarkatan", "Special", 1.45, 275),
    ("Goro", "Mortal Kombat 1/6", 1.55, 350), ("Kintaro", "Mortal Kombat 1/6", 1.5, 340),
    ("Motaro", "Mortal Kombat 1/6", 1.5, 340), ("Baraka", "Mortal Kombat 1/6", 1.4, 255),
    ("Kabal", "Mortal Kombat 1/6", 1.35, 245), ("Stryker", "Mortal Kombat 1/6", 1.3, 240),
    ("Nightwolf", "Mortal Kombat 1/6", 1.35, 250), ("Kung Lao", "Mortal Kombat 1/6", 1.4, 255),
    ("Jade", "Mortal Kombat 1/6", 1.4, 255), ("Sindel", "Mortal Kombat 1/6", 1.45, 265),
    ("Noob Saibot 1/12", "Mortal Kombat 1/12", 1.45, 95), ("Smoke 1/12", "Mortal Kombat 1/12", 1.4, 90),
    ("Goro 1/12", "Mortal Kombat 1/12", 1.5, 120), ("Shao Kahn 1/12", "Mortal Kombat 1/12", 1.5, 110),
    ("Scorpion 1/12 Klassic", "Special", 1.5, 100),
], 2021, 1, 1, 270)

# TBLeague — Phicen 1/6 seamless AF
add(data, "tbleague", "tb", [
    ("PL2019-140 Female Body", "Seamless Body", 1.4, 120), ("PL2019-141 Male Body", "Seamless Body", 1.4, 120),
    ("Captain Sparta", "Fantasy", 1.5, 220), ("Arhian Pirate", "Fantasy", 1.45, 210),
    ("Vampirella", "Licensed", 1.55, 250), ("Red Sonja", "Licensed", 1.55, 250),
    ("Barbarian Queen", "Fantasy", 1.45, 200), ("Amazon Warrior", "Fantasy", 1.4, 190),
    ("Ninja Assassin Female", "Modern", 1.4, 185), ("Ninja Assassin Male", "Modern", 1.4, 185),
    ("Egyptian Queen", "Historical", 1.45, 210), ("Cleopatra", "Historical", 1.5, 230),
    ("Roman Gladiator", "Historical", 1.4, 200), ("Spartan Warrior", "Historical", 1.45, 210),
    ("Viking Shieldmaiden", "Historical", 1.45, 205), ("Celtic Warrior", "Historical", 1.35, 190),
    ("Cyber Girl", "Sci-Fi", 1.4, 195), ("Space Marine Female", "Sci-Fi", 1.4, 200),
    ("Hunter Killer", "Sci-Fi", 1.35, 185), ("Android Operative", "Sci-Fi", 1.35, 180),
    ("PL2020-150 Suntan Body", "Seamless Body", 1.35, 125), ("PL2020-151 Pale Body", "Seamless Body", 1.35, 125),
    ("Knight of the Round", "Fantasy", 1.4, 215), ("Dark Elf Assassin", "Fantasy", 1.45, 210),
    ("Elf Archer", "Fantasy", 1.4, 200), ("Orc Berserker", "Fantasy", 1.4, 205),
    ("Samurai Female", "Historical", 1.5, 230), ("Samurai Male", "Historical", 1.5, 230),
    ("Geisha Assassin", "Historical", 1.45, 215), ("Shaolin Monk", "Historical", 1.35, 180),
    ("SWAT Female", "Modern", 1.4, 190), ("PMC Operative Female", "Modern", 1.4, 195),
    ("Agent Black", "Modern", 1.35, 180), ("Agent White", "Modern", 1.35, 180),
    ("Vampirella Red", "Special", 1.55, 270), ("Red Sonja Classic", "Special", 1.55, 270),
    ("Captain Sparta Deluxe", "Special", 1.5, 250), ("Arhian Deluxe", "Special", 1.45, 240),
    ("Seamless Body Athletic", "Seamless Body", 1.4, 130), ("Seamless Body Curvy", "Seamless Body", 1.4, 130),
    ("Knight Deluxe", "Special", 1.45, 240), ("Samurai Deluxe", "Special", 1.5, 260),
    ("Cyber Girl Neon", "Special", 1.4, 210), ("Egyptian Queen Deluxe", "Special", 1.45, 235),
    ("Barbarian Queen Chrome", "Special", 1.45, 220),
], 2016, 6, 2, 200)

# COO Model — 1/6 military / historical
add(data, "coomodel", "cm", [
    ("SE001 Roman Legionary", "Empire Series", 1.45), ("SE002 Roman Centurion", "Empire Series", 1.5),
    ("SE003 Roman Praetorian", "Empire Series", 1.5), ("SE004 Roman Standard Bearer", "Empire Series", 1.4),
    ("SE005 Gladiator Murmillo", "Empire Series", 1.45), ("SE006 Gladiator Retiarius", "Empire Series", 1.4),
    ("SE007 Spartan Hoplite", "Empire Series", 1.5), ("SE008 Spartan King", "Empire Series", 1.55),
    ("NS001 WWII German Sniper", "Nose Art", 1.4), ("NS002 WWII US Airborne", "Nose Art", 1.45),
    ("NS003 WWII US Ranger", "Nose Art", 1.45), ("NS004 WWII British SAS", "Nose Art", 1.45),
    ("NS005 WWII Soviet Sniper", "Nose Art", 1.4), ("NS006 WWII Japanese Infantry", "Nose Art", 1.35),
    ("NS007 Vietnam MACV-SOG", "Nose Art", 1.5), ("NS008 Vietnam US Marine", "Nose Art", 1.45),
    ("PE001 Knights Templar", "Paladin Empire", 1.5), ("PE002 Teutonic Knight", "Paladin Empire", 1.45),
    ("PE003 Hospitaller", "Paladin Empire", 1.45), ("PE004 Crusader Knight", "Paladin Empire", 1.5),
    ("PE005 Black Knight", "Paladin Empire", 1.5), ("PE006 Aragorn Style Ranger", "Paladin Empire", 1.4),
    ("PE007 Viking Berserker", "Paladin Empire", 1.45), ("PE008 Viking Jarl", "Paladin Empire", 1.5),
    ("SE009 Egyptian Pharaoh", "Empire Series", 1.5), ("SE010 Egyptian Guard", "Empire Series", 1.35),
    ("SE011 Persian Immortal", "Empire Series", 1.4), ("SE012 Macedonian Companion", "Empire Series", 1.4),
    ("NS009 Modern Delta", "Nose Art", 1.5), ("NS010 Modern SEAL", "Nose Art", 1.5),
    ("NS011 Modern Spetsnaz", "Nose Art", 1.45), ("NS012 Modern SAS", "Nose Art", 1.45),
    ("PE009 Samurai General", "Paladin Empire", 1.55), ("PE010 Samurai Ashigaru", "Paladin Empire", 1.4),
    ("PE011 Ninja Shadow", "Paladin Empire", 1.45), ("PE012 Shaolin Warrior", "Paladin Empire", 1.4),
    ("SE Roman Deluxe", "Special", 1.55), ("SE Spartan Deluxe", "Special", 1.55),
    ("NS Delta Deluxe", "Special", 1.55), ("PE Templar Deluxe", "Special", 1.55),
    ("NS Vietnam Deluxe", "Special", 1.5), ("PE Viking Deluxe", "Special", 1.5),
    ("SE Gladiator Deluxe", "Special", 1.5), ("PE Samurai Deluxe", "Special", 1.55),
    ("NS SEAL Night Ops", "Special", 1.5),
], 2015, 4, 2, 220)

# DiD — 1/6 military AF
add(data, "did", "did", [
    ("D80147 WWII German Panzer Crew", "WWII", 1.4), ("D80148 WWII German Infantry", "WWII", 1.4),
    ("D80149 WWII German Sniper", "WWII", 1.45), ("D80150 WWII US Airborne", "WWII", 1.5),
    ("D80151 WWII US Ranger", "WWII", 1.5), ("D80152 WWII US Marine Pacific", "WWII", 1.5),
    ("D80153 WWII British Commando", "WWII", 1.45), ("D80154 WWII British SAS", "WWII", 1.5),
    ("D80155 WWII Soviet Infantry", "WWII", 1.4), ("D80156 WWII Soviet Sniper", "WWII", 1.45),
    ("D80157 WWII Japanese Infantry", "WWII", 1.35), ("D80158 WWII Japanese Officer", "WWII", 1.4),
    ("D80159 Vietnam US SOG", "Vietnam", 1.5), ("D80160 Vietnam US Marine", "Vietnam", 1.45),
    ("D80161 Vietnam Tunnel Rat", "Vietnam", 1.4), ("D80162 Vietnam NVA", "Vietnam", 1.35),
    ("D80163 Modern US Delta", "Modern", 1.55), ("D80164 Modern US SEAL", "Modern", 1.55),
    ("D80165 Modern US Ranger", "Modern", 1.5), ("D80166 Modern British SAS", "Modern", 1.5),
    ("D80167 Modern Spetsnaz", "Modern", 1.45), ("D80168 Modern KSK", "Modern", 1.45),
    ("D80169 Modern GIGN", "Modern", 1.45), ("D80170 Modern Shayetet", "Modern", 1.4),
    ("D80171 WWI British Tommy", "WWI", 1.4), ("D80172 WWI German Stormtrooper", "WWI", 1.4),
    ("D80173 WWI US Doughboy", "WWI", 1.35), ("D80174 WWI French Poilu", "WWI", 1.35),
    ("D80175 WWII German Fallschirmjager", "WWII", 1.45), ("D80176 WWII German Afrika Korps", "WWII", 1.4),
    ("D80177 WWII US Tank Crew", "WWII", 1.35), ("D80178 WWII British Para", "WWII", 1.45),
    ("D80179 Modern PMC", "Modern", 1.4), ("D80180 Modern SWAT", "Modern", 1.35),
    ("D80181 WWII Nurse", "Support", 1.3), ("D80182 WWII Medic", "Support", 1.35),
    ("Delta Deluxe", "Special", 1.55), ("SEAL Deluxe", "Special", 1.55),
    ("Airborne Deluxe", "Special", 1.5), ("SAS Deluxe", "Special", 1.5),
    ("SOG Deluxe", "Special", 1.5), ("Panzer Crew Deluxe", "Special", 1.45),
    ("Spartan Homage", "Historical", 1.45), ("Roman Homage", "Historical", 1.4),
    ("Samurai Homage", "Historical", 1.5),
], 2014, 3, 2, 195)

# MoShow Toys — mecha / 3P AF
add(data, "moshow", "ms", [
    ("MCT-J02 Absolute Zero", "Metal Build Style", 1.55, 280), ("MCT-E02 Noble Class", "Metal Build Style", 1.5, 260),
    ("MCT-A02 Tiger", "Metal Build Style", 1.5, 250), ("MCT-B02 Eagle", "Metal Build Style", 1.45, 240),
    ("MCT-C02 Lion", "Metal Build Style", 1.5, 255), ("MCT-D02 Dragon", "Metal Build Style", 1.55, 280),
    ("MCT-F02 Wolf", "Metal Build Style", 1.45, 235), ("MCT-G02 Phoenix", "Metal Build Style", 1.5, 270),
    ("MCT-H02 Shark", "Metal Build Style", 1.4, 230), ("MCT-I02 Panther", "Metal Build Style", 1.45, 240),
    ("Progenitor Effect Date Masamune", "Progenitor", 1.5, 220), ("Progenitor Effect Takeda", "Progenitor", 1.45, 210),
    ("Progenitor Effect Uesugi", "Progenitor", 1.45, 210), ("Progenitor Effect Oda", "Progenitor", 1.5, 230),
    ("Progenitor Effect Tokugawa", "Progenitor", 1.4, 200), ("Progenitor Effect Sanada", "Progenitor", 1.45, 215),
    ("MCT Absolute Zero Chrome", "Special", 1.55, 320), ("MCT Noble Class Gold", "Special", 1.5, 300),
    ("MCT Tiger Desert", "Special", 1.45, 270), ("MCT Eagle Ghost", "Special", 1.45, 265),
    ("MCT Lion Metallic", "Special", 1.5, 290), ("MCT Dragon Clear", "Special", 1.55, 310),
    ("MCT Combiner A", "Combiner", 1.35, 100), ("MCT Combiner B", "Combiner", 1.3, 95),
    ("MCT Combiner C", "Combiner", 1.3, 95), ("MCT Combiner D", "Combiner", 1.3, 95),
    ("MCT Combiner E", "Combiner", 1.3, 95), ("MCT Combiner Complete", "Combiner", 1.55, 420),
    ("MCT Mini Absolute", "Mini", 1.25, 55), ("MCT Mini Tiger", "Mini", 1.2, 50),
    ("MCT Mini Dragon", "Mini", 1.25, 55), ("MCT Upgrade Pack", "Special", 1.3, 60),
    ("Progenitor Masamune Deluxe", "Special", 1.55, 260), ("Progenitor Oda Deluxe", "Special", 1.5, 250),
    ("MCT Wolf Night", "Special", 1.45, 255), ("MCT Phoenix Fire", "Special", 1.5, 295),
    ("MCT Shark Spec Ops", "Special", 1.4, 250), ("MCT Panther Black", "Special", 1.45, 260),
    ("MCT Absolute Zero Clear", "Special", 1.55, 300), ("Progenitor Sanada Red", "Special", 1.45, 230),
    ("MCT Tiger Chrome", "Special", 1.5, 280), ("MCT Eagle Metallic", "Special", 1.45, 270),
    ("MCT Dragon Gold", "Special", 1.55, 330), ("MCT Combiner Upgrade", "Special", 1.3, 70),
    ("Progenitor Full Set Display", "Special", 1.5, 900),
], 2018, 5, 2, 250)

# ========== DENSIFY ==========
# JoyToy
add(data, "joytoy", "jt", [
    ("Ultramarines Intercessor", "Warhammer 40K", 1.45), ("Ultramarines Captain", "Warhammer 40K", 1.5),
    ("Blood Angels Intercessor", "Warhammer 40K", 1.45), ("Blood Angels Dante", "Warhammer 40K", 1.55),
    ("Space Wolves Intercessor", "Warhammer 40K", 1.45), ("Space Wolves Ragnar", "Warhammer 40K", 1.5),
    ("Dark Angels Intercessor", "Warhammer 40K", 1.4), ("Dark Angels Azrael", "Warhammer 40K", 1.5),
    ("Black Templars Intercessor", "Warhammer 40K", 1.45), ("Black Templars Marshal", "Warhammer 40K", 1.5),
    ("Death Guard Plague Marine", "Warhammer 40K", 1.45), ("Death Guard Typhus", "Warhammer 40K", 1.5),
    ("Thousand Sons Rubric", "Warhammer 40K", 1.45), ("Thousand Sons Ahriman", "Warhammer 40K", 1.55),
    ("World Eaters Berzerker", "Warhammer 40K", 1.45), ("World Eaters Kharn", "Warhammer 40K", 1.55),
    ("Ork Boy", "Warhammer 40K", 1.4), ("Ork Warboss", "Warhammer 40K", 1.5),
    ("Necron Warrior", "Warhammer 40K", 1.4), ("Necron Overlord", "Warhammer 40K", 1.5),
    ("Tyranid Warrior", "Warhammer 40K", 1.45), ("Tyranid Hive Tyrant", "Warhammer 40K", 1.55),
    ("Adepta Sororitas Battle Sister", "Warhammer 40K", 1.45), ("Adepta Sororitas Canoness", "Warhammer 40K", 1.5),
    ("Astra Militarum Guardsman", "Warhammer 40K", 1.35), ("Astra Militarum Commissar", "Warhammer 40K", 1.4),
    ("Dark Source Soldier A", "Dark Source", 1.35), ("Dark Source Soldier B", "Dark Source", 1.35),
    ("Dark Source Commander", "Dark Source", 1.4), ("Dark Source Sniper", "Dark Source", 1.4),
    ("Dark Source Heavy", "Dark Source", 1.35), ("Dark Source Medic", "Dark Source", 1.3),
    ("Ultramarines Primaris Lieutenant", "Warhammer 40K", 1.45), ("Blood Angels Primaris", "Warhammer 40K", 1.45),
    ("Chaos Marine Rubric", "Warhammer 40K", 1.4), ("Chaos Marine Berzerker", "Warhammer 40K", 1.4),
    ("Custodes Guard", "Warhammer 40K", 1.55), ("Custodes Captain", "Warhammer 40K", 1.55),
    ("Grey Knights Interceptor", "Warhammer 40K", 1.5), ("Grey Knights Justicar", "Warhammer 40K", 1.5),
    ("Tau Fire Warrior", "Warhammer 40K", 1.4), ("Tau Commander", "Warhammer 40K", 1.45),
    ("Eldar Guardian", "Warhammer 40K", 1.4), ("Eldar Farseer", "Warhammer 40K", 1.5),
    ("Dark Source Spec Ops", "Dark Source", 1.4),
], 2020, 1, 1, 55)

# Sentinel
add(data, "sentinel", "sn", [
    ("Fighting Armor Iron Man", "Fighting Armor", 1.55), ("Fighting Armor Captain America", "Fighting Armor", 1.5),
    ("Fighting Armor Thor", "Fighting Armor", 1.5), ("Fighting Armor Hulk", "Fighting Armor", 1.45),
    ("Fighting Armor Spider-Man", "Fighting Armor", 1.55), ("Fighting Armor Wolverine", "Fighting Armor", 1.55),
    ("Fighting Armor Deadpool", "Fighting Armor", 1.5), ("Fighting Armor Venom", "Fighting Armor", 1.5),
    ("Fighting Armor Magneto", "Fighting Armor", 1.5), ("Fighting Armor Doctor Doom", "Fighting Armor", 1.5),
    ("Fighting Armor Thanos", "Fighting Armor", 1.55), ("Fighting Armor Black Panther", "Fighting Armor", 1.45),
    ("Riobot Getter 1", "Riobot", 1.55), ("Riobot Getter 2", "Riobot", 1.45),
    ("Riobot Getter 3", "Riobot", 1.45), ("Riobot Shin Getter", "Riobot", 1.55),
    ("Riobot Mazinger Z", "Riobot", 1.55), ("Riobot Great Mazinger", "Riobot", 1.5),
    ("Riobot Grendizer", "Riobot", 1.5), ("Riobot Jeeg", "Riobot", 1.45),
    ("Wonderful Acts Ultraman", "Wonderful Acts", 1.5), ("Wonderful Acts Ultraseven", "Wonderful Acts", 1.45),
    ("Wonderful Acts Ultraman Ace", "Wonderful Acts", 1.4), ("Wonderful Acts Zetton", "Wonderful Acts", 1.4),
    ("Fighting Armor Iron Man Mark 3", "Special", 1.55), ("Fighting Armor Cap Sam Wilson", "Special", 1.45),
    ("Fighting Armor Wolverine Brown", "Special", 1.55), ("Fighting Armor Spider-Man Symbiote", "Special", 1.55),
    ("Riobot Getter Dragon", "Special", 1.5), ("Riobot Mazinger Z Black", "Special", 1.55),
    ("Fighting Armor Cap Classic", "Special", 1.5), ("Fighting Armor Thor Endgame", "Special", 1.5),
    ("Riobot Shin Getter Black", "Special", 1.55), ("Wonderful Acts Ultraman Tiga", "Wonderful Acts", 1.45),
    ("Fighting Armor Deadpool X-Force", "Special", 1.5), ("Fighting Armor Venom Movie", "Special", 1.5),
    ("Riobot Grendizer Gold", "Special", 1.55), ("Wonderful Acts Alien Baltan", "Wonderful Acts", 1.35),
    ("Fighting Armor Magneto White", "Special", 1.5), ("Fighting Armor Doom Classic", "Special", 1.5),
    ("Riobot Jeeg Deluxe", "Special", 1.5), ("Wonderful Acts Ultraman Dyna", "Wonderful Acts", 1.4),
    ("Fighting Armor Thanos Infinity", "Special", 1.55), ("Fighting Armor BP Vibranium", "Special", 1.45),
    ("Riobot Mazinger Z Clear", "Special", 1.5),
], 2018, 2, 2, 95)

# 1000Toys
add(data, "thousandtoys", "tt", [
    ("Tough Guys Captain", "Tough Guys", 1.4), ("Tough Guys Sergeant", "Tough Guys", 1.35),
    ("Tough Guys Scout", "Tough Guys", 1.3), ("Tough Guys Medic", "Tough Guys", 1.3),
    ("Tough Guys Heavy", "Tough Guys", 1.35), ("Tough Guys Sniper", "Tough Guys", 1.4),
    ("Tough Guys Breacher", "Tough Guys", 1.35), ("Tough Guys Pilot", "Tough Guys", 1.3),
    ("Synthetic Human Ver 1.0", "Synthetic Human", 1.5), ("Synthetic Human Ver 1.5", "Synthetic Human", 1.5),
    ("Synthetic Human Ver 2.0", "Synthetic Human", 1.55), ("Synthetic Human Female", "Synthetic Human", 1.5),
    ("Synthetic Human Combat", "Synthetic Human", 1.5), ("Synthetic Human Civilian", "Synthetic Human", 1.4),
    ("Tough Guys Urban Camo", "Special", 1.4), ("Tough Guys Desert Camo", "Special", 1.35),
    ("Tough Guys Night Ops", "Special", 1.4), ("Tough Guys Winter", "Special", 1.35),
    ("Synthetic Human Chrome", "Special", 1.55), ("Synthetic Human Clear", "Special", 1.5),
    ("Synthetic Human Battle Damaged", "Special", 1.5), ("Tough Guys Captain Deluxe", "Special", 1.45),
    ("Tough Guys Sniper Deluxe", "Special", 1.45), ("Synthetic Human Ver 2.0 Combat", "Special", 1.55),
    ("Tough Guys PMC Pack", "Special", 1.4), ("Tough Guys SWAT Pack", "Special", 1.4),
    ("Synthetic Human Agent", "Synthetic Human", 1.45), ("Synthetic Human Soldier", "Synthetic Human", 1.45),
    ("Tough Guys Jungle", "Special", 1.35), ("Tough Guys Arctic", "Special", 1.35),
    ("Synthetic Human Prototype", "Special", 1.5), ("Tough Guys Heavy Deluxe", "Special", 1.4),
    ("Synthetic Human Female Combat", "Special", 1.5), ("Tough Guys Breacher Deluxe", "Special", 1.4),
    ("Synthetic Human Ver 1.0 Clear", "Special", 1.45),
], 2019, 4, 2, 85)

# Spin Master Bakugan
add(data, "spinmaster", "sm", [
    ("Dragonoid Battle Planet", "Battle Planet", 1.4), ("Hydorous Battle Planet", "Battle Planet", 1.35),
    ("Gorthion Battle Planet", "Battle Planet", 1.3), ("Trox Battle Planet", "Battle Planet", 1.3),
    ("Howlkor Battle Planet", "Battle Planet", 1.3), ("Pegatrix Battle Planet", "Battle Planet", 1.35),
    ("Nillious Battle Planet", "Battle Planet", 1.4), ("Auxillataur Battle Planet", "Battle Planet", 1.3),
    ("Dragonoid Armored Alliance", "Armored Alliance", 1.45), ("Hydorous Armored Alliance", "Armored Alliance", 1.35),
    ("Nillious Armored Alliance", "Armored Alliance", 1.4), ("Pegatrix Armored Alliance", "Armored Alliance", 1.35),
    ("Dragonoid Geogan Rising", "Geogan Rising", 1.45), ("Nillious Geogan Rising", "Geogan Rising", 1.4),
    ("Dragonoid Evolutions", "Evolutions", 1.5), ("Nillious Evolutions", "Evolutions", 1.45),
    ("Dragonoid Legacy", "Legacy", 1.5), ("Drago Classic", "Legacy", 1.55),
    ("Tigrerra Legacy", "Legacy", 1.4), ("Preyas Legacy", "Legacy", 1.4),
    ("Skyress Legacy", "Legacy", 1.4), ("Hydranoid Legacy", "Legacy", 1.45),
    ("Blade Tigrerra", "Legacy", 1.35), ("Dual Hydranoid", "Legacy", 1.45),
    ("Delta Dragonoid", "Legacy", 1.5), ("Ultimate Dragonoid", "Legacy", 1.55),
    ("Helios Legacy", "Legacy", 1.5), ("Vulcan Legacy", "Legacy", 1.4),
    ("Nemus Legacy", "Legacy", 1.35), ("Elfin Legacy", "Legacy", 1.35),
    ("Ingram Legacy", "Legacy", 1.35), ("Hades Legacy", "Legacy", 1.4),
    ("Dragonoid Ultra", "Special", 1.55), ("Nillious Ultra", "Special", 1.5),
    ("Drago Platinum", "Special", 1.55), ("Helios Black", "Special", 1.5),
    ("Bakugan Brawler Dan", "Character AF", 1.3), ("Bakugan Brawler Shun", "Character AF", 1.3),
    ("Bakugan Brawler Runo", "Character AF", 1.25), ("Bakugan Brawler Marucho", "Character AF", 1.25),
    ("Bakugan Brawler Julie", "Character AF", 1.25), ("Bakugan Brawler Alice", "Character AF", 1.25),
    ("Dragonoid Maximus", "Special", 1.55), ("Nillious Maximus", "Special", 1.5),
    ("Geogan Titan", "Geogan Rising", 1.45),
], 2019, 1, 1, 14.99)

# Fresh Monkey Fiction
add(data, "freshmonkey", "fm", [
    ("Army of Darkness Ash", "Army of Darkness", 1.5), ("Army of Darkness Evil Ash", "Army of Darkness", 1.5),
    ("Army of Darkness Deadite", "Army of Darkness", 1.35), ("Army of Darkness Sheila", "Army of Darkness", 1.3),
    ("ReAction Style Hero A", "Fresh Retro", 1.3), ("ReAction Style Hero B", "Fresh Retro", 1.3),
    ("ReAction Style Villain A", "Fresh Retro", 1.3), ("ReAction Style Villain B", "Fresh Retro", 1.3),
    ("Horror Host A", "Horror", 1.35), ("Horror Host B", "Horror", 1.35),
    ("Horror Monster A", "Horror", 1.4), ("Horror Monster B", "Horror", 1.4),
    ("Horror Monster C", "Horror", 1.35), ("Cult Classic Hero", "Cult", 1.4),
    ("Cult Classic Villain", "Cult", 1.4), ("Cult Classic Sidekick", "Cult", 1.3),
    ("Wrestling Legend A", "Wrestling", 1.35), ("Wrestling Legend B", "Wrestling", 1.35),
    ("Wrestling Legend C", "Wrestling", 1.3), ("Wrestling Legend D", "Wrestling", 1.3),
    ("Comic Hero Retro", "Comics", 1.4), ("Comic Villain Retro", "Comics", 1.4),
    ("Comic Sidekick Retro", "Comics", 1.3), ("TV Hero Retro", "TV", 1.35),
    ("TV Villain Retro", "TV", 1.35), ("TV Sidekick Retro", "TV", 1.25),
    ("Ash Deluxe", "Special", 1.55), ("Evil Ash Deluxe", "Special", 1.55),
    ("Deadite Deluxe", "Special", 1.4), ("Horror Host Deluxe", "Special", 1.4),
    ("Wrestling Legend Chrome", "Special", 1.4), ("Comic Hero Chrome", "Special", 1.45),
    ("Fresh Retro Clear", "Special", 1.35), ("Cult Classic Glow", "Special", 1.4),
    ("Army of Darkness Horse", "Special", 1.45), ("Army of Darkness Pit Deadite", "Special", 1.35),
    ("Fresh Retro Wave 2 A", "Fresh Retro", 1.3), ("Fresh Retro Wave 2 B", "Fresh Retro", 1.3),
    ("Fresh Retro Wave 2 C", "Fresh Retro", 1.25), ("Fresh Retro Wave 2 D", "Fresh Retro", 1.25),
    ("Horror Wave 2 A", "Horror", 1.35), ("Horror Wave 2 B", "Horror", 1.35),
    ("Wrestling Wave 2 A", "Wrestling", 1.3), ("Wrestling Wave 2 B", "Wrestling", 1.3),
    ("Comics Wave 2 A", "Comics", 1.35),
], 2018, 6, 2, 25)

# MAFEX densify
add(data, "mafex", "mx", [
    ("Spider-Man", "Comic Ver.", 1.55), ("Spider-Man", "Ben Reilly", 1.5),
    ("Spider-Man", "Symbiote", 1.55), ("Spider-Man", "Miles Morales", 1.5),
    ("Spider-Man", "2099", 1.5), ("Venom", "Comic Ver.", 1.55),
    ("Carnage", "Comic Ver.", 1.5), ("Green Goblin", "Comic Ver.", 1.5),
    ("Doctor Octopus", "Comic Ver.", 1.45), ("Mysterio", "Comic Ver.", 1.4),
    ("Batman", "Hush", 1.55), ("Batman", "The Dark Knight Returns", 1.55),
    ("Batman", "Batman Begins", 1.5), ("Batman", "The Dark Knight", 1.55),
    ("Superman", "Hush", 1.5), ("Superman", "The Dark Knight Returns", 1.5),
    ("Wonder Woman", "Hush", 1.45), ("Aquaman", "Hush", 1.4),
    ("The Joker", "Hush", 1.55), ("The Joker", "The Dark Knight", 1.55),
    ("Harley Quinn", "Comic Ver.", 1.5), ("Catwoman", "Hush", 1.45),
    ("Robin", "Hush", 1.4), ("Nightwing", "Hush", 1.45),
    ("Deadpool", "Comic Ver.", 1.55), ("Wolverine", "Comic Ver.", 1.55),
    ("Magneto", "Comic Ver.", 1.5), ("Cyclops", "Comic Ver.", 1.45),
    ("Jean Grey", "Comic Ver.", 1.45), ("Storm", "Comic Ver.", 1.45),
    ("Iron Man", "Comic Ver.", 1.5), ("Captain America", "Comic Ver.", 1.5),
    ("Thor", "Comic Ver.", 1.45), ("Hulk", "Comic Ver.", 1.45),
    ("Black Panther", "Comic Ver.", 1.45), ("Doctor Strange", "Comic Ver.", 1.45),
    ("Spider-Man", "Into the Spider-Verse", 1.55), ("Spider-Gwen", "Into the Spider-Verse", 1.5),
    ("Batman", "Year One", 1.5), ("Superman", "Kingdom Come", 1.5),
    ("Flash", "Comic Ver.", 1.4), ("Green Lantern", "Comic Ver.", 1.4),
    ("Punisher", "Comic Ver.", 1.45), ("Daredevil", "Comic Ver.", 1.45),
    ("Elektra", "Comic Ver.", 1.4),
], 2016, 1, 1, 95)

# Mezco One:12
add(data, "mezco", "mz", [
    ("Spider-Man", "One:12 Deluxe", 1.55), ("Spider-Man", "Black Suit", 1.55),
    ("Venom", "One:12", 1.55), ("Carnage", "One:12", 1.5),
    ("Green Goblin", "One:12", 1.5), ("Doctor Octopus", "One:12", 1.5),
    ("Batman", "Sovereign Knight", 1.55), ("Batman", "Ascending Knight", 1.55),
    ("Batman", "Supreme Knight", 1.55), ("The Joker", "One:12", 1.55),
    ("Harley Quinn", "One:12", 1.5), ("Catwoman", "One:12", 1.45),
    ("Superman", "One:12", 1.5), ("Wonder Woman", "One:12", 1.45),
    ("Aquaman", "One:12", 1.4), ("Flash", "One:12", 1.4),
    ("Deadpool", "One:12", 1.55), ("Wolverine", "One:12", 1.55),
    ("Magneto", "One:12", 1.5), ("Professor X", "One:12", 1.45),
    ("Cyclops", "One:12", 1.45), ("Jean Grey", "One:12", 1.45),
    ("Iron Man", "One:12", 1.5), ("Captain America", "One:12", 1.5),
    ("Punisher", "One:12", 1.5), ("Daredevil", "One:12", 1.5),
    ("Moon Knight", "One:12", 1.55), ("Ghost Rider", "One:12", 1.55),
    ("Blade", "One:12", 1.5), ("Hellboy", "One:12", 1.5),
    ("Rorschach", "One:12", 1.5), ("Dr. Manhattan", "One:12", 1.55),
    ("Judge Dredd", "One:12", 1.5), ("RoboCop", "One:12", 1.5),
    ("Predator", "One:12", 1.55), ("Alien", "One:12", 1.55),
    ("Freddy Krueger", "One:12", 1.5), ("Jason Voorhees", "One:12", 1.5),
    ("Michael Myers", "One:12", 1.5), ("Leatherface", "One:12", 1.45),
    ("Doc Strange", "One:12", 1.45), ("Black Panther", "One:12", 1.45),
    ("Thor", "One:12", 1.45), ("Hulk", "One:12", 1.45),
    ("Thanos", "One:12", 1.55),
], 2016, 2, 1, 112)

# Storm Collectibles
add(data, "storm", "st", [
    ("Ryu", "Street Fighter", 1.5), ("Ken", "Street Fighter", 1.5),
    ("Chun-Li", "Street Fighter", 1.55), ("Guile", "Street Fighter", 1.45),
    ("Akuma", "Street Fighter", 1.55), ("M. Bison", "Street Fighter", 1.5),
    ("Dhalsim", "Street Fighter", 1.4), ("Zangief", "Street Fighter", 1.45),
    ("Blanka", "Street Fighter", 1.4), ("E. Honda", "Street Fighter", 1.35),
    ("Cammy", "Street Fighter", 1.5), ("Sakura", "Street Fighter", 1.45),
    ("Evil Ryu", "Street Fighter", 1.5), ("Violent Ken", "Street Fighter", 1.45),
    ("Scorpion", "Mortal Kombat", 1.55), ("Sub-Zero", "Mortal Kombat", 1.55),
    ("Liu Kang", "Mortal Kombat", 1.5), ("Raiden", "Mortal Kombat", 1.5),
    ("Kitana", "Mortal Kombat", 1.45), ("Johnny Cage", "Mortal Kombat", 1.4),
    ("Iori Yagami", "KOF", 1.5), ("Kyo Kusanagi", "KOF", 1.5),
    ("Terry Bogard", "KOF", 1.5), ("Mai Shiranui", "KOF", 1.55),
    ("Geese Howard", "KOF", 1.5), ("Rugal Bernstein", "KOF", 1.5),
    ("Heihachi", "Tekken", 1.45), ("Kazuya", "Tekken", 1.5),
    ("Jin Kazama", "Tekken", 1.45), ("Paul Phoenix", "Tekken", 1.35),
    ("Ryu White", "Special", 1.5), ("Ken Red", "Special", 1.5),
    ("Chun-Li Pink", "Special", 1.55), ("Akuma Shin", "Special", 1.55),
    ("Scorpion Inferno", "Special", 1.55), ("Sub-Zero Cryomancer", "Special", 1.55),
    ("Mai Shiranui Pink", "Special", 1.55), ("Iori Orochi", "Special", 1.5),
    ("Ryu Player 2", "Special", 1.45), ("Ken Player 2", "Special", 1.45),
    ("Guile USA", "Special", 1.45), ("Cammy Delta Red", "Special", 1.5),
    ("Liu Kang Fire God", "Special", 1.5), ("Raiden Dark", "Special", 1.5),
    ("Terry Hungry Wolf", "Special", 1.5),
], 2017, 1, 1, 110)

# Hiya
add(data, "hiya", "hy", [
    ("Godzilla", "2014", 1.5), ("Godzilla", "2019", 1.55),
    ("Kong", "Skull Island", 1.5), ("Kong", "Godzilla vs Kong", 1.55),
    ("Rodan", "King of the Monsters", 1.45), ("Mothra", "King of the Monsters", 1.45),
    ("King Ghidorah", "King of the Monsters", 1.55), ("Mechagodzilla", "Godzilla vs Kong", 1.55),
    ("Godzilla", "Minus One", 1.55), ("Godzilla", "1989 Biollante", 1.5),
    ("Godzilla", "1991 Heisei", 1.5), ("Godzilla", "2001 GMK", 1.5),
    ("Godzilla", "Final Wars", 1.45), ("SpaceGodzilla", "Heisei", 1.5),
    ("Destoroyah", "Heisei", 1.55), ("Biollante", "Heisei", 1.5),
    ("Alien", "Exquisite Mini", 1.5), ("Predator", "Exquisite Mini", 1.5),
    ("Alien Queen", "Exquisite Mini", 1.55), ("Predator Elder", "Exquisite Mini", 1.45),
    ("T-800", "Exquisite Mini", 1.5), ("T-1000", "Exquisite Mini", 1.5),
    ("RoboCop", "Exquisite Mini", 1.45), ("ED-209", "Exquisite Mini", 1.5),
    ("Godzilla Heat Ray", "Special", 1.55), ("Kong Battle Damaged", "Special", 1.5),
    ("Ghidorah Gravity Beam", "Special", 1.55), ("Mechagodzilla Proton Scream", "Special", 1.55),
    ("Godzilla Burning", "Special", 1.55), ("Godzilla Atomic", "Special", 1.5),
    ("Alien Warrior", "Exquisite Mini", 1.45), ("Predator City Hunter", "Exquisite Mini", 1.5),
    ("T-800 Endoskeleton", "Exquisite Mini", 1.5), ("RoboCop Battle Damaged", "Special", 1.45),
    ("Godzilla 1954", "Classic", 1.5), ("Godzilla 1964", "Classic", 1.45),
    ("Anguirus", "Classic", 1.4), ("Rodan Classic", "Classic", 1.4),
    ("Mothra Classic", "Classic", 1.4), ("King Ghidorah Showa", "Classic", 1.5),
    ("Godzilla Minus One Battle", "Special", 1.55), ("Kong Axe", "Special", 1.5),
    ("Alien Covenant", "Exquisite Mini", 1.4), ("Predator Jungle Hunter", "Exquisite Mini", 1.5),
    ("T-800 Battle Damaged", "Special", 1.5),
], 2018, 3, 1, 55)

# Mondo
add(data, "mondo", "md", [
    ("He-Man", "1/6 Masters", 1.55), ("Skeletor", "1/6 Masters", 1.55),
    ("Battle Cat", "1/6 Masters", 1.5), ("Panthor", "1/6 Masters", 1.5),
    ("Teela", "1/6 Masters", 1.45), ("Man-At-Arms", "1/6 Masters", 1.45),
    ("Evil-Lyn", "1/6 Masters", 1.5), ("Beast Man", "1/6 Masters", 1.45),
    ("Stratos", "1/6 Masters", 1.4), ("Mer-Man", "1/6 Masters", 1.4),
    ("Trap Jaw", "1/6 Masters", 1.45), ("Tri-Klops", "1/6 Masters", 1.4),
    ("Orko", "1/6 Masters", 1.4), ("Hordak", "1/6 Masters", 1.5),
    ("She-Ra", "1/6 Masters", 1.5), ("Catra", "1/6 Masters", 1.5),
    ("TMNT Leonardo", "1/6 TMNT", 1.55), ("TMNT Michelangelo", "1/6 TMNT", 1.5),
    ("TMNT Donatello", "1/6 TMNT", 1.5), ("TMNT Raphael", "1/6 TMNT", 1.55),
    ("Shredder", "1/6 TMNT", 1.55), ("Krang", "1/6 TMNT", 1.5),
    ("Casey Jones", "1/6 TMNT", 1.45), ("April O'Neil", "1/6 TMNT", 1.4),
    ("He-Man Soft Goods", "Special", 1.55), ("Skeletor Soft Goods", "Special", 1.55),
    ("Leonardo Soft Goods", "Special", 1.55), ("Raphael Soft Goods", "Special", 1.55),
    ("He-Man Classic Colors", "Special", 1.5), ("Skeletor Classic Colors", "Special", 1.5),
    ("Battle Cat Soft Goods", "Special", 1.5), ("Panthor Soft Goods", "Special", 1.5),
    ("Shredder Soft Goods", "Special", 1.55), ("Krang Soft Goods", "Special", 1.5),
    ("Hordak Soft Goods", "Special", 1.5), ("She-Ra Soft Goods", "Special", 1.5),
    ("Teela Soft Goods", "Special", 1.45), ("Evil-Lyn Soft Goods", "Special", 1.5),
    ("Michelangelo Soft Goods", "Special", 1.5), ("Donatello Soft Goods", "Special", 1.5),
    ("Beast Man Soft Goods", "Special", 1.45), ("Man-At-Arms Soft Goods", "Special", 1.45),
    ("Trap Jaw Soft Goods", "Special", 1.45), ("Catra Soft Goods", "Special", 1.5),
    ("Casey Jones Soft Goods", "Special", 1.45),
], 2019, 2, 2, 200)

# SHFiguarts densify
add(data, "shfiguarts", "sf", [
    ("Goku Super Saiyan", "Dragon Ball", 1.5), ("Vegeta Super Saiyan", "Dragon Ball", 1.5),
    ("Gohan Super Saiyan", "Dragon Ball", 1.45), ("Piccolo", "Dragon Ball", 1.45),
    ("Frieza Final Form", "Dragon Ball", 1.5), ("Cell Perfect Form", "Dragon Ball", 1.5),
    ("Majin Buu", "Dragon Ball", 1.45), ("Goku Black", "Dragon Ball", 1.5),
    ("Naruto Sage Mode", "Naruto", 1.5), ("Sasuke", "Naruto", 1.5),
    ("Kakashi", "Naruto", 1.45), ("Itachi", "Naruto", 1.5),
    ("Iron Man Mark 85", "Avengers", 1.55), ("Captain America Endgame", "Avengers", 1.5),
    ("Thor Endgame", "Avengers", 1.5), ("Spider-Man No Way Home", "Avengers", 1.55),
    ("Doctor Strange Multiverse", "Avengers", 1.5), ("Scarlet Witch", "Avengers", 1.5),
    ("Batman The Batman", "DC", 1.55), ("Joker Folie a Deux", "DC", 1.5),
    ("Superman", "DC", 1.5), ("Wonder Woman 1984", "DC", 1.45),
    ("Ultraman", "Ultraman", 1.5), ("Ultraseven", "Ultraman", 1.45),
    ("Kamen Rider Zero-One", "Kamen Rider", 1.5), ("Kamen Rider Saber", "Kamen Rider", 1.45),
    ("Kamen Rider Revice", "Kamen Rider", 1.45), ("Kamen Rider Geats", "Kamen Rider", 1.5),
    ("Goku Ultra Instinct", "Special", 1.55), ("Vegeta Ultra Ego", "Special", 1.55),
    ("Naruto Kurama Link", "Special", 1.55), ("Sasuke Rinnegan", "Special", 1.55),
    ("Iron Man Mark 50", "Special", 1.55), ("Spider-Man Integrated Suit", "Special", 1.55),
    ("Batman Justice League", "Special", 1.5), ("Ultraman Trigger", "Ultraman", 1.45),
    ("Kamen Rider Faiz", "Kamen Rider", 1.5), ("Kamen Rider Kabuto", "Kamen Rider", 1.5),
    ("Goku Early Years", "Dragon Ball", 1.4), ("Vegeta Early Years", "Dragon Ball", 1.4),
    ("Frieza First Form", "Dragon Ball", 1.4), ("Cell First Form", "Dragon Ball", 1.4),
    ("Kakashi Anbu", "Special", 1.5), ("Itachi Anbu", "Special", 1.5),
    ("Doctor Strange Classic", "Special", 1.45),
], 2018, 1, 1, 75)

# Kaiyodo densify
add(data, "kaiyodo", "ky", [
    ("Amazing Yamaguchi Spider-Man", "Amazing Yamaguchi", 1.55), ("Amazing Yamaguchi Deadpool", "Amazing Yamaguchi", 1.55),
    ("Amazing Yamaguchi Wolverine", "Amazing Yamaguchi", 1.55), ("Amazing Yamaguchi Magneto", "Amazing Yamaguchi", 1.5),
    ("Amazing Yamaguchi Cyclops", "Amazing Yamaguchi", 1.45), ("Amazing Yamaguchi Storm", "Amazing Yamaguchi", 1.45),
    ("Amazing Yamaguchi Batman", "Amazing Yamaguchi", 1.55), ("Amazing Yamaguchi Joker", "Amazing Yamaguchi", 1.55),
    ("Amazing Yamaguchi Superman", "Amazing Yamaguchi", 1.5), ("Amazing Yamaguchi Harley Quinn", "Amazing Yamaguchi", 1.5),
    ("Amazing Yamaguchi Iron Man", "Amazing Yamaguchi", 1.5), ("Amazing Yamaguchi Captain America", "Amazing Yamaguchi", 1.5),
    ("Amazing Yamaguchi Venom", "Amazing Yamaguchi", 1.55), ("Amazing Yamaguchi Carnage", "Amazing Yamaguchi", 1.5),
    ("Amazing Yamaguchi Agent Venom", "Amazing Yamaguchi", 1.5), ("Amazing Yamaguchi Psylocke", "Amazing Yamaguchi", 1.45),
    ("Revoltech EVA-01", "Evangelion", 1.55), ("Revoltech EVA-02", "Evangelion", 1.5),
    ("Revoltech EVA-00", "Evangelion", 1.45), ("Revoltech EVA-13", "Evangelion", 1.5),
    ("Revoltech Godzilla", "Godzilla", 1.5), ("Revoltech Kong", "Godzilla", 1.45),
    ("Revoltech Ultraman", "Ultraman", 1.45), ("Revoltech Ultraseven", "Ultraman", 1.4),
    ("Amazing Yamaguchi Spider-Man Symbiote", "Special", 1.55), ("Amazing Yamaguchi Deadpool X-Force", "Special", 1.55),
    ("Amazing Yamaguchi Wolverine Brown", "Special", 1.55), ("Amazing Yamaguchi Batman Hush", "Special", 1.55),
    ("Amazing Yamaguchi Joker Killing Joke", "Special", 1.55), ("Amazing Yamaguchi Iron Man Bleeding Edge", "Special", 1.5),
    ("Revoltech EVA-01 Awakened", "Special", 1.55), ("Revoltech EVA-02 Beast", "Special", 1.5),
    ("Amazing Yamaguchi Nightcrawler", "Amazing Yamaguchi", 1.5), ("Amazing Yamaguchi Colossus", "Amazing Yamaguchi", 1.4),
    ("Amazing Yamaguchi Gambit", "Amazing Yamaguchi", 1.5), ("Amazing Yamaguchi Rogue", "Amazing Yamaguchi", 1.45),
    ("Amazing Yamaguchi Flash", "Amazing Yamaguchi", 1.4), ("Amazing Yamaguchi Green Lantern", "Amazing Yamaguchi", 1.4),
    ("Revoltech Mazinger Z", "Mecha", 1.5), ("Revoltech Getter 1", "Mecha", 1.5),
    ("Amazing Yamaguchi Spider-Gwen", "Amazing Yamaguchi", 1.5), ("Amazing Yamaguchi Miles Morales", "Amazing Yamaguchi", 1.5),
    ("Amazing Yamaguchi Thanos", "Amazing Yamaguchi", 1.55), ("Amazing Yamaguchi Doctor Strange", "Amazing Yamaguchi", 1.45),
    ("Revoltech Godzilla Minus One", "Special", 1.55),
], 2017, 2, 1, 90)

# Hasbro densify (ML / Black Series / Classified leftovers)
add(data, "hasbro", "hs", [
    ("Spider-Man", "Marvel Legends Retro", 1.4), ("Green Goblin", "Marvel Legends Retro", 1.4),
    ("Doctor Octopus", "Marvel Legends Retro", 1.4), ("Venom", "Marvel Legends Retro", 1.45),
    ("Carnage", "Marvel Legends Retro", 1.4), ("Hobgoblin", "Marvel Legends Retro", 1.35),
    ("Luke Skywalker", "Black Series Jedi", 1.45), ("Darth Vader", "Black Series Jedi", 1.5),
    ("Obi-Wan Kenobi", "Black Series Jedi", 1.45), ("Ahsoka Tano", "Black Series Jedi", 1.5),
    ("Din Djarin", "Black Series Mando", 1.5), ("Grogu", "Black Series Mando", 1.45),
    ("Bo-Katan", "Black Series Mando", 1.45), ("Boba Fett", "Black Series Mando", 1.5),
    ("Snake Eyes", "Classified Series", 1.45), ("Storm Shadow", "Classified Series", 1.45),
    ("Cobra Commander", "Classified Series", 1.5), ("Destro", "Classified Series", 1.45),
    ("Duke", "Classified Series", 1.4), ("Scarlett", "Classified Series", 1.4),
    ("Optimus Prime", "Studio Series 86", 1.5), ("Megatron", "Studio Series 86", 1.5),
    ("Bumblebee", "Studio Series 86", 1.45), ("Starscream", "Studio Series 86", 1.45),
    ("Grimlock", "Studio Series 86", 1.55), ("Hot Rod", "Studio Series 86", 1.45),
    ("Wolverine", "Marvel Legends X-Men 97", 1.5), ("Cyclops", "Marvel Legends X-Men 97", 1.45),
    ("Jean Grey", "Marvel Legends X-Men 97", 1.45), ("Storm", "Marvel Legends X-Men 97", 1.45),
    ("Beast", "Marvel Legends X-Men 97", 1.4), ("Rogue", "Marvel Legends X-Men 97", 1.5),
    ("Gambit", "Marvel Legends X-Men 97", 1.5), ("Morph", "Marvel Legends X-Men 97", 1.4),
    ("Rey", "Black Series Sequel", 1.4), ("Kylo Ren", "Black Series Sequel", 1.45),
    ("Finn", "Black Series Sequel", 1.35), ("Poe Dameron", "Black Series Sequel", 1.35),
    ("Baroness", "Classified Series", 1.45), ("Zartan", "Classified Series", 1.4),
    ("Firefly", "Classified Series", 1.4), ("Roadblock", "Classified Series", 1.35),
    ("Jazz", "Studio Series 86", 1.4), ("Prowl", "Studio Series 86", 1.4),
    ("Soundwave", "Studio Series 86", 1.5),
], 2020, 1, 1, 24.99)

# McFarlane densify
add(data, "mcfarlane", "mf", [
    ("Batman", "DC Multiverse Hush", 1.45), ("Superman", "DC Multiverse Hush", 1.4),
    ("Wonder Woman", "DC Multiverse Hush", 1.4), ("The Joker", "DC Multiverse Hush", 1.5),
    ("Harley Quinn", "DC Multiverse", 1.45), ("The Flash", "DC Multiverse", 1.4),
    ("Aquaman", "DC Multiverse", 1.4), ("Green Lantern", "DC Multiverse", 1.4),
    ("Batman", "DC Multiverse The Batman", 1.5), ("Penguin", "DC Multiverse The Batman", 1.4),
    ("Catwoman", "DC Multiverse The Batman", 1.45), ("Riddler", "DC Multiverse The Batman", 1.45),
    ("Spawn", "Spawn Classic", 1.5), ("Spawn", "Spawn Gunslinger", 1.45),
    ("Medieval Spawn", "Spawn", 1.5), ("Violator", "Spawn", 1.45),
    ("Angela", "Spawn", 1.4), ("Clown", "Spawn", 1.35),
    ("Batman Beyond", "DC Multiverse", 1.45), ("Batgirl", "DC Multiverse", 1.4),
    ("Nightwing", "DC Multiverse", 1.45), ("Red Hood", "DC Multiverse", 1.45),
    ("Deathstroke", "DC Multiverse", 1.5), ("Ra's al Ghul", "DC Multiverse", 1.45),
    ("Bane", "DC Multiverse", 1.45), ("Scarecrow", "DC Multiverse", 1.4),
    ("Two-Face", "DC Multiverse", 1.4), ("Mr. Freeze", "DC Multiverse", 1.4),
    ("Batman", "DC Multiverse Platinum", 1.5), ("Superman", "DC Multiverse Platinum", 1.45),
    ("Spawn", "Spawn Platinum", 1.55), ("Violator", "Spawn Platinum", 1.5),
    ("Batman", "DC Multiverse Gold Label", 1.5), ("Joker", "DC Multiverse Gold Label", 1.5),
    ("Harley Quinn", "DC Multiverse Gold Label", 1.45), ("Flash", "DC Multiverse Gold Label", 1.4),
    ("Darkseid", "DC Multiverse", 1.55), ("Steppenwolf", "DC Multiverse", 1.4),
    ("Cyborg", "DC Multiverse", 1.4), ("Martian Manhunter", "DC Multiverse", 1.45),
    ("Shazam", "DC Multiverse", 1.4), ("Black Adam", "DC Multiverse", 1.45),
    ("Page Punchers Batman", "Page Punchers", 1.35), ("Page Punchers Superman", "Page Punchers", 1.35),
    ("Page Punchers Spawn", "Page Punchers", 1.4),
], 2021, 1, 1, 22.99)

OUT.write_text(json.dumps(data, indent=2) + "\n")
counts = {k: len(v) for k, v in data.items()}
print(json.dumps(counts, indent=2))
print("TOTAL", sum(counts.values()))
print("NEW", sum(counts[k] for k in ["asmus","herocross","fanshobby","fansproject","transart","bingotoys","heatboys","ccstoys","tbleague","coomodel","did","moshow"]))
print("DENSIFY", sum(counts[k] for k in ["joytoy","sentinel","thousandtoys","spinmaster","freshmonkey","mafex","mezco","storm","hiya","mondo","shfiguarts","kaiyodo","hasbro","mcfarlane"]))

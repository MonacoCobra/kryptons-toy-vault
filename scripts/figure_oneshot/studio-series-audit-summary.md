# Hasbro Studio Series audit (plan only — NOT applied)

Built 2026-09-30 on top of main 5e0b9c7f. Source of truth: TFWiki Studio Series list (https://tfwiki.net/wiki/Studio_Series, raw wikitext fetched 2026-09-30). UPCs (TFW2005 Studio Series stock-photo/UPC thread) and retailer image filenames that carry the SS number were used only as corroboration.

Dry run: `python3 scripts/studio-series-audit.py`. Apply: `python3 scripts/studio-series-audit.py --apply` (not run).

## Counts

- Rows audited: 383 (371 Hasbro + 12 TakaraTomy Showzstore SS rows)
- correct: 120
- fixFields: 68
- merge: 111
- deleteInvented: 32
- unsure: 52
- Missing real releases (list only): 96 (81 figures, 8 multipacks, 7 package refreshes; 11 are 2027-wave announcements)
- Row delta if applied: 29,361 → 29,218 (−143 = 111 merges + 32 deletions)

## Findings

- d14ss-* numbers are made-up sequences (AOE 01–11, DOTM 12–28, 2007 70–79, ROTB 101–114, 86-01..27). Row identity was taken from character + film, and each number was then corrected from TFWiki.
- BBTS-wave rows (ss4/ss5/ss6/hs8/hs10) use placeholder $24.99 prices and made-up dates. Most are duplicates of tfss-* rows.
- Merge image fill: d14ss-bb-soundwave's image is an SS-62 Soundwave (ROTF Deluxe) package shot, so it is not copied onto tfss-ss83-soundwave (`noImageFill` in the plan). The only image filled is d14ss-dotm-chromia (UPC 630509900657 = 52 Chromia/Arcee/Elita-1).
- Many rows carry a SKU, UPC or image that belongs to a different product. These are flagged rather than changed; aliases move along with merges exactly as they are today.
- A year is changed only when it falls outside the TFWiki release year (with Oct–Dec / Jan–Feb tolerance) and is stored year-only ("2019", tagged `date-precision:year`), because no source gives the month. No YYYY-01-01 placeholder dates are written; `formatDate` shows a year-only date as just the year.

## Examples

- **d14ss-dotm-megatron** (fix): "SS-13 DOTM" → "SS-13 ROTF". UPC 630509652204 is 13 Megatron (ROTF) in the TFW2005 UPC thread; TFWiki: 13 Megatron, Revenge of the Fallen.
- **d14ss-2007-ironhide** (fix): "SS-77 2007 Film" → "SS-14 2007 Film", 2022 → 2018. UPC 630509707560 = 14 Ironhide (TFW2005); TFWiki 2018 Voyager 14 Autobot Ironhide.
- **tfss-ss80…85** (fix): 80 Brawn, 81 Wheeljack, 82 Ratchet, 83 Soundwave, 84 Ironhide, 85 Arcee were labelled "2007 Film". TFWiki lists all six as Bumblebee-film Cybertronians, so the film becomes "Bumblebee".
- **tfc-starscream-ss03** (fix): "DOTM SS-03" → "SS-06 2007 Film". TFWiki: 03 = Crowbar, 06 = Starscream (Transformers). The retailer image is starscream-06 with UPC 630509628179. d14ss-2007-starscream merges into it.
- **tfss-ss92-crosshairs** (fix+merge): "SS-92 AOE" → "SS-92 TLK" (TFWiki: 92 Crosshairs, The Last Knight). d14ss-aoe-crosshairs "SS-07 AOE" carries the same UPC 195166181677 and merges into it.
- **tfss-ss73-grindor** (fix): "SS-73 DOTM" → "SS-73 ROTF" (TFWiki: 73 Grindor & Ravage, Revenge of the Fallen).
- **d14ss-dotm-scavenger** (merge): "SS-27 DOTM" → tfss-ss55-scavenger. The retailer image is scavenger-55 (UPC 630509899401), and TFWiki has no DOTM Scavenger; 55 is the ROTF Leader.
- **ss5-ss-optimus-dotm** (fix): "Dark of the Moon" → "SS-44BB DOTM (Buzzworthy Bumblebee)", year 2023. Its SKU and image are the Buzzworthy 44BB Optimus Prime (TFWiki 2023 Buzzworthy Leader).
- **ss6-ss-predaking / abominus / bruticus / computron / defensor / menasor / superion** (delete): TFWiki has no Studio Series release of any G1 combiner. The rows are $24.99 placeholders with no SKU.
- **d14ss-86-kickback / sharpnel / bombshell** (delete): The Insecticons were never sold individually. TFWiki lists only the 2026 MTMTE Bombshell/Shrapnel/Kickback 3-pack, which is now on the missing list.
- **d14ss-rotb-strato, *-transit, d14ss-tlk-infernocus, d14ss-tlk-nitro, d14ss-aoe-slash/snooper/strafe, *-unicron, *-slag** (delete): No Studio Series release exists for these (TFWiki list; HasLab Unicron is War for Cybertron, not SS).
- **takaratomy-ss10 Jazz, ss11 Lockdown, ss13 Megatron, ss14 Ironhide, ss34 Megatron, ss-35 Jetfire** (unsure): These Showzstore Takara rows use Hasbro numbers. TFWiki TakaraTomy numbers are SS-09 Jazz, SS-10 Lockdown, SS-11 Megatron, SS-15 Ironhide, SS-27 Megatron and SS-26 Jetfire. Either the number is wrong or the row is a Hasbro release mislabelled takaratomy. Left untouched.

## Unsure (untouched)

- ss4-ss86-perceptor: Movie Perceptor = 86-11 (2022) or 2025 MTMTE Perceptor/Ratbat/Ramhorn pack; attached UPC suggests the exclusive.
- d14ss-86-starscream: "The Movie Starscream" matches 86-12 Coronation Starscream (2022 Leader) or 2026 MTMTE Voyager Starscream; attached SKU/image belongs to another product (GE +06 / Takara TS-10 / TF One Starscream).
- ss4-ss86-scourge: Scourge: claim (ROTB / Movie) and attached code (G2189 / ROTB Leader UPC) disagree; 101 (2023), 2026 ROTB refresh, 86-05 and 2026 MTMTE Scourge all exist.
- d14ss-86-megatron: "The Movie Megatron" = 2025 Leader, 2026 MTMTE Leader or 2026 Battle Damage LE; no evidence picks one (ss4 image suggests the BD exclusive).
- ss4-ss86-starscream: "The Movie Starscream" matches 86-12 Coronation Starscream (2022 Leader) or 2026 MTMTE Voyager Starscream; attached SKU/image belongs to another product (GE +06 / Takara TS-10 / TF One Starscream).
- ss4-ss86-megatron: "The Movie Megatron" = 2025 Leader, 2026 MTMTE Leader or 2026 Battle Damage LE; no evidence picks one (ss4 image suggests the BD exclusive).
- d14ss-86-cliff: Movie Cliffjumper = 86-13BB (2022) or 2026 Deluxe; code HSG2197 unverified.
- ss6-ss-scourge-rotb: Scourge: claim (ROTB / Movie) and attached code (G2189 / ROTB Leader UPC) disagree; 101 (2023), 2026 ROTB refresh, 86-05 and 2026 MTMTE Scourge all exist.
- tfss-ss-core-rumble: Claim "Core Class Blue" = 2022 Core Decepticon Rumble (Blue, The Movie), but attached UPC 5010996208316 / image is the 2024 Core Concept Art Rumble (Bumblebee film); row date 2023 fits neither.
- d14ss-86-ratchet: "The Movie Ratchet" = 2022 Core, 86-23 Voyager (2023) or 86-28 (2-pack); ss4 UPC 195166158532 is 82 Ratchet (Bumblebee film).
- tfc-optimus-rotb: ROTB Optimus Prime = 102BB (2023, Buzzworthy) or 102 (2025 regular line); $54.99 rows suggest a non-SS Leader. Rows may be duplicates of each other.
- d14ss-rotb-optimus: ROTB Optimus Prime = 102BB (2023, Buzzworthy) or 102 (2025 regular line); $54.99 rows suggest a non-SS Leader. Rows may be duplicates of each other.
- ss4-ss86-ratchet: "The Movie Ratchet" = 2022 Core, 86-23 Voyager (2023) or 86-28 (2-pack); ss4 UPC 195166158532 is 82 Ratchet (Bumblebee film).
- d14ss-86-ironhide: "The Movie Ironhide" = 86-17 Voyager, 2023 Core, or 86-24BB; attached UPC is the 2025 WFC Ironhide.
- d14ss-86-jazz: Movie Jazz = 86-01 (2021) or 2025 package refresh; no evidence picks one.
- d14ss-86-optimus: "The Movie Optimus Prime" = 86-31 Commander (2024), 86-31 Battle Damage LE (2025) or 2026 MTMTE Leader; no evidence picks one.
- ss4-ss86-optimus: "The Movie Optimus Prime" = 86-31 Commander (2024), 86-31 Battle Damage LE (2025) or 2026 MTMTE Leader; no evidence picks one.
- ss6-ss-optimus-rotb: ROTB Optimus Prime = 102BB (2023, Buzzworthy) or 102 (2025 regular line); $54.99 rows suggest a non-SS Leader. Rows may be duplicates of each other.
- ss5-ss-megatron-tlk: Only TLK Megatron in Hasbro SS is the 2027-wave Leader; d14ss row (2019) carries a 2023 Voyager UPC; ss5 row (2026) may be that Leader but unconfirmed.
- ss5-ss-grimlock-aoy: Grimlock: row claim (86 / AOE) and attached UPC (07BB Buzzworthy / Titan 2026) disagree; several real Grimlock releases fit.
- d14ss-2007-frenzy: No 2007-film Frenzy in Hasbro SS; attached UPC is 2024 Core Concept Art Frenzy (Bumblebee film).
- hs10-hs-43: Generic "Studio Series 86 <name>" BBTS placeholder; several Movie releases of the character exist and the SKU belongs to an unrelated product.
- ss5-ss-devastator-86: "86 Movie Devastator" is a retailer bundle of the six 2025 Movie Constructicons, not a Hasbro product; leave for manual decision.
- ss5-ss-ratchet-86: "The Movie Ratchet" = 2022 Core, 86-23 Voyager (2023) or 86-28 (2-pack); ss4 UPC 195166158532 is 82 Ratchet (Bumblebee film).
- hs8-hs-25: Grimlock: row claim (86 / AOE) and attached UPC (07BB Buzzworthy / Titan 2026) disagree; several real Grimlock releases fit.
- hs8-hs-24: "The Movie Starscream" matches 86-12 Coronation Starscream (2022 Leader) or 2026 MTMTE Voyager Starscream; attached SKU/image belongs to another product (GE +06 / Takara TS-10 / TF One Starscream).
- hs10-hs-35: SKU DK-32 / $80 looks like a third-party upgrade kit, not a Hasbro Studio Series figure; company fix is out of scope.
- d14ss-2007-bumblebee: 2007-film Bumblebee = 01/27 Clunker/49 Concept Camaro/27BB; attached UPC 630509984558 is 70 B-127 (Bumblebee film).
- hs8-hs-21: "The Movie Optimus Prime" = 86-31 Commander (2024), 86-31 Battle Damage LE (2025) or 2026 MTMTE Leader; no evidence picks one.
- hs10-hs-26: Generic "Studio Series 86 <name>" BBTS placeholder; several Movie releases of the character exist and the SKU belongs to an unrelated product.
- ss5-ss-megatron-86: "The Movie Megatron" = 2025 Leader, 2026 MTMTE Leader or 2026 Battle Damage LE; no evidence picks one (ss4 image suggests the BD exclusive).
- ss5-ss-optimus-86: "The Movie Optimus Prime" = 86-31 Commander (2024), 86-31 Battle Damage LE (2025) or 2026 MTMTE Leader; no evidence picks one.
- hs10-hs-24: Generic "Studio Series 86 <name>" BBTS placeholder; several Movie releases of the character exist and the SKU belongs to an unrelated product.
- hs10-hs-23: Generic "Studio Series 86 <name>" BBTS placeholder; several Movie releases of the character exist and the SKU belongs to an unrelated product.
- d14ss-tlk-drift: Claim TLK Drift = 2024 Deluxe Drift (TLK) or 36 Drift & Mini-Dinobots; attached image/UPC is 45 Drift (AOE).
- d14ss-aoe-snarl: No AOE Snarl in Hasbro SS; code HSG2188 unverified (Movie Snarl 86-19 or 2026 refresh).
- d14ss-bb-bumblebee: Bumblebee-film Beetle/Camaro Bumblebee exists as 18 (2018), 15 (w/ Charlie), 57 Offroad, 116 Beetle (2025); row gives no number/UPC that picks one (ss5 SKU is the 2026 AOE Bumblebee).
- d14ss-bb-shockwave: Bumblebee-film Shockwave = 2022 Core or 110 Voyager (2024); row is 2020/$39.99 and carries the 2026 Movie Shockwave code G2191.
- d14ss-dotm-longhaul: No DOTM Long Haul; Hasbro Long Haul = 42 ROTF Voyager (2019) or 2025 Commander Hook/Long Haul; attached UPC is the Commander.
- ss5-ss-bumblebee-bb: Bumblebee-film Beetle/Camaro Bumblebee exists as 18 (2018), 15 (w/ Charlie), 57 Offroad, 116 Beetle (2025); row gives no number/UPC that picks one (ss5 SKU is the 2026 AOE Bumblebee).
- d14ss-tlk-megatron: Only TLK Megatron in Hasbro SS is the 2027-wave Leader; d14ss row (2019) carries a 2023 Voyager UPC; ss5 row (2026) may be that Leader but unconfirmed.
- d14ss-tlk-bumblebee: TLK Bumblebee = 26 WWII Bumblebee (2019), 26BB, or 25 (2016 Camaro, Then & Now 2-pack); row gives no disambiguating evidence.
- d14ss-dotm-ironhide: No DOTM Ironhide in Hasbro SS; row number SS-14 suggests 14 (2007 film) but attached UPC 195166181592 is the 2022 Ironhide (84, Bumblebee film).
- d14ss-aoe-hound: No AOE Hound in Hasbro SS; code G2252 (2025 packaging) unverified.
- d14ss-aoe-bumblebee: AOE Bumblebee = 79BB High Octane (2021, Buzzworthy 2-pack) or 2026 Deluxe; row 2018 SS-01 has no evidence.
- afmon-hasbro-transformers-studio-series-leader-wave-5-case-of-2-hsg0374e: Retail case assortment (2 figures), not a single release.
- takaratomy-ss-35-studio-series-leader-class-jetfire-jet-fir: Showzstore Takara row uses the Hasbro number; TFWiki TakaraTomy list has Takara SS-26 Jetfire (SS-35 = KSI Boss). Either the Takara number is wrong or this is the Hasbro release mislabelled takaratomy.
- takaratomy-ss34-studio-series-34-ss-34-leader-class-megatr: Showzstore Takara row uses the Hasbro number; TFWiki TakaraTomy list has Takara SS-27 Megatron (SS-34 = Long Haul). Either the Takara number is wrong or this is the Hasbro release mislabelled takaratomy.
- takaratomy-ss11-studio-series-ss-11-deluxe-class-lockdown: Showzstore Takara row uses the Hasbro number; TFWiki TakaraTomy list has Takara SS-10 Lockdown (SS-11 = Megatron). Either the Takara number is wrong or this is the Hasbro release mislabelled takaratomy.
- takaratomy-ss10-studio-series-ss-10-deluxe-class-jazz: Showzstore Takara row uses the Hasbro number; TFWiki TakaraTomy list has Takara SS-09 Jazz (Takara SS-10 = Lockdown). Either the Takara number is wrong or this is the Hasbro release mislabelled takaratomy.
- takaratomy-ss14-studio-series-ss-14-voyager-class-ironhide: Showzstore Takara row uses the Hasbro number; TFWiki TakaraTomy list has Takara SS-15 Ironhide (SS-14 = Ratchet). Either the Takara number is wrong or this is the Hasbro release mislabelled takaratomy.
- takaratomy-ss13-studio-series-ss-13-voyager-class-megatron: Showzstore Takara row uses the Hasbro number; TFWiki TakaraTomy list has Takara SS-11 Megatron (SS-13 = Shadow Raider). Either the Takara number is wrong or this is the Hasbro release mislabelled takaratomy.

## Missing real releases (not added)

- 2018 Deluxe Class: 17 Shadow Raider (Age of Extinction)
- 2018 Deluxe Class: 18 Bumblebee (Bumblebee Beetle)
- 2018 Deluxe Class: 23 KSI Sentry (Age of Extinction)
- 2018 Voyager Class: 12 Decepticon Brawl (Transformers)
- 2018 Voyager Class: 21 Starscream (Revenge of the Fallen)
- 2018 Voyager Class: 09 Thundercracker (Dark of the Moon)
- 2018 Multi-packs: 15 Bumblebee (Bumblebee 1977 Camaro, w/ Charlie)
- 2018 Multi-packs: 19 Vol. 1 Retro Rock Garage (Bumblebee)
- 2018 Multi-packs: 20 Vol. 2 Retro Pop Highway (Bumblebee)
- 2018 Multi-packs: — Bumblebee Then & Now Two-Pack ()
- 2018 Multi-packs: 01 Bumblebee (Transformers 1977 Camaro)
- 2018 Multi-packs: 01 Bumblebee (Transformers 1977 Camaro)
- 2018 Multi-packs: 08 Decepticon Blackout (Transformers w/ Scorponok)
- 2019 Deluxe Class: 26 WWII Bumblebee (The Last Knight)
- 2019 Deluxe Class: 27 Clunker Bumblebee (Transformers)
- 2019 Deluxe Class: 30 Crankcase (Dark of the Moon)
- 2019 Deluxe Class: 41 Constructicon Scrapmetal (Revenge of the Fallen)
- 2019 Deluxe Class: 46 Dropkick (Bumblebee Javelin)
- 2019 Voyager Class: 37 Constructicon Rampage (Revenge of the Fallen)
- 2019 Voyager Class: 42 Constructicon Long Haul (Revenge of the Fallen)
- 2019 Voyager Class: 43 KSI Boss (Age of Extinction)
- 2019 Leader Class: 35 Jetfire (Revenge of the Fallen)
- 2019 Leader Class: 44 Optimus Prime (Dark of the Moon)
- 2019 Voyager Class: 31 Battle Damaged Megatron (Revenge of the Fallen)
- 2019 Leader Class: 48 As Seen In Parks Megatron (Transformers: The Ride – 3D)
- 2019 Multi-packs: 36 Autobot Drift & Dinobot&nbsp;'Tops, Dinobot&nbsp;Pterry, Dinobot&nbsp;Sharp&nbsp;T (The Last Knight)
- 2020 Deluxe Class: 49 Bumblebee (Transformers 2008 Concept Camaro)
- 2020 Buzzworthy Bumblebee Deluxe Class: 15BB Bumblebee (Bumblebee 1977 Camaro w/ Charlie)
- 2020 Buzzworthy Bumblebee Deluxe Class: 26BB WWII Bumblebee (The Last Knight)
- 2020 Buzzworthy Bumblebee Deluxe Class: 40BB Shatter (Bumblebee Plymouth)
- 2020 Buzzworthy Bumblebee Deluxe Class: 74BB Bumblebee (Revenge of the Fallen w/ Sam Witwicky)
- 2021 Deluxe Class: 70 B-127 (Bumblebee)
- 2021 Deluxe Class: 71 Autobot Dino (Dark of the Moon)
- 2021 Deluxe Class: 74 Bumblebee (Revenge of the Fallen w/ Sam Witwicky)
- 2021 Deluxe Class: 75 Jolt (Revenge of the Fallen)
- 2021 Buzzworthy Bumblebee Battle Packs: 18BB Bumblebee VS 46BB Dropkick (Bumblebee)
- 2021 Buzzworthy Bumblebee Battle Packs: 27BB Clunker Bumblebee VS 28BB Barricade (Transformers)
- 2021 Buzzworthy Bumblebee Battle Packs: 79BB High Octane Bumblebee VS 02BB Decepticon Stinger (Age of Extinction)
- 2022 Core Class: — Decepticon Rumble (Blue) (The Movie)
- 2022 Voyager Class: 86-04 Autobot Hot Rod (The Movie, package refresh) [package refresh]
- 2022 Deluxe Class: 77 N.E.S.T. Bumblebee (Bumblebee w/ "mini figure")
- 2022 Buzzworthy Bumblebee Deluxe Class: 70BB B-127 (Bumblebee)
- 2022 Multi-packs: — Movie 1 15th Anniversary Multipack (Transformers)
- 2022 Multi-packs: 86-18BB Autobot Hound (The Movie)
- 2022 Multi-packs: 94BB Hatchet (Dark of the Moon)
- 2022 Multi-packs: — Bumblebee (Bumblebee Beetle)
- 2023 Core Class: — Bumblebee (Dark of the Moon)
- 2023 Core Class: — Optimus Primal (Rise of the Beasts)
- 2023 Leader Class: 101 Scourge (Rise of the Beasts)
- 2023 Buzzworthy Bumblebee Deluxe Class: 96BB N.E.S.T. Autobot Ratchet (Dark of the Moon)
- 2023 Buzzworthy Bumblebee Voyager Class: 95BB N.E.S.T. Bonecrusher (Transformers)
- 2023 Buzzworthy Bumblebee Voyager Class: 102BB Optimus Prime (Rise of the Beasts)
- 2023 Buzzworthy Bumblebee Leader Class: 07BB Grimlock (Age of Extinction)
- 2023 Buzzworthy Bumblebee multi-packs: 86-24BB Ironhide / 86-20BB Prowl (The Movie)
- 2023 Multi-packs: — Movie 1 15th Anniversary Decepticon Multipack (Transformers)
- 2024 Core Class: — Concept Art Decepticon Rumble (Bumblebee)
- 2024 Core Class: — Concept Art Decepticon Frenzy (Bumblebee)
- 2024 Deluxe Class: — Drift (The Last Knight)
- 2024 Deluxe Class: — Gamer Edition Lifeline (Reactivate)
- 2024 Leader Class: 106 Optimus Primal (Rise of the Beasts, package refresh) [package refresh]
- 2024 Multi-packs: 86-27 Brawn / 86-28 Autobot Ratchet (The Movie)
- 2024 Multi-packs: — Revenge of the Fallen 15th Anniversary Autobot Multipack (Revenge of the Fallen)
- 2024 Multi-packs: 112 Optimus Prime (Limited Edition Battle Damage Ver.) (One)
- 2025 Deluxe Class: — Concept Art KSI Widow (Age of Extinction)
- 2025 Voyager Class: 102 Optimus Prime (Rise of the Beasts, package refresh) [package refresh]
- 2025 MTMTE Collection Voyager Class: — Optimus Prime (War for Cybertron)
- 2025 MTMTE Collection Voyager Class: — Megatron (War for Cybertron)
- 2025 MTMTE Collection Multi-packs: — Elite Seeker / Ground Soldier (Devastation)
- 2025 MTMTE Collection Multi-packs: — Autobot Perceptor / Ratbat / Ramhorn (The Movie)
- 2025 MTMTE Collection Multi-packs: — Revenge of the Fallen 3 Pack (Revenge of the Fallen)
- 2025 MTMTE Collection Multi-packs: 86-31 Optimus Prime (Battle Damage Limited Edition) (The Movie)
- 2026 Deluxe Class: — Bumblebee (Devastation)
- 2026 Deluxe Class: — Kranix (The Movie)
- 2026 Deluxe Class: — Bumblebee (Age of Extinction)
- 2026 Leader Class: — Astrotrain (The Movie)
- 2026 Leader Class: — Dinobot Snarl (The Movie, package refresh) [package refresh]
- 2026 Leader Class: — Blitzwing (The Movie)
- 2026 MTMTE Collection Voyager Class: — Scourge (The Movie, package refresh) [package refresh]
- 2026 MTMTE Collection Voyager Class: — Starscream (The Movie)
- 2026 MTMTE Collection Leader Class: — Megatron (The Movie)
- 2026 MTMTE Collection Leader Class: — Optimus Prime (The Movie)
- 2026 MTMTE Collection Multi-packs: — Insecticon Bombshell / Insecticon Shrapnel / Insecticon Kickback (The Movie)
- 2026 MTMTE Collection Multi-packs: — Optimus Prime (Energon Universe)
- 2026 MTMTE Collection Multi-packs: — Dinobot Grimlock (Battle Damage Limited Edition) / Autobot Wheelie (The Movie)
- 2026 MTMTE Collection Multi-packs: — Megatron (Battle Damage Limited Edition) (The Movie)
- 2027 Deluxe Class: — Shockwave (One)
- 2027 Deluxe Class: — Autobot Wheelie (The Movie)
- 2027 Deluxe Class: — Allicon (The Movie, package refresh from Earthrise) [package refresh]
- 2027 Deluxe Class: — Autobot Nautica (IDW Publishing)
- 2027 Deluxe Class: — Red Alert (The Transformers)
- 2027 Deluxe Class: — Crosshairs (Age of Extinction)
- 2027 Leader Class: — Megatron (The Last Knight)
- 2027 Leader Class: — Dinobot Swoop (The Movie, package refresh) [package refresh]
- 2027 Titan Class: — Scorn (Age of Extinction)
- 2027 Exclusives: — Seeker Storm Pack (The Transformers)
- 2027 Exclusives: — Shredhead (Energon Universe)

## Flags (not changed)

- ss6-ss-optimus-bb: msrp 24.99 looks wrong for Voyager
- ss4-ss86-cyclonus: msrp 24.99 looks wrong for Voyager
- ss4-ss86-soundwave: msrp 24.99 looks wrong for Leader
- tfss-ss-nemesis-2024: msrp 129.99 looks wrong for Leader
- hs8-hs-26: msrp 24.99 looks wrong for Voyager
- ss4-ss86-thundercracker: msrp 24.99 looks wrong for Voyager
- ss4-ss86-skywarp: msrp 24.99 looks wrong for Voyager
- ss6-ss-arcee-rotb: msrp 24.99 looks wrong for Core
- ss5-ss-megatron-dotm: msrp 24.99 looks wrong for Leader
- ss5-ss-optimus-dotm: msrp 24.99 looks wrong for Leader
- ss5-ss-optimus-aoy: msrp 24.99 looks wrong for Voyager
- tfc-starscream-ss03: msrp 24.99 looks wrong for Voyager
- tfss-ss56-shockwave: msrp 44.99 looks wrong for Leader
- tfss-ss55-scavenger: msrp 44.99 looks wrong for Leader

## Missing releases added (2026-09-30)

`scripts/studio-series-add-missing.py` + `studio-series-missing-plan.json`: 79 of the 96 missing TFWiki releases were added as new `tfss-*` rows (hasbro, Transformers Studio Series). All 79 have year-only dates tagged `date-precision:year`; 11 are 2027 announcements (source `tfwiki-studio-series-announce`). Multipacks are one row each with no set members, so no pack member duplicates an existing single. EAN/image/MSRP were added only where sourced: 4 EANs, 3 images, 2 MSRPs.

17 were skipped:
- 6 are cancelled per TFWiki: 86-18BB Hound, 94BB Hatchet, Buzzworthy Beetle Bumblebee, Core Optimus Primal, 2024 Deluxe Drift (TLK), and GE Lifeline.
- 11 already have an existing row carrying their EAN or product code: 70 B-127, 101 Scourge, 07BB Grimlock, Concept Art Rumble, Concept Art Frenzy, MTMTE Perceptor pack, 2026 AOE Bumblebee, 2026 Snarl refresh, 2026 MTMTE Leader Megatron, MTMTE WFC Optimus Prime, and MTMTE WFC Megatron.

New flag: tfss-ss-one-optimus and tfss-ss-one-megatron (labelled SS-112/SS-114 Transformers One Deluxe) carry the EAN and product image of the 2025 MTMTE War for Cybertron Voyager Optimus Prime (5010996346179) and Megatron (5010996346049). They were left unchanged.

## TF One follow-up (2026-09-30)

`scripts/studio-series-tfone-relabel.py`:
- tfss-ss-one-optimus and tfss-ss-one-megatron were relabelled as the 2025 MTMTE Collection War for Cybertron Voyager Optimus Prime and Megatron (Target exclusives; unnumbered on TFWiki). Changes: subtitle, class Voyager, year-only 2025, MSRP $34.99 per actionfigure411. Ids, EAN and image are unchanged.
- Added tfss-ss112-optimus-prime (TFWiki 2024 Deluxe "112 Optimus Prime (One)"): Hasbro G0221, EAN 5010996232328, MSRP $27.99 (shop.hasbro.com), cmdstore #112 image.
- Moved three TF One aliases to the new row: id:ss6-ss-optimus-tfone, TFSS-TF1-D-OPTIMUSPRIME, and G0221 (G0221 was previously on tfss-ss86-optimus-cmd).
- 114 Megatron (One) was not added: unsure row ss5-ss-megatron-tlk already carries its code HAS265216 and an image named 195166265216 (the F9849 TF One Megatron EAN). That row needs relabelling.

Further flags:
- tfss-ssge04-megatron has sku HASF9849, which is the TF One Megatron product number.
- tfss-ss-one-megatron still holds aliases id:ss6-ss-megatron-tfone and TFSS-TF1-D-MEGATRON, which are TF One Megatron identity.
- hs8-hs-21 holds alias HAS232328.

## SS-114 TF One Megatron (2026-09-30)

`scripts/studio-series-tfone-megatron.py`:
- ss5-ss-megatron-tlk is relabelled as SS-114 Transformers One Megatron: Deluxe, year-only 2024, UPC 195166265216, MSRP $27.99. The row carried code HAS265216 and an image named 195166265216 (Hasbro F9849).
- Aliases id:ss6-ss-megatron-tfone and TFSS-TF1-D-MEGATRON moved to it from tfss-ss-one-megatron. HAS265216, F9849 and HASF9849 were added as aliases on it.
- The wrong code HASF9849 was removed from tfss-ssge04-megatron (row sku and baked sku map). That row is otherwise unchanged; its image is still a Transformers One Deluxe image (flag).

## Step 5 — cleared wrong photo on tfss-ssge04-megatron (2026-09-30)

Removed the Transformers One Studio Series Deluxe photo from tfss-ssge04-megatron (oneshot imageUrl, image tags and figure-image-urls.json overlay). Recorded it in image-mismatch-audit.json `cleared` + `clearedUrlLedger`, following the clear_figure_image convention.

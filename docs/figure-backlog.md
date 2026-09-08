# Figure permanent archive (one-shot dump)

The permanent articulated **action figure** catalog is filled primarily by a
**one-shot dump** into `src/data/figure-archive/oneshot.json`, imported by
`src/data/figures.ts` and merged with the original seed (+ legacy batch-001).

Weekly Shopify New & Noteworthy ingest (`figure-storefronts.ts` →
`weekly-drop.ts`) stays separate for recent drops. Search, market, pulse, and
vault math read the permanent set via `FIGURES` / `mergeFigures`.

## Strategy

| Mode | Role |
| --- | --- |
| **One-shot dump (primary)** | Full Shopify pagination of AF storefronts + curated major-line expansions |
| Weekly N&N ingest | Live recent products (capped), real CDN images |
| Legacy batches | Optional only (`batch-NNN.json`); ~3-week cadence is **not** the growth plan |

Regenerate / refresh the dump:

```bash
cd scripts && python3 gen-figure-oneshot.py
```

## Scope

- **Release floor:** 1980-01-01 (modern → 1980; nothing older).
- **Brand universe:** `src/data/figure-backlog/company-universe.txt` — full [BigBadToyStore](https://www.bigbadtoystore.com) A–Z (~1599 names). Use for awareness; do **not** fabricate rows for every brand.
- **Segment:** articulated **action figures** only (skip board games, comics pubs, music, apparel, pins, dolls, plush, statue-only lines).
- **Images:** no generative AI art. Shopify rows carry real CDN `imageUrl` when present; curated rows use UI placeholders.

## Layout

| Path | Role |
| --- | --- |
| `src/data/figure-archive/oneshot.json` | Permanent dump rows (CatalogFigure-shaped) |
| `src/data/figure-archive/oneshot-stats.json` | Counts by source / shop |
| `src/data/figures.ts` | Seed `rows` + import/merge archive |
| `src/data/figure-backlog/manifest.json` | Strategy metadata + legacy batch ids |
| `src/data/figure-backlog/batch-NNN.json` | Optional legacy batches |
| `scripts/gen-figure-oneshot.py` | One-shot generator |
| `scripts/figure_oneshot/` | Shopify dump + curated tables |
| `src/lib/figure-storefronts.ts` | Weekly ingest storefront list (same shops) |

## Row / archive shape

Seed tuples in `figures.ts`:

```
[id, name, subtitle, line, company, kind, releaseDate, msrp, scale, demand, tags, extra?]
```

Archive JSON objects add optional `imageUrl`, `sku`, `exclusive`, and `source`
(`shopify` | `curated`). Deduplicate by **id** and by
**name|subtitle|line|company** (case-insensitive).

## Pricing / date conventions (curated)

When exact street date or MSRP is unknown:

- **Dates:** approximate month as `YYYY-MM-01` (or known wave month).
- **MSRP:** typical for the line (e.g. Marvel Legends ~$24.99, Black Series ~$24.99,
  Classified ~$24.99, One:12 ~$112, Hot Toys ~$350, SHF ~$75, MAFEX ~$95).
- Prefer real character / wave names; skip obscure BBTS brands without a feed
  rather than inventing filler SKUs.

## Honest coverage gaps

Shopify JSON is unavailable (or blocked) for many major makers: Hasbro Pulse,
BBTS, Entertainment Earth, NECA / Mezco / McFarlane official shops, Hot Toys,
Sideshow, Bandai Tamashii, threezero storefronts. Those are covered only via
**curated depth** (not complete catalogs) plus whatever appears on Super7 /
Mattel Creations / Hiya / Mondo / etc.

Most of the ~1599 BBTS brand names have **no** rows — by design (quality bar).

## Product rules

- Action figures only (articulated). No pins, dolls, statues-only, plush, apparel.
- Valid `CompanyId` values only (`src/lib/types.ts`).
- Existing `FIGURES` seed + weekly ingest must keep working.

## DC depth (2026-09-05)

Curated Mattel DCUC / JLU / Movie Masters, DC Direct & DC Collectibles,
McFarlane Multiverse densify, and Kenner Super Powers (≥1980) live in
`scripts/figure_oneshot/curated_dc.py` and merge via the oneshot dump.

## Hasbro / Super7 / DC Direct / Hot Toys densify (2026-09-05)

Curated expansions: more Marvel Legends, Black Series, Classified; Super7 ULTIMATES!/ReAction beyond Shopify; additional DC Direct/Collectibles waves; sparse Hot Toys (~50). Re-merged via `gen-figure-oneshot.py`.

## MotU / WWE / Mezco densify (2026-09-05)

Curated Mattel Masterverse + Origins lines (distinct from Shopify "Masters of the Universe" catch-all), WWE Elite Collection densify, and additional Mezco One:12 listable AF.

## JAKKS / Masterverse / BST AXN densify (2026-09-05)

`CompanyId` `jakks` added for Sonic the Hedgehog AF + MotU Primal Age. Further Masterverse leftovers (New Eternia / Revolution / Creations / Movie) and Loyal Subjects BST AXN curated densify merged via `gen-figure-oneshot.py --curated-only`.

## Image bake (2026-09-05)

Real Shopify CDN images for curated gaps: `scripts/bake-figure-images.py` →
`src/data/figure-image-urls.json` (+ oneshot `imageUrl` patches). See
`docs/figure-image-bake.md`. No AI art; high-confidence matches only.

## BBTS AF brand expansion (2026-09-05)

Company universe (`company-universe.txt`) lists ~1599 BBTS A–Z names for awareness.
This pass filled **CompanyId + curated starter depth** for collectors’ AF makers that
were missing or thin — **not** a row per universe brand.

| CompanyId | Notes |
| --- | --- |
| `takaratomy` | Transformers **MPG** (Masterpiece G) — listable releases |
| `playmates` | TMNT classic 1988–97 depth + Mutant Mayhem / Tales / Classic Collection reissues + Exo-Squad / related AF |
| `kaiyodo` | Amazing Yamaguchi + Revoltech starter |
| `jazwares` | Fortnite AF + AEW Unrivaled |
| `diamondselect` | Marvel Select + Diamond Select movie/TV AF |
| `joytoy` | Warhammer 40K + Dark Source |
| `beastkingdom` | Dynamic Action Heroes |
| `enterbay` | NBA 1:6 + movie AF |
| `funko` | Legacy Collection / AF only (**not** Pops) |
| densify | `storm`, `shfiguarts` (Tamashii), `threezero` |

Most of the ~1599 BBTS names still have **no** rows — by design (quality bar, AF-only).
Regenerate with `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 2 (2026-09-05)

Second curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art.

| CompanyId | Notes |
| --- | --- |
| `fourhorsemen` | **NEW** — Mythic Legions + Cosmic Legions + Figura Obscura |
| `spinmaster` | **NEW** — Bakugan AF (Battle Planet → Legacy) + early MotU Origins SM |
| `bandai` | Robot Spirits / Gundam Universe / G Frame / MSiA **AF** (not Gunpla kits) |
| densify | McFarlane DC/Spawn, NECA TMNT/Aliens/Horror, Storm, SHFiguarts |
| densify | Hasbro Lightning Collection (PR), GI Joe Classified, Marvel Legends |
| densify | ToyBiz classic ML, Loyal Subjects BST AXN, Boss Fight H.A.C.K.S. |
| densify | figma, Valaverse Action Force, Hiya, Mondo articulated, JAKKS WWE/Nintendo/Sonic, Hot Toys sparse |

Skipped (not AF / soft / statue-primary): Cosbaby, FREEing scales-only, Moose Goo Jit, Sideshow statues.

Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 3 (2026-09-05)

Third curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art. ACBA-adjacent and bare
**Fresh** brand skipped; Nano Metalfigs diecast skipped.

| CompanyId | Notes |
| --- | --- |
| `sentinel` | **NEW** — Fighting Armor / Riobot / Wonderful Acts |
| `thousandtoys` | **NEW** — 1000Toys Tough Guys + Synthetic Human |
| `acidrain` | **NEW** — Toys Alliance Acid Rain World / FAV / AG / B2Five |
| `freshmonkey` | **NEW** — Fresh Monkey Fiction + Fresh Retro AF |
| `jada` | **NEW** — Street Fighter AF + Universal Monsters / DC / Marvel AF |
| densify | Super7 ULTIMATES!/ReAction, Premium DNA, Hiya, Mondo, Beast Kingdom DAH |
| densify | Hot Toys sparse real, threezero DLX, Cosmic Legions (fourhorsemen) |
| densify | Mattel Creations leftovers, WWE Elite/Ultimate, Masterverse |
| densify | Hasbro Black Series + Marvel Legends BAFs, NECA Ultimate, Mezco One:12 |
| densify | Boss Fight H.A.C.K.S., Loyal Subjects BST AXN, McFarlane DC/Spawn |
| densify | Bandai Robot Spirits / Gundam Universe AF, SHFiguarts (Tamashii) |

Figura Obscura remains under `fourhorsemen`. Tamashii SHF stays `shfiguarts` (Bandai).
Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 4 (2026-09-05)

Fourth curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art. Skipped statue-primary
**Unique Art** / **XM Studios** and non-AF **Crossovers**.

| CompanyId | Notes |
| --- | --- |
| `blokees` | **NEW** — Galaxy Version Transformers + Gundam assembleable AF |
| `robosen` | **NEW** — sparse robotic Transformers (Flagship / Elite / Performance) |
| `newage` | **NEW** — third-party Transformers H-series |
| `fanstoys` | **NEW** — third-party Masterpiece-scale Transformers |
| `tunshi` | **NEW** — Tunshi Studio 1/12 Street Fighter / Mortal Kombat |
| `damtoys` | **NEW** — DamToys 1/12 Gangsters Kingdom / Pocket Elite / military |
| `easysimple` | **NEW** — Easy & Simple 1/12 PMC / SOF |
| `soldierstory` | **NEW** — Soldier Story 1/12 special ops |
| `minitimes` | **NEW** — Mini Times 1/12 military |
| `verycool` | **NEW** — Very Cool 1/12 female operative AF |
| densify | Hasbro ML / Black Series / Classified / Studio Series |
| densify | Mattel Masterverse / WWE Elite+Ultimate |
| densify | Super7, NECA Ultimate, Mezco One:12, McFarlane DC/Spawn |
| densify | Hiya, Mondo, SHFiguarts, Storm Collectibles |
| densify | Four Horsemen, Boss Fight, Loyal Subjects BST AXN, Playmates TMNT |
| densify | ToyBiz ML leftovers, Kenner Super Powers leftovers, DC Direct gaps |
| densify | Takara MPG leftovers / Diaclone reboot AF |

Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 5 (2026-09-05)

Fifth curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art. Skipped statue-primary
**Unique Art** and Medicom **Kubrick** (non-AF). MAFEX remains under `mafex`.

| CompanyId | Notes |
| --- | --- |
| `ironfactory` | **NEW** — third-party Transformers EX-series |
| `magicsquare` | **NEW** — third-party Transformers Light of Justice / B-series / combiners |
| `cangtoys` | **NEW** — third-party Transformers combiners + Beast Wars AF |
| `medicom` | **NEW** — Real Action Heroes 1/6 AF only (Kubrick skip; MAFEX stays `mafex`) |
| densify | SHFiguarts, Kaiyodo Revoltech / Amazing Yamaguchi |
| densify | Hasbro Lightning Collection / Classified / Marvel Legends / Black Series / Studio Series |
| densify | McFarlane DC/Spawn, NECA Ultimate, Super7 ULTIMATES!/ReAction |
| densify | DC Direct leftovers, Playmates TMNT, JAKKS Sonic/WWE/Nintendo/Primal Age |
| densify | Mezco One:12, Hiya, Storm Collectibles |

Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 6 (2026-09-05)

Sixth curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art. **APC Toys** and
**Unique Toys** are not listed in the BBTS A–Z universe dump (skipped). Statue /
garage-kit / DNA Design upgrade-kit brands skipped. Flame Toys **Furai** model
kits skipped (Kuro Kara Kuri articulated AF only).

| CompanyId | Notes |
| --- | --- |
| `drwu` | **NEW** — third-party Transformers EX / Mini / Combiner |
| `dx9` | **NEW** — third-party Transformers War in Pocket / K-series |
| `mastermind` | **NEW** — MMC Reformatted + Ocular Max |
| `maketoys` | **NEW** — MakeToys MTRM / MTCM |
| `planetx` | **NEW** — Planet X PX-series |
| `kfc` | **NEW** — Keiths Fantasy Club Phase / named |
| `xtransbots` | **NEW** — XTransbots MX-series |
| `flametoys` | **NEW** — Kuro Kara Kuri articulated mecha AF |
| `tfc` | **NEW** — TFC Toys combiners (Hercules / Uranos / Prometheus) |
| `gcreation` | **NEW** — GCreation ShuraKing / YX |
| densify | Kotobukiya Frame Arms / Hexa Gear (existing `kotobukiya`) |
| densify | SHFiguarts, Kaiyodo Revoltech / Amazing Yamaguchi |
| densify | Hasbro Lightning / Classified / Marvel Legends / Black Series / Studio Series |
| densify | Mattel Masterverse / WWE Elite+Ultimate |
| densify | McFarlane DC/Spawn, NECA Ultimate, Super7 ULTIMATES!/ReAction |
| densify | DC Direct leftovers, Playmates TMNT, Mezco One:12 |

Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 7 (2026-09-05)

Seventh curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art. **ToyWorld** and
**Unique Toys** are not listed in the BBTS A–Z universe dump (skipped). Statue /
garage-kit / Perfect Effect / DNA Design upgrade-kit brands skipped. Good Smile
kept under existing `figma` densify (Max Factory / GSC figma AF) — no separate
`goodsmile` CompanyId.

| CompanyId | Notes |
| --- | --- |
| `generationtoy` | **NEW** — third-party Transformers Gravity Builder / Sea King / Monster King |
| `zeta` | **NEW** — Zeta Toys ZA/ZB/ZE + combiners |
| `mechfans` | **NEW** — Mech Fans Toys MF-series |
| `toywolf` | **NEW** — ToyWolf W-series |
| `evolutiontoy` | **NEW** — Evolution-Toy ET-series |
| `starace` | **NEW** — Star Ace sixth-scale movie AF |
| `exo6` | **NEW** — EXO-6 Star Trek 1/6 AF |
| `blitzway` | **NEW** — Superb Scale / Carbotix / Ultraman AF |
| `toynami` | **NEW** — Robotech / Macross Valkyrie + characters |
| `creativebeast` | **NEW** — Beasts of the Mesozoic dinosaurs |
| `alertline` | **NEW** — 1/6 military AF |
| `snailshell` | **NEW** — 1/12 original tactical AF |
| densify | Bandai Robot Spirits / Gundam Universe AF (not Gunpla kits) |
| densify | figma (Max Factory / Good Smile) |
| densify | Beast Kingdom DAH, Enterbay, Hot Toys, threezero DLX/FigZero |
| densify | Valaverse Action Force, Premium DNA Filmation, Acid Rain |
| densify | Four Horsemen Mythic/Cosmic/Figura Obscura |
| densify | Jada Street Fighter / Universal / Nano, JAKKS Sonic/Nintendo/Primal Age |
| densify | ToyBiz Marvel Legends era, Kenner Super Powers / Batman movies |

Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 8 (2026-09-05)

Eighth curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art. **ToyWorld** and
**Unique Toys** are not listed in the BBTS A–Z universe dump (skipped). Statue /
garage-kit / Perfect Effect / DNA Design upgrade-kit brands skipped. Brick lines
(Pantasy / Keeppley) skipped.

| CompanyId | Notes |
| --- | --- |
| `asmus` | **NEW** — Asmus Toys LOTR / Hobbit / Witcher 1/6 |
| `herocross` | **NEW** — HeroCross Hybrid Metal Figuration |
| `fanshobby` | **NEW** — Fans Hobby Master Builder |
| `fansproject` | **NEW** — FansProject Causality / Function X / Seacon |
| `transart` | **NEW** — TransArt Beast Wars Metal + combiners |
| `bingotoys` | **NEW** — BingoToys BT-series |
| `heatboys` | **NEW** — Heatboys metal-style TF / mecha |
| `ccstoys` | **NEW** — CCS Toys Mortal Kombat 1/6 + 1/12 |
| `tbleague` | **NEW** — TBLeague / Phicen seamless 1/6 |
| `coomodel` | **NEW** — COO Model Empire / Nose Art / Paladin |
| `did` | **NEW** — DiD 1/6 military |
| `moshow` | **NEW** — MoShow Metal Build-style + Progenitor Effect |
| densify | JoyToy 40K / Dark Source, Sentinel Fighting Armor / Riobot |
| densify | 1000Toys Tough Guys / Synthetic Human, Spin Master Bakugan |
| densify | Fresh Monkey Fiction / Fresh Retro |
| densify | MAFEX, Mezco One:12, Storm Collectibles |
| densify | Hiya Godzilla / Exquisite Mini, Mondo 1/6 MotU+TMNT |
| densify | SHFiguarts, Kaiyodo Amazing Yamaguchi / Revoltech |
| densify | Hasbro ML / Black Series / Classified / Studio Series 86 |
| densify | McFarlane DC Multiverse / Spawn |

Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 9 (2026-09-05)

Ninth curated pass from the BBTS company universe — densify thin AF makers + add
missing collector brands. Floor 1980; AF only; no AI art. Statue / garage-kit /
Perfect Effect / DNA Design upgrade-kit brands skipped. Brick lines (Pantasy /
Keeppley) skipped. **ToyWorld** / **Unique Toys** / **APC Toys** not targeted.

| CompanyId | Notes |
| --- | --- |
| `mego` | **NEW** — World's Greatest Super Heroes + Marvel / Trek / Horror reissues |
| `worldbox` | **NEW** — 1/6 bodies + military / fantasy / sci-fi AF |
| `kaustic` | **NEW** — Kaustic Plastik 1/6 historical AF |
| `poptoys` | **NEW** — POP Toys EX-series 1/6 historical / fantasy |
| `deviltoys` | **NEW** — Devil Toys designer / Devilman / street AF |
| `kingarts` | **NEW** — King Arts diecast metal AF |
| `jtstudio` | **NEW** — JT Studio 1/6 movie / martial-arts AF |
| `artspirits` | **NEW** — Art Spirits Sonic / mecha / tokusatsu AF |
| `artstorm` | **NEW** — Art Storm Sonic / mecha AF |
| `fiftytwo` | **NEW** — 52Toys BeastBOX / MegaBOX transformable AF |
| `actiontoys` | **NEW** — Action Toys ES Gokin / Hero Action AF |
| `underverse` | **NEW** — Underverse 1/12 speculative AF |
| densify | NECA Ultimate, Super7 ULTIMATES!/ReAction, threezero DLX/FigZero |
| densify | Hot Toys MMS sparse, Beast Kingdom DAH, Enterbay NBA/movie |
| densify | Four Horsemen Mythic/Cosmic/Figura Obscura, Valaverse Action Force |
| densify | Boss Fight H.A.C.K.S., Loyal Subjects BST AXN, Jada SF/Universal/DC/Marvel |
| densify | Bandai Robot Spirits / Gundam Universe AF, Playmates TMNT, Mattel Masterverse/WWE |

Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## BBTS AF brand expansion wave 10 — FINAL (2026-09-05)

Tenth and **final** curated pass from the BBTS company universe — densify thin AF
makers + add missing collector brands. Floor 1980; AF only; no AI art. Statue /
garage-kit / Perfect Effect / DNA Design upgrade-kit brands skipped. Brick lines
skipped. MegaHouse scales-only, Kids Logic statue-leaning, Quantum Mechanix
diorama-leaning, and Super Duck accessory-head lines skipped.

| CompanyId | Notes |
| --- | --- |
| `haoyu` | **NEW** — HaoYu Toys 1/6 WWII / modern military / historical |
| `bigchief` | **NEW** — BIG Chief Studios Doctor Who / film 1/6 |
| `iconiq` | **NEW** — Iconiq Studios SF / MK / iconic 1/6 |
| `figurestoy` | **NEW** — Figures Toy Company retro WGSH-style 8" |
| `toynotch` | **NEW** — Toy Notch 1/6 Asian historical |
| `actoys` | **NEW** — ACToys 1/6 modern military / PMC |
| `newwave` | **NEW** — New Wave Toys Replicade + arcade ReAction-style |
| `flirtygirl` | **NEW** — Flirty Girl Collectibles 1/6 female AF |
| `firegirl` | **NEW** — Fire Girl Toys 1/6 tactical / cyber female AF |
| `i8toys` | **NEW** — i8Toys 1/6 military / sci-fi / fantasy |
| `nanmu` | **NEW** — Nanmu Studio dinosaur / prehistoric creature AF |
| `vtoys` | **NEW** — VTOYS 1/6 bodies + military / fantasy / sci-fi |
| densify | Hasbro ML / Black Series / Classified / Studio Series / Lightning |
| densify | McFarlane DC Multiverse / Spawn, Mezco One:12, MAFEX |
| densify | Storm Collectibles, Hiya Godzilla/Exquisite, Mondo 1/6 |
| densify | SHFiguarts, Kaiyodo Amazing Yamaguchi / Revoltech, figma |
| densify | JAKKS Sonic/Nintendo/Primal Age, JoyToy 40K/Dark Source |
| densify | Sentinel Fighting Armor / Riobot, Kenner Super Powers / Batman movies |

**No wave 11.** Regenerate: `python3 scripts/gen-figure-oneshot.py --curated-only`.

## Small brands: Blokees / Jada / JAKKS / Yolopark / SoSkill (2026-09-07)

CompanyIds `yolopark` + `soskill` added. Blokees refreshed from first-party Shopify;
Yolopark AMK kits from shop.yolopark.com; Jada/JAKKS densified from specialty
`product-sku-index` (GTIN when known). SoSkill reserved with **no rows** until a
verified GTIN/image feed exists (see `docs/figure-storefronts.md` rejected list).
Listing codes demoted to aliases; Nano Metalfigs removed from Jada.

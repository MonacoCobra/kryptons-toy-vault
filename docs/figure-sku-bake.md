# Figure SKU bake (accurate storefront / specialty SKUs)

Fills missing `sku` on permanent-archive oneshot action figures using **real
Shopify variant SKUs** (barcode/GTIN fallback only when `variant.sku` is empty).
Never invents codes. Same high-confidence company/line/name/subtitle matcher as
image bake (`scripts/bake-figure-images.py`).

## What it does

1. Re-paginates first-party AF storefronts (`figure_oneshot/shopify_dump.STOREFRONTS`)
   plus specialty retailer feeds used for image bake (`RETAILER_FEEDS`).
2. Builds `src/data/figure-archive/product-sku-index.json` (product → sku[/barcode]).
3. Matches oneshot rows that lack `sku`:
   - **Exact** `sf-{shop}-{handle}` for native Shopify archive rows
   - **Fuzzy** high-confidence (`minScore` 18, same-company gate, line-family rules)
4. Writes:
   - patches `sku` on matched `oneshot.json` rows (+ `sku-bake` / `sku:{shop}` tags)
   - `src/data/figure-sku-map.json` — id → sku overlay
   - `src/data/figure-archive/sku-bake-stats.json` — before/after report

Existing non-fake SKUs are **never** overwritten. One SKU and one product index
id assign to at most one figure.

## Run

```bash
cd /workspace/collection-app/scripts
python3 bake-figure-skus.py --fetch          # live pagination + match
python3 bake-figure-skus.py --cache-only     # reuse product-sku-index.json
python3 bake-figure-skus.py --dry-run --cache-only
```

## Honest leftovers

Hasbro Pulse, BBTS, Entertainment Earth, Mezco official, Hot Toys, Sideshow,
Bandai Tamashii US, MAFEX/Medicom first-party, threezero, and Takara Tomy mall
still lack a stable public `products.json` we verified — do not scrape them.

Densify / BBTS-wave curated placeholders without a clear specialty-retailer
title cue stay SKU-less. Bundle/multipack Shopify rows with null `variant.sku`
stay empty. JLU / DCUC blocked families stay empty.

## Coordinate

Do not expand catalog rows except `sku` (and bake tags). Comic UPC workers may
touch `comic-upc-map.json` / LOCG caches — leave those files alone.

**No Build Publish** for data-only bumps (Lyra publishes).

## Feed probe notes (2026-09-06)

**Added (verified open `products.json` + non-empty `variant.sku`):**
- `staractionfigures` — https://www.staractionfigures.co.uk (Hasbro ML/BS/Classified, McFarlane)
- `toydojo` — https://www.toydojo.com (SHFiguarts / Bandai / Hasbro / MAFEX / Mezco)
- `toynk` — https://www.toynk.com (mixed specialty; bag clips/costumes skipped via `RETAILER_SKIP`)
- `indemandtoys` — https://www.indemandtoys.co.uk (UK AF specialist; Hasbro ML/BS/Classified/TF + Mattel/NECA)
- `hobbyfigures` — https://www.hobbyfigures.co.uk (UK import; Hasbro/McFarlane/SHF/MAFEX; nendoroid/scale skipped)

**Also this pass:** raised `maxPages` on truncated Shopify catalogs (toyarena/cmdstore/toynk/afac/japan-figure/solarisjapan/shop-mattel) up toward the ~page-100 products.json ceiling.

**Probed and rejected (no usable AF SKU feed):**
- FYE / CultureFly / Kidrobot / Iron Studios / QMx — wrong product mix (music, vinyl art, statues, Q-Fig)
- Soap Studio — `products.json` open but `variant.sku` empty (or weak AF)
- Travelling Man — comics/games dominant
- ShowZ Store — timeout / unreliable
- Kapow Toys — not Shopify (HTML storefront)
- Action Figure Essentials — open JSON but empty `variant.sku`
- Hobbytron / Toyworld NZ / Ozzie Collectables / Character Options — wrong mix or too few AF
- Popcultcha, HLJ, AmiAmi, Forbidden Planet, TFSource, Diamond Select, Playmates official, JAKKS, McFarlane official, The Chosen Prime, Brian's Toys, Figure Realm, Robot Kingdom — 403/404/HTML/non-Shopify
- Pulse / BBTS / EE / Mezco / Hot Toys / Tamashii / MAFEX 1P / threezero / Takara mall / Sideshow — still blocked or no public JSON (reconfirmed)

### Pass 2026-09-06 night
**Added (verified open `products.json` + non-empty `variant.sku`):**
- `collecticon` — https://www.collecticontoys.com (Hasbro TF/ML/BS, McFarlane, NECA, Mattel Origins; comic product_type skipped)
- `nerdzoic` — https://nerdzoic.com (Hasbro/Mattel/McFarlane/NECA/Four Horsemen/Mezco One:12; GW/Warhammer skipped)

**Probed and rejected this pass:**
- hobbytron — RC drones/helis dominant (wrong mix)
- toyworldnz — general toy/plush/LEGO (too few AF)
- ironstudios / culturefly / fye / kidrobot / soapstudio / qmx — statues/vinyl/merch (reconfirmed)
- cherrybombtoys / mintedstore / tokullectibles / actionfigureessentials — empty or weak `variant.sku`
- actioncity — Hot Toys / blind-box dominant
- notjusttoyz / popcultcha / brianstoys / thechosenprime / tfsource / diamondselect / Pulse/BBTS/EE/Mezco/McFarlane official/Hot Toys/threezero/Sideshow — 403/404/non-Shopify/blocked
- sifi-toys — open JSON but page-1 AF brand infer too thin to trust without deeper cool-down pass
- kitsap-comics-and-games — open JSON + SKUs on page1 but deep infer blocked by Shopify 429 this pass (deferred)

**Bake result:** 8181 → 8476 / 19085 (42.87% → 44.41%), +295 assigned; index 38203 → 39920. New shop tags: collecticon 54, nerdzoic 35. Hasbro leftovers 619→508; NECA 270→229; McFarlane 277→256; Mattel 675→643.

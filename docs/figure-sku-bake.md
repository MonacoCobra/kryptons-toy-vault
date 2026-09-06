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

**Probed and rejected (no usable AF SKU feed):**
- FYE / CultureFly / Kidrobot / Iron Studios / QMx — wrong product mix (music, vinyl art, statues, Q-Fig)
- Soap Studio — `products.json` open but `variant.sku` empty
- Travelling Man — comics/games dominant
- ShowZ Store — timeout / unreliable
- Popcultcha, HLJ, AmiAmi, Forbidden Planet, TFSource, Diamond Select, Playmates official, JAKKS, McFarlane official — 403/404/HTML/non-Shopify
- Pulse / BBTS / EE / Mezco / Hot Toys / Tamashii / MAFEX 1P / threezero / Takara mall / Sideshow — still blocked or no public JSON (reconfirmed)


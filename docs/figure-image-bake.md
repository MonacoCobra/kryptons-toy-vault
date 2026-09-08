# Figure image bake (real product photos)

Fills missing `imageUrl` on curated/placeholder action figures using **real
Shopify CDN product images** — never generative AI art. Analogous to
`comic-cover-urls.json`, but sourced from AF storefront `products.json`.

## What it does

1. Builds a searchable product index (normalized name / subtitle / line /
   company tags → CDN `imageUrl`) from the same shops as
   `src/lib/figure-storefronts.ts` / `scripts/figure_oneshot/shopify_dump.py`.
2. **SKU-first** (optional `--sku-first`): exact-join `oneshot.sku` →
   `product-sku-index` product `imageUrl`, overwriting fuzzy mismatches.
3. Fuzzy-matches remaining oneshot rows that lack `imageUrl` (high-confidence only);
   never overwrites an `image-sku` proven URL.
4. Writes:
   - `src/data/figure-image-urls.json` — id → URL overlay
   - patches `imageUrl` on matched `oneshot.json` rows
   - `src/data/figure-archive/image-bake-stats.json` — before/after report

`figures.ts` resolves `imageUrl` as **row/archive URL first**, then baked map
(`resolveFigureImageUrl`). `FigureArt` already prefers `figure.imageUrl`.

## Run

```bash
# Fast: index from existing oneshot Shopify rows
cd scripts && python3 bake-figure-images.py

# Live: re-paginate storefronts (polite delays), cache index, then match
cd scripts && python3 bake-figure-images.py --fetch
```

## Safeguards (false-match controls)

- Same-`company` hard gate (no Marvel Legends ← Super7 ULTIMATES swaps).
- Blocked families with no honest feed line: JLU, DCUC, DC Direct/Collectibles.
- Line-family regex required when known (Masterverse, Origins, ULTIMATES!,
  ReAction, BST AXN, WWE, Multiverse, TMNT, etc.).
- Character-focused matching: for ULTIMATES!/ReAction header titles, the
  character is taken from the subtitle.
- First significant name token must appear; multi-token subtitles need ≥1 hit.
- Multi-token names need more than a lone shared honorific; color antonyms; hyphen-prefix only.
- Word-boundary token hits (no "he" ⊂ "the"); MOTU trailing-character peel.
- One product image URL assigns to at most one figure id (best score wins; variants may not share a CDN shot).
- Prefer product titles that include distinguishing subtitle/wave tokens (e.g. Hush, Knightfall, wave numbers).
- After rematch, any remaining shared `imageUrl` keeps the best-scoring row; others clear back to placeholder.
- Unmatched rows stay as CSS placeholders.

## Honest leftovers

Hasbro Pulse, Mezco official, Hot Toys, Bandai Tamashii first-party, threezero,
and DCUC/JLU curated rows still lack honest first-party feeds. Specialty retailers
can fill many Hasbro / SHF / MAFEX / Mezco One:12 / Playmates / JAKKS / Toy Biz /
classic DC Direct / Four Horsemen / Kaiyodo / Loyal Subjects BST rows when titles are unambiguous.
Densify placeholders without a real SKU stay empty — do not scrape Pulse/BBTS.

## Weekday-friendly `--fetch`

Preferred cadence: **weekday mornings** (America/Chicago), after restocks land.

```bash
cd /workspace/collection-app/scripts
python3 bake-figure-images.py --fetch
```

- Polite pagination delays are built in (~0.12s/page).
- Writes/refreshes `src/data/figure-archive/product-image-index.json` then matches.
- `--cache-only` reuses the cached index (no network).
- Default (no flags) merges oneshot Shopify rows + any cached index.
- Commit updated JSON only when match counts move. **No Build Publish** for data-only bumps.

Hasbro Pulse / BBTS / Mezco official / Hot Toys / Tamashii first-party still lack
stable public `products.json`. Bake `--fetch` also indexes specialty retailers
(ToyArena, CmdStore, Planet AF, Cool Toy Den, AFCollector, Legendz Toys, shop.mattel,
Solaris Japan, JB Hi-Fi, ActionFiguresAndComics, Japan Figure) + Storm Collectibles HK +
Store Horsemen for high-confidence Hasbro / Mattel MOTU / Mezco One:12 / MAFEX /
SHFiguarts / Playmates / JAKKS / Toy Biz / classic DC Direct / Four Horsemen / Kaiyodo /
Loyal Subjects BST matches. Leftovers without clear title cues stay placeholders.


## SKU-first rematch (preferred)

Fuzzy name/line matching can attach the wrong specialty-retailer CDN shot.
When a figure already has a real `sku`, the correct photo is the product image
for that exact SKU in `product-sku-index.json` (same feeds as SKU bake).

```bash
cd /workspace/collection-app/scripts
# Exact SKU → imageUrl join; overwrite mismatched prior bake images; no fuzzy
python3 bake-figure-images.py --cache-only --sku-first --sku-only

# SKU-first, then fuzzy gap-fill for rows still missing art (never overwrites image-sku)
python3 bake-figure-images.py --cache-only --sku-first
```

- Builds `sku → imageUrl` from `product-sku-index.json` (prefers first-party tier).
- Tags SKU-proven rows with `image-sku` (+ `imgsku:{shop}` provenance).
- Strict 1:1 URL and 1:1 SKU; SKU-proven rows win shared-URL conflicts.
- Writes `sku-image-rematch-stats.json` with `changedMismatch` / `filledEmpty` counts.
- Fuzzy `--rematch` keeps `image-sku` overlays (does not clear them).

## Rematch (strict 1:1)

```bash
cd /workspace/collection-app/scripts
# Reuse cached product-image-index.json; clear prior image-bake overlays; re-assign 1:1
python3 bake-figure-images.py --cache-only --rematch
```

Near-duplicate densify rows (same character + filler Wave/Classic subtitle):

```bash
python3 dedupe-figure-oneshot.py          # write
python3 dedupe-figure-oneshot.py --dry-run
```


## Image mismatch audit

Wrong specialty / Mephitsu / fuzzy CDN shots (same class of bug as Elektra D&W
showing Skrull Elektra & Ronin pack art) are cleared by:

```bash
cd /workspace/collection-app
python3 scripts/audit-figure-image-mismatches.py              # dry-run report
python3 scripts/audit-figure-image-mismatches.py --apply       # clear high-confidence
python3 scripts/audit-figure-image-mismatches.py --apply --refill  # + GTIN-proven refill
```

Rules (conservative — prefer empty/placeholder over wrong photo):

- Audits every figure with `oneshot.imageUrl` and/or `figure-image-urls.json`
  overlay (`resolveFigureImageUrl` falls through to the overlay, so **both**
  must be cleared).
- **GTIN path:** primary GTIN → `product-sku-index` title hard-disagrees
  (multipack→single, Skrull/theme clash, score_reject+char_missing) → clear.
- **URL path:** image URL indexed under a product whose title hard-disagrees
  (and no co-indexed product high-matches) → clear.
- Soft flags are reported only. Never invents SKUs/images.
- `--refill` re-attaches only when the figure’s GTIN product title
  high-confidence matches (score ≥ 22, contiguous name, never multipack→single).
- Writes `src/data/figure-archive/image-mismatch-audit.json`.
- Mephitsu bake refuses to re-apply URLs listed in this report (and the SKU
  mismatch audit report). Comics/UPC untouched.

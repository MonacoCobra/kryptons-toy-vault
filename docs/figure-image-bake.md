# Figure image bake (real product photos)

Fills missing `imageUrl` on curated/placeholder action figures using **real
Shopify CDN product images** — never generative AI art. Analogous to
`comic-cover-urls.json`, but sourced from AF storefront `products.json`.

## What it does

1. Builds a searchable product index (normalized name / subtitle / line /
   company tags → CDN `imageUrl`) from the same shops as
   `src/lib/figure-storefronts.ts` / `scripts/figure_oneshot/shopify_dump.py`.
2. Fuzzy-matches oneshot rows that lack `imageUrl` (high-confidence only).
3. Writes:
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
- One product image assigns to at most one figure (best score wins).
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

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

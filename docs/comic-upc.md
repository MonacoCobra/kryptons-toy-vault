# Comic UPC / ISBN identity (LOCG-first)

## Why

Cover art must match the **actual issue** (especially vs A/B variants). UPC/ISBN is the durable identity key. Variant side-scroll on comic detail is live (see below); mass UPC backfill continues separately.

## Sources (priority)

1. **League of Comic Geeks** — primary UPC/ISBN on issue pages (`UPC` / `ISBN` fields). Never invent codes.
2. **LOCG CSV import** — `src/lib/locg-import.ts` already maps `upc` / `isbn` / `upc/isbn` headers into `LocgRow.upc` when the export includes them. Shelby’s current profile export often omits the column; use issue-page lookup or a fuller export when available.
3. **Comic Vine `barcode`** — optional fallback only when LOCG has no code (many pre-barcode / older issues).

No generative AI art. Covers come from LOCG CDN or Comic Vine scans.

## Runtime

- `CatalogComic.upc` merges `comics.ts` extras + `src/data/comic-upc-map.json`.
- Cover prefer order: explicit `extra.cover` → **UPC map LOCG cover** → `comic-cover-urls.json` → live `getComicCover`.
- `getComicCover` (`src/lib/comic-covers.ts`): **UPC / LOCG id first**, then Comic Vine series+issue(+variant). Caches in `comic_covers` (see migration `0007_comic_covers_upc.sql`).

## Backfill

```bash
python3 scripts/backfill-comic-upcs.py --seeds-only --limit 40 --delay 30
python3 scripts/backfill-comic-upcs.py --from-catalog --limit 220 --max-minutes 85 --delay 30 --cv-sweep
```

| Flag | Meaning |
|------|---------|
| `--delay 30` | Default. Matches LOCG `robots.txt` Crawl-delay. |
| `--seeds-only` | Only `src/data/comic-locg-seeds.json` rows with `locgId`. |
| `--from-catalog` | Rank popular modern singles (barcode era) missing UPC. |
| `--ones-only` | Only issue #1 / 0 / nn (best LOCG discovery rate). |
| `--min-year` | Cover-year floor for catalog mode (default 1995). |
| `--max-minutes` | Stop starting new LOCG work after N minutes. |
| `--cv-sweep` | After LOCG pass, Comic Vine barcode sweep for leftovers. |
| `--only id,id` | Explicit catalog ids. |
| `--no-cv` | Skip Comic Vine barcode fallback. |

Writes:

- `src/data/comic-upc-map.json`
- updates `src/data/comic-cover-urls.json` when LOCG cover is verified
- `scripts/comic-upc-backfill-stats.json`
- `scripts/comic-locg-series-cache.json` (seriesId + issue→locgId map)

Seeds live in `src/data/comic-locg-seeds.json` (numeric LOCG comic ids + slugs). Discovery without a seed: publisher-matched series search → series issue list → main-cover locgId (not only #1). Foreign editions rejected.

## Honest leftovers

- Pre-UPC era / many 1970s–80s floppies: LOCG often has **no UPC** — we still store `locgId` + cover when known.
- Reprints vs originals: prefer first-print LOCG ids in seeds; verify title/publisher on fetch.
- Full 35k+ archive: not fully backfilled in one weekday pass — rate limit is ~2 LOCG pages/minute. Re-run with more seeds over time.
- User LOCG CSV without UPC column cannot populate barcodes until re-exported with that field or issue pages are fetched.


## Variant side-scroll (detail)

Catalog/list cards stay on the **primary / Cover A** issue (`collapseComicVariants`). On comic detail (`/comics/$comicId`), a horizontal snap-scroller lists **real** open-order variants for the same family:

- Grouping key: normalized `series` + `issue` + `publisher` (`comicFamilyKey` in `src/lib/comic-variants.ts`)
- Helper: `getComicVariants(comic, catalog)` — only rows already in baked + live merge; never invents covers
- Tap a thumb → navigate to that catalog id (cover, UPC, badges, own/wishlist follow the id)
- Same `format` + cover **year** soft-filter; hidden when only one cover; reboot/facsimile collisions without variant/UPC differentiation are not treated as open-order variants
- Labels use `CatalogComic.variant` (fallback **Cover A**)

As LOCG/UPC backfill adds Cover B / virgin / etc. rows, the strip populates automatically. Do not invent sample issues for demos.

## Profile

Collection context: https://leagueofcomicgeeks.com/profile/KryptonsToyVault/collection

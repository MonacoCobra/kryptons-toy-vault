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

## Catalog growth from real LOCG series (not gen-batch)

Highest-trust way to add **new** `comics.ts` rows after the catalog prune:
walk real League of Comic Geeks series → issue pages. Script:
`scripts/ingest-locg-series-to-catalog.py`.

Hard gates on every new row: real LOCG page, `locgId`, UPC and/or cover URL,
LOCG series/issue/publisher (never invented), no duplicate catalog id or
`locgId`. Failed issues are skipped. UPC/cover/`locgId` merge into
`comic-upc-map.json` / `comic-cover-urls.json` without clobbering a stronger
existing UPC.

**Glyph / Lyra:** feed numeric LOCG series ids (Image / Boom / IDW / Dark Horse
/ indie first). Pull ids from `scripts/comic-locg-series-cache.json` (`seriesId`)
or a series URL. Do **not** invent ids, UPCs, or interpolated ghost rows. Do
**not** run `gen-batch-*`.

```bash
# List preferred cache seeds (no LOCG traffic)
python3 scripts/ingest-locg-series-to-catalog.py --list-cache-seeds

# Dry-run a real series (polite 30s Crawl-delay)
python3 scripts/ingest-locg-series-to-catalog.py --series-id 148147 --delay 30 --max-issues 10 --dry-run

# Mass file (one id per line; see scripts/locg-series-ids.example.txt)
python3 scripts/ingest-locg-series-to-catalog.py --series-ids-file scripts/locg-series-ids.example.txt --delay 30

# Fixture proof (no live LOCG)
python3 scripts/ingest-locg-series-to-catalog.test.py
python3 scripts/ingest-locg-series-to-catalog.py \
  --fixture-dir scripts/fixtures/locg-series-ingest --series-id 900001 --dry-run
```

## Catalog growth from real GCD series (comics.org API)

Parallel highest-trust path for **new** `comics.ts` rows: walk real Grand
Comics Database series → issues via `https://www.comics.org/api/`. Script:
`scripts/ingest-gcd-series-to-catalog.py`.

**GCD-only gates** (Shelby / Lyra — not the same as LOCG): keep a row if it
has **any** of `gcdIssueId` **or** UPC **or** ISBN, plus real GCD
series/issue/publisher. Barcode is **not** required when a real GCD issue id
is present. Store `gcdIssueId` (and API url) in `comic-upc-map.json`. Never
invent UPCs; LOCG / Metron barcodes win on merge.

LOCG importer gates stay `locgId` + UPC|cover.

Polite comics.org pacing: default `--delay 7` (live floor 6s). On 429 the
client pauses, **raises** the session delay, and aborts after two retries —
it does not retry into a 600s ceiling. Identify as KryptonsToyVault personal
collection (same family as `scripts/backfill-comic-upcs-gcd.py`).

**Glyph / Lyra:** feed numeric GCD series ids (Image / Boom / IDW / Dark Horse
/ indie first) from `https://www.comics.org/series/<id>/` or
`scripts/comic-gcd-series-cache.json`. Do **not** invent ids, UPCs, or
interpolated ghost rows. Do **not** run `gen-batch-*`. Do **not** mass
live-ingest from a cloud agent.

```bash
# List series ids already in the GCD UPC-backfill cache (no live API)
python3 scripts/ingest-gcd-series-to-catalog.py --list-cache-seeds

# Dry-run a real series (polite ≥6–8s)
python3 scripts/ingest-gcd-series-to-catalog.py --series-id 122674 --delay 7 --max-issues 10 --dry-run

# Mass file (one id per line; see scripts/gcd-series-ids.example.txt)
python3 scripts/ingest-gcd-series-to-catalog.py --series-ids-file scripts/gcd-series-ids.example.txt --delay 7

# Optional publisher filter (name or GCD publisher id)
python3 scripts/ingest-gcd-series-to-catalog.py --series-id 122674 --publisher Valiant --dry-run

# Fixture proof (no live comics.org)
python3 scripts/ingest-gcd-series-to-catalog.test.py
python3 scripts/ingest-gcd-series-to-catalog.py \
  --fixture-dir scripts/fixtures/gcd-series-ingest --series-id 900101 --dry-run
```

## Backfill

```bash
python3 scripts/backfill-comic-upcs.py --seeds-only --limit 40 --delay 30
python3 scripts/backfill-comic-upcs.py --from-catalog --limit 220 --max-minutes 85 --delay 30 --cv-sweep
python3 scripts/backfill-comic-upcs.py --from-catalog --series-batch --limit 2500 --max-per-series 100 --min-year 2005 --max-minutes 360 --delay 30 --no-cv
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
| `--series-batch` | Group by series; paginate full LOCG issue lists (`list_mode_offset`); process recent issues first. |
| `--refresh-lists` | Force re-fetch of cached series issue lists. |
| `--max-series` | Cap number of series groups in series-batch mode. |
| `--max-per-series` | Cap comics per series (keeps newest first). |

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


## Publisher / API sources (parallel to LOCG)

| Source | Status | Notes |
|--------|--------|-------|
| **Marvel Comics API** (`gateway.marvel.com`) | **Shut down — do not use** | Marvel ended the public API. Use LOCG / retailer Shopify feeds instead. |
| **IDW Shopify** `idwpublishing.com/products.json` | Live; exclusives-heavy | `scripts/backfill-comic-upcs-idw-shop.py`. SKUs often real UPC/ISBN, but storefront currently skews foil/exclusive — primary Cover A rows are skipped unless a non-exclusive SKU exists. |
| **Dark Horse / BOOM / Dynamite / Image shop JSON** | No usable public UPC | `products.json` either missing, blocked, or omits barcode; Image shop 403. |
| **GCD (comics.org API)** | Live; 429-prone | `scripts/ingest-gcd-series-to-catalog.py` for **new** rows; `scripts/backfill-comic-upcs-gcd.py` for keep-set UPC enrich. `gcdIssueId` in the UPC map. Polite ≥6–8s + 429 pull-back. |
| **Comic Vine barcode** | Optional fallback | Often empty on search/detail in current API; LOCG remains primary. |

All writers merge-safe-save `comic-upc-map.json` so LOCG + publisher jobs can run in parallel without clobbering each other.


## Parallel LOCG workers

Three disjoint publisher partitions share `comic-upc-map.json` via flock merge:

```bash
# Marvel / DC / other — stagger ~10s, each --delay 30
python3 scripts/backfill-comic-upcs.py --from-catalog --series-batch --publisher-group marvel \
  --limit 2000 --max-per-series 80 --min-year 2005 --max-minutes 360 --delay 30 --no-cv \
  --worker-id marvel --stats-file scripts/comic-upc-backfill-stats-marvel.json
python3 scripts/backfill-comic-upcs.py --from-catalog --series-batch --publisher-group dc ...
python3 scripts/backfill-comic-upcs.py --from-catalog --series-batch --publisher-group other ...
```

Or: `bash scripts/run-locg-upc-workers.sh`

## Profile

Collection context: https://leagueofcomicgeeks.com/profile/KryptonsToyVault/collection

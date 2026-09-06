# Live figure SKU overlay

Add articulated **action figure** rows to the permanent archive **at runtime**
without a Build republish. New AF batches (e.g. weekday BBTS / Entertainment Earth
monitor) upsert into Postgres figure_catalog keyed by **SKU**, and the client
merges them on top of baked oneshot.json / FIGURES.

Mirrors the comics pattern (comic_catalog + getComicLibrary) with figure-specific
dedupe (prefer SKU).

## Why

Baked oneshot.json only updates when code ships. After this overlay ships once,
Lyra can ingest new SKUs into the live DB; list/search/company/detail pick them up.

## Constraints

- AF only (kind: figure or kit)
- Release floor 1980-01-01+
- No AI art; imageUrl must be real http(s) when set
- No fake SKUs; sku required
- Valid CompanyId only

## Storage

See migrations/0006_figure_catalog.sql and src/lib/figure-catalog.ts.


## Upsert

Server fn upsertFigureSkuOverlay:

1. Validate each row
2. Skip if SKU, id, or name-key already in baked FIGURES
3. Skip if already in figure_catalog
4. Otherwise insert (on conflict do nothing)

Lyra CLI: scripts/ingest-figure-sku-overlay.py (dry-run or with DATABASE_URL).
Helper: scripts/ingest-figure-sku-overlay.mjs

Required fields: id, name, subtitle, line, company, kind, releaseDate, msrp, scale, demand, tags, sku.
Optional: exclusive, imageUrl, source.

## Merge and dedupe

Preference order: sku, then id, then name|subtitle|line|company (case-insensitive).

Client extras = weekly live figures plus figure_catalog overlay via useFigureExtras.
App shell loads overlay once with useEnsureFigureLibrary.

## Notes

Weekly Shopify N and N stays separate. One-shot bake remains for bulk densify.
Do not Build Publish per batch; ship this code once, then ingest only.

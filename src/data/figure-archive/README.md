# Figure archive (one-shot permanent dump)

- `oneshot.json` — CatalogFigure-shaped rows imported by `../figures.ts`
- `oneshot-stats.json` — generation counts
- `product-image-index.json` — Shopify product→CDN image index (image bake)
- `image-bake-stats.json` — last bake before/after report

Regenerate archive: `cd scripts && python3 gen-figure-oneshot.py`

Bake real product images onto curated gaps:
`cd scripts && python3 bake-figure-images.py` (add `--fetch` for live pagination)

See `docs/figure-backlog.md` and `docs/figure-image-bake.md`.

Bake accurate SKUs onto curated gaps:
`cd scripts && python3 bake-figure-skus.py --fetch` (or `--cache-only`).
See `docs/figure-sku-bake.md`. Writes `product-sku-index.json`, `sku-bake-stats.json`,
and `../figure-sku-map.json`.

## Identity / dedupe

Canonical figure `sku` is GTIN; listing codes are aliases.
See `docs/figure-identity.md`. Collapse script:
`python3 scripts/collapse-figure-identity.py` (dry-run) / `--apply`.

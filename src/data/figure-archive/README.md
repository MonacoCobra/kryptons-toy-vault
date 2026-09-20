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

## Toyark densify

`scripts/toyark-densify.py` / `scripts/dry-run-toyark-densify.py` poll The
Toyark WP REST API (Hasbro / McFarlane / NECA / Jazwares / Super7 plus vault
1/6 ids: Hot Toys, Mondo, threezero, Enterbay, Asmus, Star Ace, EXO-6).
Dry-run writes `toyark-densify-dry-run.json`. `--apply` appends accepted
singles to oneshot + aliases + image URLs (never invents GTINs; comics
untouched). Cap ~50/run. See `docs/toyark-densify.md`.

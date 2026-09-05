# Figure archive (one-shot permanent dump)

- `oneshot.json` — CatalogFigure-shaped rows imported by `../figures.ts`
- `oneshot-stats.json` — generation counts
- `product-image-index.json` — Shopify product→CDN image index (image bake)
- `image-bake-stats.json` — last bake before/after report

Regenerate archive: `cd scripts && python3 gen-figure-oneshot.py`

Bake real product images onto curated gaps:
`cd scripts && python3 bake-figure-images.py` (add `--fetch` for live pagination)

See `docs/figure-backlog.md` and `docs/figure-image-bake.md`.

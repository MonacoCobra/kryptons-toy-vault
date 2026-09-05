# Figure storefront ingest

Weekly New & Noteworthy figures prefer live Shopify `products.json` feeds.

## Working sources (verified)

- Super7 — `https://super7.com/products.json`
- Good Smile US — `https://goodsmileus.com/products.json`

Add more in `src/lib/figure-storefronts.ts` → `FIGURE_STOREFRONTS`.

## Not available as stable JSON (yet)

- **Hasbro Pulse** — returns HTML for products.json (gated)
- **Big Bad Toy Store** — rich preorder HTML search, no public API/RSS
- **Entertainment Earth** — same; third-party scrapers exist but are fragile/ToS-gray

Product images come from the storefront CDN only (no AI art).

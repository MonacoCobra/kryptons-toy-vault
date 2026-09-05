# Figure storefront ingest

Weekly New & Noteworthy figures prefer live Shopify `products.json` feeds with real CDN images (no AI art).

## Working sources

| Shop | Base URL | Company |
| --- | --- | --- |
| Super7 | https://super7.com | super7 |
| Good Smile US | https://goodsmileus.com | figma |
| Boss Fight Studio | https://bossfightstudio.com | bossfight |
| The Loyal Subjects | https://theloyalsubjects.com | loyalsubjects |
| Mattel Creations | https://creations.mattel.com | mattel (filtered: Masterverse / WWE / etc.) |

Add more in `src/lib/figure-storefronts.ts` → `FIGURE_STOREFRONTS`.

## Not available as stable JSON (yet)

- **Hasbro Pulse**, **BBTS**, **Entertainment Earth**, NECA, Mezco, Hot Toys, Sideshow — HTML or gated; no reliable public `products.json` from our network.

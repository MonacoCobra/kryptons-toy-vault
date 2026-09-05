# Figure storefront ingest (action figures)

Weekly New & Noteworthy **action figures** prefer live Shopify `products.json`
feeds with real CDN images (no AI art). The **permanent archive one-shot dump**
paginates **all** pages from these same shops (see `scripts/gen-figure-oneshot.py`).

## Active sources

| Shop | Base URL | Notes |
| --- | --- | --- |
| Super7 | https://super7.com | ULTIMATES / ReAction (filter apparel/accessories) |
| Good Smile US | https://goodsmileus.com | figma / action figures only |
| Boss Fight Studio | https://bossfightstudio.com | H.A.C.K.S. |
| The Loyal Subjects | https://theloyalsubjects.com | BST AXN |
| Mattel Creations | https://creations.mattel.com | Masterverse / WWE / Jurassic / etc. |
| Premium DNA | https://www.premiumdnatoys.com | 1:12 licensed figures |
| Hiya Toys | https://www.hiyatoys.com | Exquisite Mini / Basic |
| Mondo | https://www.mondoshop.com | 1/12 / 1/6 / Soft Vinyl figures |
| Shop DC | https://shop.dc.com | McFarlane Multiverse AF (filter merch) |
| NECA Store | https://store.necaonline.com | Official NECA AF (filter pins/plush/apparel) |

## Out of scope

Pins, Barbie/dolls, poster/print merch, board games, drinkware, puzzles.

## Still no stable Shopify JSON

Hasbro Pulse, BBTS, Entertainment Earth, Mezco official, McFarlane Toys store,
Hot Toys, Sideshow, Bandai Tamashii, threezero — covered via curated archive
depth and/or weekly seed, not live JSON. DC Direct / Kenner Super Powers /
Mattel DCUC are curated in `scripts/figure_oneshot/curated_dc.py`.

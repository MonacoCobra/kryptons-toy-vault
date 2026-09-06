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
| Blokees | https://blokees.com | Champion/Galaxy model figures |
| Blitzway | https://blitzway.com | Carbotix / Figure Complex / AF |
| EXO-6 | https://exo-6.com | Star Trek 1:6 articulated |
| Star Ace | https://www.staracetoys.com | 1/6 AF + DefoStyle soft vinyl |
| DamToys | https://shop.damtoys.com | 1/6 / 1/12 military & GK |
| Storm Collectibles | https://www.stormco.com.hk | First-party HK Shopify |
| Store Horsemen | https://store-horsemen.myshopify.com | Four Horsemen Mythic/Cosmic/Figura Obscura |

## Out of scope

Pins, Barbie/dolls, poster/print merch, board games, drinkware, puzzles.

## Still no stable Shopify JSON

Hasbro Pulse, BBTS, Entertainment Earth, Mezco official, McFarlane Toys store,
Hot Toys, Sideshow, Bandai Tamashii US, MAFEX/Medicom first-party, threezero, Takara Tomy mall —
still no stable public `products.json` we verified. **Image bake** may still fill
Hasbro / Mezco One:12 / MAFEX / SHFiguarts / Playmates / JAKKS / Toy Biz /
classic DC Direct / Loyal Subjects BST / Four Horsemen curated rows from specialty
retailer Shopify catalogs (ToyArena, CmdStore, Planet AF, Cool Toy Den, AFCollector,
Legendz Toys) with high-confidence vendor/title→company mapping only. Kenner Super
Powers / Mattel DCUC / JLU leftovers stay placeholders without honest feeds.

## Image bake

Curated rows without CDN art are filled (high-confidence only) by
`scripts/bake-figure-images.py` → `src/data/figure-image-urls.json`. See
`docs/figure-image-bake.md`.

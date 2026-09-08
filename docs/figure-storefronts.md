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
| Yolopark | https://shop.yolopark.com | AMK / AMK PRO assembleable model kits |
| Blitzway | https://blitzway.com | Carbotix / Figure Complex / AF |
| EXO-6 | https://exo-6.com | Star Trek 1:6 articulated |
| Star Ace | https://www.staracetoys.com | 1/6 AF + DefoStyle soft vinyl |
| DamToys | https://shop.damtoys.com | 1/6 / 1/12 military & GK |
| Storm Collectibles | https://www.stormco.com.hk | First-party HK Shopify |
| Store Horsemen | https://store-horsemen.myshopify.com | Four Horsemen Mythic/Cosmic/Figura Obscura |
| Mattel Shop (bake) | https://shop.mattel.com | MOTU Origins/Masterverse/WWE — image-bake index only |
| Solaris Japan (bake) | https://www.solarisjapan.com | SHFiguarts/AY import — image-bake index only |
| ActionFiguresAndComics (bake) | https://www.actionfiguresandcomics.com | Large specialty AF — image-bake index only |
| Japan Figure (bake) | https://www.japan-figure.com | JP import SHF/MAFEX/Kaiyodo — image-bake index only |
| Star Action Figures (bake) | https://www.staractionfigures.co.uk | UK specialty Hasbro/McFarlane — SKU+image bake |
| ToyDojo (bake) | https://www.toydojo.com | US import SHF/Bandai/Hasbro/MAFEX — SKU+image bake |
| Toynk (bake) | https://www.toynk.com | US specialty (noisy; skip bag clips/costumes) — SKU+image bake |
| Collecticon (bake) | https://www.collecticontoys.com | US specialty Hasbro/McFarlane/NECA — SKU+image bake |
| Nerdzoic (bake) | https://nerdzoic.com | US specialty Hasbro/Mattel/NECA/Four Horsemen/Mezco — SKU+image bake |
| Kitsap Comics (bake) | https://www.kitsapcomics.com | Specialty AF aisle Hasbro/McFarlane/Mattel — SKU+image bake |
| SiFi Toys (bake) | https://www.sifitoys.com | Specialty Mezco One:12 / Four Horsemen / Hasbro — SKU+image bake |
| Hasbro Pulse (bake) | https://hasbropulse.myshopify.com | Listing SKUs→aliases; rare GTIN primary — SKU bake |

## Out of scope

Pins, Barbie/dolls, poster/print merch, board games, drinkware, puzzles.

## Still no stable Shopify JSON

BBTS / Entertainment Earth / Walmart / Target / McFarlane official still lack a usable public **GTIN** feed (BBTS/EE expose listing ids only; WM/Target bot-blocked; McFarlane is Wix). Hasbro Pulse `hasbropulse.myshopify.com/products.json` is open but mostly listing codes (aliases). Mezco official, Hot Toys, Sideshow, Bandai Tamashii US, MAFEX/Medicom first-party, threezero, Takara Tomy mall — still no stable public `products.json` we verified. **Image bake** may still fill
Hasbro / Mezco One:12 / MAFEX / SHFiguarts / Playmates / JAKKS / Toy Biz /
classic DC Direct / Loyal Subjects BST / Four Horsemen curated rows from specialty
retailer Shopify catalogs (ToyArena, CmdStore, Planet AF, Cool Toy Den, AFCollector,
Legendz Toys, shop.mattel, Solaris Japan, JB Hi-Fi, ActionFiguresAndComics, Japan Figure, Star Action Figures, ToyDojo, Toynk, Collecticon, Nerdzoic, Kitsap Comics, SiFi Toys) with high-confidence vendor/title→company mapping only. Kenner Super
Powers / Mattel DCUC / JLU leftovers stay placeholders without honest feeds.

## SKU bake

Missing archive `sku` values are filled (high-confidence only) by
`scripts/bake-figure-skus.py` → `src/data/figure-sku-map.json` + oneshot patches.
See `docs/figure-sku-bake.md`. Same shops + specialty retailers as image bake;
Pulse/BBTS/EE remain blocked.

## Image bake

Curated rows without CDN art are filled (high-confidence only) by
`scripts/bake-figure-images.py` → `src/data/figure-image-urls.json`. See
`docs/figure-image-bake.md`.

## Small-brand feed probe (2026-09-07)

**Added / confirmed:**
- Blokees — https://blokees.com (first-party; listing SKUs → aliases; barcodes usually empty)
- Yolopark — https://shop.yolopark.com (AMK/AMK PRO kits; listing SKUs → aliases)

**Specialty (already in RETAILER_FEEDS) with real variant.sku / GTIN for these brands:**
- Jada Toys — CmdStore / ToyArena / ToyDojo / HobbyFigures / Collecticon / etc. (no first-party Shopify JSON)
- JAKKS Pacific — CmdStore / Toynk / HobbyFigures / CoolToyDen (no first-party Shopify JSON; official sites 404/HTML)

**Rejected (SoSkill / others):**
- soskill.com / www.soskill.com — SSL/EOF, not usable products.json
- soskilltoys.com — HTML catalog (not Shopify JSON)
- soskill.myshopify.com — 404
- topgkstore.com — bot interstitial / non-JSON
- shop.jadatoys.de — Magento HTML (not Shopify products.json)
- jakks.com / jakkspacific.com — 404 / non-Shopify
- www.yolopark.com — Peppa/merch mix; use shop.yolopark.com for AMK AF kits

## Model-kits specialty feeds (2026-09-08)

**Used:**
- Blokees — https://blokees.com (first-party; kits reclass + densify)
- Flame Toys specialty — https://www.toyarena.com (Furai Model / Furai Action / KKK vendor hits)
- Flame Toys specialty — https://www.planetactionfigures.co.uk/collections/flame-toys

**Rejected (Flame Toys first-party / SoSkill):**
- flametoys.com / www / shop / store — SSL/EOF, no products.json
- soskill.com / www — SSL/EOF
- soskilltoys.com / www — 404 on products.json
- soskill.myshopify.com — 404
- shop.soskill.com / soskill.store / shop.soskilltoys.com / soskillofficial.com — DNS miss
- topgkstore.com — HTML / bot interstitial
- showzstore.com / robotkingdom.com — non-Shopify or blocked
- ToyArena/PlanetAF — 0 SoSkill vendor hits

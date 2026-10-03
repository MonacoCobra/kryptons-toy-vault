# Figure values: real eBay sold comps (SoldComps)

Figure detail pages show **Current value = average of the 5 most recent matching eBay
sold listings**, sourced from [SoldComps](https://sold-comps.com) (`GET
https://api.sold-comps.com/v1/scrape?keyword=…&ebaySite=ebay.com&count=40`). When fewer
than 3 matching sales exist, the page shows a clearly labeled **Estimated value**
(modeled from MSRP × demand) and **no sold rows** — modeled comps are never shown as sales.

## Pieces

- `src/lib/soldcomps.ts` — pure logic shared by server + box script: tight keyword
  (`line` without brand prefix + distinctive name tokens, e.g. `age of the primes snarl slug`),
  title relevance filter (all name tokens + line tokens/acronym; rejects lots, partials,
  customs/KO, trading cards, non-USD), prefers new/sealed sales when ≥3 exist, averages the
  5 newest by `soldPrice`, flags best-offer sales (listed price = upper bound).
- `src/data/market-comps.json` — repo cache (public sold data, **no key**). Read by the app
  for detail pages and for list / collection / vault values.
- `scripts/soldcomps-refresh.mjs` — box-side refresh for explicit ids (max 5/run, skips
  entries < 30 days old, stops at `x-usage-remaining` ≤ 10, `--seed-file` = no API call).
- `src/lib/soldcomps-market.ts` — server function for live refresh on detail-page open.
  Only active when the deploy has **both** `SOLDCOMPS_API_KEY` and `DATABASE_URL`; caches in
  `market_comps` (`soldcomps:figure:<id>`), 30-day refresh, ≤ 5 calls/day, stops at 10 left.

## Budget

Free plan = 100 searches/month. Nothing loops over the catalog. Each figure costs at most
one search per 30 days, and only when opened (server) or explicitly listed (box script).

## Key

`SOLDCOMPS_API_KEY` lives only in the box env (and, optionally, the deploy's server env).
Never commit, log or print it; it never reaches the client bundle.

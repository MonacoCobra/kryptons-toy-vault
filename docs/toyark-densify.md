# Toyark densify (dry-run)

Babysit slice: poll [The Toyark](https://www.toyark.com/) WordPress REST API and
propose **new-figure densify candidates**. v1 is **dry-run only** — it writes a
JSON report and does not touch `oneshot.json`, `figure-sku-map.json`,
`figure-sku-aliases.json`, `figure-image-urls.json`, or any other catalog file.

`--apply` is **not wired**. If passed, the script exits with a refusal message
and makes no writes.

## Endpoint

- REST: `https://www.toyark.com/wp-json/wp/v2/posts?_embed=1`
- `robots.txt` for `User-agent: *` disallows `/feed/` (so we do **not** use RSS)
  and does **not** disallow `/wp-json/`.
- Polite pagination (`--per-page`, `--max-pages` / `--page-cap`, `--sleep`).
- User-Agent identifies the vault dry-run bot.

Some hosts see a Cloudflare challenge on `www.toyark.com`. The script records
that as `fetch.blocker = cloudflare-challenge` and can replay a saved REST
payload with `--posts-json` (still dry-run; date window still applied).

## Allowlist (vault CompanyId only)

Toyark `companies-*` class_list (plus conservative body-text fallback) maps to
**existing** vault ids from `src/data/companies.ts` / `src/lib/types.ts`.
Nothing is invented — there is **no** `sideshow` CompanyId (Sideshow is a
retailer for Hot Toys, not a maker row).

Shelby wants **1/6 coverage** on this slice (Hot Toys, Mondo, and the other
sixth-scale makers already in the vault), plus Super7 (Mephitsu hub; was
held back only for v1 noise control).

| Toyark cue | CompanyId | Why |
|---|---|---|
| `companies-hasbro` / “Hasbro” | `hasbro` | Original v1 |
| `companies-mcfarlane` / “McFarlane Toys” | `mcfarlane` | Original v1 |
| `companies-neca` / “NECA” | `neca` | Original v1 |
| `companies-jazwares` / Wicked Cool Toys | `jazwares` | Original v1 |
| `companies-super-7` / Super7 | `super7` | Mephitsu hub / ULTIMATES + ReAction |
| `companies-hot-toys` / Hot Toys | `hottoys` | Premium 1/6 (Shelby) |
| `companies-mondo` / Mondo | `mondo` | Premium 1/6 + 1/12 (Shelby) |
| `companies-threezero` / threezero | `threezero` | DLX / FigZero / sixth-scale |
| `companies-enterbay` / Enterbay | `enterbay` | 1:6 movie / NBA |
| `companies-asmus` / Asmus Toys | `asmus` | Sixth-scale LOTR / Hobbit / Witcher |
| `companies-star-ace` / Star Ace | `starace` | Sixth-scale movie / pop-culture |
| `companies-exo-6` / EXO-6 | `exo6` | Sixth-scale Star Trek |

`blitzway` exists as a CompanyId (Superb Scale mixed with Carbotix) but is
**not** on this allowlist — keep the 1/6 lane to licensed sixth-scale peers,
not every 1/6 military/third-party id.

Other recognized makers (Kaiyodo, Tamashii, Hiya, Mezco, …) stay
`company-not-allowlisted`.

## Filters

Rejected: sponsor newsletters, sales/deals, customs, photo-of-the-day, pure
review/in-hand with no new product identity, vehicles/props-only (e.g. 1:1
cowls), non-figure entertainment news.

Accepted only with a new/reveal/pre-order/official-image signal **and** a
recognizable company + line/variant. Multi-figure posts split one candidate per
explicitly named figure; a 2-pack/multipack stays one set when the source
treats it as one product.

Identity is **company + line + year + variant** — same character name is not a
merge. GTIN is preferred when the post labels one; codes found in prose
(`MMS897`, `HAS*`, labeled UPC) are aliases only. Nothing is invented.

Featured/source image URLs are stored **on candidates only** for a future apply
pass. Existing catalog photos are not rematched.

Oneshot is read-only, via `figure_identity` keys, to flag `already-in-oneshot`
/ `possible-reissue`.

## Run

```bash
python3 scripts/dry-run-toyark-densify.py
python3 scripts/dry-run-toyark-densify.py --days 14 --per-page 20 --max-pages 4
python3 scripts/dry-run-toyark-densify.py --after 2026-09-13T00:00:00Z --company hottoys
python3 scripts/dry-run-toyark-densify.py --posts-json /tmp/toyark-posts.json
# --apply  →  refused (exit 2); no catalog writes
```

Default report: `src/data/figure-archive/toyark-densify-dry-run.json`.

Comics / Build Publish / Mephitsu crawl: untouched.

See also `docs/figure-identity.md` and `docs/figure-sku-bake.md`.

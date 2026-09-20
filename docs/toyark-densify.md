# Toyark densify

Babysit slice: poll [The Toyark](https://www.toyark.com/) WordPress REST API and
propose **new-figure densify candidates**. Default is **dry-run** (JSON report
only). **`--apply` is wired** — accepted candidates are appended to
`oneshot.json` automatically. Shelby policy (2026-09-20): do **not** wait for
manual approval; noon + 11:30pm MT Mephitsu babysits apply, then commit+push
figure densify to **main** so Lyra’s early-morning Publish picks them up.

Ping Shelby with 1–2 spot-checks when material lands (babysit routine, not this
script).

## Endpoint

- REST: `https://www.toyark.com/wp-json/wp/v2/posts?_embed=1`
- `robots.txt` for `User-agent: *` disallows `/feed/` (so we do **not** use RSS)
  and does **not** disallow `/wp-json/`.
- Polite pagination (`--per-page`, `--max-pages` / `--page-cap`, `--sleep`).
- User-Agent identifies the vault densify bot. Live urllib retries briefly on
  429 / 5xx / Cloudflare 403, then records a blocker.

Some hosts see a Cloudflare challenge on `www.toyark.com`. Dry-run records
`fetch.blocker = cloudflare-challenge` and can replay a saved REST payload with
`--posts-json`. **`--apply` without `--posts-json` exits non-zero** when live
fetch is blocked (babysit reports the blocker; no catalog writes).

## Allowlist (vault CompanyId only)

Toyark `companies-*` class_list (plus conservative body-text fallback) maps to
**existing** vault ids from `src/data/companies.ts` / `src/lib/types.ts`.
Nothing is invented — there is **no** `sideshow` CompanyId (Sideshow is a
retailer for Hot Toys, not a maker row).

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
treats it as one product. **Apply skips those pack/set rows** (low-and-slow
singles, same as Mephitsu listing densify).

Identity is **company + line + year + variant** — same character name is not a
merge. GTIN is preferred when the post **labels** one; codes found in prose
(`MMS897`, `HAS*`, labeled UPC) are aliases only. Nothing is invented.

Featured/source image URLs are written on **new** apply rows only. Existing
catalog photos are not rematched (Miku owns rematch).

## Apply writes (safe)

`--apply` refuses when `oneshot.json` is not a list, when `--skip-oneshot` is
set, or when live REST is blocked (no `--posts-json`). It never touches comics.

For each accepted single not already in oneshot (cap `--cap`, default 50):

- **id** `ta-<sha1[:12] of postId+name+company+line+variant>` (lengthens on clash)
- **sku** omitted unless the post labeled a real GTIN; manufacturer codes stay
  aliases
- **aliases** (`figure-sku-aliases.json`): `MMS*` / `HAS*` / listing codes,
  `toyark:<postId>`, Toyark permalink
- **imageUrl** + `figure-image-urls.json` from featured/source URL (new rows)
- **tags** `toyark`, `toyark-densify`, company id, `toyark-<postId>`
- **source** `toyark-densify`
- Reports: `toyark-densify-apply.json` + `toyark-densify-stats.json`

Street year comes from prose/window when present; otherwise the post’s
publication year is used as an announcement-year `releaseDate` (`YYYY-01-01`).
A year is never fabricated from whole cloth.

## Run

```bash
# Dry-run (report only)
python3 scripts/toyark-densify.py
python3 scripts/dry-run-toyark-densify.py --days 14 --per-page 20 --max-pages 4
python3 scripts/dry-run-toyark-densify.py --after 2026-09-13T00:00:00Z --company hottoys
python3 scripts/dry-run-toyark-densify.py --posts-json scripts/fixtures/toyark-densify/posts.json

# Apply (babysit — noon + 11:30pm MT)
python3 scripts/toyark-densify.py --apply --days 7
python3 scripts/dry-run-toyark-densify.py --apply --days 7 --cap 50
# Replay / tests (no live Toyark)
python3 scripts/dry-run-toyark-densify.py --apply --posts-json scripts/fixtures/toyark-densify/posts.json \
  --oneshot /tmp/oneshot-copy.json --aliases /tmp/aliases.json \
  --image-urls /tmp/urls.json --sku-map /tmp/sku-map.json
python3 scripts/dry-run-toyark-densify.test.py
```

`scripts/toyark-densify.py` is a thin wrapper around
`scripts/dry-run-toyark-densify.py` (same module).

Default dry-run report: `src/data/figure-archive/toyark-densify-dry-run.json`.
Default apply report: `src/data/figure-archive/toyark-densify-apply.json`.

## Babysit commit (Meph wires the routine)

After a successful `--apply`, commit **only** figure densify deltas:

- `src/data/figure-archive/oneshot.json`
- `src/data/figure-archive/oneshot-stats.json` (if bumped)
- `src/data/figure-archive/toyark-densify-apply.json`
- `src/data/figure-archive/toyark-densify-stats.json`
- `src/data/figure-sku-aliases.json`
- `src/data/figure-image-urls.json`
- `src/data/figure-sku-map.json` (only when a source-labeled GTIN landed)

Do **not** commit comics, Mephitsu crawl caches, or Build Publish output. Push
those figure files to **main**. If live fetch exits non-zero, report the
blocker and skip the commit.

Comics / Build Publish / Mephitsu crawl: untouched.

See also `docs/figure-identity.md` and `docs/figure-sku-bake.md`.

# Comic permanent archive backlog

## Floor

**Release/cover date floor: 1980-01-01** (modern → 1980; nothing older).

Former floor was 1986-10-01; raised for DC mass fill and future Marvel/indie passes.

## Files

| Path | Role |
|------|------|
| `src/data/comics.ts` | Permanent catalog (`COMICS`) |
| `src/data/comic-backlog/batch-*.json` | Audit trail / inject source |
| `src/data/comic-backlog/manifest.json` | Injected / queued metadata |
| `scripts/comic_backlog_common.py` | Shared FLOOR, dedupe, inject |
| `scripts/gen-batch-006-dc-mass-1980.py` | DC mass generator (Superman → Batman → Flash/GL → majors) |
| `scripts/gen-batch-010-western-thin.py` | Archie/Titan/Rebellion/2000AD + light Viz/Kodansha + densify |
| `scripts/gen-batch-011-vertigo-ws-indie.py` | Vertigo densify, Black Label, WildStorm, Milestone, CrossGen, Eclipse/First≥1980, Avatar, SW/TF/Joe/Hellboy |
| `scripts/gen-batch-012-flagship-thin.py` | Flagship thin densify: GA/HQ/SS/BoP, Marvel DS/BP/SS/Excalibur/Punisher, Skybound, Image, Pacific/Eclipse |
| `scripts/gen-batch-013-highvalue-gaps.py` | Absolute siblings, Black Label densify, Ultimate 2020s, Hellboy/BPRD leftovers, Invincible leftovers, TWD Deluxe, Sandman Universe |

## Publishers

DC / Marvel / Image primary; also Vertigo/Black Label/WildStorm/Milestone, CrossGen, Eclipse/First (≥1980), Avatar, Archie, Titan, Rebellion/2000 AD, Dark Horse, BOOM!, IDW, Dynamite, Valiant, Oni; light Viz/Kodansha (not manga overload); Star Wars / Transformers / GI Joe / Hellboy densify.

## Covers

No generative AI cover art. Palette placeholders in backlog rows; Comic Vine URLs via existing cover tooling when the API key is available.

## UPC / cover identity

See **[comic-upc.md](./comic-upc.md)**. LOCG-first UPC/ISBN; cover matching prefers UPC so variants do not steal art. Backfill: `scripts/backfill-comic-upcs.py` (Crawl-delay 30s).

**New catalog rows from real LOCG series** (post-prune growth):
`scripts/ingest-locg-series-to-catalog.py`. Glyph/Lyra feed numeric series ids
(`--series-id` / `--series-ids-file` / `--list-cache-seeds`). Gates: real page +
`locgId` + UPC and/or cover; no invented metadata; no `gen-batch-*`. Fixture
proof: `python3 scripts/ingest-locg-series-to-catalog.test.py`.

**New catalog rows from a local GCD dump** (parallel path; **hold the API**):
`scripts/ingest-gcd-series-to-catalog.py --dump-dir`. Glyph waits for Lyra to
drop Shelby’s official MySQL dump, then feeds series ids or `--publisher`.
Gates: real GCD series+issue + **any of** `gcdIssueId` / UPC / ISBN. `--use-api`
is off by default. Fixture proof:
`python3 scripts/ingest-gcd-series-to-catalog.test.py`.

## Variant covers on detail

See **[comic-upc.md](./comic-upc.md)** § Variant side-scroll. List shows primary/Cover A; detail page scrolls real catalog variants for the series+issue+publisher family (`getComicVariants`).

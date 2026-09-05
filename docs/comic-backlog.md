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

## Publishers

DC / Marvel / Image primary; also Vertigo/Black Label/WildStorm/Milestone, CrossGen, Eclipse/First (≥1980), Avatar, Archie, Titan, Rebellion/2000 AD, Dark Horse, BOOM!, IDW, Dynamite, Valiant, Oni; light Viz/Kodansha (not manga overload); Star Wars / Transformers / GI Joe / Hellboy densify.

## Covers

No generative AI cover art. Palette placeholders in backlog rows; Comic Vine URLs via existing cover tooling when the API key is available.

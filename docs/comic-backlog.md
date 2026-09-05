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

## Publishers

DC Comics and DC imprints that belong in the DC catalog (Elseworlds, Black Label where appropriate).

## Covers

No generative AI cover art. Palette placeholders in backlog rows; Comic Vine URLs via existing cover tooling when the API key is available.

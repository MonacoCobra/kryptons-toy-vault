# Comic archive backlog

Queued batches of historically accurate comics. Rows use the same tuple shape as
`comics.ts` `Row` entries.

**Release/cover floor: `1980-01-01`** — include issues from 1980 through present;
nothing older than 1980 (update from the former Oct 1986 floor).

## Batch file shape

```json
{
  "id": "batch-001",
  "title": "…",
  "created": "2026-09-05",
  "status": "queued",
  "focus": "…",
  "rows": [
    ["mv-asm-1", "Amazing Spider-Man", "1", "Marvel Comics", "1963-03-01", "Stan Lee", "Steve Ditko", "…", 0.12, "single", 5000, 1, "dc2626,1e3a8a,f8fafc"]
  ]
}
```

Statuses: `queued` → `injected` (set when merged) → never re-inject.

## Mass inject

Shelby may mass-inject large DC/Marvel fills in one pass (see `batch-006`). Legacy
cadence was ~one batch every 3 weeks with New & Noteworthy promotion; mass fills
are allowed when explicitly requested.

## Conventions

- Prefer real published issue numbers and approximate cover dates (interpolated
  between bibliographic anchors).
- Action Comics skips unpublished #905–956 (New 52 used Vol. 2 / `Action Comics (2011)`).
- Palette placeholders OK; Comic Vine covers resolved at runtime (never generative AI art).
- Deduplicate by id and `series|issue|publisher` (variant-aware at merge time).

## Tooling

- `scripts/comic_backlog_common.py` — `FLOOR`, blocklists, `BatchBuilder`, `inject`
- `scripts/gen-batch-*.py` — generators (do **not** use for post-prune mass growth)
- `python3 scripts/comic_backlog_common.py inject batch-00N`
- **`scripts/ingest-locg-series-to-catalog.py`** — highest-trust growth: real LOCG
  series → new `comics.ts` rows (`locgId` + UPC and/or cover). Glyph/Lyra feed
  numeric series ids via `--series-id` / `--series-ids-file` (Image / Boom / IDW /
  Dark Horse / indie first). See `scripts/locg-series-ids.example.txt` and
  `docs/comic-upc.md`.

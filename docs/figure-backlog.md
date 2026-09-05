# Figure backlog (permanent archive)

Already-released articulated **action figures** are queued in
`src/data/figure-backlog/` and injected into `src/data/figures.ts` on a
~3-week cadence — the same pattern as the comic archive backlog.

Weekly Shopify New & Noteworthy ingest (`figure-storefronts.ts` →
`weekly-drop.ts`) stays separate. Backlog batches grow the permanent catalog
that search, market, pulse, and vault math already read via `FIGURES` /
`mergeFigures`.

## Layout

| Path | Role |
| --- | --- |
| `src/data/figure-backlog/manifest.json` | queued / injected batch ids + cadence metadata |
| `src/data/figure-backlog/batch-NNN.json` | row tuples ready to merge |
| `scripts/figure_backlog_common.py` | parse / dedupe / `inject` helper |
| `scripts/gen-figure-batch-001.py` | generator for batch-001 |
| `src/lib/figure-catalog.ts` | `NOTEWORTHY_WEEKS=3` + `splitFiguresClient` (comics parity) |

## Row shape

Same tuple as `figures.ts` `Row`:

```
[id, name, subtitle, line, company, kind, releaseDate, msrp, scale, demand, tags, extra?]
```

- `kind` is almost always `"figure"` (articulated). Kits stay out of backlog batches.
- `extra` is optional `{ sku?, exclusive? }`.
- No generative AI art — omit `imageUrl`; UI uses CSS/palette placeholders.
- Deduplicate by **id** and by **name|subtitle|line|company** (case-insensitive).

## Inject cadence

1. Keep the next batch as `"status": "queued"` in JSON + `manifest.queued`.
2. About every **3 weeks** (when weekly figures graduate out of New & Noteworthy), inject:

```bash
cd scripts && python3 -c "from figure_backlog_common import inject_batch; print(inject_batch('batch-00N'))"
```

3. That appends a comment block + rows into `figures.ts`, sets batch status to
   `injected`, and updates `manifest.json`. Never re-inject an injected batch.

## Batch-001 (injected 2026-09-05)

~250 figures already released, focused on gaps vs the original ~176 seed:

- Marvel Legends waves (2020–2025)
- Star Wars Black Series expansions
- GI Joe Classified expansions
- Transformers Studio Series + Legacy
- Power Rangers Lightning Collection
- Super7 ULTIMATES / ReAction, Boss Fight H.A.C.K.S., Loyal Subjects BST AXN, Masterverse deeper cuts

## Suggested next batches

| Batch | Focus |
| --- | --- |
| `batch-002` | McFarlane DC Multiverse + Spawn expansions; NECA TMNT / horror depth |
| `batch-003` | MAFEX / Mezco One:12 / SH Figuarts imports (articulated only) |
| `batch-004` | More Hasbro (Vintage Collection adjacent Black Series, Classified vehicles-as-figures skipped — figures only) |
| `batch-005` | Hiya / Mondo / Premium DNA / Figma — keep `CompanyId` valid |

## Product rules

- Action figures only (articulated). No pins, dolls, statues, plush, apparel.
- Valid `CompanyId` values only (`src/lib/types.ts`).
- Prefer real-ish MSRP, release dates, and line names over filler SKUs.

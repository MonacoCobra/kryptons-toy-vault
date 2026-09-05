# Figure archive backlog

Queued batches of already-released articulated action figures (~180–250 each).
Every ~3 weeks, when New & Noteworthy promotes into the permanent archive,
the next unused `batch-NNN.json` is merged into `src/data/figures.ts`.

See also `docs/figure-backlog.md`.

## Batch file shape

`rows` match `figures.ts` Row tuples (optional 12th object: `{ sku?, exclusive? }`).
Statuses: `queued` → `injected` → never re-inject.
Action figures only — no pins, dolls, statues, plush, or apparel.

# Comic archive backlog

Queued batches of historically accurate comics (~400–500 titles each).
Every ~3 weeks, when New & Noteworthy promotes into the permanent archive,
the next unused `batch-NNN.json` is merged into `src/data/comics.ts`.

## Batch file shape

```json
{
  "id": "batch-001",
  "title": "Marvel Silver Age keys",
  "created": "2026-09-05",
  "status": "queued",
  "rows": [
    ["mv-asm-1", "Amazing Spider-Man", "1", "Marvel Comics", "1963-03-01", "Stan Lee", "Steve Ditko", "First solo Spider-Man title.", 0.12, "single", 5000, 1, "dc2626,1e3a8a,f8fafc"]
  ]
}
```

`rows` use the same tuple shape as `comics.ts` Row entries.
Statuses: `queued` → `injected` (set when merged) → never re-inject.

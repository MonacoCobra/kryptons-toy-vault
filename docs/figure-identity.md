# Figure identity (GTIN canonical + listing aliases)

Retailers label the same action figure with different codes (Hasbro Pulse
`HAS359605`, assort `G2370`, specialty listing `MLDEADM3`, BBTS handle, vs the
universal EAN/UPC `5010996359605`). Without a shared identity those become
2–3 catalog rows.

## Policy (Shelby, 2026-09-07)

1. **Primary `sku`** on a figure row is the **universal GTIN** (EAN-8 / UPC-A /
   EAN-13 / GTIN-14) when known. Never invent codes.
2. **Listing codes** (Hasbro Pulse `HAS*`, assort `F####` / `G####`, house SKUs
   like `MLDEADM3`, shop item numbers) are **aliases**, not separate figures.
3. SKU bake may **upgrade** a listing-code primary → GTIN and move the listing
   into aliases. It must **never** overwrite a GTIN with a listing code.
4. When two rows are clearly the same figure (same company + character + line +
   wave/theme) but one carries GTIN and the other a listing code, **collapse**
   into one row: keep the GTIN as `sku`, attach listing codes as aliases, keep
   the best real `imageUrl`.
5. When two rows carry **distinct GTINs**, leave both and flag — do not guess.

## Files

| Path | Role |
|------|------|
| `src/data/figure-archive/oneshot.json` | Catalog rows (`sku` = GTIN when known) |
| `src/data/figure-sku-map.json` | id → primary sku overlay |
| `src/data/figure-sku-aliases.json` | Rich alias doc (see schema below) |
| `src/data/figure-archive/identity-collapse-stats.json` | Last collapse report |

## Alias schema

```json
{
  "version": 1,
  "policy": "gtin-canonical",
  "updatedAt": "ISO-8601",
  "aliasesByFigureId": {
    "ml5-ml-cassandra-nova": ["HAS359605", "G2370", "HASG2370", "HSG2370"]
  },
  "aliasToFigureId": {
    "HAS359605": "ml5-ml-cassandra-nova",
    "G2370": "ml5-ml-cassandra-nova"
  },
  "collapsed": [ { "keepId", "dropId", "canonicalSku", "aliasesAdded", "reason" } ],
  "flagged": [ { "ids", "reason" } ]
}
```

`figures.ts` resolves `figureById("HAS359605")` (and collapsed `id:…` keys)
through `aliasToFigureId` onto the surviving row. Future SKU bake merges into
`aliasesByFigureId` without wiping collapse metadata.

## Commands

```bash
cd /workspace/collection-app
# Dry-run counts first
python3 scripts/collapse-figure-identity.py
# Apply high-confidence merges only
python3 scripts/collapse-figure-identity.py --apply

# SKU bake (GTIN primary + listing aliases) — see docs/figure-sku-bake.md
python3 scripts/bake-figure-skus.py --cache-only
python3 scripts/bake-figure-skus.py --fetch
```

Shared helpers: `scripts/figure_identity.py`.

## Deadpool & Wolverine wave (example)

| Keep (GTIN primary) | Collapsed listing row | Aliases |
|---------------------|----------------------|---------|
| `ml5-ml-cassandra-nova` `5010996359605` | `mlc-cassandra-nova` | `HAS359605`, `G2370`, … |
| `ml5-ml-deadpool-wolverine-movie` `5010996283757` | `mlc-deadpool-movie` | `MLDEADM3` |
| `ml5-ml-x23-movie-dpw` `5010996359629` | `mlc-x23-movie` | `HAS359629` |
| `mlc-nicepool` (no sku yet) | `ml5-ml-nicepool` | — |

**Not collapsed:** `mlc-wolverine-movie` (`5010996267245` Legacy Collection) vs
`ml5-ml-wolverine-movie-dpw` (`5010996283764` Wave 2) — distinct GTINs; flagged.

## Going forward (avoid new dupes)

- Curated / BBTS-wave generators: before inserting a row, check
  `aliasToFigureId` and existing GTINs; attach as alias instead of a new id.
- SKU bake: only assign GTIN to `sku`; put `listingSku` into aliases.
- Live overlay ingest (`ingest-figure-sku-overlay`): treat alias hits as
  “already baked” (same as sku/id/name-key skip).
- Comics / UPC workers are unrelated — do not touch those files for figure
  identity work.
- **No Build Publish** for data-only identity bumps (Lyra publishes).

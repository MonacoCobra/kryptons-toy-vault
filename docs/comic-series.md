# Comics ladder & series-year rule

## Ladder

Catalog browse is **Publisher → Series (run year) → Issues**.

- Search params: `publisher`, `series` (base title), `year` (run year).
- Breadcrumbs + Back move one rung up.
- Issue lists under a series sort by issue number by default.
- Search (`q`) bypasses the ladder and returns a flat issue grid.

## Series-year rule

Implemented in `src/lib/comic-series.ts`.

**Series key** = normalized publisher + normalized series base title + run year.

Run year priority:

1. **Title-embedded start year** from `parseSeriesMeta` (LOCG-style strings like `Batman (2016)` or `Action Comics (Vol. 3) (2016 - Present)`).
2. Else **run clustering** within the same publisher + base title:
   - Non-facsimile `#1` street/cover years are run anchors (so Amazing Spider-Man **2022** stays separate from the classic run).
   - Other issues join the latest anchor year ≤ their own street/cover year.
   - Issues dated before every `#1` anchor form a **legacy** run keyed by the earliest street/cover year among those older issues.
3. Date year prefers `streetDate`, then `coverDate` (ISO `YYYY…` prefix).
4. Unresolved → year `0` (UI: “Year unknown”).

Facsimile `#1`s are **not** run anchors (they would otherwise invent false modern runs).

Catalog permanence is untouched — this is browse/grouping only.

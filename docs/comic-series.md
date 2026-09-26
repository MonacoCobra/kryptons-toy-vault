# Comics ladder & series-year rule

## Ladder

Catalog browse is **Publisher → Series (run year) → Issues**.

- Search params: `publisher`, `series` (base title), `year` (run year).
- Breadcrumbs + Back move one rung up.
- Issue lists under a series sort by issue number by default; **Release date / A–Z / Recently acquired** tabs reorder the visible list (including publisher and series rungs).
- Search (`q`) bypasses the ladder and returns a flat issue grid (same sort tabs).

## Collected Editions

Collected books (`format` ∈ `tpb` | `hc` | `omnibus`; `hardcover` normalizes to
`hc`) are **not** a global catalog mode. They live under the publisher they
belong to:

1. Publisher → Series (singles only; collected rows are excluded from runs).
2. On that publisher page, a **Collected Editions** section appears **above**
   the series list only when the publisher has ≥1 collected-format row. Hidden
   when zero.
3. Opening it (`?publisher=…&section=collected`) lists **series**, not a flat
   wall of volumes: series name, start year (earliest street/cover year),
   volume count, and a representative cover (lowest volume number). Sort tabs
   match the singles series ladder (release date, A–Z, recently acquired).
4. Opening a series (`?publisher=…&section=collected&series=…`) lists that
   series' volumes in volume-number order. `nn` / `[nn]` and other non-numeric
   issues fall back to title, then date. Release date, A–Z, and recently
   acquired still reorder the volume grid. The list is virtualized.

Series identity is the normalized series name already on each row (the same
base-title rules as singles). There is no separate GCD series id on catalog
rows. Blank series land in **Series unknown** instead of disappearing. Edition
titles that differ in the stored name ("One Piece" vs "One Piece [Omnibus
Edition]") stay separate. Grouping does not use run-year clustering, so a
collected `#1` does not split or move the singles ladder.

Compendiums are stored as `tpb` until a dedicated format exists. Global search
(`q`) still finds collected titles. Singles variant collapse is unchanged.

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

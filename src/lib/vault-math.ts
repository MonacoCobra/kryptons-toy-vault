import type { CatalogComic, CatalogFigure, VaultState } from "@/lib/types";

/** A real price: finite and > 0 (catalog MSRP 0 / missing means "unknown"). */
function positive(n: number | null | undefined): number | null {
  return typeof n === "number" && Number.isFinite(n) && n > 0 ? n : null;
}

/** What the owner paid, when entered (0 counts — e.g. a gift). */
export function paidPrice(acquiredPrice: number | null | undefined): number | null {
  return typeof acquiredPrice === "number" && Number.isFinite(acquiredPrice) && acquiredPrice >= 0
    ? acquiredPrice
    : null;
}

/** MSRP / cover price when known. */
export function msrpPrice(msrp: number | null | undefined): number | null {
  return positive(msrp);
}

/** Per-item value: price paid if set, else MSRP; null when neither is known. */
export function itemValue(
  acquiredPrice: number | null | undefined,
  msrp: number | null | undefined,
): number | null {
  return paidPrice(acquiredPrice) ?? msrpPrice(msrp);
}

type Totals = {
  count: number;
  /** Sum of prices paid (items with a price paid). */
  paid: number;
  paidCount: number;
  /** Sum of MSRP / cover prices (items with a known MSRP). */
  msrp: number;
  msrpCount: number;
  /** Sum of per-item value (paid, falling back to MSRP). */
  total: number;
  /** Items with neither a price paid nor an MSRP. */
  missing: number;
};

function emptyTotals(): Totals {
  return { count: 0, paid: 0, paidCount: 0, msrp: 0, msrpCount: 0, total: 0, missing: 0 };
}

function add(t: Totals, acquiredPrice: number | null | undefined, msrp: number | null | undefined) {
  t.count += 1;
  const paid = paidPrice(acquiredPrice);
  const retail = msrpPrice(msrp);
  if (paid != null) {
    t.paid += paid;
    t.paidCount += 1;
  }
  if (retail != null) {
    t.msrp += retail;
    t.msrpCount += 1;
  }
  const value = paid ?? retail;
  if (value == null) t.missing += 1;
  else t.total += value;
}

function rounded(t: Totals): Totals {
  const r = (n: number) => Math.round(n * 100) / 100;
  return { ...t, paid: r(t.paid), msrp: r(t.msrp), total: r(t.total) };
}

/**
 * Collection totals from what was paid and MSRP only — no market estimates.
 * Owned figures whose catalog row isn't loaded yet still count, with no MSRP.
 */
export function summarizeVault(
  state: Pick<VaultState, "ownedFigures" | "ownedComics">,
  extras?: { figures?: CatalogFigure[]; comics?: CatalogComic[] },
) {
  const figMap = new Map((extras?.figures ?? []).map((f) => [f.id, f]));
  const comicMap = new Map((extras?.comics ?? []).map((c) => [c.id, c]));
  const figures = emptyTotals();
  const comics = emptyTotals();

  for (const owned of Object.values(state.ownedFigures)) {
    add(figures, owned.acquiredPrice, figMap.get(owned.figureId)?.msrp);
  }
  for (const owned of Object.values(state.ownedComics)) {
    const comic = owned.catalogId ? comicMap.get(owned.catalogId) : undefined;
    add(comics, owned.acquiredPrice, comic?.msrp ?? owned.custom?.msrp);
  }

  const all = emptyTotals();
  for (const t of [figures, comics]) {
    all.count += t.count;
    all.paid += t.paid;
    all.paidCount += t.paidCount;
    all.msrp += t.msrp;
    all.msrpCount += t.msrpCount;
    all.total += t.total;
    all.missing += t.missing;
  }

  return {
    figures: rounded(figures),
    comics: rounded(comics),
    all: rounded(all),
    figureCount: figures.count,
    comicCount: comics.count,
  };
}

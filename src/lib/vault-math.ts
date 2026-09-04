import { COMIC_BY_ID } from "@/data/comics";
import { FIGURE_BY_ID, FIGURES } from "@/data/figures";
import { comicEstimate, comicHistory, figureHistory, figureMarket } from "@/lib/market";
import type { CatalogComic, CatalogFigure, VaultState } from "@/lib/types";

export function summarizeVault(
  state: Pick<VaultState, "ownedFigures" | "ownedComics">,
  extras?: { figures?: CatalogFigure[]; comics?: CatalogComic[] },
) {
  let figureValue = 0;
  let figureCost = 0;
  let comicValue = 0;
  let comicCost = 0;
  const historyMap = new Map<string, number>();
  const figMap: Record<string, CatalogFigure> = { ...FIGURE_BY_ID };
  for (const f of extras?.figures ?? []) figMap[f.id] = f;
  const comicMap: Record<string, CatalogComic> = { ...COMIC_BY_ID };
  for (const c of extras?.comics ?? []) comicMap[c.id] = c;

  for (const owned of Object.values(state.ownedFigures)) {
    const fig = figMap[owned.figureId];
    if (!fig) continue;
    const est = figureMarket(fig).estimate;
    figureValue += est;
    figureCost += owned.acquiredPrice ?? fig.msrp;
    for (const p of figureHistory(fig, 12)) {
      historyMap.set(p.label, (historyMap.get(p.label) ?? 0) + p.value);
    }
  }

  for (const owned of Object.values(state.ownedComics)) {
    const comic = owned.catalogId ? comicMap[owned.catalogId] : undefined;
    const est = comic
      ? comicEstimate(comic)
      : owned.acquiredPrice ?? owned.custom?.msrp ?? 4.99;
    comicValue += est;
    comicCost += owned.acquiredPrice ?? comic?.msrp ?? owned.custom?.msrp ?? 0;
    if (comic) {
      for (const p of comicHistory(comic, 12)) {
        historyMap.set(p.label, (historyMap.get(p.label) ?? 0) + p.value);
      }
    }
  }

  const value = figureValue + comicValue;
  const cost = figureCost + comicCost;
  const history = [...historyMap.entries()].map(([label, v]) => ({
    label,
    value: Math.round(v * 100) / 100,
  }));

  const catalogFigures = extras?.figures?.length ? [...FIGURES, ...extras.figures] : FIGURES;
  const byCompany = catalogFigures.reduce(
    (acc, f) => {
      const row = acc[f.company] ?? { total: 0, owned: 0 };
      row.total += 1;
      if (state.ownedFigures[f.id]) row.owned += 1;
      acc[f.company] = row;
      return acc;
    },
    {} as Record<string, { total: number; owned: number }>,
  );

  return {
    figureValue,
    comicValue,
    value,
    cost,
    gain: value - cost,
    gainPct: cost ? ((value - cost) / cost) * 100 : 0,
    figureCount: Object.keys(state.ownedFigures).length,
    comicCount: Object.keys(state.ownedComics).length,
    history,
    byCompany,
  };
}
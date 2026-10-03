/** Repo-side SoldComps cache (key-free, public sold data) — safe for client and server. */
import cache from "@/data/market-comps.json";
import type { FigureSoldComps } from "@/lib/soldcomps";

const FIGURES = (cache as { figures?: Record<string, FigureSoldComps> }).figures ?? {};

/** Cached real sold comps for a figure (any status), or undefined. */
export function cachedFigureComps(figureId: string): FigureSoldComps | undefined {
  return FIGURES[figureId];
}

/** Real estimate when the cache has ≥3 matching sales, else null. */
export function cachedFigureEstimate(figureId: string): number | null {
  const row = FIGURES[figureId];
  return row && row.status === "ok" && row.estimate ? row.estimate : null;
}

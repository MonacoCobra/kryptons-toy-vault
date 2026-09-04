import type { CatalogComic, CatalogFigure, PulseBaseline, PulseSlice, VaultState } from "@/lib/types";
import { summarizeVault } from "@/lib/vault-math";
import { weekKey } from "@/lib/utils";

export type PulseDelta = {
  count: number;
  value: number;
};

export type WeeklyPulse = {
  week: string;
  figures: { current: PulseSlice; delta: PulseDelta };
  comics: { current: PulseSlice; delta: PulseDelta };
  total: { current: PulseSlice; delta: PulseDelta };
  baseline: PulseBaseline | null;
};

function slice(count: number, value: number): PulseSlice {
  return { count, value: Math.round(value * 100) / 100 };
}

function delta(current: PulseSlice, base: PulseSlice | undefined): PulseDelta {
  if (!base) return { count: 0, value: 0 };
  return {
    count: current.count - base.count,
    value: Math.round((current.value - base.value) * 100) / 100,
  };
}

export function capturePulseSnapshot(
  state: Pick<VaultState, "ownedFigures" | "ownedComics">,
  extras?: { figures?: CatalogFigure[]; comics?: CatalogComic[] },
  week = weekKey(),
): PulseBaseline {
  const stats = summarizeVault(state, extras);
  const figures = slice(stats.figureCount, stats.figureValue);
  const comics = slice(stats.comicCount, stats.comicValue);
  const total = slice(figures.count + comics.count, stats.value);
  return {
    week,
    figures,
    comics,
    total,
    capturedAt: new Date().toISOString(),
  };
}

export function buildWeeklyPulse(
  state: Pick<VaultState, "ownedFigures" | "ownedComics" | "pulseBaselines">,
  extras?: { figures?: CatalogFigure[]; comics?: CatalogComic[] },
  week = weekKey(),
): WeeklyPulse {
  const current = capturePulseSnapshot(state, extras, week);
  const baseline = state.pulseBaselines[week] ?? null;
  return {
    week,
    figures: { current: current.figures, delta: delta(current.figures, baseline?.figures) },
    comics: { current: current.comics, delta: delta(current.comics, baseline?.comics) },
    total: { current: current.total, delta: delta(current.total, baseline?.total) },
    baseline,
  };
}

export function formatQtyDelta(n: number): string {
  if (n > 0) return `+${n}`;
  if (n < 0) return `${n}`;
  return "0";
}

export function formatValueDelta(n: number): string {
  const abs = Math.abs(n);
  const body = abs >= 100 ? abs.toFixed(0) : abs.toFixed(abs % 1 === 0 ? 0 : 2);
  if (n > 0) return `+$${body}`;
  if (n < 0) return `-$${body}`;
  return "$0";
}

export function hasMeaningfulDelta(pulse: WeeklyPulse): boolean {
  return (
    pulse.total.delta.count !== 0 ||
    pulse.total.delta.value !== 0 ||
    pulse.figures.delta.count !== 0 ||
    pulse.comics.delta.count !== 0
  );
}

import { useEffect, useMemo } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { PulseBoard } from "@/components/pulse-board";
import { useLiveComics, useLiveFigures } from "@/lib/live-store";
import { useHydrated, useVault } from "@/lib/store";
import { weekKey } from "@/lib/utils";
import {
  buildWeeklyPulse,
  capturePulseSnapshot,
  formatQtyDelta,
  formatValueDelta,
  hasMeaningfulDelta,
} from "@/lib/weekly-pulse";

export const Route = createFileRoute("/pulse")({
  component: PulsePage,
});

function PulsePage() {
  const hydrated = useHydrated();
  const ownedFigures = useVault((s) => s.ownedFigures);
  const ownedComics = useVault((s) => s.ownedComics);
  const pulseBaselines = useVault((s) => s.pulseBaselines);
  const ensurePulseBaseline = useVault((s) => s.ensurePulseBaseline);
  const liveFigures = useLiveFigures();
  const liveComics = useLiveComics();
  const week = weekKey();

  useEffect(() => {
    if (!hydrated) return;
    ensurePulseBaseline(
      capturePulseSnapshot(
        { ownedFigures, ownedComics },
        { figures: liveFigures, comics: liveComics },
        week,
      ),
    );
  }, [hydrated, ownedFigures, ownedComics, liveFigures, liveComics, week, ensurePulseBaseline]);

  const pulse = useMemo(
    () =>
      buildWeeklyPulse(
        { ownedFigures, ownedComics, pulseBaselines },
        { figures: liveFigures, comics: liveComics },
        week,
      ),
    [ownedFigures, ownedComics, pulseBaselines, liveFigures, liveComics, week],
  );

  const headline = hasMeaningfulDelta(pulse)
    ? `${formatQtyDelta(pulse.total.delta.count)}  ·  ${formatValueDelta(pulse.total.delta.value)}`
    : "Holding steady";

  return (
    <main className="mx-auto flex max-w-xl flex-col gap-6">
      <header>
        <h1 className="font-display text-4xl tracking-wide uppercase">This week</h1>
        <p className="mt-2 text-sm text-muted">
          Qty and estimate changes since the start of {week}. Toys and comics use mixed-condition
          eBay sold averages when available.
        </p>
        <p className="mt-4 font-display text-3xl tracking-wide text-gold tabular">{headline}</p>
      </header>

      <PulseBoard pulse={pulse} />

      <p className="text-xs leading-relaxed text-subtle">
        Baseline locks on your first visit each ISO week. Adding pieces or market moves show up as
        clean deltas here — and in the weekly popup.
      </p>
    </main>
  );
}

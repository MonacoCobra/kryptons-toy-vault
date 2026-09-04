import { PulseDeltaCard } from "@/components/pulse-delta-card";
import type { WeeklyPulse } from "@/lib/weekly-pulse";

export function PulseBoard({ pulse }: { pulse: WeeklyPulse }) {
  return (
    <div className="grid gap-3">
      <PulseDeltaCard label="Toys" current={pulse.figures.current} delta={pulse.figures.delta} />
      <PulseDeltaCard label="Comics" current={pulse.comics.current} delta={pulse.comics.delta} />
      <PulseDeltaCard
        label="Total"
        current={pulse.total.current}
        delta={pulse.total.delta}
        emphasis
      />
    </div>
  );
}

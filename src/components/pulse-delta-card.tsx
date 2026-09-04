import { cn } from "@/lib/utils";
import { formatQtyDelta, formatValueDelta, type PulseDelta } from "@/lib/weekly-pulse";
import type { PulseSlice } from "@/lib/types";
import { usd } from "@/lib/format";

export function PulseDeltaCard({
  label,
  current,
  delta,
  emphasis,
}: {
  label: string;
  current: PulseSlice;
  delta: PulseDelta;
  emphasis?: boolean;
}) {
  const qtyTone = delta.count > 0 ? "text-gain" : delta.count < 0 ? "text-loss" : "text-muted";
  const valTone = delta.value > 0 ? "text-gain" : delta.value < 0 ? "text-loss" : "text-muted";

  return (
    <div
      className={cn(
        "rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]",
        emphasis && "ring-1 ring-gold/35",
      )}
    >
      <p className="text-[11px] tracking-[0.2em] text-muted uppercase">{label}</p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <div>
          <p className={cn("font-display text-3xl tracking-wide tabular", qtyTone)}>
            {formatQtyDelta(delta.count)}
          </p>
          <p className="mt-1 text-xs text-subtle">{current.count} in vault</p>
        </div>
        <div className="text-right">
          <p className={cn("font-display text-3xl tracking-wide tabular", valTone)}>
            {formatValueDelta(delta.value)}
          </p>
          <p className="mt-1 text-xs text-subtle">{usd(current.value)} est.</p>
        </div>
      </div>
    </div>
  );
}

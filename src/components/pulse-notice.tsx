import { useEffect, useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PulseBoard } from "@/components/pulse-board";
import { useLiveComics, useLiveFigures } from "@/lib/live-store";
import { useHydrated, useVault } from "@/lib/store";
import { weekKey } from "@/lib/utils";
import {
  buildWeeklyPulse,
  capturePulseSnapshot,
  hasMeaningfulDelta,
} from "@/lib/weekly-pulse";

export function PulseNotice() {
  const hydrated = useHydrated();
  const ownedFigures = useVault((s) => s.ownedFigures);
  const ownedComics = useVault((s) => s.ownedComics);
  const pulseBaselines = useVault((s) => s.pulseBaselines);
  const lastPulseNoticeWeek = useVault((s) => s.lastPulseNoticeWeek);
  const ensurePulseBaseline = useVault((s) => s.ensurePulseBaseline);
  const markPulseNoticeSeen = useVault((s) => s.markPulseNoticeSeen);
  const liveFigures = useLiveFigures();
  const liveComics = useLiveComics();
  const week = weekKey();
  const [open, setOpen] = useState(false);

  const pulse = useMemo(
    () =>
      buildWeeklyPulse(
        { ownedFigures, ownedComics, pulseBaselines },
        { figures: liveFigures, comics: liveComics },
        week,
      ),
    [ownedFigures, ownedComics, pulseBaselines, liveFigures, liveComics, week],
  );

  useEffect(() => {
    if (!hydrated) return;
    const snapshot = capturePulseSnapshot(
      { ownedFigures, ownedComics },
      { figures: liveFigures, comics: liveComics },
      week,
    );
    ensurePulseBaseline(snapshot);
  }, [
    hydrated,
    ownedFigures,
    ownedComics,
    liveFigures,
    liveComics,
    week,
    ensurePulseBaseline,
  ]);

  useEffect(() => {
    if (!hydrated) return;
    if (lastPulseNoticeWeek === week) return;
    // Show once per ISO week after baseline exists for the week.
    if (!pulseBaselines[week]) return;
    const t = window.setTimeout(() => setOpen(true), 600);
    return () => window.clearTimeout(t);
  }, [hydrated, lastPulseNoticeWeek, week, pulseBaselines]);

  function dismiss() {
    markPulseNoticeSeen(week);
    setOpen(false);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) dismiss();
        else setOpen(true);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>This week&apos;s pulse</DialogTitle>
          <DialogDescription>
            {hasMeaningfulDelta(pulse)
              ? "How your vault moved since the start of the week — toys, comics, and total."
              : "Your vault is holding steady so far this week. Check back as you add pieces."}
          </DialogDescription>
        </DialogHeader>
        <PulseBoard pulse={pulse} />
        <div className="mt-5 flex flex-wrap gap-2">
          <Button asChild>
            <Link to="/pulse" onClick={dismiss}>
              Open Pulse
            </Link>
          </Button>
          <Button variant="secondary" onClick={dismiss}>
            Got it
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

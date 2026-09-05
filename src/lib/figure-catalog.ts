import { FIGURES } from "@/data/figures";
import type { CatalogFigure } from "@/lib/types";

/** Weeks a figure stays in New & Noteworthy before counting as archive-only. */
export const NOTEWORTHY_WEEKS = 3;

export type FigureLibrary = {
  noteworthy: CatalogFigure[];
  archive: CatalogFigure[];
  weekHintMs: number;
};

function figureKey(f: { name: string; subtitle: string; line: string; company: string }) {
  return `${f.name}|${f.subtitle}|${f.line}|${f.company}`.toLowerCase();
}

function isRecentRelease(releaseDate: string | undefined, now: Date, windowMs: number): boolean {
  if (!releaseDate) return false;
  const t = Date.parse(releaseDate);
  if (!Number.isFinite(t)) return false;
  return now.getTime() - t < windowMs;
}

/**
 * Client-side split mirroring comics: weekly/live extras + very recent static
 * releases stay in New & Noteworthy; the permanent FIGURES catalog (seed + backlog)
 * forms the archive. Figures UI may still show a single merged list via mergeFigures.
 */
export function splitFiguresClient(extras: CatalogFigure[] = [], now = new Date()): FigureLibrary {
  const windowMs = NOTEWORTHY_WEEKS * 7 * 24 * 3600 * 1000;
  const noteworthyKeys = new Set<string>();
  const noteworthy: CatalogFigure[] = [];

  for (const f of extras) {
    const k = figureKey(f);
    if (noteworthyKeys.has(k)) continue;
    noteworthyKeys.add(k);
    noteworthy.push(f);
  }

  for (const f of FIGURES) {
    const k = figureKey(f);
    if (noteworthyKeys.has(k)) continue;
    if (isRecentRelease(f.releaseDate, now, windowMs)) {
      noteworthyKeys.add(k);
      noteworthy.push(f);
    }
  }

  const archive = FIGURES.filter((f) => !noteworthyKeys.has(figureKey(f)));

  return {
    noteworthy: noteworthy.sort((a, b) => (a.releaseDate < b.releaseDate ? 1 : -1)),
    archive,
    weekHintMs: windowMs,
  };
}

/** Permanent archive view: static FIGURES minus anything currently in the N&N window from extras. */
export function figureArchive(extras: CatalogFigure[] = [], now = new Date()): CatalogFigure[] {
  return splitFiguresClient(extras, now).archive;
}

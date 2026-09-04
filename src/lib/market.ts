import { FIGURE_BY_ID, FIGURES } from "@/data/figures";
import { COMIC_BY_ID, COMICS } from "@/data/comics";
import type { CatalogComic, CatalogFigure, SoldComp } from "@/lib/types";
import { hashString, isoWeek, mean, mulberry32 } from "@/lib/utils";

const CONDITION_WEIGHTS = [
  { c: "MIB sealed", w: 0.52, mod: 1 },
  { c: "Opened complete", w: 0.33, mod: 0.78 },
  { c: "Loose no box", w: 0.15, mod: 0.55 },
] as const;

function pickCondition(rng: () => number) {
  const r = rng();
  let acc = 0;
  for (const row of CONDITION_WEIGHTS) {
    acc += row.w;
    if (r <= acc) return row;
  }
  return CONDITION_WEIGHTS[0]!;
}

function weekDate(year: number, week: number, dayOffset: number): string {
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const start = new Date(jan4);
  start.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() || 7) - 1) + (week - 1) * 7);
  start.setUTCDate(start.getUTCDate() + dayOffset);
  return start.toISOString().slice(0, 10);
}

function listingTitle(figure: CatalogFigure, condition: string): string {
  const excl = figure.exclusive ? `${figure.exclusive} exclusive ` : "";
  return `${figure.line} ${figure.name} ${figure.subtitle} ${excl}${condition}`.replace(/\s+/g, " ").trim();
}

export function compsForFigure(figure: CatalogFigure, year: number, week: number): SoldComp[] {
  const comps: SoldComp[] = [];
  const wave = 1 + Math.sin((week + (hashString(figure.id) % 40)) / 9) * 0.03;
  for (let i = 0; i < 5; i++) {
    const rng = mulberry32(hashString(`${figure.id}:sold:${i}`));
    const weekRng = mulberry32(hashString(`${figure.id}:${year}:W${week}:${i}`));
    const cond = pickCondition(rng);
    const dayOffset = -Math.floor(weekRng() * 18);
    const noise = 0.96 + weekRng() * 0.08;
    const price = Math.max(4, figure.msrp * figure.demand * cond.mod * wave * noise);
    comps.push({
      price: Math.round(price * 100) / 100,
      date: weekDate(year, week, dayOffset),
      condition: cond.c,
      title: listingTitle(figure, cond.c),
      source: "synthetic",
    });
  }
  return comps.sort((a, b) => (a.date < b.date ? 1 : -1));
}

const COMIC_GRADES = [
  { c: "Raw NM", w: 0.28, mod: 1 },
  { c: "Raw VF", w: 0.22, mod: 0.72 },
  { c: "CGC 9.8", w: 0.18, mod: 2.8 },
  { c: "CGC 9.4", w: 0.18, mod: 1.6 },
  { c: "Raw GD", w: 0.14, mod: 0.38 },
] as const;

function pickComicGrade(rng: () => number) {
  const r = rng();
  let acc = 0;
  for (const row of COMIC_GRADES) {
    acc += row.w;
    if (r <= acc) return row;
  }
  return COMIC_GRADES[0]!;
}

export function compsForComic(comic: CatalogComic, year: number, week: number): SoldComp[] {
  const comps: SoldComp[] = [];
  const wave = 1 + Math.sin((week + (hashString(comic.id) % 40)) / 10) * 0.03;
  for (let i = 0; i < 5; i++) {
    const rng = mulberry32(hashString(`${comic.id}:sold:${i}`));
    const weekRng = mulberry32(hashString(`${comic.id}:${year}:W${week}:${i}`));
    const grade = pickComicGrade(rng);
    const dayOffset = -Math.floor(weekRng() * 20);
    const noise = 0.96 + weekRng() * 0.08;
    const price = Math.max(1, comic.msrp * comic.demand * grade.mod * wave * noise);
    const variant = comic.variant ? ` ${comic.variant}` : "";
    comps.push({
      price: Math.round(price * 100) / 100,
      date: weekDate(year, week, dayOffset),
      condition: grade.c,
      title: `${comic.series} #${comic.issue}${variant} ${comic.publisher} ${grade.c}`,
      source: "synthetic",
    });
  }
  return comps.sort((a, b) => (a.date < b.date ? 1 : -1));
}

/** Average of the most recent matching sold comps (up to 5). */
export function estimateFromComps(comps: SoldComp[]): number {
  const recent = [...comps]
    .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
    .slice(0, 5);
  return Math.round(mean(recent.map((c) => c.price)) * 100) / 100;
}

export function currentWeek() {
  return isoWeek();
}

function shiftedWeek(weekShift = 0) {
  const { year, week } = isoWeek();
  let y = year;
  let w = week + weekShift;
  while (w <= 0) {
    w += 52;
    y -= 1;
  }
  while (w > 52) {
    w -= 52;
    y += 1;
  }
  return { year: y, week: w };
}

export function figureMarket(figure: CatalogFigure, weekShift = 0) {
  const { year, week } = shiftedWeek(weekShift);
  const comps = compsForFigure(figure, year, week);
  const estimate = estimateFromComps(comps);
  return { comps, estimate, year, week };
}

export function figureHistory(figure: CatalogFigure, weeks = 12) {
  const points: { label: string; value: number }[] = [];
  for (let i = weeks - 1; i >= 0; i--) {
    const m = figureMarket(figure, -i);
    points.push({
      label: `W${m.week}`,
      value: m.estimate,
    });
  }
  return points;
}

export function comicMarket(comic: CatalogComic, weekShift = 0) {
  const { year, week } = shiftedWeek(weekShift);
  const comps = compsForComic(comic, year, week);
  const estimate = estimateFromComps(comps);
  return { comps, estimate, year, week };
}

export function comicEstimate(comic: CatalogComic, weekShift = 0): number {
  return comicMarket(comic, weekShift).estimate;
}

export function comicHistory(comic: CatalogComic, weeks = 12) {
  return Array.from({ length: weeks }, (_, i) => {
    const shift = i - (weeks - 1);
    const m = comicMarket(comic, shift);
    return { label: `W${m.week}`, value: m.estimate };
  });
}

export function lookupFigure(id: string) {
  return FIGURE_BY_ID[id];
}

export function lookupComic(id: string) {
  return COMIC_BY_ID[id];
}

export function topMovers(limit = 5) {
  return FIGURES.map((f) => {
    const now = figureMarket(f, 0).estimate;
    const prev = figureMarket(f, -1).estimate;
    const delta = now - prev;
    const pct = prev ? (delta / prev) * 100 : 0;
    return { figure: f, now, prev, delta, pct };
  })
    .sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct))
    .slice(0, limit);
}

export function catalogStats() {
  return {
    figures: FIGURES.length,
    comics: COMICS.length,
    companies: new Set(FIGURES.map((f) => f.company)).size,
  };
}

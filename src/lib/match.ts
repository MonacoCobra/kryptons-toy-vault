import { comicLabel, mergeComics } from "@/data/comics";
import { FIGURES } from "@/data/figures";
import type { CatalogComic, CatalogFigure } from "@/lib/types";

function norm(s: string) {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function scoreName(hay: string, needle: string) {
  const h = norm(hay);
  const n = norm(needle);
  if (!n) return 0;
  if (h === n) return 100;
  if (h.includes(n)) return 70 + Math.min(20, n.length);
  const tokens = n.split(" ").filter(Boolean);
  let hit = 0;
  for (const t of tokens) if (h.includes(t)) hit += 1;
  return tokens.length ? (hit / tokens.length) * 55 : 0;
}

export type CoverGuess = {
  series: string;
  issue: string;
  publisher?: string;
  year?: string;
  variant?: string;
  writers?: string[];
  artists?: string[];
};

export function matchComicsFromGuess(guess: CoverGuess, limit = 5, extras: CatalogComic[] = []): CatalogComic[] {
  const scored = mergeComics(extras).map((c) => {
    let s = scoreName(c.series, guess.series);
    if (guess.issue && c.issue === String(guess.issue).replace(/^#/, "")) s += 25;
    if (guess.publisher && norm(c.publisher).includes(norm(guess.publisher))) s += 10;
    if (guess.variant && c.variant && norm(c.variant).includes(norm(guess.variant))) s += 8;
    return { c, s };
  })
    .filter((x) => x.s >= 40)
    .sort((a, b) => b.s - a.s);
  return scored.slice(0, limit).map((x) => x.c);
}

export function matchFigures(query: string, limit = 8): CatalogFigure[] {
  const q = query.trim();
  if (!q) return [];
  return FIGURES.map((f) => ({
    f,
    s:
      scoreName(`${f.name} ${f.subtitle} ${f.line}`, q) +
      scoreName(f.company, q) * 0.2,
  }))
    .filter((x) => x.s > 20)
    .sort((a, b) => b.s - a.s)
    .slice(0, limit)
    .map((x) => x.f);
}

export { comicLabel };

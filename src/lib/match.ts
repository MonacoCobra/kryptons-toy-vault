import { comicLabel, mergeComics } from "@/data/comics";
import { FIGURES } from "@/data/figures";
import { rankComicsFromGuess, scoreName, type CoverGuess } from "@/lib/cover-match";
import type { CatalogComic, CatalogFigure } from "@/lib/types";

export type { CoverGuess };

export function matchComicsFromGuess(
  guess: CoverGuess,
  limit = 5,
  extras: CatalogComic[] = [],
  promoted: CatalogComic[] = [],
): CatalogComic[] {
  return rankComicsFromGuess(guess, mergeComics(extras, promoted), limit);
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

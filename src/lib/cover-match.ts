import type { CatalogComic } from "@/lib/types";

export type CoverGuess = {
  series: string;
  issue: string;
  publisher?: string;
  year?: string;
  variant?: string;
  writers?: string[];
  artists?: string[];
};

export function normalizeToken(s: string) {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** Strip # and leading zeros so AI "001" matches catalog "1". */
export function normalizeIssue(s: string) {
  return String(s ?? "")
    .trim()
    .replace(/^#/, "")
    .replace(/^0+(?=\d)/, "")
    .toLowerCase();
}

export function scoreName(hay: string, needle: string) {
  const h = normalizeToken(hay);
  const n = normalizeToken(needle);
  if (!n) return 0;
  if (h === n) return 100;
  if (h.includes(n)) return 70 + Math.min(20, n.length);
  const tokens = n.split(" ").filter(Boolean);
  let hit = 0;
  for (const t of tokens) if (h.includes(t)) hit += 1;
  return tokens.length ? (hit / tokens.length) * 55 : 0;
}

export function scoreCoverGuess(comic: CatalogComic, guess: CoverGuess): number {
  let score = scoreName(comic.series, guess.series);
  if (guess.issue && normalizeIssue(comic.issue) === normalizeIssue(guess.issue)) score += 25;
  if (guess.publisher && normalizeToken(comic.publisher).includes(normalizeToken(guess.publisher))) score += 10;
  if (guess.variant && comic.variant && normalizeToken(comic.variant).includes(normalizeToken(guess.variant))) {
    score += 8;
  }
  return score;
}

/** Rank existing catalog rows only — never invents titles. */
export function rankComicsFromGuess(
  guess: CoverGuess,
  catalog: CatalogComic[],
  limit = 5,
): CatalogComic[] {
  return catalog
    .map((comic) => ({ comic, score: scoreCoverGuess(comic, guess) }))
    .filter((row) => row.score >= 40)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((row) => row.comic);
}

import type { CatalogComic, ComicFormat, CustomComic } from "@/lib/types";

export const COMIC_FORMATS: ComicFormat[] = [
  "single",
  "annual",
  "tpb",
  "hc",
  "omnibus",
  "facsimile",
];

export const COLLECTED_FORMATS: readonly ComicFormat[] = ["tpb", "hc", "omnibus"];

export const COMIC_FORMAT_LABELS: Record<ComicFormat, string> = {
  single: "Single",
  annual: "Annual",
  tpb: "TPB",
  hc: "HC",
  omnibus: "Omnibus",
  facsimile: "Facsimile",
};

const KNOWN = new Set<string>(COMIC_FORMATS);

/** Map dump / import aliases onto `ComicFormat` (`hardcover` → `hc`). */
export function normalizeComicFormat(raw: unknown): ComicFormat {
  const s = String(raw ?? "")
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ");
  if (!s) return "single";
  if (KNOWN.has(s)) return s as ComicFormat;
  if (s === "hardcover" || s === "hard cover" || s === "hardback" || s === "hb") return "hc";
  if (s === "trade" || s === "trade paperback" || s === "tp") return "tpb";
  if (s === "omni") return "omnibus";
  if (s.includes("omnibus")) return "omnibus";
  if (s.includes("hardcover") || s.includes("hard cover") || /\bhc\b/.test(s)) return "hc";
  if (s.includes("trade") || /\btpb\b/.test(s)) return "tpb";
  if (s.includes("facsimile")) return "facsimile";
  if (s.includes("annual")) return "annual";
  return "single";
}

export function isCollectedFormat(raw: unknown): boolean {
  const format = normalizeComicFormat(raw);
  return format === "tpb" || format === "hc" || format === "omnibus";
}

export function isCollectedComic(comic: { format?: unknown }): boolean {
  return isCollectedFormat(comic.format);
}

export function comicFormatLabel(raw: unknown): string {
  return COMIC_FORMAT_LABELS[normalizeComicFormat(raw)];
}

/** Vault custom row → catalog-shaped book for Collected browse / search. */
export function catalogFromCustom(custom: CustomComic): CatalogComic {
  return {
    id: custom.id,
    series: custom.series,
    issue: custom.issue,
    publisher: custom.publisher,
    coverDate: custom.coverDate ?? "",
    writers: custom.writers ?? [],
    artists: custom.artists ?? [],
    description: custom.description ?? "",
    msrp: custom.msrp ?? 0,
    format: normalizeComicFormat(custom.format),
    variant: custom.variant,
    upc: custom.upc,
    demand: 0,
    key: false,
    palette: ["#111827", "#eab308", "#f8fafc"],
  };
}

export function filterCollectedComics<T extends { format?: unknown }>(comics: T[]): T[] {
  return comics.filter(isCollectedComic);
}

export function filterIssueComics<T extends { format?: unknown }>(comics: T[]): T[] {
  return comics.filter((c) => !isCollectedComic(c));
}

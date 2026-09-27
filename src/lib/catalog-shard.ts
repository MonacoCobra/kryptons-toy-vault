/**
 * Shared shard paths and hashes for the build-time catalog splitter and the browser.
 * Source dumps stay in src/data; these helpers only name the derived files.
 */

export const CATALOG_ROOT = "/catalog";

export type CatalogManifest = {
  generatedAt: string;
  figures: number;
  comics: number;
  companies: number;
  recentComics: import("@/lib/types").CatalogComic[];
  figureBrowse: string;
  publishers: string;
  noteworthy: string;
  comicSearch: string[];
  figureAliases: string;
};

export type FigureLineStat = { name: string; count: number };

export type FigurePartyStat = { total: number; lines: string[] };

export type FigureCompanyStat = {
  id: string;
  total: number;
  lines: FigureLineStat[];
  shard: string;
};

export type FranchiseCompanyStat = {
  id: string;
  total: number;
  lines: string[];
  parties?: Record<string, FigurePartyStat>;
};

export type FranchiseStat = {
  id: string;
  /** Set-collapsed count, matching the popular-franchise rail. */
  count: number;
  parties?: Record<string, number>;
  shard: string;
  partyShards?: Record<string, string>;
  companies: FranchiseCompanyStat[];
};

export type FigureBrowseIndex = {
  total: number;
  companies: FigureCompanyStat[];
  franchises: FranchiseStat[];
  /** Ordered slices of the full figure list, for the unfiltered grid and global search. */
  parts: string[];
};

export type PublisherIndexEntry = {
  publisher: string;
  slug: string;
  seriesCount: number;
  issueCount: number;
  latestDate: string;
  collectedCount: number;
  shard: string;
};

export type PublisherIndex = { publishers: PublisherIndexEntry[] };

export type SeriesShardRef = import("@/lib/comic-series").SeriesRef & { shard: string };

export type PublisherDetail = {
  publisher: string;
  series: SeriesShardRef[];
  collectedSeries: SeriesShardRef[];
  collectedCount: number;
  collectedFormats: string[];
};

export type ComicRunFile = {
  comics: import("@/lib/types").CatalogComic[];
  /** Same-family rows that landed in another run (facsimile / reboot collisions). */
  related: import("@/lib/types").CatalogComic[];
  years: Record<string, number>;
};

export type ComicBucketFile = {
  comics: import("@/lib/types").CatalogComic[];
  years: Record<string, number>;
  /** Relative catalog path of the run shard for each id. */
  run: Record<string, string>;
};

export type NoteworthyFile = {
  comics: import("@/lib/types").CatalogComic[];
  years: Record<string, number>;
};

/** FNV-1a, first `chars` hex digits. Stable across the shard script and the browser. */
export function bucketKey(id: string, chars: number): string {
  let h = 2166136261;
  for (let i = 0; i < id.length; i++) {
    h ^= id.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16).padStart(8, "0").slice(0, chars);
}

/** 48-bit id for run / set filenames. */
export function shardId(input: string): string {
  let h1 = 2166136261;
  let h2 = 0x811c9dc5;
  for (let i = 0; i < input.length; i++) {
    const c = input.charCodeAt(i);
    h1 ^= c;
    h1 = Math.imul(h1, 16777619);
    h2 ^= c;
    h2 = Math.imul(h2, 2246822519);
  }
  const a = (h1 >>> 0).toString(16).padStart(8, "0");
  const b = (h2 >>> 0).toString(16).padStart(8, "0");
  return (a + b).slice(0, 12);
}

export function figureBucketPath(id: string): string {
  return `figures/b/${bucketKey(id, 2)}.json`;
}

export function figureSetPath(setId: string): string {
  return `figures/sets/${shardId(setId)}.json`;
}

export function comicBucketPath(id: string): string {
  return `comics/b/${bucketKey(id, 3)}.json`;
}

export function upcBucketPath(id: string): string {
  return `upc/${bucketKey(id, 3)}.json`;
}

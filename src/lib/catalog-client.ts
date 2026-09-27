import { scoreCoverGuess, searchCatalogLimited, type CoverGuess } from "@/lib/cover-match";
import { searchComicList } from "@/lib/catalog-search";
import {
  comicBucketPath,
  figureBucketPath,
  figureSetPath,
  type CatalogManifest,
  type ComicBucketFile,
  type ComicRunFile,
  type FigureBrowseIndex,
  type NoteworthyFile,
  type PublisherDetail,
  type PublisherIndex,
} from "@/lib/catalog-shard";
import type { CatalogComic, CatalogFigure } from "@/lib/types";

const memory = new Map<string, unknown>();
const pending = new Map<string, Promise<unknown>>();

function cached<T>(key: string, load: () => Promise<T>): Promise<T> {
  const hit = memory.get(key);
  if (hit !== undefined) return Promise.resolve(hit as T);
  const existing = pending.get(key);
  if (existing) return existing as Promise<T>;
  const task = load()
    .then((data) => {
      memory.set(key, data);
      pending.delete(key);
      return data;
    })
    .catch((err) => {
      pending.delete(key);
      throw err;
    });
  pending.set(key, task);
  return task;
}

let manifestPromise: Promise<CatalogManifest> | null = null;

export function loadManifest(): Promise<CatalogManifest> {
  if (!manifestPromise) {
    manifestPromise = fetch("/catalog/manifest.json", { cache: "no-cache" }).then(async (res) => {
      if (!res.ok) throw new Error("Catalog manifest is not ready yet.");
      return (await res.json()) as CatalogManifest;
    });
    manifestPromise.catch(() => {
      manifestPromise = null;
    });
  }
  return manifestPromise;
}

export async function loadCatalogJson<T>(relPath: string): Promise<T> {
  const manifest = await loadManifest();
  const url = `/catalog/${relPath.replace(/^\/+/, "")}?v=${encodeURIComponent(manifest.generatedAt)}`;
  return cached(url, async () => {
    const res = await fetch(url);
    if (!res.ok) {
      const empty = [] as unknown as T;
      if (res.status === 404) return empty;
      throw new Error(`Catalog file missing (${res.status})`);
    }
    return (await res.json()) as T;
  });
}

export async function loadFigureBrowse(): Promise<FigureBrowseIndex> {
  const manifest = await loadManifest();
  return loadCatalogJson<FigureBrowseIndex>(manifest.figureBrowse);
}

export async function loadFigureParts(): Promise<CatalogFigure[]> {
  const browse = await loadFigureBrowse();
  const parts = await Promise.all(browse.parts.map((part) => loadCatalogJson<CatalogFigure[]>(part)));
  return parts.flat();
}

export async function loadFiguresByIds(ids: string[]): Promise<CatalogFigure[]> {
  const unique = [...new Set(ids.filter(Boolean))];
  if (!unique.length) return [];
  const groups = new Map<string, Set<string>>();
  for (const id of unique) {
    const path = figureBucketPath(id);
    const set = groups.get(path) ?? new Set<string>();
    set.add(id);
    groups.set(path, set);
  }
  const out: CatalogFigure[] = [];
  await Promise.all(
    [...groups.entries()].map(async ([path, want]) => {
      const rows = await loadCatalogJson<CatalogFigure[]>(path);
      if (!Array.isArray(rows)) return;
      for (const row of rows) if (want.has(row.id)) out.push(row);
    }),
  );
  return out;
}

export async function loadFigureSet(setId: string | undefined): Promise<CatalogFigure[]> {
  if (!setId?.trim()) return [];
  const rows = await loadCatalogJson<CatalogFigure[]>(figureSetPath(setId.trim()));
  return Array.isArray(rows) ? rows : [];
}

let aliasPromise: Promise<Record<string, string>> | null = null;

export function loadFigureAliases(): Promise<Record<string, string>> {
  if (!aliasPromise) {
    aliasPromise = loadManifest()
      .then(async (manifest) => {
        const data = await loadCatalogJson<Record<string, string> | unknown[]>(manifest.figureAliases);
        if (!data || Array.isArray(data)) return {};
        return data;
      })
      .catch(() => ({}));
  }
  return aliasPromise;
}

export async function resolveFigure(id: string, extras: CatalogFigure[] = []): Promise<CatalogFigure | undefined> {
  const q = id.trim().toLowerCase();
  const fromExtra = extras.find((f) => f.id === id || (q && (f.sku ?? "").trim().toLowerCase() === q));
  if (fromExtra) return fromExtra;
  const direct = await loadFiguresByIds([id]);
  if (direct[0]) return direct[0];
  const aliases = await loadFigureAliases();
  const upper = id.trim().toUpperCase();
  const mapped = aliases[upper] || aliases[`ID:${upper}`];
  if (!mapped || mapped === id) return undefined;
  const via = await loadFiguresByIds([mapped]);
  return via[0] ?? extras.find((f) => f.id === mapped);
}

export async function loadPublisherIndex(): Promise<PublisherIndex> {
  const manifest = await loadManifest();
  return loadCatalogJson<PublisherIndex>(manifest.publishers);
}

export async function loadPublisherDetail(shard: string): Promise<PublisherDetail> {
  return loadCatalogJson<PublisherDetail>(shard);
}

export async function loadComicRun(shard: string): Promise<ComicRunFile> {
  const file = await loadCatalogJson<ComicRunFile>(shard);
  if (!file || !Array.isArray(file.comics)) return { comics: [], related: [], years: {} };
  return { comics: file.comics, related: file.related ?? [], years: file.years ?? {} };
}

export async function loadNoteworthy(): Promise<NoteworthyFile> {
  const manifest = await loadManifest();
  const file = await loadCatalogJson<NoteworthyFile>(manifest.noteworthy);
  if (!file || !Array.isArray(file.comics)) return { comics: [], years: {} };
  return file;
}

type SearchRow = [
  string,
  number,
  string,
  number,
  string,
  string,
  string,
  string,
  string,
  number,
  number,
  number,
  string,
  string,
  string,
  string,
  string,
  number,
];

type ComicSearchShard = { series: string[]; pubs: string[]; rows: SearchRow[] };

function paletteOf(raw: string): [string, string, string] {
  const parts = raw.split(",").map((p) => (p.startsWith("#") ? p : `#${p}`));
  return [parts[0] || "#1e3a8a", parts[1] || "#e30613", parts[2] || "#f8fafc"];
}

function expandRow(shard: ComicSearchShard, row: SearchRow): CatalogComic {
  const writers = row[14] ? row[14].split(", ").filter(Boolean) : [];
  const artists = row[15] ? row[15].split(", ").filter(Boolean) : [];
  return {
    id: row[0],
    series: shard.series[row[1]] ?? "",
    issue: row[2],
    publisher: shard.pubs[row[3]] ?? "",
    coverDate: row[7],
    streetDate: row[8] || undefined,
    writers,
    artists,
    description: row[16] ?? "",
    msrp: row[10],
    format: (row[4] || "single") as CatalogComic["format"],
    variant: row[5] || undefined,
    upc: row[6] || undefined,
    demand: row[11],
    key: row[9] === 1,
    palette: paletteOf(row[13] || ""),
    cover: row[12] || undefined,
  };
}

function rowHay(shard: ComicSearchShard, row: SearchRow): string {
  const series = shard.series[row[1]] ?? "";
  const publisher = shard.pubs[row[3]] ?? "";
  return `${series} ${row[2]} ${publisher} ${row[14]} ${row[15]} ${row[5]} ${row[6]} ${row[4]} ${row[16]}`.toLowerCase();
}

function rowMatches(shard: ComicSearchShard, row: SearchRow, q: string, issueMatch: RegExpMatchArray | null): boolean {
  const hay = rowHay(shard, row);
  if (hay.includes(q)) return true;
  if (issueMatch && row[2] === issueMatch[1] && hay.includes(q.replace(issueMatch[0], "").trim())) return true;
  return false;
}

async function searchShards(): Promise<ComicSearchShard[]> {
  const manifest = await loadManifest();
  return Promise.all(manifest.comicSearch.map((path) => loadCatalogJson<ComicSearchShard>(path)));
}

export type ComicSearchHit = { comic: CatalogComic; year: number };

/** Global comic search over compact shards. Does not download run files. */
export async function searchComicShards(query: string, limit = 4000): Promise<ComicSearchHit[]> {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const issueMatch = q.match(/#?\s*(\d+[a-z]?)$/i);
  const shards = await searchShards();
  const hits: ComicSearchHit[] = [];
  for (const shard of shards) {
    if (!shard?.rows) continue;
    for (const row of shard.rows) {
      if (!rowMatches(shard, row, q, issueMatch)) continue;
      hits.push({ comic: expandRow(shard, row), year: row[17] ?? 0 });
      if (hits.length >= limit) return hits;
    }
  }
  return hits;
}

/** First `limit` text hits, scanning shards in catalog order (same idea as the old in-memory scan). */
export async function searchComicsLimited(
  query: string,
  extras: CatalogComic[][],
  limit = 8,
): Promise<CatalogComic[]> {
  const fromExtras = searchCatalogLimited(query, extras, limit);
  if (fromExtras.length >= limit) return fromExtras;
  const q = query.trim().toLowerCase();
  if (!q) return fromExtras;
  const issueMatch = q.match(/#?\s*(\d+[a-z]?)$/i);
  const seen = new Set(fromExtras.map((c) => c.id));
  const out = [...fromExtras];
  const manifest = await loadManifest();
  for (const path of manifest.comicSearch) {
    const shard = await loadCatalogJson<ComicSearchShard>(path);
    if (!shard?.rows) continue;
    for (const row of shard.rows) {
      if (!rowMatches(shard, row, q, issueMatch)) continue;
      if (seen.has(row[0])) continue;
      seen.add(row[0]);
      out.push(expandRow(shard, row));
      if (out.length >= limit) return out;
    }
  }
  return out;
}

/** Rank a cover guess across shards. Only winning rows are expanded into comics. */
export async function rankComicGuess(
  guess: CoverGuess,
  extras: CatalogComic[],
  limit = 5,
): Promise<CatalogComic[]> {
  let best: { comic: CatalogComic; score: number }[] = extras
    .map((comic) => ({ comic, score: scoreCoverGuess(comic, guess) }))
    .filter((row) => row.score >= 40);
  const manifest = await loadManifest();
  for (const path of manifest.comicSearch) {
    const shard = await loadCatalogJson<ComicSearchShard>(path);
    if (!shard?.rows) continue;
    for (const row of shard.rows) {
      const stub = {
        series: shard.series[row[1]] ?? "",
        issue: row[2],
        publisher: shard.pubs[row[3]] ?? "",
        variant: row[5] || undefined,
      } as CatalogComic;
      const score = scoreCoverGuess(stub, guess);
      if (score < 40) continue;
      best.push({ comic: expandRow(shard, row), score });
    }
    best.sort((a, b) => b.score - a.score);
    if (best.length > limit * 4) best = best.slice(0, limit * 4);
  }
  best.sort((a, b) => b.score - a.score);
  const seen = new Set<string>();
  const out: CatalogComic[] = [];
  for (const row of best) {
    if (seen.has(row.comic.id)) continue;
    seen.add(row.comic.id);
    out.push(row.comic);
    if (out.length >= limit) break;
  }
  return out;
}

export async function loadComicsByIds(ids: string[]): Promise<ComicSearchHit[]> {
  const unique = [...new Set(ids.filter(Boolean))];
  if (!unique.length) return [];
  const groups = new Map<string, Set<string>>();
  for (const id of unique) {
    const path = comicBucketPath(id);
    const set = groups.get(path) ?? new Set<string>();
    set.add(id);
    groups.set(path, set);
  }
  const out: ComicSearchHit[] = [];
  await Promise.all(
    [...groups.entries()].map(async ([path, want]) => {
      const file = await loadCatalogJson<ComicBucketFile | CatalogComic[]>(path);
      const comics = Array.isArray(file) ? file : (file?.comics ?? []);
      const years = Array.isArray(file) ? {} : (file?.years ?? {});
      for (const comic of comics) {
        if (!want.has(comic.id)) continue;
        out.push({ comic, year: years[comic.id] ?? 0 });
      }
    }),
  );
  return out;
}

export async function loadComicBundle(id: string): Promise<{
  comic: CatalogComic;
  year: number;
  run: ComicRunFile | null;
} | null> {
  const file = await loadCatalogJson<ComicBucketFile>(comicBucketPath(id));
  if (!file || Array.isArray(file) || !file.comics) return null;
  const comic = file.comics.find((c) => c.id === id);
  if (!comic) return null;
  const year = file.years?.[id] ?? 0;
  const runPath = file.run?.[id];
  const run = runPath ? await loadComicRun(runPath) : null;
  return { comic: run?.comics.find((c) => c.id === id) ?? comic, year: run?.years?.[id] ?? year, run };
}

/** Materialize every search shard. Used by LOCG import, which has to score the whole catalog. */
export async function loadComicSearchCatalog(): Promise<{ comics: CatalogComic[]; years: Map<string, number> }> {
  const shards = await searchShards();
  const comics: CatalogComic[] = [];
  const years = new Map<string, number>();
  for (const shard of shards) {
    if (!shard?.rows) continue;
    for (const row of shard.rows) {
      const comic = expandRow(shard, row);
      comics.push(comic);
      years.set(comic.id, row[17] ?? 0);
    }
  }
  return { comics, years };
}

export function searchLoadedComics(list: CatalogComic[], query: string): CatalogComic[] {
  return searchComicList(list, query);
}

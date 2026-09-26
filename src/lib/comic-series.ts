/**
 * Comics ladder grouping: Publisher → Series (run year) → Issues.
 *
 * ## Series-year rule
 *
 * Series key = normalized publisher + normalized series base title + run year.
 *
 * Run year for each comic (priority order):
 * 1. Start year embedded in the series title via `parseSeriesMeta`
 *    (e.g. "Batman (2016)", "Action Comics (Vol. 3) (2016 - Present)").
 * 2. Otherwise assigned by run clustering within the same publisher + base title:
 *    - Non-facsimile issue `#1` cover/street years are run anchors
 *      (so Amazing Spider-Man 2022 stays separate from the classic run).
 *    - Each other issue joins the latest anchor year ≤ its own street/cover year.
 *    - Issues dated before every `#1` anchor form a legacy run keyed by the
 *      earliest street/cover year among those older issues.
 * 3. Date year itself prefers `streetDate`, then `coverDate` (ISO `YYYY…` prefix).
 * 4. If no date and no title year can be resolved → run year `0` (shown as "Year unknown").
 *
 * Issue lists under a series sort by issue number by default; browse tabs can
 * switch the visible list to release date, A–Z, or recently acquired.
 */

import { isCollectedComic } from "@/lib/comic-format";
import { normalizeIssue, normalizePublisher, normalizeSeries, parseSeriesMeta } from "@/lib/locg-import";
import type { CatalogComic, ComicFormat } from "@/lib/types";

export type ComicSeriesLike = {
  id?: string;
  series: string;
  issue?: string;
  publisher: string;
  coverDate?: string;
  streetDate?: string;
  format?: ComicFormat | string;
};

export type SeriesRef = {
  /** Stable key: publisherNorm|seriesBaseNorm|year */
  key: string;
  publisher: string;
  /** Display base title (articles preserved from a representative row). */
  title: string;
  /** Normalized base title (no articles). */
  titleNorm: string;
  /** Run start year; 0 = unknown. */
  year: number;
  issueCount: number;
  /** Newest street/cover date among issues in this run (ISO-ish); empty if none. */
  latestDate: string;
  /** Representative cover comic (earliest issue, prefer primary-ish). */
  sample?: CatalogComic;
};

export type PublisherRef = {
  publisher: string;
  seriesCount: number;
  issueCount: number;
  /** Newest street/cover date among series under this publisher. */
  latestDate: string;
};

export type ComicSortMode = "release" | "name" | "acquired" | "issue";
export type LadderSortMode = "release" | "name" | "acquired";

export type CatalogComicSortable = {
  id: string;
  series: string;
  issue: string;
  streetDate?: string;
  coverDate?: string;
};

/** Street date, then cover date — empty string when neither is set. */
export function comicReleaseDate(c: Pick<ComicSeriesLike, "coverDate" | "streetDate">): string {
  const raw = c.streetDate || c.coverDate || "";
  return String(raw).trim();
}

/** Newest first. Missing dates sink. Equal dates compare as 0 (stable). */
export function compareIsoDateDesc(a: string, b: string): number {
  if (!a && !b) return 0;
  if (!a) return 1;
  if (!b) return -1;
  if (a === b) return 0;
  return a < b ? 1 : -1;
}

/** YYYY from ISO-ish date; prefers streetDate then coverDate. */
export function comicDateYear(c: Pick<ComicSeriesLike, "coverDate" | "streetDate">): number | undefined {
  for (const raw of [c.streetDate, c.coverDate]) {
    if (!raw) continue;
    const m = String(raw).trim().match(/^((?:19|20)\d{2})/);
    if (m) return Number(m[1]);
  }
  return undefined;
}

/** Title-embedded series start year, if any. */
export function comicTitleYear(series: string): number | undefined {
  return parseSeriesMeta(series).year;
}

export function seriesBaseTitle(series: string): string {
  return parseSeriesMeta(series).base || series.trim();
}

export function seriesBaseNorm(series: string): string {
  return parseSeriesMeta(series).baseNorm || normalizeSeries(series);
}

export function makeSeriesKey(publisher: string, seriesTitle: string, year: number): string {
  return `${normalizePublisher(publisher)}|${seriesBaseNorm(seriesTitle)}|${year || 0}`;
}

export function parseSeriesKey(key: string): { publisherNorm: string; titleNorm: string; year: number } | null {
  const parts = key.split("|");
  if (parts.length < 3) return null;
  const year = Number(parts[parts.length - 1]);
  const titleNorm = parts[parts.length - 2] ?? "";
  const publisherNorm = parts.slice(0, -2).join("|");
  if (!publisherNorm || !titleNorm || !Number.isFinite(year)) return null;
  return { publisherNorm, titleNorm, year };
}

export function seriesDisplayLabel(title: string, year: number): string {
  const base = seriesBaseTitle(title);
  if (!year) return `${base} (Year unknown)`;
  return `${base} (${year})`;
}

function isFacsimile(c: ComicSeriesLike): boolean {
  return String(c.format ?? "").toLowerCase() === "facsimile";
}

function isNumberOne(c: ComicSeriesLike): boolean {
  return normalizeIssue(String(c.issue ?? "")) === "1";
}

/**
 * Assign a run year to every comic in `comics` (full catalog or a publisher slice).
 * Same publisher + base title share clustering; different publishers never merge.
 */
export function assignSeriesRunYears(comics: ComicSeriesLike[]): Map<string, number> {
  const out = new Map<string, number>();
  const groups = new Map<string, ComicSeriesLike[]>();

  for (const c of comics) {
    const gkey = `${normalizePublisher(c.publisher)}|${seriesBaseNorm(c.series)}`;
    const bucket = groups.get(gkey);
    if (bucket) bucket.push(c);
    else groups.set(gkey, [c]);
  }

  for (const group of groups.values()) {
    const titleYears = new Set<number>();
    const anchors = new Set<number>();

    for (const c of group) {
      const ty = comicTitleYear(c.series);
      if (ty) titleYears.add(ty);
      if (isNumberOne(c) && !isFacsimile(c)) {
        const y = ty ?? comicDateYear(c);
        if (y) anchors.add(y);
      }
    }

    const anchorList = [...new Set([...anchors, ...titleYears])].sort((a, b) => a - b);

    const legacyYears: number[] = [];
    const provisional = new Map<ComicSeriesLike, number>();

    for (const c of group) {
      const ty = comicTitleYear(c.series);
      if (ty) {
        provisional.set(c, ty);
        continue;
      }
      const cy = comicDateYear(c);
      if (!cy) {
        provisional.set(c, 0);
        continue;
      }
      if (anchorList.length === 0) {
        provisional.set(c, cy);
        continue;
      }
      let chosen: number | undefined;
      for (const a of anchorList) {
        if (a <= cy) chosen = a;
      }
      if (chosen != null) {
        provisional.set(c, chosen);
      } else {
        legacyYears.push(cy);
        provisional.set(c, -1); // placeholder → legacy
      }
    }

    const legacyRun =
      legacyYears.length > 0 ? Math.min(...legacyYears) : anchorList.length ? Math.min(...anchorList) : 0;

    // If no anchors at all, collapse the whole group to the earliest dated year.
    let groupFallback = legacyRun;
    if (anchorList.length === 0) {
      const dated = group.map(comicDateYear).filter((y): y is number => y != null);
      groupFallback = dated.length ? Math.min(...dated) : 0;
      for (const c of group) {
        const id = c.id ?? `${c.publisher}|${c.series}|${c.issue}`;
        const ty = comicTitleYear(c.series);
        out.set(id, ty ?? groupFallback);
      }
      continue;
    }

    for (const c of group) {
      const id = c.id ?? `${c.publisher}|${c.series}|${c.issue}`;
      const p = provisional.get(c);
      out.set(id, p === -1 ? legacyRun : (p ?? groupFallback));
    }
  }

  return out;
}

export function seriesRunYearFor(
  comic: ComicSeriesLike,
  yearById: Map<string, number>,
): number {
  if (comic.id && yearById.has(comic.id)) return yearById.get(comic.id)!;
  const ty = comicTitleYear(comic.series);
  if (ty) return ty;
  return comicDateYear(comic) ?? 0;
}

export function comicMatchesSeries(
  comic: ComicSeriesLike,
  opts: { publisher: string; seriesTitle: string; year: number },
  yearById: Map<string, number>,
): boolean {
  if (normalizePublisher(comic.publisher) !== normalizePublisher(opts.publisher)) return false;
  if (seriesBaseNorm(comic.series) !== seriesBaseNorm(opts.seriesTitle)) return false;
  return seriesRunYearFor(comic, yearById) === opts.year;
}

function issueSortValue(issue: string): [number, string] {
  const n = normalizeIssue(issue);
  if (n === "nn") return [Number.POSITIVE_INFINITY, n];
  const m = n.match(/^(\d+(?:\.\d+)?)/);
  if (m) return [Number(m[1]), n];
  return [Number.POSITIVE_INFINITY - 1, n];
}

export function sortIssuesByNumber<T extends { issue: string }>(list: T[]): T[] {
  return [...list].sort((a, b) => {
    const [na, sa] = issueSortValue(a.issue);
    const [nb, sb] = issueSortValue(b.issue);
    if (na !== nb) return na - nb;
    return sa.localeCompare(sb, undefined, { numeric: true });
  });
}

function compareSeriesName(a: SeriesRef, b: SeriesRef): number {
  const byTitle = a.title.localeCompare(b.title, undefined, { sensitivity: "base" });
  if (byTitle !== 0) return byTitle;
  return b.year - a.year;
}

/** Reorder publisher series cards for the browse sort tabs. */
export function sortSeriesList<T extends SeriesRef>(
  list: T[],
  mode: LadderSortMode,
  acquiredAtByKey?: Map<string, string>,
): T[] {
  const out = [...list];
  out.sort((a, b) => {
    if (mode === "name") return compareSeriesName(a, b);
    if (mode === "acquired") {
      const byAcq = compareIsoDateDesc(acquiredAtByKey?.get(a.key) ?? "", acquiredAtByKey?.get(b.key) ?? "");
      if (byAcq !== 0) return byAcq;
      return compareSeriesName(a, b);
    }
    const byDate = compareIsoDateDesc(a.latestDate, b.latestDate);
    if (byDate !== 0) return byDate;
    return compareSeriesName(a, b);
  });
  return out;
}

function comparePublisherName(a: PublisherRef, b: PublisherRef): number {
  return a.publisher.localeCompare(b.publisher, undefined, { sensitivity: "base" });
}

/** Reorder the publisher ladder for the browse sort tabs. */
export function sortPublisherList<T extends PublisherRef>(
  list: T[],
  mode: LadderSortMode,
  acquiredAtByPublisher?: Map<string, string>,
): T[] {
  const out = [...list];
  out.sort((a, b) => {
    if (mode === "name") return comparePublisherName(a, b);
    if (mode === "acquired") {
      const byAcq = compareIsoDateDesc(
        acquiredAtByPublisher?.get(normalizePublisher(a.publisher)) ?? "",
        acquiredAtByPublisher?.get(normalizePublisher(b.publisher)) ?? "",
      );
      if (byAcq !== 0) return byAcq;
      return comparePublisherName(a, b);
    }
    const byDate = compareIsoDateDesc(a.latestDate, b.latestDate);
    if (byDate !== 0) return byDate;
    return comparePublisherName(a, b);
  });
  return out;
}

/** Sort a comic card list (issues, collected, search, noteworthy). */
export function sortCatalogComics<T extends CatalogComicSortable>(
  list: T[],
  mode: ComicSortMode,
  opts?: {
    ownedByCatalog?: Map<string, { addedAt: string; acquiredDate?: string }>;
    label?: (c: T) => string;
  },
): T[] {
  if (mode === "issue") return sortIssuesByNumber(list);
  const ownedByCatalog = opts?.ownedByCatalog;
  const label = opts?.label ?? ((c: T) => `${c.series} ${c.issue}`);
  const out = [...list];
  out.sort((a, b) => {
    if (mode === "name") {
      const bySeries = a.series.localeCompare(b.series, undefined, { sensitivity: "base" });
      if (bySeries !== 0) return bySeries;
      return a.issue.localeCompare(b.issue, undefined, { numeric: true });
    }
    if (mode === "acquired") {
      const oa = ownedByCatalog?.get(a.id);
      const ob = ownedByCatalog?.get(b.id);
      if (!oa && !ob) {
        const byDate = compareIsoDateDesc(comicReleaseDate(a), comicReleaseDate(b));
        if (byDate !== 0) return byDate;
        return label(a).localeCompare(label(b));
      }
      if (!oa) return 1;
      if (!ob) return -1;
      const byAdded = compareIsoDateDesc(oa.addedAt, ob.addedAt);
      if (byAdded !== 0) return byAdded;
      const byAcq = compareIsoDateDesc(oa.acquiredDate || "", ob.acquiredDate || "");
      if (byAcq !== 0) return byAcq;
      return label(a).localeCompare(label(b));
    }
    const byDate = compareIsoDateDesc(comicReleaseDate(a), comicReleaseDate(b));
    if (byDate !== 0) return byDate;
    const bySeries = a.series.localeCompare(b.series, undefined, { sensitivity: "base" });
    if (bySeries !== 0) return bySeries;
    return a.issue.localeCompare(b.issue, undefined, { numeric: true });
  });
  return out;
}

/** Build series cards for a publisher (or all publishers if omitted). */
export function buildSeriesList(
  comics: CatalogComic[],
  yearById: Map<string, number>,
  publisher?: string,
): SeriesRef[] {
  const filtered = publisher
    ? comics.filter((c) => normalizePublisher(c.publisher) === normalizePublisher(publisher))
    : comics;

  const map = new Map<string, SeriesRef & { _sampleIssue: string }>();

  for (const c of filtered) {
    const year = seriesRunYearFor(c, yearById);
    const title = seriesBaseTitle(c.series);
    const titleNorm = seriesBaseNorm(c.series);
    const key = makeSeriesKey(c.publisher, c.series, year);
    const prev = map.get(key);
    const latestDate = comicReleaseDate(c);
    if (!prev) {
      map.set(key, {
        key,
        publisher: c.publisher,
        title,
        titleNorm,
        year,
        issueCount: 1,
        latestDate,
        sample: c,
        _sampleIssue: c.issue,
      });
      continue;
    }
    prev.issueCount += 1;
    if (latestDate && (!prev.latestDate || latestDate > prev.latestDate)) prev.latestDate = latestDate;
    // Prefer lower issue number as sample cover; tie-break earlier date.
    const [na] = issueSortValue(c.issue);
    const [nb] = issueSortValue(prev._sampleIssue);
    if (na < nb) {
      prev.sample = c;
      prev._sampleIssue = c.issue;
    }
  }

  return [...map.values()]
    .map(({ _sampleIssue: _, ...rest }) => rest)
    .sort((a, b) => {
      const byTitle = a.title.localeCompare(b.title, undefined, { sensitivity: "base" });
      if (byTitle !== 0) return byTitle;
      return b.year - a.year; // newest run first when same title
    });
}

/** Publisher rollup for the top ladder rung. */
export function buildPublisherList(
  comics: CatalogComic[],
  yearById: Map<string, number>,
): PublisherRef[] {
  const series = buildSeriesList(comics, yearById);
  const map = new Map<string, PublisherRef>();
  for (const s of series) {
    const prev = map.get(s.publisher);
    if (!prev) {
      map.set(s.publisher, {
        publisher: s.publisher,
        seriesCount: 1,
        issueCount: s.issueCount,
        latestDate: s.latestDate,
      });
    } else {
      prev.seriesCount += 1;
      prev.issueCount += s.issueCount;
      if (s.latestDate && (!prev.latestDate || s.latestDate > prev.latestDate)) prev.latestDate = s.latestDate;
    }
  }
  return [...map.values()].sort(comparePublisherName);
}

export function collectedForPublisher<T extends { format?: unknown; publisher: string }>(
  comics: T[],
  publisher: string,
): T[] {
  const want = normalizePublisher(publisher);
  return comics.filter((c) => isCollectedComic(c) && normalizePublisher(c.publisher) === want);
}

export function collectedCountByPublisher(
  comics: { format?: unknown; publisher: string }[],
): Map<string, number> {
  const map = new Map<string, number>();
  for (const c of comics) {
    if (!isCollectedComic(c)) continue;
    const key = normalizePublisher(c.publisher);
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return map;
}

/**
 * Collected Editions group by series title inside one publisher.
 *
 * This is separate from the singles run-year ladder. Trades and manga volumes
 * of one series stay together even when their cover years span decades, and
 * a collected `#1` never becomes a singles run anchor.
 *
 * Identity is the normalized series base title (`seriesBaseNorm` / GCD series
 * name already stored on the row). There is no per-issue GCD series id on
 * catalog rows. Blank series land in one "Series unknown" group — they are
 * not dropped. Distinct titles that only differ by a bracketed edition
 * ("One Piece" vs "One Piece [Omnibus Edition]") stay separate.
 */
export const COLLECTED_SERIES_UNKNOWN = "Series unknown";
const COLLECTED_SERIES_UNKNOWN_NORM = "__unknown__";

export function collectedSeriesIdentity(series: string | null | undefined): {
  title: string;
  titleNorm: string;
} {
  const trimmed = String(series ?? "").trim();
  if (!trimmed) return { title: COLLECTED_SERIES_UNKNOWN, titleNorm: COLLECTED_SERIES_UNKNOWN_NORM };
  const title = seriesBaseTitle(trimmed).trim();
  const titleNorm = seriesBaseNorm(trimmed);
  if (!title || !titleNorm) {
    return { title: COLLECTED_SERIES_UNKNOWN, titleNorm: COLLECTED_SERIES_UNKNOWN_NORM };
  }
  return { title, titleNorm };
}

/** Stable key: normalized publisher + normalized series base. No run year. */
export function makeCollectedSeriesKey(publisher: string, series: string | null | undefined): string {
  return `${normalizePublisher(publisher)}|${collectedSeriesIdentity(series).titleNorm}`;
}

export function collectedComicMatchesSeries(
  comic: { publisher: string; series: string | null | undefined },
  opts: { publisher: string; seriesTitle: string },
): boolean {
  if (normalizePublisher(comic.publisher) !== normalizePublisher(opts.publisher)) return false;
  return collectedSeriesIdentity(comic.series).titleNorm === collectedSeriesIdentity(opts.seriesTitle).titleNorm;
}

/**
 * Volume index from the issue field. Accepts `12`, `#12`, `[12]`.
 * `nn` / `[nn]` / blank / non-numeric → undefined (sort falls back to title, then date).
 */
export function parseVolumeNumber(issue: string | number | null | undefined): number | undefined {
  let s = String(issue ?? "").trim().toLowerCase();
  if (!s) return undefined;
  s = s.replace(/^#+/, "");
  if (s.startsWith("[") && s.endsWith("]") && s.length >= 2) s = s.slice(1, -1).trim();
  if (!s || s === "nn") return undefined;
  const m = s.match(/^(\d+(?:\.\d+)?)/);
  if (!m) return undefined;
  const n = Number(m[1]);
  return Number.isFinite(n) ? n : undefined;
}

function volumeFallbackTitle(c: { series?: string; issue?: string | number; description?: string }): string {
  const desc = String(c.description ?? "").trim();
  if (desc) return desc;
  return `${c.series ?? ""} ${c.issue ?? ""}`.trim();
}

/** Oldest first. Missing dates sink so undated books don't jump ahead of real dates. */
function compareIsoDateAsc(a: string, b: string): number {
  if (!a && !b) return 0;
  if (!a) return 1;
  if (!b) return -1;
  if (a === b) return 0;
  return a < b ? -1 : 1;
}

/**
 * Volume-number order. Numbered books come first (1, 2, 10).
 * Books with no volume number sort by title (description, else series) then date.
 */
export function sortCollectedVolumes<
  T extends {
    id: string;
    series: string;
    issue: string | number;
    description?: string;
    coverDate?: string;
    streetDate?: string;
  },
>(list: T[]): T[] {
  return [...list].sort((a, b) => {
    const na = parseVolumeNumber(a.issue);
    const nb = parseVolumeNumber(b.issue);
    if (na != null && nb != null && na !== nb) return na - nb;
    if (na != null && nb == null) return -1;
    if (na == null && nb != null) return 1;
    if (na == null && nb == null) {
      const byTitle = volumeFallbackTitle(a).localeCompare(volumeFallbackTitle(b), undefined, {
        sensitivity: "base",
        numeric: true,
      });
      if (byTitle !== 0) return byTitle;
    }
    const byDate = compareIsoDateAsc(comicReleaseDate(a), comicReleaseDate(b));
    if (byDate !== 0) return byDate;
    return a.id.localeCompare(b.id);
  });
}

/**
 * Series cards for a publisher's collected editions.
 * `issueCount` is the volume count. `year` is the earliest street/cover year (0 = unknown).
 * Sample cover is the lowest volume number, then the earliest date.
 * Singles in `comics` are ignored so this cannot change the singles ladder.
 */
export function buildCollectedSeriesList(comics: CatalogComic[], publisher?: string): SeriesRef[] {
  const want = publisher ? normalizePublisher(publisher) : null;
  const map = new Map<string, SeriesRef & { _vol: number; _sampleDate: string }>();

  for (const c of comics) {
    if (!isCollectedComic(c)) continue;
    if (want && normalizePublisher(c.publisher) !== want) continue;
    const { title, titleNorm } = collectedSeriesIdentity(c.series);
    const key = `${normalizePublisher(c.publisher)}|${titleNorm}`;
    const latestDate = comicReleaseDate(c);
    const vol = parseVolumeNumber(c.issue);
    const volN = vol ?? Number.POSITIVE_INFINITY;
    const year = comicDateYear(c) ?? 0;
    const prev = map.get(key);
    if (!prev) {
      map.set(key, {
        key,
        publisher: c.publisher,
        title,
        titleNorm,
        year,
        issueCount: 1,
        latestDate,
        sample: c,
        _vol: volN,
        _sampleDate: latestDate,
      });
      continue;
    }
    prev.issueCount += 1;
    if (latestDate && (!prev.latestDate || latestDate > prev.latestDate)) prev.latestDate = latestDate;
    if (year && (!prev.year || year < prev.year)) prev.year = year;
    const earlier =
      volN < prev._vol ||
      (volN === prev._vol && latestDate && (!prev._sampleDate || latestDate < prev._sampleDate));
    if (earlier) {
      prev.sample = c;
      prev._vol = volN;
      prev._sampleDate = latestDate;
    }
  }

  return [...map.values()]
    .map(({ _vol: _v, _sampleDate: _d, ...rest }) => rest)
    .sort((a, b) => {
      const byTitle = a.title.localeCompare(b.title, undefined, { sensitivity: "base" });
      if (byTitle !== 0) return byTitle;
      return b.year - a.year;
    });
}

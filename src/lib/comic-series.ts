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
 * Issue lists under a series sort by issue number (numeric where possible).
 */

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
  /** Representative cover comic (earliest issue, prefer primary-ish). */
  sample?: CatalogComic;
};

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
    if (!prev) {
      map.set(key, {
        key,
        publisher: c.publisher,
        title,
        titleNorm,
        year,
        issueCount: 1,
        sample: c,
        _sampleIssue: c.issue,
      });
      continue;
    }
    prev.issueCount += 1;
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
): { publisher: string; seriesCount: number; issueCount: number }[] {
  const series = buildSeriesList(comics, yearById);
  const map = new Map<string, { publisher: string; seriesCount: number; issueCount: number }>();
  for (const s of series) {
    const prev = map.get(s.publisher);
    if (!prev) {
      map.set(s.publisher, { publisher: s.publisher, seriesCount: 1, issueCount: s.issueCount });
    } else {
      prev.seriesCount += 1;
      prev.issueCount += s.issueCount;
    }
  }
  return [...map.values()].sort((a, b) => a.publisher.localeCompare(b.publisher));
}

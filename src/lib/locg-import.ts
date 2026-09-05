import { mergeComics } from "@/data/comics";
import type { CatalogComic, ComicFormat, ComicGrade, CustomComic, OwnedComic } from "@/lib/types";
import { slug } from "@/lib/utils";

/** One normalized row from a League of Comic Geeks export. */
export type LocgRow = {
  series: string;
  issue: string;
  publisher: string;
  variant?: string;
  title?: string;
  coverDate?: string;
  upc?: string;
  inCollection: boolean;
  inWishlist: boolean;
  markedRead?: boolean;
  mediaFormat?: string;
  grade?: string;
  pricePaid?: number;
  dateAdded?: string;
  notes?: string;
  /** Start year parsed from LOCG series string, e.g. (2016 - Present). */
  seriesYear?: number;
  /** End year when present (Present → undefined). */
  seriesYearEnd?: number;
  /** Volume number from (Vol. N), when present. */
  seriesVol?: number;
  /** Base series title with Vol/year suffixes stripped. */
  seriesBase?: string;
  raw: Record<string, string>;
};

export type LocgMatch =
  | { kind: "catalog"; comic: CatalogComic; row: LocgRow }
  | { kind: "custom"; custom: CustomComic; row: LocgRow }
  | { kind: "skip"; row: LocgRow; reason: string };

export type LocgParseResult = {
  headers: string[];
  rows: LocgRow[];
  warnings: string[];
};

const HEADER_ALIASES: Record<string, keyof LocgRow | "flagCollection" | "flagWishlist" | "flagRead"> = {
  series: "series",
  "series name": "series",
  "series title": "series",
  issue: "issue",
  "issue number": "issue",
  "issue #": "issue",
  "issue no": "issue",
  "issue no.": "issue",
  publisher: "publisher",
  "publisher name": "publisher",
  "publisher title": "publisher",
  variant: "variant",
  "cover variant": "variant",
  title: "title",
  "issue title": "title",
  "full title": "title",
  "issue's full title": "title",
  "issues full title": "title",
  date: "coverDate",
  "cover date": "coverDate",
  "release date": "coverDate",
  "street date": "coverDate",
  upc: "upc",
  isbn: "upc",
  isbn13: "upc",
  "upc/isbn": "upc",
  "upc / isbn": "upc",
  "in collection": "flagCollection",
  collection: "flagCollection",
  owned: "flagCollection",
  "in wish list": "flagWishlist",
  "in wishlist": "flagWishlist",
  wishlist: "flagWishlist",
  "wish list": "flagWishlist",
  "marked read": "flagRead",
  read: "flagRead",
  "media format": "mediaFormat",
  format: "mediaFormat",
  grade: "grade",
  grading: "grade",
  condition: "grade",
  "price paid": "pricePaid",
  price: "pricePaid",
  cost: "pricePaid",
  "date added": "dateAdded",
  "added date": "dateAdded",
  "my added date": "dateAdded",
  "date purchased": "dateAdded",
  "purchase date": "dateAdded",
  "purchased date": "dateAdded",
  notes: "notes",
  note: "notes",
  comments: "notes",
};

/** Canonical publisher keys for alias matching. */
const PUBLISHER_ALIASES: Record<string, string> = {
  dc: "dc comics",
  "dc comics": "dc comics",
  "dc entertainment": "dc comics",
  marvel: "marvel comics",
  "marvel comics": "marvel comics",
  "marvel entertainment": "marvel comics",
  image: "image comics",
  "image comics": "image comics",
  idw: "idw publishing",
  "idw publishing": "idw publishing",
  "dark horse": "dark horse comics",
  "dark horse comics": "dark horse comics",
  boom: "boom! studios",
  "boom studios": "boom! studios",
  "boom! studios": "boom! studios",
  dynamite: "dynamite",
  "dynamite entertainment": "dynamite",
  valiant: "valiant",
  "valiant entertainment": "valiant",
};

function normHeader(h: string): string {
  return h.trim().toLowerCase().replace(/\s+/g, " ");
}

function truthy(v: string | undefined): boolean {
  if (!v) return false;
  const s = v.trim().toLowerCase();
  return (
    s === "1" ||
    s === "y" ||
    s === "yes" ||
    s === "true" ||
    s === "x" ||
    s === "owned" ||
    s === "collection"
  );
}

function parsePrice(v: string | undefined): number | undefined {
  if (!v?.trim()) return undefined;
  const n = Number(v.replace(/[^0-9.]/g, ""));
  return Number.isFinite(n) ? n : undefined;
}

/** Minimal RFC4180-ish CSV parse (handles quotes and commas). */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let i = 0;
  let inQuotes = false;
  const s = text.replace(/^\uFEFF/, "");
  while (i < s.length) {
    const ch = s[i]!;
    if (inQuotes) {
      if (ch === '"') {
        if (s[i + 1] === '"') {
          cell += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i += 1;
        continue;
      }
      cell += ch;
      i += 1;
      continue;
    }
    if (ch === '"') {
      inQuotes = true;
      i += 1;
      continue;
    }
    if (ch === ",") {
      row.push(cell);
      cell = "";
      i += 1;
      continue;
    }
    if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && s[i + 1] === "\n") i += 1;
      row.push(cell);
      cell = "";
      if (row.some((c) => c.trim())) rows.push(row);
      row = [];
      i += 1;
      continue;
    }
    cell += ch;
    i += 1;
  }
  row.push(cell);
  if (row.some((c) => c.trim())) rows.push(row);
  return rows;
}

/** Strip articles / punctuation for loose comparison. */
export function normalizeSeries(s: string): string {
  return s
    .toLowerCase()
    .replace(/\b(the|a|an)\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Parse LOCG-style series strings into base title + optional vol/year.
 * Examples:
 *   "Action Comics (Vol. 3) (2016 - Present)" → base Action Comics, vol 3, year 2016
 *   "Batman (Vol. 3) (2016 - 2026)" → base Batman, vol 3, year 2016
 *   "All-Star Superman (2005 - 2008)" → base All-Star Superman, year 2005
 *   "Batman (2016)" → base Batman, year 2016
 */
export function parseSeriesMeta(raw: string): {
  base: string;
  baseNorm: string;
  year?: number;
  yearEnd?: number;
  vol?: number;
} {
  let s = raw.trim();
  let vol: number | undefined;
  let year: number | undefined;
  let yearEnd: number | undefined;

  const volM = s.match(/\(\s*vol\.?\s*(\d+)\s*\)/i);
  if (volM) {
    vol = Number(volM[1]);
    s = s.replace(volM[0], " ").trim();
  }

  // (2016 - Present) / (2016 - 2026) / (2026)
  const rangeM = s.match(
    /\(\s*((?:19|20)\d{2})(?:\s*[-–—]\s*(present|(?:19|20)\d{2}))?\s*\)\s*$/i,
  );
  if (rangeM) {
    year = Number(rangeM[1]);
    if (rangeM[2] && !/^present$/i.test(rangeM[2])) yearEnd = Number(rangeM[2]);
    s = s.slice(0, rangeM.index).trim();
  }

  // Catalog-style leftover "Vol. N:" in title (rare for series name)
  s = s.replace(/\bvol\.?\s*\d+\b/gi, " ").replace(/\s+/g, " ").trim();
  // Trailing em-dashes / punctuation
  s = s.replace(/[-–—:\s]+$/g, "").trim();

  const base = s || raw.trim();
  return { base, baseNorm: normalizeSeries(base), year, yearEnd, vol };
}

export function normalizeIssue(issue: string): string {
  let s = issue.trim().toLowerCase();
  s = s.replace(/^#+/, "");
  s = s.replace(/^0+(\d)/, "$1"); // leading zeros
  if (/^nn$/i.test(s) || s === "") return "nn";
  // "annual 1" → keep; strip spaces for key
  return s.replace(/\s+/g, "");
}

export function normalizePublisher(p: string): string {
  const n = p
    .toLowerCase()
    .replace(/[!.,]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return PUBLISHER_ALIASES[n] ?? n;
}

export function publishersMatch(a: string, b: string): boolean {
  const na = normalizePublisher(a);
  const nb = normalizePublisher(b);
  if (!na || !nb) return true; // unknown → don't block
  if (na === "unknown" || nb === "unknown") return true;
  return na === nb || na.includes(nb) || nb.includes(na);
}

/** Pull issue # and trailing variant text from an LOCG Full Title. */
export function parseFullTitle(
  title: string,
  seriesHint?: string,
): { issue?: string; variant?: string; facsimile?: boolean; formatHint?: ComicFormat } {
  const t = title.trim();
  if (!t) return {};

  const facsimile = /facsimile/i.test(t);
  let formatHint: ComicFormat | undefined;
  if (/\bTPB?\b|\btrade\b|compact comics/i.test(t)) formatHint = "tpb";
  else if (/\bHC\b|hardcover/i.test(t)) formatHint = "hc";
  else if (/\bomnibus\b/i.test(t)) formatHint = "omnibus";
  else if (facsimile) formatHint = "facsimile";
  else if (/\bannual\b/i.test(t)) formatHint = "annual";

  // Prefer "#123" anywhere (LOCG almost always uses this for singles)
  const hash = t.match(/#\s*(\d+[A-Za-z]?)\b(.*)$/i);
  if (hash) {
    const issue = hash[1]!;
    let rest = (hash[2] ?? "").trim();
    // Drop leading series echo if present
    if (seriesHint) {
      const sn = normalizeSeries(seriesHint);
      const rn = normalizeSeries(rest);
      if (rn.startsWith(sn)) rest = rest.slice(seriesHint.length).trim();
    }
    // Common noise prefixes
    rest = rest
      .replace(/^(facsimile\s+edition(?:\s+\d{4})?)\s*/i, "")
      .replace(/^(2nd|3rd|4th|\d+th)\s+printing\b/i, (m) => m)
      .trim();
    const variant = rest
      ? rest
          .replace(/\s+Facsimile Edition(?:\s+\d{4})?/gi, "")
          .replace(/\s+/g, " ")
          .trim() || undefined
      : undefined;
    // Keep printing / cover / variant wording
    const variantOut =
      variant ||
      (/\d+(st|nd|rd|th)\s+printing/i.test(hash[2] ?? "")
        ? (hash[2] ?? "").trim()
        : undefined);
    return {
      issue,
      variant: variantOut || (facsimile && !variant ? "Facsimile Edition" : undefined),
      facsimile,
      formatHint,
    };
  }

  // "Batman Vol. 1: The Court of Owls TP" — collected edition, no issue #
  if (formatHint === "tpb" || formatHint === "hc" || formatHint === "omnibus") {
    return { issue: "nn", facsimile, formatHint };
  }

  // Trailing bare number (legacy sample CSV title style)
  const trail = t.match(/^(.*?)(?:\s+#|\s+)(\d+[A-Za-z]?|nn|annual\s*\d+)\s*$/i);
  if (trail) {
    return { issue: trail[2]!.replace(/^#/i, "").trim(), facsimile, formatHint };
  }

  return { facsimile, formatHint };
}

function catalogSeriesYear(series: string): number | undefined {
  const m = series.trim().match(/\(\s*((?:19|20)\d{2})\s*\)\s*$/);
  return m ? Number(m[1]) : undefined;
}

function comicKey(c: { series: string; issue: string; publisher: string; variant?: string }) {
  return `${c.series}|${c.issue}|${c.publisher}|${c.variant ?? ""}`.toLowerCase();
}

function inferFormat(row: LocgRow): ComicFormat {
  if (/tpb|trade|compact comics/i.test(row.mediaFormat ?? "") || /tpb?\b|trade/i.test(row.title ?? "")) {
    return "tpb";
  }
  if (/hardcover|\bhc\b/i.test(row.mediaFormat ?? "") || /\bHC\b/.test(row.title ?? "")) return "hc";
  if (/omnibus/i.test(row.title ?? row.series)) return "omnibus";
  if (/facsimile/i.test(row.title ?? row.series)) return "facsimile";
  if (/annual/i.test(row.issue) || /annual/i.test(row.title ?? "")) return "annual";
  return "single";
}

export function parseLocgSpreadsheet(text: string): LocgParseResult {
  const table = parseCsv(text);
  const warnings: string[] = [];
  if (table.length < 2) {
    return { headers: [], rows: [], warnings: ["File looks empty — need a header row and at least one comic."] };
  }
  const headers = table[0]!.map((h) => h.trim());
  const mapped = headers.map((h) => HEADER_ALIASES[normHeader(h)]);
  if (!mapped.includes("series") && !mapped.includes("title")) {
    warnings.push("Could not find a Series or Title column. Check that this is an LOCG export.");
  }

  const rows: LocgRow[] = [];
  for (let r = 1; r < table.length; r += 1) {
    const cells = table[r]!;
    const raw: Record<string, string> = {};
    headers.forEach((h, idx) => {
      raw[h] = (cells[idx] ?? "").trim();
    });

    let series = "";
    let issue = "";
    let publisher = "";
    let variant: string | undefined;
    let title: string | undefined;
    let coverDate: string | undefined;
    let upc: string | undefined;
    let mediaFormat: string | undefined;
    let grade: string | undefined;
    let notes: string | undefined;
    let dateAdded: string | undefined;
    let pricePaid: number | undefined;
    let flagCollection: boolean | undefined;
    let flagWishlist: boolean | undefined;
    let flagRead: boolean | undefined;

    headers.forEach((h, idx) => {
      const key = HEADER_ALIASES[normHeader(h)];
      const val = (cells[idx] ?? "").trim();
      if (!key || !val) return;
      switch (key) {
        case "series":
          series = val;
          break;
        case "issue":
          issue = val.replace(/^#/, "");
          break;
        case "publisher":
          publisher = val;
          break;
        case "variant":
          variant = val;
          break;
        case "title":
          title = val;
          break;
        case "coverDate":
          coverDate = val.slice(0, 10);
          break;
        case "upc":
          upc = val;
          break;
        case "mediaFormat":
          mediaFormat = val;
          break;
        case "grade":
          grade = val;
          break;
        case "notes":
          notes = val;
          break;
        case "dateAdded":
          dateAdded = val.slice(0, 10);
          break;
        case "pricePaid":
          pricePaid = parsePrice(val);
          break;
        case "flagCollection":
          flagCollection = truthy(val);
          break;
        case "flagWishlist":
          flagWishlist = truthy(val);
          break;
        case "flagRead":
          flagRead = truthy(val);
          break;
        default:
          break;
      }
    });

    const meta = series ? parseSeriesMeta(series) : { base: "", baseNorm: "" };
    const fromTitle = title ? parseFullTitle(title, meta.base || series) : {};

    // Always enrich issue/variant from Full Title when column missing or nn
    if ((!issue || issue.toLowerCase() === "nn") && fromTitle.issue) {
      issue = fromTitle.issue;
    }
    if (!variant && fromTitle.variant) {
      variant = fromTitle.variant;
    }

    // Legacy: title-only rows with "Series #123" at end
    if ((!series || !issue) && title && !fromTitle.issue) {
      const m = title.match(/^(.*?)(?:\s+#|\s+)(\d+[A-Za-z]?|nn|annual\s*\d+)\s*$/i);
      if (m) {
        series = series || m[1]!.trim();
        issue = issue || m[2]!.replace(/^#/i, "").trim();
      } else if (!series) {
        series = title;
      }
    }

    if (!series && title) series = title;
    if (!series) continue;
    if (!issue) issue = fromTitle.issue || "nn";
    if (!publisher) publisher = "Unknown";

    // Re-parse meta if series came from title
    const finalMeta = parseSeriesMeta(series);

    const hasFlags =
      mapped.includes("flagCollection") || mapped.includes("flagWishlist") || mapped.includes("flagRead");
    const inCollection = hasFlags ? Boolean(flagCollection) : true;
    const inWishlist = Boolean(flagWishlist);

    rows.push({
      series,
      issue,
      publisher,
      variant,
      title,
      coverDate,
      upc,
      inCollection,
      inWishlist,
      markedRead: flagRead,
      mediaFormat,
      grade,
      pricePaid,
      dateAdded,
      notes,
      seriesYear: finalMeta.year,
      seriesYearEnd: finalMeta.yearEnd,
      seriesVol: finalMeta.vol,
      seriesBase: finalMeta.base,
      raw,
    });
  }

  return { headers, rows, warnings };
}

type Scored = { comic: CatalogComic; score: number };

function scoreCandidate(row: LocgRow, comic: CatalogComic): number {
  const rowBase = row.seriesBase ? normalizeSeries(row.seriesBase) : parseSeriesMeta(row.series).baseNorm;
  const catMeta = parseSeriesMeta(comic.series);
  const catYear = catalogSeriesYear(comic.series) ?? catMeta.year;

  let score = 0;

  // Series base equality only (articles already stripped) — avoids "Batman" ⊂ "Batman / Superman: …"
  if (catMeta.baseNorm === rowBase) score += 40;
  else return -1;

  const rowIss = normalizeIssue(row.issue);
  const catIss = normalizeIssue(comic.issue);
  if (rowIss === catIss) score += 35;
  else return -1;

  if (publishersMatch(row.publisher, comic.publisher)) score += 15;
  else score -= 20;

  // Format / facsimile — Facsimile Edition is a distinct product from the original key
  const wantFacsimile = /facsimile/i.test(row.title ?? "") || /facsimile/i.test(row.variant ?? "");
  if (wantFacsimile && comic.format === "facsimile") score += 18;
  else if (wantFacsimile && comic.format !== "facsimile") return -1;
  else if (!wantFacsimile && comic.format === "facsimile") score -= 10;

  // Year / volume heuristics — never prefer a differently year-tagged run
  const coverYear = (() => {
    const d = comic.streetDate ?? comic.coverDate;
    if (!d) return undefined;
    const y = Number(String(d).slice(0, 4));
    return Number.isFinite(y) && y > 1900 ? y : undefined;
  })();

  if (row.seriesYear && catYear) {
    if (row.seriesYear === catYear) score += 25;
    else if (Math.abs(row.seriesYear - catYear) <= 1) score += 5;
    else return -1; // e.g. LOCG 2025 must not land on catalog (2022)
  } else if (row.seriesYear && !catYear) {
    // Bare catalog series — only if cover date sits in the LOCG run window
    // Facsimile reprints are modern and may sit outside the original run years.
    if (wantFacsimile && comic.format === "facsimile") {
      score += 8;
    } else {
      const end = row.seriesYearEnd ?? Math.max(row.seriesYear + 25, new Date().getFullYear() + 1);
      if (coverYear != null) {
        if (coverYear < row.seriesYear - 1 || coverYear > end + 1) return -1;
        score += 10;
      } else {
        score += 3;
      }
    }
  } else if (!row.seriesYear && !catYear) {
    score += 10; // both bare
  } else if (!row.seriesYear && catYear) {
    score += 2; // prefer bare row → bare catalog slightly over year-tagged
  }

  const wantTpb = inferFormat(row) === "tpb";
  if (wantTpb && comic.format === "tpb") score += 12;
  else if (wantTpb && comic.format === "single") score -= 8;

  // Variant
  const rowVar = normalizeSeries(row.variant ?? "");
  const catVar = normalizeSeries(comic.variant ?? "");
  if (rowVar && catVar) {
    if (rowVar === catVar || rowVar.includes(catVar) || catVar.includes(rowVar)) score += 12;
    else if (/cover\s*[a-z]/i.test(row.variant ?? "") && /cover\s*[a-z]/i.test(comic.variant ?? "")) {
      // different cover letters
      score -= 5;
    }
  } else if (!rowVar && !catVar) {
    score += 8; // both main covers
  } else if (!rowVar && catVar) {
    score -= 4; // prefer non-variant catalog when LOCG is main
  } else if (rowVar && !catVar) {
    // LOCG variant, catalog main — still a usable catalog link
    score += 3;
  }

  // Exact raw series string bonus
  if (comic.series.toLowerCase() === row.series.toLowerCase()) score += 5;
  if (normalizeSeries(comic.series) === normalizeSeries(row.series)) score += 5;

  return score;
}

function pickBestMatch(row: LocgRow, catalog: CatalogComic[]): CatalogComic | undefined {
  const rowBase = row.seriesBase ? normalizeSeries(row.seriesBase) : parseSeriesMeta(row.series).baseNorm;
  const rowIss = normalizeIssue(row.issue);
  if (!rowBase || !rowIss) return undefined;

  // Exact key first (raw strings)
  const exact = catalog.find((c) => comicKey(c) === comicKey(row));
  if (exact) return exact;

  // Exact with normalized publisher alias + issue + raw series
  const exactLoose = catalog.find(
    (c) =>
      c.series.toLowerCase() === row.series.toLowerCase() &&
      normalizeIssue(c.issue) === rowIss &&
      publishersMatch(c.publisher, row.publisher) &&
      normalizeSeries(c.variant ?? "") === normalizeSeries(row.variant ?? ""),
  );
  if (exactLoose) return exactLoose;

  const scored: Scored[] = [];
  for (const c of catalog) {
    const catMeta = parseSeriesMeta(c.series);
    if (catMeta.baseNorm !== rowBase) continue;
    if (normalizeIssue(c.issue) !== rowIss) continue;
    if (!publishersMatch(c.publisher, row.publisher)) continue;
    const catYear = catalogSeriesYear(c.series) ?? catMeta.year;
    // Hard reject: LOCG year-tagged run vs differently year-tagged catalog entry
    if (row.seriesYear && catYear && Math.abs(row.seriesYear - catYear) > 1) continue;
    const score = scoreCandidate(row, c);
    if (score >= 60) scored.push({ comic: c, score });
  }

  if (!scored.length) return undefined;
  scored.sort((a, b) => b.score - a.score);
  const best = scored[0]!;
  const second = scored[1];
  // If tie between year-tagged and bare, prefer year match when row has year
  if (second && second.score === best.score) {
    if (row.seriesYear) {
      const yearHit = scored.find((s) => catalogSeriesYear(s.comic.series) === row.seriesYear);
      if (yearHit) return yearHit.comic;
    }
    const noVar = scored.find((s) => !s.comic.variant && s.score === best.score);
    if (noVar) return noVar.comic;
  }
  // Ambiguous near-ties with different years and no row year → skip to avoid wrong match
  if (
    second &&
    best.score - second.score < 8 &&
    catalogSeriesYear(best.comic.series) !== catalogSeriesYear(second.comic.series) &&
    !row.seriesYear
  ) {
    // Prefer bare series if present
    const bare = scored.find((s) => !catalogSeriesYear(s.comic.series));
    if (bare && bare.score >= best.score - 5) return bare.comic;
  }
  return best.comic;
}

/**
 * Match LOCG rows to catalog comics.
 * Pass live weekly extras and permanent-archive promotions so matching uses the full library.
 */
export function matchLocgRows(
  rows: LocgRow[],
  extras: CatalogComic[] = [],
  promoted: CatalogComic[] = [],
): { matches: LocgMatch[]; owned: number; wanted: number; unmatched: number; matched: number } {
  const catalog = mergeComics(extras, promoted);

  const matches: LocgMatch[] = [];
  let owned = 0;
  let wanted = 0;
  let unmatched = 0;
  let matched = 0;

  for (const row of rows) {
    if (!row.inCollection && !row.inWishlist) {
      matches.push({ kind: "skip", row, reason: "Not marked collection or wishlist" });
      continue;
    }

    const comic = pickBestMatch(row, catalog);

    if (comic) {
      matches.push({ kind: "catalog", comic, row });
      matched += 1;
      if (row.inCollection) owned += 1;
      else wanted += 1;
    } else {
      const custom: CustomComic = {
        id: `locg-${slug(row.seriesBase || row.series)}-${slug(row.issue)}-${slug(row.publisher)}-${slug(row.variant ?? "a")}`,
        series: row.seriesBase || row.series,
        issue: row.issue,
        publisher: row.publisher,
        coverDate: row.coverDate,
        variant: row.variant,
        upc: row.upc,
        format: inferFormat(row),
        msrp: row.pricePaid,
        description: row.title,
      };
      matches.push({ kind: "custom", custom, row });
      unmatched += 1;
      if (row.inCollection) owned += 1;
      else wanted += 1;
    }
  }

  return { matches, owned, wanted, unmatched, matched };
}

function mapGrade(raw?: string): ComicGrade {
  if (!raw) return "raw";
  const s = raw.trim().toLowerCase();
  if (s === "raw" || s.includes("ungraded")) return "raw";
  const m = s.match(/(\d+\.\d+)/);
  if (m) {
    const g = m[1] as ComicGrade;
    const allowed: ComicGrade[] = [
      "10.0",
      "9.8",
      "9.6",
      "9.4",
      "9.2",
      "9.0",
      "8.5",
      "8.0",
      "7.5",
      "7.0",
      "6.0",
      "5.0",
      "4.0",
      "3.0",
      "2.0",
      "1.0",
    ];
    if (allowed.includes(g)) return g;
  }
  return "raw";
}

/** Apply matched rows into vault actions (caller provides store methods). */
export function buildOwnedFromMatch(match: Extract<LocgMatch, { kind: "catalog" | "custom" }>): {
  owned?: Omit<OwnedComic, "id" | "addedAt"> & { id?: string };
  wantId?: string;
  custom?: CustomComic;
} {
  const { row } = match;
  if (row.inWishlist && !row.inCollection) {
    if (match.kind === "catalog") return { wantId: match.comic.id };
    return { custom: match.custom, wantId: match.custom.id };
  }

  if (match.kind === "catalog") {
    return {
      owned: {
        catalogId: match.comic.id,
        acquiredDate: row.dateAdded || row.coverDate,
        acquiredPrice: row.pricePaid,
        grade: mapGrade(row.grade),
        notes: [
          row.notes,
          row.mediaFormat ? `LOCG media: ${row.mediaFormat}` : null,
          row.markedRead ? "Marked read on LOCG" : null,
        ]
          .filter(Boolean)
          .join(" · ") || undefined,
      },
    };
  }

  return {
    custom: match.custom,
    owned: {
      catalogId: undefined,
      custom: match.custom,
      acquiredDate: row.dateAdded || row.coverDate,
      acquiredPrice: row.pricePaid,
      grade: mapGrade(row.grade),
      notes: [row.notes, "Imported from League of Comic Geeks"].filter(Boolean).join(" · "),
    },
  };
}

import { mergeComics } from "@/data/comics";
import type { CatalogComic, ComicGrade, CustomComic, OwnedComic } from "@/lib/types";
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
  "isbn13": "upc",
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
  "price paid": "pricePaid",
  price: "pricePaid",
  cost: "pricePaid",
  "date added": "dateAdded",
  "added date": "dateAdded",
  "my added date": "dateAdded",
  notes: "notes",
  note: "notes",
  comments: "notes",
};

function normHeader(h: string): string {
  return h.trim().toLowerCase().replace(/\s+/g, " ");
}

function truthy(v: string | undefined): boolean {
  if (!v) return false;
  const s = v.trim().toLowerCase();
  return s === "1" || s === "y" || s === "yes" || s === "true" || s === "x" || s === "owned" || s === "collection";
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

    // LOCG sometimes puts "Amazing Spider-Man #300" only in Title
    if ((!series || !issue) && title) {
      const m = title.match(/^(.*?)(?:\s+#|\s+)(\d+[A-Za-z]?|nn|annual\s*\d+)\s*$/i);
      if (m) {
        series = series || m[1]!.trim();
        issue = issue || m[2]!.replace(/^#/i, "").trim();
      } else if (!series) {
        series = title;
      }
    }

    if (!series) continue;
    if (!issue) issue = "nn";
    if (!publisher) publisher = "Unknown";

    // Default: if no collection/wishlist flags at all, treat as owned (collection export)
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
      raw,
    });
  }

  return { headers, rows, warnings };
}

function comicKey(c: { series: string; issue: string; publisher: string; variant?: string }) {
  return `${c.series}|${c.issue}|${c.publisher}|${c.variant ?? ""}`.toLowerCase();
}

function normalizeSeries(s: string): string {
  return s
    .toLowerCase()
    .replace(/\b(the|a|an)\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function matchLocgRows(
  rows: LocgRow[],
  extras: CatalogComic[] = [],
): { matches: LocgMatch[]; owned: number; wanted: number; unmatched: number } {
  const catalog = mergeComics(extras);
  const byKey = new Map(catalog.map((c) => [comicKey(c), c]));
  const byLoose = new Map<string, CatalogComic[]>();
  for (const c of catalog) {
    const k = `${normalizeSeries(c.series)}|${c.issue.toLowerCase()}`;
    const list = byLoose.get(k) ?? [];
    list.push(c);
    byLoose.set(k, list);
  }

  const matches: LocgMatch[] = [];
  let owned = 0;
  let wanted = 0;
  let unmatched = 0;

  for (const row of rows) {
    if (!row.inCollection && !row.inWishlist) {
      matches.push({ kind: "skip", row, reason: "Not marked collection or wishlist" });
      continue;
    }

    const exact = byKey.get(comicKey(row));
    let comic = exact;
    if (!comic) {
      const loose = byLoose.get(`${normalizeSeries(row.series)}|${row.issue.toLowerCase()}`) ?? [];
      if (loose.length === 1) comic = loose[0];
      else if (loose.length > 1) {
        comic =
          loose.find((c) => c.publisher.toLowerCase() === row.publisher.toLowerCase()) ??
          loose.find((c) => !c.variant) ??
          loose[0];
      }
    }

    if (comic) {
      matches.push({ kind: "catalog", comic, row });
      if (row.inCollection) owned += 1;
      else wanted += 1;
    } else {
      const custom: CustomComic = {
        id: `locg-${slug(row.series)}-${slug(row.issue)}-${slug(row.publisher)}-${slug(row.variant ?? "a")}`,
        series: row.series,
        issue: row.issue,
        publisher: row.publisher,
        coverDate: row.coverDate,
        variant: row.variant,
        upc: row.upc,
        format: /tpb|trade/i.test(row.mediaFormat ?? "")
          ? "tpb"
          : /hardcover|\bhc\b/i.test(row.mediaFormat ?? "")
            ? "hc"
            : /facsimile/i.test(row.title ?? row.series)
              ? "facsimile"
              : /annual/i.test(row.issue)
                ? "annual"
                : "single",
        msrp: row.pricePaid,
        description: row.title,
      };
      matches.push({ kind: "custom", custom, row });
      unmatched += 1;
      if (row.inCollection) owned += 1;
      else wanted += 1;
    }
  }

  return { matches, owned, wanted, unmatched };
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
        notes: [row.notes, row.mediaFormat ? `LOCG media: ${row.mediaFormat}` : null, row.markedRead ? "Marked read on LOCG" : null]
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
      notes: [row.notes, "Imported from League of Comic Geeks"]
        .filter(Boolean)
        .join(" · "),
    },
  };
}

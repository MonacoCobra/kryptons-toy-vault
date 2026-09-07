import { createServerFn } from "@tanstack/react-start";
import { COMICS } from "@/data/comics";
import type { CatalogComic } from "@/lib/types";
import { weekKey } from "@/lib/utils";

/** Weeks a title stays in New & Noteworthy before graduating to the permanent archive. */
export const NOTEWORTHY_WEEKS = 3;

type DropRow = {
  week: string;
  comics: unknown;
  fetched_at: string;
  status: string;
};

type CatalogRow = {
  id: string;
  series: string;
  issue: string;
  publisher: string;
  cover_date: string;
  street_date: string | null;
  writers: unknown;
  artists: unknown;
  description: string;
  msrp: number;
  format: string;
  variant: string | null;
  upc: string | null;
  demand: number;
  key_issue: boolean;
  palette: unknown;
  cover: string | null;
  source_week: string | null;
};

export type ComicLibrary = {
  noteworthy: CatalogComic[];
  archive: CatalogComic[];
  promoted: number;
  week: string;
};

function comicKey(c: { series: string; issue: string; publisher: string; variant?: string }) {
  return `${c.series}|${c.issue}|${c.publisher}|${c.variant ?? ""}`.toLowerCase();
}

function asArray(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value) as unknown;
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

function parseIsoWeek(week: string): { year: number; week: number } | null {
  const m = week.match(/^(\d{4})-W(\d{2})$/i);
  if (!m) return null;
  return { year: Number(m[1]), week: Number(m[2]) };
}

/** Approximate Monday UTC for an ISO week key. */
function weekStartUtc(week: string): Date | null {
  const parsed = parseIsoWeek(week);
  if (!parsed) return null;
  const jan4 = new Date(Date.UTC(parsed.year, 0, 4));
  const start = new Date(jan4);
  start.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() || 7) - 1) + (parsed.week - 1) * 7);
  return start;
}

export function weeksAgo(week: string, from = new Date()): number {
  const start = weekStartUtc(week);
  if (!start) return 0;
  const diff = from.getTime() - start.getTime();
  return Math.floor(diff / (7 * 24 * 3600 * 1000));
}

function rowToComic(row: CatalogRow): CatalogComic {
  const paletteRaw = asArray(row.palette).map(String);
  const palette: [string, string, string] = [
    paletteRaw[0] || "#1e3a8a",
    paletteRaw[1] || "#e30613",
    paletteRaw[2] || "#f8fafc",
  ];
  return {
    id: String(row.id),
    series: String(row.series ?? ""),
    issue: String(row.issue ?? "").replace(/^#/, "").trim() || "1",
    publisher: String(row.publisher ?? ""),
    coverDate: row.cover_date || row.street_date || "",
    streetDate: row.street_date || undefined,
    writers: asArray(row.writers).map(String),
    artists: asArray(row.artists).map(String),
    description: row.description || "",
    msrp: Number(row.msrp) || 4.99,
    format: (row.format as CatalogComic["format"]) || "single",
    variant: row.variant || undefined,
    upc: row.upc || undefined,
    demand: Number(row.demand) || 1,
    key: Boolean(row.key_issue),
    palette,
    cover: row.cover || undefined,
  };
}

function peopleField(value: unknown): string[] {
  if (Array.isArray(value)) return value.map((v) => String(v ?? "").trim()).filter(Boolean);
  if (value == null) return [];
  return String(value)
    .split(/,|&| and /i)
    .map((p) => p.trim())
    .filter(Boolean);
}

function asComic(value: unknown): CatalogComic | null {
  if (!value || typeof value !== "object") return null;
  const raw = value as Record<string, unknown>;
  const id = String(raw.id ?? "").trim();
  const series = String(raw.series ?? "").trim();
  const issue = String(raw.issue ?? "").replace(/^#/, "").trim();
  const publisher = String(raw.publisher ?? "").trim();
  if (!id || !series || !issue || !publisher) return null;
  const paletteRaw = asArray(raw.palette).map(String);
  const palette: [string, string, string] = [
    paletteRaw[0] || "#1e3a8a",
    paletteRaw[1] || "#e30613",
    paletteRaw[2] || "#f8fafc",
  ];
  const coverDate = String(raw.coverDate ?? raw.cover_date ?? raw.streetDate ?? raw.street_date ?? "").trim();
  const streetDateRaw = String(raw.streetDate ?? raw.street_date ?? "").trim();
  const variant = String(raw.variant ?? "").trim();
  const cover = String(raw.cover ?? raw.coverUrl ?? "").trim();
  return {
    id,
    series,
    issue,
    publisher,
    coverDate: coverDate || streetDateRaw,
    streetDate: streetDateRaw || undefined,
    writers: peopleField(raw.writers),
    artists: peopleField(raw.artists),
    description: String(raw.description ?? ""),
    msrp: Number(raw.msrp) || 4.99,
    format: (String(raw.format || "single") as CatalogComic["format"]) || "single",
    variant: variant || undefined,
    upc: String(raw.upc ?? "").trim() || undefined,
    demand: Number(raw.demand) || 1,
    key: Boolean(raw.key ?? raw.key_issue),
    palette,
    cover: cover.startsWith("http") || cover.startsWith("/") ? cover : undefined,
  };
}

async function readDrops(): Promise<DropRow[]> {
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    return await sql.query<DropRow>(
      "select week, comics, fetched_at, status from weekly_drops where status = 'ok' order by week desc",
    );
  } catch {
    return [];
  }
}

async function readPermanent(): Promise<CatalogComic[]> {
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    const rows = await sql.query<CatalogRow>("select * from comic_catalog");
    return rows.map(rowToComic);
  } catch {
    return [];
  }
}

async function upsertPermanent(comics: CatalogComic[], sourceWeek: string): Promise<number> {
  if (!comics.length) return 0;
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    let n = 0;
    for (const c of comics) {
      await sql.query(
        `insert into comic_catalog (
           id, series, issue, publisher, cover_date, street_date, writers, artists,
           description, msrp, format, variant, upc, demand, key_issue, palette, cover,
           source_week, promoted_at, updated_at
         ) values (
           $1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9,$10,$11,$12,$13,$14,$15,$16::jsonb,$17,$18,now(),now()
         )
         on conflict (id) do update set
           series = excluded.series,
           issue = excluded.issue,
           publisher = excluded.publisher,
           cover_date = excluded.cover_date,
           street_date = excluded.street_date,
           writers = excluded.writers,
           artists = excluded.artists,
           description = excluded.description,
           msrp = excluded.msrp,
           format = excluded.format,
           variant = excluded.variant,
           upc = excluded.upc,
           demand = excluded.demand,
           key_issue = excluded.key_issue,
           palette = excluded.palette,
           cover = coalesce(excluded.cover, comic_catalog.cover),
           source_week = coalesce(excluded.source_week, comic_catalog.source_week),
           updated_at = now()`,
        [
          c.id,
          c.series,
          c.issue,
          c.publisher,
          c.coverDate || c.streetDate || "",
          c.streetDate ?? null,
          JSON.stringify(c.writers ?? []),
          JSON.stringify(c.artists ?? []),
          c.description || "",
          c.msrp ?? 4.99,
          c.format || "single",
          c.variant ?? null,
          c.upc ?? null,
          c.demand ?? 1,
          Boolean(c.key),
          JSON.stringify(c.palette ?? ["#1e3a8a", "#e30613", "#f8fafc"]),
          c.cover ?? null,
          sourceWeek,
        ],
      );
      n += 1;
    }
    return n;
  } catch {
    return 0;
  }
}

/** Promote weekly-drop comics older than NOTEWORTHY_WEEKS into comic_catalog. */
export async function promoteAgedWeeklyComics(now = new Date()): Promise<number> {
  const drops = await readDrops();
  let promoted = 0;
  for (const drop of drops) {
    const age = weeksAgo(drop.week, now);
    if (age < NOTEWORTHY_WEEKS) continue;
    const comics = asArray(drop.comics).map(asComic).filter(Boolean) as CatalogComic[];
    if (!comics.length) continue;
    promoted += await upsertPermanent(comics, drop.week);
  }
  return promoted;
}

function mergeUnique(base: CatalogComic[], extra: CatalogComic[]): CatalogComic[] {
  const seen = new Set(base.map(comicKey));
  const out = [...base];
  for (const c of extra) {
    const k = comicKey(c);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(c);
  }
  return out;
}

function buildLibrary(
  permanentDb: CatalogComic[],
  drops: DropRow[],
  liveExtras: CatalogComic[],
  now = new Date(),
): Omit<ComicLibrary, "promoted"> {
  const week = weekKey(now);
  const noteworthy: CatalogComic[] = [];
  const noteworthyKeys = new Set<string>();

  for (const drop of drops) {
    const age = weeksAgo(drop.week, now);
    if (age >= NOTEWORTHY_WEEKS) continue;
    for (const raw of asArray(drop.comics)) {
      const c = asComic(raw);
      if (!c) continue;
      const k = comicKey(c);
      if (noteworthyKeys.has(k)) continue;
      noteworthyKeys.add(k);
      noteworthy.push(c);
    }
  }

  for (const c of liveExtras) {
    const k = comicKey(c);
    if (noteworthyKeys.has(k)) continue;
    const street = c.streetDate ?? c.coverDate;
    const recent =
      c.id.startsWith("live-c-") ||
      (street && Date.now() - Date.parse(street) < NOTEWORTHY_WEEKS * 7 * 24 * 3600 * 1000);
    if (!recent) continue;
    noteworthyKeys.add(k);
    noteworthy.push(c);
  }

  // Recent street dates in the static catalog also count as noteworthy
  for (const c of COMICS) {
    const k = comicKey(c);
    if (noteworthyKeys.has(k)) continue;
    const street = c.streetDate ?? c.coverDate;
    if (!street) continue;
    const t = Date.parse(street);
    if (!Number.isFinite(t)) continue;
    if (Date.now() - t < NOTEWORTHY_WEEKS * 7 * 24 * 3600 * 1000) {
      noteworthyKeys.add(k);
      noteworthy.push(c);
    }
  }

  const archive = mergeUnique(COMICS, permanentDb).filter((c) => !noteworthyKeys.has(comicKey(c)));

  return {
    noteworthy: noteworthy.sort((a, b) => {
      const da = a.streetDate ?? a.coverDate;
      const db = b.streetDate ?? b.coverDate;
      return da < db ? 1 : -1;
    }),
    archive,
    week,
  };
}

/** Client-side fallback when the server library has not loaded yet. */
export function splitComicsClient(extras: CatalogComic[] = [], now = new Date()): {
  noteworthy: CatalogComic[];
  archive: CatalogComic[];
} {
  const noteworthyKeys = new Set<string>();
  const noteworthy: CatalogComic[] = [];
  const windowMs = NOTEWORTHY_WEEKS * 7 * 24 * 3600 * 1000;

  for (const c of extras) {
    const k = comicKey(c);
    if (noteworthyKeys.has(k)) continue;
    noteworthyKeys.add(k);
    noteworthy.push(c);
  }

  for (const c of COMICS) {
    const k = comicKey(c);
    if (noteworthyKeys.has(k)) continue;
    const street = c.streetDate ?? c.coverDate;
    if (!street) continue;
    const t = Date.parse(street);
    if (Number.isFinite(t) && now.getTime() - t < windowMs) {
      noteworthyKeys.add(k);
      noteworthy.push(c);
    }
  }

  const archive = COMICS.filter((c) => !noteworthyKeys.has(comicKey(c)));
  return {
    noteworthy: noteworthy.sort((a, b) => {
      const da = a.streetDate ?? a.coverDate;
      const db = b.streetDate ?? b.coverDate;
      return da < db ? 1 : -1;
    }),
    archive,
  };
}

export const getComicLibrary = createServerFn({ method: "POST" })
  .validator((data: unknown) => {
    const extras =
      data && typeof data === "object" && Array.isArray((data as { extras?: unknown }).extras)
        ? ((data as { extras: CatalogComic[] }).extras ?? [])
        : [];
    return { extras };
  })
  .handler(async ({ data }): Promise<ComicLibrary> => {
    const promoted = await promoteAgedWeeklyComics();
    const [permanentDb, drops] = await Promise.all([readPermanent(), readDrops()]);
    const built = buildLibrary(permanentDb, drops, data.extras ?? []);
    return { ...built, promoted };
  });

import { createServerFn } from "@tanstack/react-start";
import { FIGURES } from "@/data/figures";
import type { CatalogFigure, CompanyId, ItemKind } from "@/lib/types";

/** Weeks a figure stays in New & Noteworthy before counting as archive-only. */
export const NOTEWORTHY_WEEKS = 3;

/** Permanent archive release floor — nothing older. */
export const RELEASE_FLOOR = "1980-01-01";

export type FigureLibrary = {
  noteworthy: CatalogFigure[];
  archive: CatalogFigure[];
  /** Live DB overlay rows not already present in baked FIGURES. */
  overlay: CatalogFigure[];
  weekHintMs: number;
};

export type FigureUpsertResult = {
  inserted: number;
  skippedBaked: number;
  skippedOverlay: number;
  skippedInvalid: number;
  total: number;
};

type FigureRow = {
  id: string;
  name: string;
  subtitle: string;
  line: string;
  company: string;
  kind: string;
  release_date: string;
  msrp: number;
  scale: string;
  demand: number;
  tags: unknown;
  sku: string;
  exclusive: string | null;
  image_url: string | null;
  source: string | null;
};

export type FigureOverlayInput = {
  id: string;
  name: string;
  subtitle: string;
  line: string;
  company: string;
  kind?: string;
  releaseDate: string;
  msrp: number;
  scale: string;
  demand: number;
  tags: string[] | string;
  sku: string;
  exclusive?: string;
  imageUrl?: string;
  source?: string;
};

function figureNameKey(f: { name: string; subtitle: string; line: string; company: string }) {
  return `${f.name}|${f.subtitle}|${f.line}|${f.company}`.toLowerCase();
}

function normSku(sku: string | undefined | null): string | undefined {
  const s = (sku ?? "").trim();
  return s ? s.toLowerCase() : undefined;
}

function asArray(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value) as unknown;
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return value
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
    }
  }
  return [];
}

function isRecentRelease(releaseDate: string | undefined, now: Date, windowMs: number): boolean {
  if (!releaseDate) return false;
  const t = Date.parse(releaseDate);
  if (!Number.isFinite(t)) return false;
  return now.getTime() - t < windowMs;
}

function rowToFigure(row: FigureRow): CatalogFigure {
  return {
    id: row.id,
    name: row.name,
    subtitle: row.subtitle || "",
    line: row.line,
    company: row.company as CompanyId,
    kind: (row.kind as ItemKind) || "figure",
    releaseDate: row.release_date,
    msrp: Number(row.msrp) || 24.99,
    scale: row.scale || '6"',
    demand: Number(row.demand) || 1,
    tags: asArray(row.tags).map(String),
    sku: row.sku,
    exclusive: row.exclusive || undefined,
    imageUrl: row.image_url || undefined,
    source: row.source || undefined,
  };
}

function isHttpUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

/** Validate an overlay candidate. Returns null when the row must not be stored. */
export function validateFigureOverlayInput(raw: unknown): CatalogFigure | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as FigureOverlayInput;
  const id = typeof r.id === "string" ? r.id.trim() : "";
  const name = typeof r.name === "string" ? r.name.trim() : "";
  const subtitle = typeof r.subtitle === "string" ? r.subtitle.trim() : "";
  const line = typeof r.line === "string" ? r.line.trim() : "";
  const company = typeof r.company === "string" ? r.company.trim() : "";
  const sku = typeof r.sku === "string" ? r.sku.trim() : "";
  const releaseDate = typeof r.releaseDate === "string" ? r.releaseDate.trim() : "";
  const kind = (typeof r.kind === "string" ? r.kind.trim() : "figure") || "figure";
  if (!id || !name || !line || !company || !sku || !releaseDate) return null;
  if (kind !== "figure" && kind !== "kit") return null;
  if (releaseDate < RELEASE_FLOOR) return null;
  if (!Number.isFinite(Date.parse(releaseDate))) return null;
  const msrp = Number(r.msrp);
  if (!Number.isFinite(msrp) || msrp < 0) return null;
  const demand = Number(r.demand);
  if (!Number.isFinite(demand) || demand <= 0) return null;
  const scale = typeof r.scale === "string" && r.scale.trim() ? r.scale.trim() : '6"';
  const tags = Array.isArray(r.tags)
    ? r.tags.map(String).map((t) => t.trim()).filter(Boolean)
    : typeof r.tags === "string"
      ? r.tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean)
      : [];
  const imageUrl =
    typeof r.imageUrl === "string" && r.imageUrl.trim() ? r.imageUrl.trim() : undefined;
  if (imageUrl && !isHttpUrl(imageUrl)) return null;
  const exclusive =
    typeof r.exclusive === "string" && r.exclusive.trim() ? r.exclusive.trim() : undefined;
  const source = typeof r.source === "string" && r.source.trim() ? r.source.trim() : undefined;
  return {
    id,
    name,
    subtitle,
    line,
    company: company as CompanyId,
    kind: kind as ItemKind,
    releaseDate,
    msrp,
    scale,
    demand,
    tags,
    sku,
    exclusive,
    imageUrl,
    source,
  };
}

function bakedIndex() {
  const skus = new Set<string>();
  const ids = new Set<string>();
  const keys = new Set<string>();
  for (const f of FIGURES) {
    ids.add(f.id);
    keys.add(figureNameKey(f));
    const s = normSku(f.sku);
    if (s) skus.add(s);
  }
  return { skus, ids, keys };
}

function isInIndex(
  f: CatalogFigure,
  idx: { skus: Set<string>; ids: Set<string>; keys: Set<string> },
): boolean {
  const s = normSku(f.sku);
  if (s && idx.skus.has(s)) return true;
  if (idx.ids.has(f.id)) return true;
  if (idx.keys.has(figureNameKey(f))) return true;
  return false;
}

async function readOverlay(): Promise<CatalogFigure[]> {
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    const rows = await sql.query<FigureRow>("select * from figure_catalog");
    return rows.map(rowToFigure);
  } catch {
    return [];
  }
}

async function upsertOverlayRows(figures: CatalogFigure[]): Promise<FigureUpsertResult> {
  const result: FigureUpsertResult = {
    inserted: 0,
    skippedBaked: 0,
    skippedOverlay: 0,
    skippedInvalid: 0,
    total: figures.length,
  };
  if (!figures.length) return result;

  const baked = bakedIndex();
  let existing: CatalogFigure[] = [];
  try {
    existing = await readOverlay();
  } catch {
    existing = [];
  }
  const overlayIdx = {
    skus: new Set<string>(),
    ids: new Set<string>(),
    keys: new Set<string>(),
  };
  for (const f of existing) {
    overlayIdx.ids.add(f.id);
    overlayIdx.keys.add(figureNameKey(f));
    const s = normSku(f.sku);
    if (s) overlayIdx.skus.add(s);
  }

  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();

    for (const f of figures) {
      if (isInIndex(f, baked)) {
        result.skippedBaked += 1;
        continue;
      }
      if (isInIndex(f, overlayIdx)) {
        result.skippedOverlay += 1;
        continue;
      }

      try {
        const rows = await sql.query<{ id: string }>(
          `insert into figure_catalog (
             id, name, subtitle, line, company, kind, release_date, msrp, scale,
             demand, tags, sku, exclusive, image_url, source, promoted_at, updated_at
           ) values (
             $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12,$13,$14,$15,now(),now()
           )
           on conflict do nothing
           returning id`,
          [
            f.id,
            f.name,
            f.subtitle || "",
            f.line,
            f.company,
            f.kind || "figure",
            f.releaseDate,
            f.msrp ?? 24.99,
            f.scale || '6"',
            f.demand ?? 1,
            JSON.stringify(f.tags ?? []),
            f.sku,
            f.exclusive ?? null,
            f.imageUrl ?? null,
            f.source ?? null,
          ],
        );
        if (rows.length) {
          result.inserted += 1;
          overlayIdx.ids.add(f.id);
          overlayIdx.keys.add(figureNameKey(f));
          const s = normSku(f.sku);
          if (s) overlayIdx.skus.add(s);
        } else {
          result.skippedOverlay += 1;
        }
      } catch {
        result.skippedInvalid += 1;
      }
    }
  } catch {
    // DB unavailable (preview without migrate) — treat as no inserts
  }
  return result;
}

/**
 * Client-side split mirroring comics: weekly/live extras + very recent static
 * releases stay in New & Noteworthy; the permanent FIGURES catalog (seed + backlog)
 * plus live SKU overlay forms the archive. Figures UI may still show a single merged
 * list via mergeFigures.
 */
export function splitFiguresClient(
  extras: CatalogFigure[] = [],
  overlayOrNow: CatalogFigure[] | Date = [],
  nowArg = new Date(),
): FigureLibrary {
  const overlay = overlayOrNow instanceof Date ? [] : overlayOrNow;
  const now = overlayOrNow instanceof Date ? overlayOrNow : nowArg;
  const windowMs = NOTEWORTHY_WEEKS * 7 * 24 * 3600 * 1000;
  const noteworthyKeys = new Set<string>();
  const noteworthy: CatalogFigure[] = [];

  for (const f of extras) {
    const k = figureNameKey(f);
    if (noteworthyKeys.has(k)) continue;
    noteworthyKeys.add(k);
    noteworthy.push(f);
  }

  for (const f of FIGURES) {
    const k = figureNameKey(f);
    if (noteworthyKeys.has(k)) continue;
    if (isRecentRelease(f.releaseDate, now, windowMs)) {
      noteworthyKeys.add(k);
      noteworthy.push(f);
    }
  }

  const permanent = mergeOverlayOntoBaked(overlay);
  const archive = permanent.filter((f) => !noteworthyKeys.has(figureNameKey(f)));

  return {
    noteworthy: noteworthy.sort((a, b) => (a.releaseDate < b.releaseDate ? 1 : -1)),
    archive,
    overlay,
    weekHintMs: windowMs,
  };
}

/** Permanent archive view: baked + overlay minus N&N extras window. */
export function figureArchive(
  extras: CatalogFigure[] = [],
  overlayOrNow: CatalogFigure[] | Date = [],
  nowArg = new Date(),
): CatalogFigure[] {
  return splitFiguresClient(extras, overlayOrNow, nowArg).archive;
}

/** Merge live overlay on top of baked FIGURES (sku → id → name|subtitle|line|company). */
export function mergeOverlayOntoBaked(overlay: CatalogFigure[]): CatalogFigure[] {
  if (!overlay.length) return FIGURES;
  const skus = new Set<string>();
  const ids = new Set<string>();
  const keys = new Set<string>();
  for (const f of FIGURES) {
    ids.add(f.id);
    keys.add(figureNameKey(f));
    const s = normSku(f.sku);
    if (s) skus.add(s);
  }
  const add: CatalogFigure[] = [];
  for (const f of overlay) {
    const s = normSku(f.sku);
    if (s && skus.has(s)) continue;
    if (ids.has(f.id)) continue;
    if (keys.has(figureNameKey(f))) continue;
    add.push(f);
    if (s) skus.add(s);
    ids.add(f.id);
    keys.add(figureNameKey(f));
  }
  return add.length ? [...FIGURES, ...add] : FIGURES;
}

export const getFigureLibrary = createServerFn({ method: "POST" })
  .validator((data: unknown) => {
    const extras =
      data && typeof data === "object" && Array.isArray((data as { extras?: unknown }).extras)
        ? ((data as { extras: CatalogFigure[] }).extras ?? [])
        : [];
    return { extras };
  })
  .handler(async ({ data }): Promise<FigureLibrary> => {
    const overlay = await readOverlay();
    return splitFiguresClient(data.extras ?? [], overlay);
  });

export const upsertFigureSkuOverlay = createServerFn({ method: "POST" })
  .validator((data: unknown) => {
    const figures =
      data && typeof data === "object" && Array.isArray((data as { figures?: unknown }).figures)
        ? ((data as { figures: unknown[] }).figures ?? [])
        : [];
    return { figures };
  })
  .handler(async ({ data }): Promise<FigureUpsertResult> => {
    const valid: CatalogFigure[] = [];
    let skippedInvalid = 0;
    for (const raw of data.figures ?? []) {
      const f = validateFigureOverlayInput(raw);
      if (!f) {
        skippedInvalid += 1;
        continue;
      }
      valid.push(f);
    }
    const result = await upsertOverlayRows(valid);
    result.skippedInvalid += skippedInvalid;
    result.total = (data.figures ?? []).length;
    return result;
  });

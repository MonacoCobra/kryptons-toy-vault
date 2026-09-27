import { createServerFn } from "@tanstack/react-start";
import { stampFigureFranchise } from "@/lib/figure-property";
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

function rowToFigure(row: FigureRow): CatalogFigure {
  return stampFigureFranchise({
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
  });
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
  return stampFigureFranchise({
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
  });
}

async function bakedIndex() {
  const { readFigureIdentity } = await import("@/lib/figure-identity.server");
  const identity = await readFigureIdentity();
  return {
    skus: new Set(identity.skus),
    ids: new Set(identity.ids),
    keys: new Set(identity.keys),
  };
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

  const baked = await bakedIndex();
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
 * Live DB overlay only. The baked figure catalog is static JSON under /catalog
 * and is not shipped through this function.
 */
export function splitFiguresClient(
  _extras: CatalogFigure[] = [],
  overlayOrNow: CatalogFigure[] | Date = [],
  _nowArg = new Date(),
): FigureLibrary {
  const overlay = overlayOrNow instanceof Date ? [] : overlayOrNow;
  const windowMs = NOTEWORTHY_WEEKS * 7 * 24 * 3600 * 1000;
  return {
    noteworthy: [],
    archive: [],
    overlay,
    weekHintMs: windowMs,
  };
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

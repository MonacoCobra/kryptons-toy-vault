import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { fetchLocgIssueById, normalizeUpc } from "@/lib/locg-upc";
import upcMapJson from "@/data/comic-upc-map.json";

/**
 * Resolve real published cover art for catalog comics.
 * Identity: prefer UPC/ISBN (LOCG-first) so A/B variants do not steal art.
 * Cover art sources: LOCG CDN (when UPC-matched) → Comic Vine (fallback).
 * Never generates or synthesizes artwork.
 */

const Input = z.object({
  comicId: z.string().min(1),
  series: z.string().min(1),
  issue: z.string().min(1),
  publisher: z.string().optional(),
  variant: z.string().optional(),
  upc: z.string().optional(),
  locgId: z.string().optional(),
  force: z.boolean().optional(),
});

export type ComicCoverResult = {
  status: "ok" | "missing" | "no_key" | "error";
  coverUrl?: string;
  thumbUrl?: string;
  source?: string;
  upc?: string;
  error?: string;
};

async function apiKey(): Promise<string | undefined> {
  const raw = typeof process !== "undefined" ? process.env.COMICVINE_API_KEY : undefined;
  if (raw?.trim()) return raw.trim();
  try {
    const { readFile } = await import("node:fs/promises");
    const fromFile = (await readFile("/home/box/.config/krypton/comicvine-api-key", "utf8")).trim();
    return fromFile || undefined;
  } catch {
    return undefined;
  }
}

type CoverRow = {
  comic_id: string;
  cover_url: string;
  thumb_url: string | null;
  source: string;
  fetched_at: string;
  upc?: string | null;
};

type UpcMapEntry = {
  upc?: string;
  locgId?: string;
  coverUrl?: string;
  source?: string;
};

function readUpcMap(comicId: string): UpcMapEntry | null {
  const map = upcMapJson as Record<string, UpcMapEntry>;
  return map[comicId] ?? null;
}

async function readCached(comicId: string): Promise<CoverRow | null> {
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    const rows = await sql.query<CoverRow>(
      "select comic_id, cover_url, thumb_url, source, fetched_at, upc from comic_covers where comic_id = $1",
      [comicId],
    );
    return rows[0] ?? null;
  } catch {
    try {
      const { getSql } = await import("@/lib/db");
      const sql = await getSql();
      const rows = await sql.query<CoverRow>(
        "select comic_id, cover_url, thumb_url, source, fetched_at from comic_covers where comic_id = $1",
        [comicId],
      );
      return rows[0] ?? null;
    } catch {
      return null;
    }
  }
}

async function writeCached(row: {
  comicId: string;
  series: string;
  issue: string;
  publisher: string;
  source: string;
  sourceId?: string;
  coverUrl: string;
  thumbUrl?: string;
  upc?: string;
}): Promise<void> {
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    try {
      await sql.query(
        `insert into comic_covers (
           comic_id, series, issue, publisher, source, source_id, cover_url, thumb_url, upc, fetched_at, updated_at
         ) values ($1,$2,$3,$4,$5,$6,$7,$8,$9,now(),now())
         on conflict (comic_id) do update set
           cover_url = excluded.cover_url,
           thumb_url = excluded.thumb_url,
           source = excluded.source,
           source_id = excluded.source_id,
           upc = coalesce(excluded.upc, comic_covers.upc),
           updated_at = now()`,
        [
          row.comicId,
          row.series,
          row.issue,
          row.publisher,
          row.source,
          row.sourceId ?? null,
          row.coverUrl,
          row.thumbUrl ?? null,
          row.upc ?? null,
        ],
      );
    } catch {
      await sql.query(
        `insert into comic_covers (
           comic_id, series, issue, publisher, source, source_id, cover_url, thumb_url, fetched_at, updated_at
         ) values ($1,$2,$3,$4,$5,$6,$7,$8,now(),now())
         on conflict (comic_id) do update set
           cover_url = excluded.cover_url,
           thumb_url = excluded.thumb_url,
           source = excluded.source,
           source_id = excluded.source_id,
           updated_at = now()`,
        [
          row.comicId,
          row.series,
          row.issue,
          row.publisher,
          row.source,
          row.sourceId ?? null,
          row.coverUrl,
          row.thumbUrl ?? null,
        ],
      );
    }
  } catch {
    // preview without DB still returns live URL
  }
}

function issueNumber(issue: string): string {
  const cleaned = issue.trim().replace(/^#/, "");
  if (/^nn$/i.test(cleaned)) return "";
  return cleaned;
}

type VineIssue = {
  id?: number;
  name?: string;
  issue_number?: string;
  barcode?: string | null;
  image?: {
    medium_url?: string;
    small_url?: string;
    thumb_url?: string;
    original_url?: string;
    super_url?: string;
  };
  volume?: { name?: string };
};

async function searchComicVine(
  series: string,
  issue: string,
  variant?: string,
): Promise<VineIssue | null> {
  const key = await apiKey();
  if (!key) return null;
  const num = issueNumber(issue);
  const q = num ? `${series} ${num}` : series;
  const url = new URL("https://comicvine.gamespot.com/api/search/");
  url.searchParams.set("api_key", key);
  url.searchParams.set("format", "json");
  url.searchParams.set("resources", "issue");
  url.searchParams.set("query", q);
  url.searchParams.set("limit", "10");
  url.searchParams.set("field_list", "id,name,issue_number,image,volume,barcode");

  const res = await fetch(url.toString(), {
    headers: {
      "User-Agent": "KryptonsToyVault/1.0 (personal collection; cover lookup)",
    },
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { results?: VineIssue[] };
  const results = data.results ?? [];
  if (!results.length) return null;

  const want = num.toLowerCase();
  const seriesCore = series.toLowerCase().split("(")[0]!.trim();
  const variantCore = (variant ?? "").toLowerCase();
  const scored = results
    .map((r) => {
      const vol = (r.volume?.name ?? "").toLowerCase();
      const iss = String(r.issue_number ?? "").toLowerCase();
      const name = (r.name ?? "").toLowerCase();
      let score = 0;
      if (iss === want) score += 5;
      if (vol === seriesCore) score += 6;
      else if (vol.includes(seriesCore) || seriesCore.includes(vol)) score += 3;
      if (r.image?.medium_url || r.image?.super_url) score += 1;
      if (vol.includes("w.i.p") || vol.includes("wip")) score -= 4;
      if (variantCore) {
        if (name.includes(variantCore) || vol.includes(variantCore)) score += 4;
      } else {
        // Prefer main/A covers when no variant requested
        if (/\b(variant|cover\s*[b-z]|1:\d+)/i.test(name)) score -= 2;
      }
      return { r, score };
    })
    .sort((a, b) => b.score - a.score);
  const best = scored[0];
  return best && best.score >= 5 && best.r.image ? best.r : null;
}

function pickUrl(issue: VineIssue): { cover?: string; thumb?: string } {
  const img = issue.image;
  if (!img) return {};
  const cover = img.super_url || img.medium_url || img.original_url || img.small_url;
  const thumb = img.thumb_url || img.small_url || img.medium_url;
  return { cover, thumb };
}

async function resolveViaUpc(opts: {
  comicId: string;
  upc?: string;
  locgId?: string;
  series: string;
  issue: string;
  publisher: string;
}): Promise<ComicCoverResult | null> {
  const mapped = readUpcMap(opts.comicId);
  const upc = normalizeUpc(opts.upc) || normalizeUpc(mapped?.upc);
  const locgId = opts.locgId || mapped?.locgId;

  // Durable map already has a UPC-tied cover
  if (upc && mapped?.coverUrl) {
    await writeCached({
      comicId: opts.comicId,
      series: opts.series,
      issue: opts.issue,
      publisher: opts.publisher,
      source: mapped.source || "locg-upc",
      sourceId: mapped.locgId,
      coverUrl: mapped.coverUrl,
      thumbUrl: mapped.coverUrl,
      upc,
    });
    return {
      status: "ok",
      coverUrl: mapped.coverUrl,
      thumbUrl: mapped.coverUrl,
      source: mapped.source || "locg-upc",
      upc,
    };
  }

  // Live LOCG fetch when we have an id (polite single request — not a scrape loop)
  if (locgId) {
    const hit = await fetchLocgIssueById(locgId);
    if (hit?.coverUrl) {
      const code = hit.upc || upc;
      await writeCached({
        comicId: opts.comicId,
        series: opts.series,
        issue: opts.issue,
        publisher: opts.publisher,
        source: "locg",
        sourceId: hit.locgId,
        coverUrl: hit.coverUrl,
        thumbUrl: hit.coverUrl,
        upc: code,
      });
      return {
        status: "ok",
        coverUrl: hit.coverUrl,
        thumbUrl: hit.coverUrl,
        source: "locg",
        upc: code,
      };
    }
  }

  return null;
}

export const getComicCover = createServerFn({ method: "POST" })
  .validator((data: unknown) => Input.parse(data))
  .handler(async ({ data }): Promise<ComicCoverResult> => {
    const upcNorm = normalizeUpc(data.upc);

    if (!data.force) {
      const cached = await readCached(data.comicId);
      if (cached?.cover_url) {
        // If caller now has a UPC and cache was series-only, allow refresh
        const cacheUpc = normalizeUpc(cached.upc ?? undefined);
        const upcMismatch = Boolean(upcNorm && cacheUpc && upcNorm !== cacheUpc);
        const preferUpcRefresh =
          Boolean(upcNorm) &&
          !cacheUpc &&
          (cached.source === "comicvine" || cached.source === "comicvine-search");
        if (!upcMismatch && !preferUpcRefresh) {
          return {
            status: "ok",
            coverUrl: cached.cover_url,
            thumbUrl: cached.thumb_url ?? undefined,
            source: cached.source,
            upc: cacheUpc,
          };
        }
      }
    }

    // 1) UPC / LOCG identity first
    try {
      const viaUpc = await resolveViaUpc({
        comicId: data.comicId,
        upc: upcNorm,
        locgId: data.locgId,
        series: data.series,
        issue: data.issue,
        publisher: data.publisher ?? "",
      });
      if (viaUpc) return viaUpc;
    } catch {
      // fall through to Comic Vine
    }

    // 2) Comic Vine by series+issue(+variant)
    if (!(await apiKey())) {
      return { status: "no_key", error: "Set COMICVINE_API_KEY for real cover lookup." };
    }

    try {
      const hit = await searchComicVine(data.series, data.issue, data.variant);
      if (!hit) return { status: "missing" };
      const { cover, thumb } = pickUrl(hit);
      if (!cover) return { status: "missing" };
      const vineUpc = normalizeUpc(hit.barcode ?? undefined) || upcNorm;

      await writeCached({
        comicId: data.comicId,
        series: data.series,
        issue: data.issue,
        publisher: data.publisher ?? "",
        source: "comicvine",
        sourceId: hit.id != null ? String(hit.id) : undefined,
        coverUrl: cover,
        thumbUrl: thumb,
        upc: vineUpc,
      });

      return {
        status: "ok",
        coverUrl: cover,
        thumbUrl: thumb,
        source: "comicvine",
        upc: vineUpc,
      };
    } catch (err) {
      return {
        status: "error",
        error: err instanceof Error ? err.message : "Cover lookup failed",
      };
    }
  });

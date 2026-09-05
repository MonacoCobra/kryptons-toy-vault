import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

/**
 * Resolve real published cover art for catalog comics.
 * Sources: Comic Vine API (non-AI photographic / scanned publisher covers).
 * Never generates or synthesizes artwork.
 */

const Input = z.object({
  comicId: z.string().min(1),
  series: z.string().min(1),
  issue: z.string().min(1),
  publisher: z.string().optional(),
  force: z.boolean().optional(),
});

export type ComicCoverResult = {
  status: "ok" | "missing" | "no_key" | "error";
  coverUrl?: string;
  thumbUrl?: string;
  source?: string;
  error?: string;
};

function apiKey(): string | undefined {
  const raw = typeof process !== "undefined" ? process.env.COMICVINE_API_KEY : undefined;
  return raw?.trim() || undefined;
}

type CoverRow = {
  comic_id: string;
  cover_url: string;
  thumb_url: string | null;
  source: string;
  fetched_at: string;
};

async function readCached(comicId: string): Promise<CoverRow | null> {
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

async function writeCached(row: {
  comicId: string;
  series: string;
  issue: string;
  publisher: string;
  source: string;
  sourceId?: string;
  coverUrl: string;
  thumbUrl?: string;
}): Promise<void> {
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
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
  image?: {
    medium_url?: string;
    small_url?: string;
    thumb_url?: string;
    original_url?: string;
    super_url?: string;
  };
  volume?: { name?: string };
};

async function searchComicVine(series: string, issue: string): Promise<VineIssue | null> {
  const key = apiKey();
  if (!key) return null;
  const num = issueNumber(issue);
  const q = num ? `${series} ${num}` : series;
  const url = new URL("https://comicvine.gamespot.com/api/search/");
  url.searchParams.set("api_key", key);
  url.searchParams.set("format", "json");
  url.searchParams.set("resources", "issue");
  url.searchParams.set("query", q);
  url.searchParams.set("limit", "10");
  url.searchParams.set("field_list", "id,name,issue_number,image,volume");

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
  const seriesLower = series.toLowerCase();
  const exact = results.find((r) => {
    const vol = (r.volume?.name ?? "").toLowerCase();
    const iss = String(r.issue_number ?? "").toLowerCase();
    return iss === want && (vol.includes(seriesLower.split("(")[0]!.trim()) || seriesLower.includes(vol.slice(0, 12)));
  });
  if (exact?.image) return exact;

  const byIssue = results.find((r) => String(r.issue_number ?? "").toLowerCase() === want && r.image);
  return byIssue ?? results.find((r) => r.image) ?? null;
}

function pickUrl(issue: VineIssue): { cover?: string; thumb?: string } {
  const img = issue.image;
  if (!img) return {};
  const cover = img.super_url || img.medium_url || img.original_url || img.small_url;
  const thumb = img.thumb_url || img.small_url || img.medium_url;
  return { cover, thumb };
}

export const getComicCover = createServerFn({ method: "POST" })
  .validator((data: unknown) => Input.parse(data))
  .handler(async ({ data }): Promise<ComicCoverResult> => {
    if (!data.force) {
      const cached = await readCached(data.comicId);
      if (cached?.cover_url) {
        return {
          status: "ok",
          coverUrl: cached.cover_url,
          thumbUrl: cached.thumb_url ?? undefined,
          source: cached.source,
        };
      }
    }

    if (!apiKey()) {
      return { status: "no_key", error: "Set COMICVINE_API_KEY for real cover lookup." };
    }

    try {
      const hit = await searchComicVine(data.series, data.issue);
      if (!hit) return { status: "missing" };
      const { cover, thumb } = pickUrl(hit);
      if (!cover) return { status: "missing" };

      await writeCached({
        comicId: data.comicId,
        series: data.series,
        issue: data.issue,
        publisher: data.publisher ?? "",
        source: "comicvine",
        sourceId: hit.id != null ? String(hit.id) : undefined,
        coverUrl: cover,
        thumbUrl: thumb,
      });

      return { status: "ok", coverUrl: cover, thumbUrl: thumb, source: "comicvine" };
    } catch (err) {
      return {
        status: "error",
        error: err instanceof Error ? err.message : "Cover lookup failed",
      };
    }
  });

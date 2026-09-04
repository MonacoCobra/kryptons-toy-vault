import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { estimateFromComps } from "@/lib/market";
import type { SoldComp } from "@/lib/types";

const Input = z.object({
  kind: z.enum(["figure", "comic"]),
  itemId: z.string().min(1).max(120),
  query: z.string().min(3).max(240),
  force: z.boolean().optional(),
});

export type EbayMarketResult = {
  comps: SoldComp[];
  estimate: number;
  status: "ok" | "error" | "unavailable";
  source: "ebay" | "cache" | "none";
  error?: string;
  fetchedAt?: string;
  query: string;
};

type CompRow = {
  item_key: string;
  fetched_at: string;
  comps: unknown;
  estimate: number;
  status: string;
  error: string | null;
  query: string;
};

type MemSlot = { key: string; result: EbayMarketResult; at: number };
const memRef = globalThis as typeof globalThis & { __kryptonEbayComps__?: MemSlot };

const CACHE_HOURS = 72;

function neonConfigured(): boolean {
  return Boolean(typeof process !== "undefined" && process.env.DATABASE_URL?.trim());
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

function str(value: unknown): string {
  return typeof value === "string" ? value.trim() : value == null ? "" : String(value).trim();
}

function num(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  const n = Number.parseFloat(str(value).replace(/[^0-9.]/g, ""));
  return Number.isFinite(n) ? n : null;
}

function dateish(value: unknown): string {
  const s = str(value);
  const iso = s.match(/(\d{4}-\d{2}-\d{2})/);
  if (iso) return iso[1]!;
  const d = new Date(s);
  if (!Number.isNaN(d.getTime())) return d.toISOString().slice(0, 10);
  return new Date().toISOString().slice(0, 10);
}

function extractJson(text: string): { listings?: unknown[] } {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const raw = fenced?.[1] ?? text;
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start < 0 || end <= start) return {};
  try {
    return JSON.parse(raw.slice(start, end + 1)) as { listings?: unknown[] };
  } catch {
    return {};
  }
}

function outputText(payload: { output?: unknown }): string {
  const output = payload.output;
  if (!Array.isArray(output)) return "";
  const chunks: string[] = [];
  for (const item of output) {
    if (!item || typeof item !== "object") continue;
    const rec = item as { type?: string; content?: unknown };
    if (rec.type !== "message") continue;
    if (!Array.isArray(rec.content)) continue;
    for (const part of rec.content) {
      if (part && typeof part === "object" && "text" in part) {
        const text = (part as { text?: unknown }).text;
        if (typeof text === "string") chunks.push(text);
      }
    }
  }
  return chunks.join("\n");
}

function normalizeListings(rows: unknown[]): SoldComp[] {
  const out: SoldComp[] = [];
  const seen = new Set<string>();
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const r = row as Record<string, unknown>;
    const price = num(r.price ?? r.soldPrice ?? r.amount);
    const title = str(r.title ?? r.name);
    if (price == null || price <= 0 || !title) continue;
    const date = dateish(r.date ?? r.soldDate ?? r.endDate);
    const key = `${title}|${price}|${date}`.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    const url = str(r.url ?? r.link);
    out.push({
      price: Math.round(price * 100) / 100,
      date,
      condition: str(r.condition) || "Sold",
      title,
      url: url.startsWith("http") ? url : undefined,
      source: "ebay",
    });
  }
  return out
    .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
    .slice(0, 5);
}

function stale(iso: string | undefined, hours: number): boolean {
  if (!iso) return true;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return true;
  return Date.now() - t > hours * 3600 * 1000;
}

async function readCached(itemKey: string): Promise<EbayMarketResult | null> {
  if (!neonConfigured()) return null;
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    const rows = await sql.query<CompRow>(
      "select item_key, fetched_at, comps, estimate, status, error, query from market_comps where item_key = $1",
      [itemKey],
    );
    const row = rows[0];
    if (!row) return null;
    const comps = asArray(row.comps) as SoldComp[];
    return {
      comps,
      estimate: Number(row.estimate) || estimateFromComps(comps),
      status: row.status === "ok" && comps.length ? "ok" : "error",
      source: "cache",
      error: row.error ?? undefined,
      fetchedAt: row.fetched_at,
      query: row.query,
    };
  } catch {
    return null;
  }
}

async function writeCached(itemKey: string, kind: string, query: string, result: EbayMarketResult): Promise<void> {
  if (!neonConfigured()) return;
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    await sql.query(
      `insert into market_comps (item_key, kind, query, fetched_at, comps, estimate, status, error)
       values ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
       on conflict (item_key) do update set
         kind = excluded.kind,
         query = excluded.query,
         fetched_at = excluded.fetched_at,
         comps = excluded.comps,
         estimate = excluded.estimate,
         status = excluded.status,
         error = excluded.error`,
      [
        itemKey,
        kind,
        query,
        result.fetchedAt ?? new Date().toISOString(),
        JSON.stringify(result.comps),
        result.estimate,
        result.status,
        result.error ?? null,
      ],
    );
  } catch {
    /* cache is best-effort */
  }
}

async function ingestEbaySold(query: string): Promise<EbayMarketResult> {
  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    return {
      comps: [],
      estimate: 0,
      status: "unavailable",
      source: "none",
      error: "unavailable",
      query,
    };
  }

  const soldUrl = `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(query)}&LH_Sold=1&LH_Complete=1&_sop=13`;
  const body = {
    model: "grok-4.5",
    max_tool_calls: 3,
    tools: [
      {
        type: "web_search",
        filters: {
          allowed_domains: ["ebay.com"],
        },
      },
    ],
    input: [
      {
        role: "user",
        content: `Open this eBay completed/sold search and extract the 5 MOST RECENT matching SOLD listings only. Do not invent listings.

${soldUrl}

Search query: ${query}

Return ONLY JSON:
{"listings":[{"title":"","price":0,"date":"YYYY-MM-DD","condition":"","url":"https://www.ebay.com/..."}]}

Rules:
- Only sold/completed prices (not active asks).
- Most recent first; max 5.
- Skip lots/bundles that mix unrelated items, and skip obvious mismatches to the query.
- Price is the sold amount in USD (number).
- If fewer than 5 exist, return what you find.`,
      },
    ],
  };

  const res = await fetch("https://api.x.ai/v1/responses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(90_000),
  });

  if (!res.ok) {
    return {
      comps: [],
      estimate: 0,
      status: "error",
      source: "none",
      error: `ebay ingest ${res.status}`,
      query,
    };
  }

  const payload = (await res.json()) as { output?: unknown };
  const parsed = extractJson(outputText(payload));
  const comps = normalizeListings(parsed.listings ?? []);
  const estimate = estimateFromComps(comps);
  return {
    comps,
    estimate,
    status: comps.length ? "ok" : "error",
    source: comps.length ? "ebay" : "none",
    error: comps.length ? undefined : "empty",
    fetchedAt: new Date().toISOString(),
    query,
  };
}

export function figureEbayQuery(figure: {
  name: string;
  subtitle: string;
  line: string;
  exclusive?: string;
}): string {
  return [figure.line, figure.name, figure.subtitle, figure.exclusive]
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

export function comicEbayQuery(comic: {
  series: string;
  issue: string;
  publisher: string;
  variant?: string;
}): string {
  const variant = comic.variant ? ` ${comic.variant}` : "";
  return `${comic.series} ${comic.issue}${variant} ${comic.publisher} comic`
    .replace(/\s+/g, " ")
    .trim();
}

export const getEbayMarket = createServerFn({ method: "POST" })
  .validator((data: unknown) => Input.parse(data))
  .handler(async ({ data }): Promise<EbayMarketResult> => {
    const itemKey = `${data.kind}:${data.itemId}`;
    const mem = memRef.__kryptonEbayComps__;
    if (
      mem &&
      mem.key === itemKey &&
      !data.force &&
      mem.result.status === "ok" &&
      mem.result.comps.length &&
      Date.now() - mem.at < CACHE_HOURS * 3600 * 1000
    ) {
      return mem.result;
    }

    const cached = await readCached(itemKey);
    if (
      cached &&
      !data.force &&
      cached.status === "ok" &&
      cached.comps.length &&
      !stale(cached.fetchedAt, CACHE_HOURS)
    ) {
      memRef.__kryptonEbayComps__ = { key: itemKey, result: cached, at: Date.now() };
      return cached;
    }

    try {
      const live = await ingestEbaySold(data.query);
      if (live.status !== "ok" && cached?.comps.length) {
        return cached;
      }
      await writeCached(itemKey, data.kind, data.query, live);
      memRef.__kryptonEbayComps__ = { key: itemKey, result: live, at: Date.now() };
      return live;
    } catch (err) {
      if (cached?.comps.length) return cached;
      return {
        comps: [],
        estimate: 0,
        status: "error",
        source: "none",
        error: err instanceof Error ? err.message : "ebay fetch failed",
        query: data.query,
      };
    }
  });

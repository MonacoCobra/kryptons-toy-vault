/**
 * Server function: real eBay sold comps from SoldComps for ONE figure, on detail-page
 * open. The API key (env SOLDCOMPS_API_KEY) never leaves the server.
 *
 * Budget rules (free plan = 100 searches/month):
 *   - repo cache (src/data/market-comps.json) or DB cache younger than 30 days → no call
 *   - live calls need DATABASE_URL (so results persist) and the key
 *   - stop at x-usage-remaining ≤ 10 until the reset date; at most 5 calls per UTC day
 *   - failed/insufficient lookups are cached too (30 days; transport errors 1 day)
 */
import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { cachedFigureComps } from "@/lib/market-comps-cache";
import {
  BUDGET_FLOOR,
  CACHE_DAYS,
  buildFigureSoldComps,
  cacheAgeDays,
  figureKeyword,
  soldCompsRequestUrl,
  type FigureSoldComps,
  type SoldCompsResponse,
} from "@/lib/soldcomps";

const Input = z.object({
  id: z.string().min(1).max(160),
  name: z.string().min(1).max(240),
  line: z.string().min(1).max(160),
  subtitle: z.string().max(240).optional(),
  scale: z.string().max(60).optional(),
});

export type SoldCompsLookup = {
  result: FigureSoldComps | null;
  /** Why no live lookup happened (when result is null or stale). */
  note?: "not-configured" | "budget" | "daily-cap" | "error";
};

const DAILY_MAX = 5;
const ERROR_RETRY_DAYS = 1;
const BUDGET_KEY = "soldcomps:budget";

type Budget = { remaining?: number; resetAt?: string; day?: string; dayCount?: number };

function liveConfigured(): boolean {
  return Boolean(process.env.SOLDCOMPS_API_KEY?.trim() && process.env.DATABASE_URL?.trim());
}

async function sql() {
  const { getSql } = await import("@/lib/db");
  return getSql();
}

async function readRow(itemKey: string): Promise<unknown | null> {
  const db = await sql();
  const rows = await db.query<{ comps: unknown }>(
    "select comps from market_comps where item_key = $1",
    [itemKey],
  );
  const raw = rows[0]?.comps;
  if (raw == null) return null;
  return typeof raw === "string" ? JSON.parse(raw) : raw;
}

async function writeRow(itemKey: string, kind: string, query: string, payload: unknown, estimate: number, status: string) {
  const db = await sql();
  await db.query(
    `insert into market_comps (item_key, kind, query, fetched_at, comps, estimate, status, error)
     values ($1, $2, $3, now(), $4::jsonb, $5, $6, null)
     on conflict (item_key) do update set kind = excluded.kind, query = excluded.query,
       fetched_at = excluded.fetched_at, comps = excluded.comps, estimate = excluded.estimate,
       status = excluded.status, error = null`,
    [itemKey, kind, query, JSON.stringify(payload), estimate, status],
  );
}

function fresh(row: FigureSoldComps | null | undefined): boolean {
  if (!row) return false;
  const maxAge = row.status === "error" ? ERROR_RETRY_DAYS : CACHE_DAYS;
  return cacheAgeDays(row.fetchedAt) < maxAge;
}

export const getFigureSoldComps = createServerFn({ method: "POST" })
  .validator((data: unknown) => Input.parse(data))
  .handler(async ({ data }): Promise<SoldCompsLookup> => {
    const seed = cachedFigureComps(data.id) ?? null;
    if (fresh(seed)) return { result: seed };
    if (!liveConfigured()) return { result: seed, note: "not-configured" };

    const itemKey = `soldcomps:figure:${data.id}`;
    try {
      const dbRow = (await readRow(itemKey)) as FigureSoldComps | null;
      if (fresh(dbRow)) return { result: dbRow };
      const stale = dbRow ?? seed;

      const today = new Date().toISOString().slice(0, 10);
      const budget = ((await readRow(BUDGET_KEY)) as Budget | null) ?? {};
      const resetAt = Date.parse(budget.resetAt ?? "");
      const resetPassed = Number.isFinite(resetAt) && Date.now() > resetAt;
      if (budget.remaining != null && budget.remaining <= BUDGET_FLOOR && !resetPassed) {
        return { result: stale, note: "budget" };
      }
      const dayCount = budget.day === today ? budget.dayCount ?? 0 : 0;
      if (dayCount >= DAILY_MAX) return { result: stale, note: "daily-cap" };

      const keyword = figureKeyword(data);
      // Count the call before making it so concurrent opens can't overshoot the cap.
      await writeRow(BUDGET_KEY, "meta", "soldcomps", { ...budget, day: today, dayCount: dayCount + 1 }, 0, "meta");
      const res = await fetch(soldCompsRequestUrl(keyword), {
        headers: { Authorization: `Bearer ${process.env.SOLDCOMPS_API_KEY!.trim()}` },
        signal: AbortSignal.timeout(45_000),
      });
      const remaining = Number(res.headers.get("x-usage-remaining"));
      const nextBudget: Budget = {
        ...budget,
        day: today,
        dayCount: dayCount + 1,
        remaining: Number.isFinite(remaining) ? remaining : budget.remaining,
        resetAt: res.headers.get("x-usage-reset") ?? budget.resetAt,
      };
      await writeRow(BUDGET_KEY, "meta", "soldcomps", nextBudget, 0, "meta");

      if (!res.ok) {
        const failed: FigureSoldComps = {
          figureId: data.id,
          source: "soldcomps",
          keyword,
          fetchedAt: new Date().toISOString(),
          status: "error",
          estimate: null,
          comps: [],
          passing: 0,
          totalItems: 0,
          bestOfferInAvg: 0,
          conditionBasis: "none",
          error: `http ${res.status}`,
        };
        await writeRow(itemKey, "figure", keyword, failed, 0, "error");
        console.warn(`[soldcomps] ${data.id}: http ${res.status}`);
        return { result: stale?.status === "ok" ? stale : failed, note: "error" };
      }
      const body = (await res.json()) as SoldCompsResponse;
      const out = buildFigureSoldComps(data, keyword, body, new Date().toISOString());
      await writeRow(itemKey, "figure", keyword, out, out.estimate ?? 0, out.status);
      return { result: out };
    } catch (err) {
      console.warn(`[soldcomps] ${data.id}: ${err instanceof Error ? err.message : "lookup failed"}`);
      return { result: seed, note: "error" };
    }
  });

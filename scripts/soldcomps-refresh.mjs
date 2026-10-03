#!/usr/bin/env node
/**
 * Box-side SoldComps refresh → src/data/market-comps.json (public, key-free cache the
 * app reads for figure values). Budget-conscious: explicit ids only (max 5/run, never a
 * catalog loop), skips entries younger than 30 days, stops at x-usage-remaining ≤ 10.
 *
 *   node --experimental-strip-types scripts/soldcomps-refresh.mjs --id <figureId> [--id …]
 *   node --experimental-strip-types scripts/soldcomps-refresh.mjs --id <figureId> --seed-file saved.json
 *       (seed from a saved SoldComps response — no API call)
 *
 * The key comes from env SOLDCOMPS_API_KEY and is never printed or written.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  BUDGET_FLOOR,
  CACHE_DAYS,
  buildFigureSoldComps,
  cacheAgeDays,
  figureKeyword,
  soldCompsRequestUrl,
} from "../src/lib/soldcomps.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CACHE = join(ROOT, "src/data/market-comps.json");
const ONESHOT = join(ROOT, "src/data/figure-archive/oneshot.json");
const MAX_IDS = 5;

function parseArgs(argv) {
  const out = { ids: [], seedFile: null, force: false, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--id") out.ids.push(argv[++i]);
    else if (a === "--seed-file") out.seedFile = argv[++i];
    else if (a === "--force") out.force = true;
    else if (a === "--dry-run") out.dryRun = true;
    else throw new Error(`unknown arg ${a}`);
  }
  return out;
}

function loadCache() {
  if (!existsSync(CACHE)) return { version: 1, source: "soldcomps", budget: {}, figures: {} };
  const doc = JSON.parse(readFileSync(CACHE, "utf8"));
  doc.budget ??= {};
  doc.figures ??= {};
  return doc;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.ids.length) throw new Error("pass --id <figureId> (explicit ids only)");
  if (args.ids.length > MAX_IDS) throw new Error(`max ${MAX_IDS} ids per run`);
  if (args.seedFile && args.ids.length !== 1) throw new Error("--seed-file needs exactly one --id");
  const rows = JSON.parse(readFileSync(ONESHOT, "utf8"));
  const byId = new Map(rows.map((r) => [r.id, r]));
  const cache = loadCache();
  let calls = 0;

  for (const id of args.ids) {
    const fig = byId.get(id);
    if (!fig) {
      console.log(`[skip] ${id}: not in oneshot`);
      continue;
    }
    const keyword = figureKeyword(fig);
    const prev = cache.figures[id];
    if (!args.force && !args.seedFile && prev && cacheAgeDays(prev.fetchedAt) < CACHE_DAYS) {
      console.log(`[cached] ${id}: ${prev.status} est=${prev.estimate} (${prev.fetchedAt})`);
      continue;
    }
    let res;
    let fetchedAt;
    if (args.seedFile) {
      res = JSON.parse(readFileSync(args.seedFile, "utf8"));
      fetchedAt = res.items?.map((x) => x.scrapedAt).filter(Boolean).sort().pop() ?? new Date().toISOString();
      if (res.keyword && res.keyword !== keyword) {
        console.log(`[note] seed keyword "${res.keyword}" vs built "${keyword}"`);
      }
    } else {
      const key = process.env.SOLDCOMPS_API_KEY;
      if (!key) throw new Error("SOLDCOMPS_API_KEY not set");
      const rem = cache.budget.remaining;
      const resetAt = Date.parse(cache.budget.resetAt || "");
      if (rem != null && rem <= BUDGET_FLOOR && !(Number.isFinite(resetAt) && Date.now() > resetAt)) {
        console.log(`[budget] stop: remaining=${rem} ≤ ${BUDGET_FLOOR} until ${cache.budget.resetAt}`);
        break;
      }
      if (args.dryRun) {
        console.log(`[dry-run] would query "${keyword}" for ${id}`);
        continue;
      }
      const r = await fetch(soldCompsRequestUrl(keyword), {
        headers: { Authorization: `Bearer ${key}` },
        signal: AbortSignal.timeout(60_000),
      });
      calls++;
      const remaining = Number(r.headers.get("x-usage-remaining"));
      if (Number.isFinite(remaining)) cache.budget.remaining = remaining;
      const reset = r.headers.get("x-usage-reset");
      if (reset) cache.budget.resetAt = reset;
      cache.budget.checkedAt = new Date().toISOString();
      if (!r.ok) {
        console.log(`[error] ${id}: HTTP ${r.status}`);
        continue;
      }
      res = await r.json();
      fetchedAt = new Date().toISOString();
    }
    const out = buildFigureSoldComps(fig, keyword, res, fetchedAt);
    cache.figures[id] = out;
    console.log(
      `[${out.status}] ${id}: "${keyword}" passing=${out.passing}/${out.totalItems} est=${out.estimate} basis=${out.conditionBasis} bestOffer=${out.bestOfferInAvg}`,
    );
  }
  if (!args.dryRun) writeFileSync(CACHE, `${JSON.stringify(cache, null, 2)}\n`);
  console.log(`api calls this run: ${calls}; last known remaining: ${cache.budget.remaining ?? "unknown"}`);
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});

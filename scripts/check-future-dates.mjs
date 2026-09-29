#!/usr/bin/env node
// Release-date guard for the figure catalog (date audit 2026-09-28).
//
// ERROR  releaseDate more than MAX_MONTHS (24) after today — the 2027-2032
//        placeholder class that bbts_wave5_data.json injected (commit 8b3d20ec).
// WARN   future releaseDate from a source that is not an announcement feed.
//
// Mode: warn-only by default while the date clean-up (phases 3-4) is running.
// Pass --strict (or FIGURE_DATE_STRICT=1) to exit non-zero on errors.
// Allowlist ids in scripts/future-date-allowlist.json (JSON array).
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

export const MAX_MONTHS = 24;
const LEGIT_SOURCES = ["toyark", "preorder", "announce", "inject-shelby", "curated-mpg"];

export function horizon(today = new Date(), months = MAX_MONTHS) {
  const d = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + months, today.getUTCDate()));
  return d.toISOString().slice(0, 10);
}

export function checkRows(rows, { today = new Date(), allow = new Set() } = {}) {
  const now = today.toISOString().slice(0, 10);
  const hard = horizon(today);
  const errors = [];
  const warnings = [];
  for (const r of rows) {
    const d = r.releaseDate || "";
    if (!d || allow.has(r.id)) continue;
    if (d > hard) errors.push(`${r.id}: releaseDate ${d} is more than ${MAX_MONTHS} months out`);
    else if (d > now && !LEGIT_SOURCES.some((s) => String(r.source || "").includes(s)))
      warnings.push(`${r.id}: future releaseDate ${d} from non-announcement source ${r.source}`);
  }
  return { errors, warnings };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const strict = args.includes("--strict") || process.env.FIGURE_DATE_STRICT === "1";
  const file = args.find((a) => !a.startsWith("--")) || "src/data/figure-archive/oneshot.json";
  const allowFile = "scripts/future-date-allowlist.json";
  const allow = new Set(existsSync(allowFile) ? JSON.parse(readFileSync(allowFile, "utf8")) : []);
  const { errors, warnings } = checkRows(JSON.parse(readFileSync(file, "utf8")), { allow });
  for (const e of errors) console.log(`${strict ? "ERROR" : "WARN(strict:error)"} ${e}`);
  for (const w of warnings) console.log(`WARN  ${w}`);
  console.log(`${errors.length} beyond-horizon, ${warnings.length} warnings (${strict ? "strict" : "warn-only"})`);
  process.exit(strict && errors.length ? 1 : 0);
}

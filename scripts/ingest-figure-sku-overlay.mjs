#!/usr/bin/env node
/**
 * Node helper for scripts/ingest-figure-sku-overlay.py
 * Reads { figures: [...] } JSON on stdin; upserts into figure_catalog.
 * Skip if SKU / id / name|subtitle|line|company already in baked oneshot+seed or overlay.
 *
 * Requires DATABASE_URL. Applies 0006_figure_catalog.sql if table missing.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const RELEASE_FLOOR = "1980-01-01";

function normSku(sku) {
  const s = String(sku ?? "").trim();
  return s ? s.toLowerCase() : undefined;
}

function nameKey(f) {
  return `${f.name}|${f.subtitle}|${f.line}|${f.company}`.toLowerCase();
}

function loadBakedIndex() {
  const skus = new Set();
  const ids = new Set();
  const keys = new Set();

  const oneshotPath = join(ROOT, "src/data/figure-archive/oneshot.json");
  try {
    const rows = JSON.parse(readFileSync(oneshotPath, "utf8"));
    for (const f of rows) {
      ids.add(f.id);
      keys.add(nameKey(f));
      const s = normSku(f.sku);
      if (s) skus.add(s);
    }
  } catch (err) {
    console.error("[ingest-figure-overlay] warn: oneshot.json:", err.message);
  }

  // Seed tuples in figures.ts: ["id", "name", "subtitle", "line", "company", ...]
  try {
    const src = readFileSync(join(ROOT, "src/data/figures.ts"), "utf8");
    const re =
      /\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]+)",\s*"(figure|kit)"/g;
    let m;
    while ((m = re.exec(src))) {
      ids.add(m[1]);
      keys.add(`${m[2]}|${m[3]}|${m[4]}|${m[5]}`.toLowerCase());
    }
    // optional sku in trailing { sku: "..." }
    const skuRe = /\["([^"]+)"[\s\S]*?\{\s*sku:\s*"([^"]+)"/g;
    while ((m = skuRe.exec(src))) {
      const s = normSku(m[2]);
      if (s) skus.add(s);
    }
  } catch (err) {
    console.error("[ingest-figure-overlay] warn: figures.ts seed:", err.message);
  }

  return { skus, ids, keys };
}

function inIndex(f, idx) {
  const s = normSku(f.sku);
  if (s && idx.skus.has(s)) return true;
  if (idx.ids.has(f.id)) return true;
  if (idx.keys.has(nameKey(f))) return true;
  return false;
}

function validate(f) {
  if (!f?.id || !f?.name || !f?.line || !f?.company || !f?.sku || !f?.releaseDate) return null;
  if (f.kind !== "figure" && f.kind !== "kit") return null;
  if (String(f.releaseDate) < RELEASE_FLOOR) return null;
  return f;
}

async function ensureTable(client) {
  const mig = join(ROOT, "migrations/0006_figure_catalog.sql");
  const sql = readFileSync(mig, "utf8");
  await client.query(sql);
}

async function main() {
  const databaseUrl = process.env.DATABASE_URL?.trim();
  if (!databaseUrl) {
    console.error("[ingest-figure-overlay] DATABASE_URL required");
    process.exit(3);
  }

  const stdin = readFileSync(0, "utf8");
  const payload = JSON.parse(stdin || "{}");
  const figures = Array.isArray(payload) ? payload : payload.figures ?? [];
  const baked = loadBakedIndex();

  const pool = new pg.Pool({ connectionString: databaseUrl, max: 1 });
  const client = await pool.connect();
  const result = {
    inserted: 0,
    skippedBaked: 0,
    skippedOverlay: 0,
    skippedInvalid: 0,
    total: figures.length,
  };

  try {
    await ensureTable(client);

    const existing = (
      await client.query("select id, name, subtitle, line, company, sku from figure_catalog")
    ).rows;
    const overlayIdx = { skus: new Set(), ids: new Set(), keys: new Set() };
    for (const row of existing) {
      overlayIdx.ids.add(row.id);
      overlayIdx.keys.add(nameKey(row));
      const s = normSku(row.sku);
      if (s) overlayIdx.skus.add(s);
    }

    for (const raw of figures) {
      const f = validate(raw);
      if (!f) {
        result.skippedInvalid += 1;
        continue;
      }
      if (inIndex(f, baked)) {
        result.skippedBaked += 1;
        continue;
      }
      if (inIndex(f, overlayIdx)) {
        result.skippedOverlay += 1;
        continue;
      }

      const tags = Array.isArray(f.tags) ? f.tags : [];
      const res = await client.query(
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
          f.subtitle ?? "",
          f.line,
          f.company,
          f.kind || "figure",
          f.releaseDate,
          Number(f.msrp) || 24.99,
          f.scale || '6"',
          Number(f.demand) || 1,
          JSON.stringify(tags),
          f.sku,
          f.exclusive ?? null,
          f.imageUrl ?? null,
          f.source ?? null,
        ],
      );
      if (res.rowCount) {
        result.inserted += 1;
        overlayIdx.ids.add(f.id);
        overlayIdx.keys.add(nameKey(f));
        const s = normSku(f.sku);
        if (s) overlayIdx.skus.add(s);
      } else {
        result.skippedOverlay += 1;
      }
    }
  } finally {
    client.release();
    await pool.end();
  }

  console.log(JSON.stringify(result));
}

main().catch((err) => {
  console.error("[ingest-figure-overlay]", err.message || err);
  process.exit(1);
});

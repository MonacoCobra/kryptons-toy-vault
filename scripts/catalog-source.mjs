/**
 * Inputs for the build-time catalog shards.
 *
 * Comic rows and the UPC map come from the sharded loaders in
 * src/data/SHARDING.md — not from comics.ts line scanning and not from a
 * filename search. comics.ts is only the app-facing loader.
 *
 *   src/data/comics/load.ts            loadComicRows()
 *   src/data/comic-upc-map/load.ts     UPC_MAP
 *
 * Figures still come from src/data/figures.ts, which reads the single-file
 * oneshot archive. The product SKU index is sharded too; its directory is
 * part of the freshness check even though this script does not merge it.
 */
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

/** Shard datasets from src/data/SHARDING.md. */
const SHARD_DIRS = [
  "src/data/comics",
  "src/data/comic-upc-map",
  "src/data/figure-archive/product-sku-index",
];

/** Single files that still feed the derived catalog. Each is well under 40 MB. */
const SINGLE_FILES = [
  "src/data/comics.ts",
  "src/data/comic-cover-urls.json",
  "src/data/figures.ts",
  "src/data/figure-archive/oneshot.json",
  "src/data/figure-image-urls.json",
  "src/data/figure-sku-aliases.json",
  "src/data/figure-sku-map.json",
  "scripts/shard-catalog.mjs",
  "scripts/catalog-source.mjs",
  "src/lib/comic-format.ts",
  "src/lib/comic-series.ts",
  "src/lib/comic-variants.ts",
  "src/lib/figure-property.ts",
  "src/lib/catalog-shard.ts",
];

function pal(s) {
  const parts = String(s ?? "")
    .split(",")
    .map((p) => `#${String(p).replace(/^#/, "")}`);
  return [parts[0] ?? "#1e3a8a", parts[1] ?? "#e30613", parts[2] ?? "#f8fafc"];
}

function people(s) {
  return String(s ?? "")
    .split(",")
    .map((w) => w.trim())
    .filter(Boolean);
}

function newestUnder(absDir) {
  if (!fs.existsSync(absDir)) return 0;
  let max = 0;
  const stack = [absDir];
  while (stack.length) {
    const dir = stack.pop();
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      if (ent.name === "node_modules" || ent.name === ".git" || ent.name === ".lock") continue;
      const full = path.join(dir, ent.name);
      if (ent.isDirectory()) {
        stack.push(full);
        continue;
      }
      try {
        const m = fs.statSync(full).mtimeMs;
        if (m > max) max = m;
      } catch {
        /* file disappeared mid-walk */
      }
    }
  }
  return max;
}

function newestOf(root, rels) {
  let max = 0;
  for (const rel of rels) {
    try {
      const m = fs.statSync(path.join(root, rel)).mtimeMs;
      if (m > max) max = m;
    } catch {
      /* a shard dir is required; a missing single file fails later at read */
    }
  }
  return max;
}

/**
 * True when public/catalog/manifest.json is newer than the shard directories
 * and the remaining single-file inputs.
 */
export async function catalogInputsAreFresh(root, manifestPath) {
  if (process.env.FORCE_CATALOG_SHARD === "1") return false;
  if (!fs.existsSync(manifestPath)) return false;
  const built = fs.statSync(manifestPath).mtimeMs;
  let newest = newestOf(root, SINGLE_FILES);
  for (const rel of SHARD_DIRS) {
    const abs = path.join(root, rel);
    if (!fs.existsSync(path.join(abs, "manifest.json"))) {
      throw new Error(`[catalog-source] missing shard manifest at ${rel}/manifest.json`);
    }
    newest = Math.max(newest, newestUnder(abs));
  }
  return newest <= built;
}

function mapComicRow(row, upcMap, coverUrls) {
  const [id, series, issue, publisher, coverDate, writers, artists, description, msrp, format, demand, key, palette, extra] =
    row;
  const mapped = upcMap[id];
  const comic = {
    id,
    series,
    issue,
    publisher,
    coverDate,
    writers: people(writers),
    artists: people(artists),
    description: description ?? "",
    msrp,
    format,
    demand,
    key: key === 1,
    palette: pal(palette),
  };
  if (extra?.streetDate) comic.streetDate = extra.streetDate;
  if (extra?.variant) comic.variant = extra.variant;
  const upc = extra?.upc ?? mapped?.upc;
  if (upc) comic.upc = upc;
  const cover = extra?.cover ?? mapped?.coverUrl ?? coverUrls[id];
  if (cover) comic.cover = cover;
  return comic;
}

export async function loadComicInputs(root, normalizeComicFormat) {
  const comicsUrl = pathToFileURL(path.join(root, "src/data/comics/load.ts")).href;
  const upcUrl = pathToFileURL(path.join(root, "src/data/comic-upc-map/load.ts")).href;
  const { loadComicRows } = await import(comicsUrl);
  const { UPC_MAP } = await import(upcUrl);
  if (typeof loadComicRows !== "function") {
    throw new Error("[catalog-source] src/data/comics/load.ts did not export loadComicRows");
  }
  if (!UPC_MAP || typeof UPC_MAP !== "object") {
    throw new Error("[catalog-source] src/data/comic-upc-map/load.ts did not export UPC_MAP");
  }
  const coverUrls = JSON.parse(fs.readFileSync(path.join(root, "src/data/comic-cover-urls.json"), "utf8"));
  const rows = loadComicRows();
  if (!Array.isArray(rows)) throw new Error("[catalog-source] loadComicRows() did not return an array");
  console.log(`[catalog-source] ${rows.length} comic rows from src/data/comics/load.ts`);
  const comics = rows.map((row) => {
    const comic = mapComicRow(row, UPC_MAP, coverUrls);
    comic.format = normalizeComicFormat(comic.format);
    return comic;
  });
  return { comics, upcMap: UPC_MAP };
}

export async function loadFigureInputs(root) {
  const figuresUrl = pathToFileURL(path.join(root, "src/data/figures.ts")).href;
  const { FIGURES } = await import(figuresUrl);
  if (!Array.isArray(FIGURES)) throw new Error("[catalog-source] src/data/figures.ts did not export FIGURES");
  console.log(`[catalog-source] ${FIGURES.length} figures from src/data/figures.ts`);
  const aliasFile = path.join(root, "src/data/figure-sku-aliases.json");
  const aliasDoc = JSON.parse(fs.readFileSync(aliasFile, "utf8"));
  return { figures: FIGURES, aliasDoc };
}

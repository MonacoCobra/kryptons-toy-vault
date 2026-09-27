/**
 * Inputs for the build-time catalog shards.
 *
 * Another change is splitting the oversized ingest files (comics.ts,
 * comic-upc-map.json, and any other large src/data file) into shards behind
 * a shared loader. This module is the only place that opens those files.
 *
 * When that loader is in the tree it wins. A loader is any small module under
 * src/data or src/lib whose filename contains "loader" (or catalog-source /
 * data-store / source-store) and that exports one or more of:
 *
 *   loadComics() | readComics() | getComics() | COMICS
 *   loadUpcMap() | readUpcMap() | getUpcMap() | upcMap | UPC_MAP
 *   loadFigures() | readFigures() | FIGURES
 *   loadFigureAliases() | readFigureAliases() | figureAliases
 *   sourceRoots: string[]   // extra directories, relative to the repo root
 *
 * Until that module exists, the fallbacks below read the current single files.
 * Do not add a second shard format here — rebase onto their loader instead.
 */
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { pathToFileURL } from "node:url";

const PIPELINE_FILES = [
  "scripts/shard-catalog.mjs",
  "scripts/catalog-source.mjs",
  "src/lib/comic-format.ts",
  "src/lib/comic-series.ts",
  "src/lib/comic-variants.ts",
  "src/lib/figure-property.ts",
  "src/lib/catalog-shard.ts",
];

const LOADER_NAME = /loader|catalog-source|data-store|source-store/i;

function pickFn(mod, names) {
  for (const name of names) {
    if (typeof mod?.[name] === "function") return mod[name].bind(mod);
  }
  return null;
}

function loaderCandidates(root) {
  const found = [];
  for (const dir of ["src/data", "src/lib"]) {
    const abs = path.join(root, dir);
    if (!fs.existsSync(abs)) continue;
    const stack = [abs];
    while (stack.length) {
      const current = stack.pop();
      for (const ent of fs.readdirSync(current, { withFileTypes: true })) {
        const full = path.join(current, ent.name);
        if (ent.isDirectory()) {
          if (ent.name === "node_modules") continue;
          stack.push(full);
          continue;
        }
        if (!/\.(ts|mjs|js)$/.test(ent.name) || /\.test\./.test(ent.name) || ent.name.endsWith(".d.ts")) continue;
        if (!LOADER_NAME.test(ent.name)) continue;
        try {
          if (fs.statSync(full).size > 1_500_000) continue;
        } catch {
          continue;
        }
        found.push(full);
      }
    }
  }
  return found;
}

async function discoverLoader(root) {
  let best = null;
  let bestScore = 0;
  for (const full of loaderCandidates(root)) {
    let mod;
    try {
      mod = await import(pathToFileURL(full).href);
    } catch (err) {
      console.warn(`[catalog-source] skipped ${path.relative(root, full)}: ${err?.message ?? err}`);
      continue;
    }
    const comics = pickFn(mod, ["loadComics", "readComics", "getComics", "loadCatalogComics"]);
    const upc = pickFn(mod, ["loadUpcMap", "readUpcMap", "getUpcMap", "loadComicUpcMap"]);
    const figures = pickFn(mod, ["loadFigures", "readFigures", "getFigures"]);
    const aliases = pickFn(mod, ["loadFigureAliases", "readFigureAliases", "getFigureAliases"]);
    const score = [comics, upc, figures, aliases].filter(Boolean).length;
    if (!score) continue;
    if (score > bestScore) {
      bestScore = score;
      best = { full, mod, comics, upc, figures, aliases };
    }
  }
  return best;
}

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

/** Rows are JS literals. The trailing extra is `{ key: "value" }`, not JSON. */
function parseComicRow(expr) {
  try {
    return JSON.parse(expr);
  } catch {
    const brace = expr.lastIndexOf(", {");
    if (brace < 0 || !expr.endsWith("]")) throw new Error("not a row");
    const head = expr.slice(0, brace);
    let obj = expr.slice(brace + 2, -1);
    obj = obj.replace(/([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:/g, '$1"$2":');
    return JSON.parse(`${head}, ${obj}]`);
  }
}

async function readComicsFile(root, normalizeComicFormat, coverUrls, upcMap) {
  const comics = [];
  let failures = 0;
  const stream = fs.createReadStream(path.join(root, "src/data/comics.ts"), { encoding: "utf8" });
  const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });
  let lineNo = 0;
  for await (const line of rl) {
    lineNo += 1;
    const trimmed = line.trim();
    if (!trimmed.startsWith("[")) continue;
    const expr = trimmed.endsWith(",") ? trimmed.slice(0, -1) : trimmed;
    let row;
    try {
      row = parseComicRow(expr);
    } catch {
      failures += 1;
      if (failures <= 5) console.error(`[catalog-source] unparsable comic line ${lineNo}: ${trimmed.slice(0, 180)}`);
      continue;
    }
    if (!Array.isArray(row) || row.length < 13) continue;
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
      format: normalizeComicFormat(format),
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
    comics.push(comic);
    if (comics.length % 50000 === 0) console.log(`[catalog-source] parsed ${comics.length} comics`);
  }
  if (failures) throw new Error(`[catalog-source] ${failures} comic rows failed to parse`);
  console.log(`[catalog-source] parsed ${comics.length} comics`);
  return comics;
}

function readJsonIfPresent(file) {
  if (!fs.existsSync(file)) return null;
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function newestUnder(absDir) {
  if (!fs.existsSync(absDir)) return 0;
  let max = 0;
  const stack = [absDir];
  while (stack.length) {
    const dir = stack.pop();
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      if (ent.name === "node_modules" || ent.name === ".git") continue;
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
      /* optional until the split lands */
    }
  }
  return max;
}

/**
 * True when public/catalog/manifest.json is newer than every ingest file
 * under src/data, the pipeline sources, and any sourceRoots the loader names.
 */
export async function catalogInputsAreFresh(root, manifestPath) {
  if (process.env.FORCE_CATALOG_SHARD === "1") return false;
  if (!fs.existsSync(manifestPath)) return false;
  const built = fs.statSync(manifestPath).mtimeMs;
  const loader = await discoverLoader(root);
  const roots = ["src/data"];
  if (loader) {
    const extra = loader.mod.sourceRoots ?? loader.mod.sourceFiles;
    if (Array.isArray(extra)) {
      for (const rel of extra) {
        if (typeof rel !== "string") continue;
        const abs = path.resolve(root, rel);
        try {
          if (fs.statSync(abs).isDirectory()) roots.push(path.relative(root, abs));
          else if (fs.statSync(abs).mtimeMs > built) return false;
        } catch {
          return false;
        }
      }
    }
  }
  let newest = newestOf(root, PIPELINE_FILES);
  for (const rel of roots) newest = Math.max(newest, newestUnder(path.join(root, rel)));
  return newest <= built;
}

export async function loadComicInputs(root, normalizeComicFormat) {
  const loader = await discoverLoader(root);
  const coverFile = path.join(root, "src/data/comic-cover-urls.json");
  const upcFile = path.join(root, "src/data/comic-upc-map.json");

  let upcMap = loader?.upc ? await loader.upc() : readJsonIfPresent(upcFile);
  if (!upcMap || typeof upcMap !== "object" || Array.isArray(upcMap)) {
    throw new Error(
      "[catalog-source] No UPC map. Export loadUpcMap() from the shared catalog loader, or keep src/data/comic-upc-map.json.",
    );
  }

  let comics;
  if (loader?.comics) {
    console.log(`[catalog-source] comics via ${path.relative(root, loader.full)}`);
    comics = await loader.comics();
    if (!Array.isArray(comics)) throw new Error("[catalog-source] catalog loader comics export was not an array");
  } else if (fs.existsSync(path.join(root, "src/data/comics.ts"))) {
    console.log("[catalog-source] comics via src/data/comics.ts (single file)");
    const coverUrls = readJsonIfPresent(coverFile) ?? {};
    comics = await readComicsFile(root, normalizeComicFormat, coverUrls, upcMap);
  } else {
    throw new Error(
      "[catalog-source] No comics source. Export loadComics() from the shared catalog loader, or keep src/data/comics.ts.",
    );
  }

  if (loader?.upc) console.log(`[catalog-source] upc map via ${path.relative(root, loader.full)}`);
  return { comics, upcMap };
}

export async function loadFigureInputs(root) {
  const loader = await discoverLoader(root);
  let figures;
  if (loader?.figures) {
    console.log(`[catalog-source] figures via ${path.relative(root, loader.full)}`);
    figures = await loader.figures();
  } else {
    console.log("[catalog-source] figures via src/data/figures.ts");
    figures = (await import(pathToFileURL(path.join(root, "src/data/figures.ts")).href)).FIGURES;
  }
  if (!Array.isArray(figures)) throw new Error("[catalog-source] figure catalog was not an array");

  let aliasDoc = loader?.aliases ? await loader.aliases() : readJsonIfPresent(path.join(root, "src/data/figure-sku-aliases.json"));
  if (!aliasDoc || typeof aliasDoc !== "object") aliasDoc = {};
  return { figures, aliasDoc };
}

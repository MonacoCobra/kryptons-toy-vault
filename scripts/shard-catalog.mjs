/**
 * Build-time catalog shards.
 *
 * Source of truth stays the ingest files. scripts/catalog-source.mjs is the
 * only reader: it uses the shared catalog loader when that module exists
 * (the upcoming source-file split) and otherwise the current single files.
 * This script only writes derived JSON under public/catalog.
 *
 * Run: node --max-old-space-size=6144 --import ./scripts/register-ts-paths.mjs --experimental-strip-types scripts/shard-catalog.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { catalogInputsAreFresh, loadComicInputs, loadFigureInputs } from "./catalog-source.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outFinal = path.join(root, "public/catalog");
const outStaging = path.join(root, "public/catalog-staging");
const lockDir = "/tmp/krypton-catalog-shard.lock";

const NOTEWORTHY_MS = 3 * 7 * 24 * 3600 * 1000;
const SEARCH_SHARDS = 8;
const DESC_CAP = 180;

function pidAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function withLock(fn) {
  for (let i = 0; i < 900; i++) {
    try {
      fs.mkdirSync(lockDir);
      fs.writeFileSync(path.join(lockDir, "pid"), String(process.pid));
      break;
    } catch {
      const pidFile = path.join(lockDir, "pid");
      let pid = 0;
      try {
        pid = Number(fs.readFileSync(pidFile, "utf8"));
      } catch {
        pid = 0;
      }
      if (!pid || !pidAlive(pid)) {
        fs.rmSync(lockDir, { recursive: true, force: true });
        continue;
      }
      if (i === 899) throw new Error("Timed out waiting for catalog shard lock");
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
  try {
    await fn();
  } finally {
    fs.rmSync(lockDir, { recursive: true, force: true });
  }
}

function slug(s) {
  return (
    String(s ?? "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "") || "item"
  );
}

let bytesWritten = 0;

async function writeJson(rel, data) {
  const full = path.join(outStaging, rel);
  await fs.promises.mkdir(path.dirname(full), { recursive: true });
  const body = JSON.stringify(data);
  bytesWritten += body.length;
  await fs.promises.writeFile(full, body);
}

async function pool(items, limit, fn) {
  let cursor = 0;
  async function worker() {
    while (cursor < items.length) {
      const idx = cursor++;
      await fn(items[idx], idx);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => worker()));
}

function slimSample(c) {
  if (!c) return undefined;
  return {
    id: c.id,
    series: c.series,
    issue: c.issue,
    publisher: c.publisher,
    coverDate: c.coverDate,
    streetDate: c.streetDate,
    writers: (c.writers ?? []).slice(0, 4),
    artists: (c.artists ?? []).slice(0, 4),
    description: "",
    msrp: c.msrp,
    format: c.format,
    variant: c.variant,
    upc: c.upc,
    demand: c.demand,
    key: c.key,
    palette: c.palette,
    cover: c.cover,
  };
}

/** Mirrors buildAliasToFigureId in src/data/figures.ts. */
function buildAliasToFigureId(doc) {
  const out = {};
  const rev = doc.aliasToFigureId;
  if (rev && typeof rev === "object") {
    for (const [code, fid] of Object.entries(rev)) {
      if (typeof fid === "string" && fid) out[code.toUpperCase()] = fid;
    }
  }
  const byFig = doc.aliasesByFigureId;
  if (byFig && typeof byFig === "object") {
    for (const [fid, codes] of Object.entries(byFig)) {
      if (!Array.isArray(codes)) continue;
      for (const c of codes) {
        const key = String(c).trim().toUpperCase();
        if (!key || key.startsWith("ID:")) continue;
        if (!out[key]) out[key] = fid;
      }
    }
  }
  if (!byFig) {
    for (const [k, v] of Object.entries(doc)) {
      if (k === "version" || k === "policy" || k === "updatedAt") continue;
      if (!Array.isArray(v)) continue;
      for (const c of v) {
        const key = String(c).trim().toUpperCase();
        if (!key || key.startsWith("ID:")) continue;
        if (!out[key]) out[key] = k;
      }
    }
  }
  return out;
}

function dateOf(c) {
  return c.streetDate || c.coverDate || "";
}

function uniquePath(used, base) {
  if (!used.has(base)) {
    used.add(base);
    return base;
  }
  let n = 2;
  while (used.has(`${base}-${n}`)) n += 1;
  const next = `${base}-${n}`;
  used.add(next);
  return next;
}

async function shardComics() {
  const { normalizeComicFormat, isCollectedComic, comicFormatLabel } = await import("../src/lib/comic-format.ts");
  const {
    assignSeriesRunYears,
    buildSeriesList,
    buildPublisherList,
    buildCollectedSeriesList,
    makeSeriesKey,
    makeCollectedSeriesKey,
  } = await import("../src/lib/comic-series.ts");
  const { comicFamilyKey } = await import("../src/lib/comic-variants.ts");
  const { shardId, comicBucketPath, upcBucketPath } = await import("../src/lib/catalog-shard.ts");

  const loaded = await loadComicInputs(root, normalizeComicFormat);
  const comics = loaded.comics;
  let upcMap = loaded.upcMap;

  const upcGroups = new Map();
  for (const [id, entry] of Object.entries(upcMap)) {
    const rel = upcBucketPath(id);
    let bucket = upcGroups.get(rel);
    if (!bucket) {
      bucket = {};
      upcGroups.set(rel, bucket);
    }
    bucket[id] = entry;
  }
  console.log(`[shard-catalog] writing ${upcGroups.size} upc buckets`);
  await pool([...upcGroups.entries()], 24, async ([rel, bucket]) => {
    await writeJson(rel, bucket);
  });
  upcGroups.clear();
  upcMap = null;

  const yearById = assignSeriesRunYears(comics);
  const issues = [];
  const collected = [];
  for (const c of comics) {
    if (isCollectedComic(c)) collected.push(c);
    else issues.push(c);
  }

  const issueRuns = new Map();
  for (const c of issues) {
    const year = yearById.get(c.id) ?? 0;
    const key = makeSeriesKey(c.publisher, c.series, year);
    let bucket = issueRuns.get(key);
    if (!bucket) {
      bucket = [];
      issueRuns.set(key, bucket);
    }
    bucket.push(c);
  }
  const collectedRuns = new Map();
  for (const c of collected) {
    const key = makeCollectedSeriesKey(c.publisher, c.series);
    let bucket = collectedRuns.get(key);
    if (!bucket) {
      bucket = [];
      collectedRuns.set(key, bucket);
    }
    bucket.push(c);
  }

  const usedNames = new Set();
  const issuePath = new Map();
  for (const key of issueRuns.keys()) {
    const name = uniquePath(usedNames, shardId(`issue:${key}`));
    issuePath.set(key, `comics/runs/${name}.json`);
  }
  const collectedPath = new Map();
  for (const key of collectedRuns.keys()) {
    const name = uniquePath(usedNames, shardId(`collected:${key}`));
    collectedPath.set(key, `comics/runs/${name}.json`);
  }

  const family = new Map();
  function rememberFamily(c, runRel) {
    const key = comicFamilyKey(c);
    let list = family.get(key);
    if (!list) {
      list = [];
      family.set(key, list);
    }
    list.push({ comic: c, runRel });
  }
  for (const [key, rows] of issueRuns) {
    const rel = issuePath.get(key);
    for (const c of rows) rememberFamily(c, rel);
  }
  for (const [key, rows] of collectedRuns) {
    const rel = collectedPath.get(key);
    for (const c of rows) rememberFamily(c, rel);
  }

  function runFile(rows, rel) {
    const years = {};
    for (const c of rows) years[c.id] = yearById.get(c.id) ?? 0;
    const related = [];
    const seen = new Set(rows.map((c) => c.id));
    for (const c of rows) {
      const members = family.get(comicFamilyKey(c)) ?? [];
      for (const member of members) {
        if (member.runRel === rel || seen.has(member.comic.id)) continue;
        seen.add(member.comic.id);
        related.push(member.comic);
        years[member.comic.id] = yearById.get(member.comic.id) ?? 0;
      }
    }
    return { comics: rows, related, years };
  }

  console.log(`[shard-catalog] writing ${issueRuns.size + collectedRuns.size} comic runs`);
  const runJobs = [];
  for (const [key, rows] of issueRuns) {
    const rel = issuePath.get(key);
    runJobs.push([rel, runFile(rows, rel)]);
  }
  for (const [key, rows] of collectedRuns) {
    const rel = collectedPath.get(key);
    runJobs.push([rel, runFile(rows, rel)]);
  }
  await pool(runJobs, 24, async ([rel, file]) => {
    await writeJson(rel, file);
  });

  const buckets = new Map();
  function putBucket(c, rel) {
    const brel = comicBucketPath(c.id);
    let bucket = buckets.get(brel);
    if (!bucket) {
      bucket = { comics: [], years: {}, run: {} };
      buckets.set(brel, bucket);
    }
    bucket.comics.push(c);
    bucket.years[c.id] = yearById.get(c.id) ?? 0;
    bucket.run[c.id] = rel;
  }
  for (const [key, rows] of issueRuns) {
    const rel = issuePath.get(key);
    for (const c of rows) putBucket(c, rel);
  }
  for (const [key, rows] of collectedRuns) {
    const rel = collectedPath.get(key);
    for (const c of rows) putBucket(c, rel);
  }
  console.log(`[shard-catalog] writing ${buckets.size} comic id buckets`);
  await pool([...buckets.entries()], 24, async ([rel, file]) => {
    await writeJson(rel, file);
  });
  buckets.clear();

  const seriesAll = buildSeriesList(issues, yearById);
  const seriesByPub = new Map();
  for (const series of seriesAll) {
    const list = seriesByPub.get(series.publisher) ?? [];
    list.push(series);
    seriesByPub.set(series.publisher, list);
  }
  const collectedAll = buildCollectedSeriesList(collected);
  const collectedByPub = new Map();
  for (const series of collectedAll) {
    const list = collectedByPub.get(series.publisher) ?? [];
    list.push(series);
    collectedByPub.set(series.publisher, list);
  }

  const publishers = buildPublisherList(issues, yearById);
  const seenPub = new Set(publishers.map((p) => p.publisher));
  for (const c of collected) {
    if (seenPub.has(c.publisher)) continue;
    seenPub.add(c.publisher);
    publishers.push({
      publisher: c.publisher,
      seriesCount: 0,
      issueCount: 0,
      latestDate: dateOf(c),
    });
  }

  const collectedCount = new Map();
  const collectedFormats = new Map();
  for (const c of collected) {
    collectedCount.set(c.publisher, (collectedCount.get(c.publisher) ?? 0) + 1);
    const label = comicFormatLabel(c.format);
    const set = collectedFormats.get(c.publisher) ?? new Set();
    set.add(label);
    collectedFormats.set(c.publisher, set);
  }

  const usedSlugs = new Set();
  const publisherEntries = [];
  for (const p of publishers) {
    const slugBase = uniquePath(usedSlugs, slug(p.publisher));
    const shard = `comics/pub/${slugBase}.json`;
    const series = (seriesByPub.get(p.publisher) ?? []).map((s) => ({
      ...s,
      sample: slimSample(s.sample),
      shard: issuePath.get(s.key),
    }));
    const collectedSeries = (collectedByPub.get(p.publisher) ?? []).map((s) => ({
      ...s,
      sample: slimSample(s.sample),
      shard: collectedPath.get(s.key),
    }));
    await writeJson(shard, {
      publisher: p.publisher,
      series,
      collectedSeries,
      collectedCount: collectedCount.get(p.publisher) ?? 0,
      collectedFormats: [...(collectedFormats.get(p.publisher) ?? [])],
    });
    publisherEntries.push({
      publisher: p.publisher,
      slug: slugBase,
      seriesCount: p.seriesCount,
      issueCount: p.issueCount,
      latestDate: p.latestDate,
      collectedCount: collectedCount.get(p.publisher) ?? 0,
      shard,
    });
  }
  await writeJson("comics/publishers.json", { publishers: publisherEntries });

  const now = Date.now();
  const noteworthy = [];
  const noteworthyYears = {};
  for (const c of comics) {
    const street = c.streetDate ?? c.coverDate;
    if (!street) continue;
    const t = Date.parse(street);
    if (!Number.isFinite(t) || now - t >= NOTEWORTHY_MS) continue;
    noteworthy.push(c);
    noteworthyYears[c.id] = yearById.get(c.id) ?? 0;
  }
  noteworthy.sort((a, b) => {
    const da = dateOf(a);
    const db = dateOf(b);
    if (da === db) return 0;
    if (!da) return 1;
    if (!db) return -1;
    return da < db ? 1 : -1;
  });
  await writeJson("comics/noteworthy.json", { comics: noteworthy, years: noteworthyYears });

  const recent = [...comics].sort((a, b) => {
    const da = dateOf(a);
    const db = dateOf(b);
    if (da === db) return 0;
    if (!da) return 1;
    if (!db) return -1;
    return da < db ? 1 : -1;
  });

  const searchShards = Array.from({ length: SEARCH_SHARDS }, () => ({
    series: [],
    pubs: [],
    seriesIdx: new Map(),
    pubIdx: new Map(),
    rows: [],
  }));
  let truncated = 0;
  const searchSize = Math.ceil(comics.length / SEARCH_SHARDS) || 1;
  comics.forEach((c, i) => {
    const shard = searchShards[Math.min(SEARCH_SHARDS - 1, Math.floor(i / searchSize))];
    let sIdx = shard.seriesIdx.get(c.series);
    if (sIdx == null) {
      sIdx = shard.series.length;
      shard.series.push(c.series);
      shard.seriesIdx.set(c.series, sIdx);
    }
    let pIdx = shard.pubIdx.get(c.publisher);
    if (pIdx == null) {
      pIdx = shard.pubs.length;
      shard.pubs.push(c.publisher);
      shard.pubIdx.set(c.publisher, pIdx);
    }
    const description = String(c.description ?? "");
    if (description.length > DESC_CAP) truncated += 1;
    shard.rows.push([
      c.id,
      sIdx,
      c.issue,
      pIdx,
      c.format,
      c.variant ?? "",
      c.upc ?? "",
      c.coverDate ?? "",
      c.streetDate ?? "",
      c.key ? 1 : 0,
      c.msrp ?? 0,
      c.demand ?? 0,
      c.cover ?? "",
      (c.palette ?? []).map((p) => String(p).replace(/^#/, "")).join(","),
      (c.writers ?? []).join(", "),
      (c.artists ?? []).join(", "),
      description.slice(0, DESC_CAP),
      yearById.get(c.id) ?? 0,
    ]);
  });
  const comicSearch = [];
  for (let i = 0; i < searchShards.length; i++) {
    const rel = `comics/search/${String(i).padStart(2, "0")}.json`;
    comicSearch.push(rel);
    const shard = searchShards[i];
    await writeJson(rel, { series: shard.series, pubs: shard.pubs, rows: shard.rows });
  }
  console.log(`[shard-catalog] search descriptions truncated: ${truncated}`);

  return {
    comicCount: comics.length,
    recentComics: recent.slice(0, 10).map(slimSample),
    comicSearch,
    companyCountWait: true,
  };
}

async function shardFigures() {
  const { figures: FIGURES, aliasDoc } = await loadFigureInputs(root);
  const { POPULAR_FRANCHISES } = await import("../src/lib/figure-property.ts");
  const { shardId, figureBucketPath, figureSetPath } = await import("../src/lib/catalog-shard.ts");
  console.log(`[shard-catalog] ${FIGURES.length} figures`);

  const byCompany = new Map();
  for (const figure of FIGURES) {
    const list = byCompany.get(figure.company) ?? [];
    list.push(figure);
    byCompany.set(figure.company, list);
  }

  const companies = [];
  for (const [id, rows] of byCompany) {
    const lines = [];
    const seen = new Set();
    for (const figure of rows) {
      if (seen.has(figure.line)) continue;
      seen.add(figure.line);
      lines.push({ name: figure.line, count: 0 });
    }
    for (const figure of rows) {
      const line = lines.find((l) => l.name === figure.line);
      if (line) line.count += 1;
    }
    const shard = `figures/company/${id}.json`;
    await writeJson(shard, rows);
    companies.push({ id, total: rows.length, lines, shard });
  }
  companies.sort((a, b) => a.id.localeCompare(b.id));

  function collapsedCount(rows) {
    const seen = new Set();
    let n = 0;
    for (const figure of rows) {
      const setId = figure.setId?.trim();
      const key = setId ? `set:${setId}` : `solo:${figure.id}`;
      if (seen.has(key)) continue;
      seen.add(key);
      n += 1;
    }
    return n;
  }

  const franchises = [];
  for (const franchise of POPULAR_FRANCHISES) {
    const rows = FIGURES.filter((f) => f.property === franchise.id);
    if (!rows.length) continue;
    const shard = `figures/franchise/${franchise.id}.json`;
    await writeJson(shard, rows);
    const entry = {
      id: franchise.id,
      count: collapsedCount(rows),
      shard,
      companies: [],
    };
    if (franchise.id === "transformers") {
      entry.parties = { "1p": 0, "2p": 0, "3p": 0 };
      entry.partyShards = {};
      for (const party of ["1p", "2p", "3p"]) {
        const partyRows = rows.filter((f) => f.party === party);
        entry.parties[party] = partyRows.length;
        const rel = `figures/franchise/transformers-${party}.json`;
        entry.partyShards[party] = rel;
        await writeJson(rel, partyRows);
      }
    }
    const companyMap = new Map();
    for (const figure of rows) {
      let co = companyMap.get(figure.company);
      if (!co) {
        co = { id: figure.company, total: 0, lines: [], lineSet: new Set(), parties: {} };
        companyMap.set(figure.company, co);
      }
      co.total += 1;
      if (!co.lineSet.has(figure.line)) {
        co.lineSet.add(figure.line);
        co.lines.push(figure.line);
      }
      if (franchise.id === "transformers" && figure.party) {
        const party = co.parties[figure.party] ?? { total: 0, lines: [], lineSet: new Set() };
        party.total += 1;
        if (!party.lineSet.has(figure.line)) {
          party.lineSet.add(figure.line);
          party.lines.push(figure.line);
        }
        co.parties[figure.party] = party;
      }
    }
    entry.companies = [...companyMap.values()].map((co) => {
      const out = { id: co.id, total: co.total, lines: co.lines };
      if (franchise.id === "transformers") {
        out.parties = {};
        for (const [party, stat] of Object.entries(co.parties)) {
          out.parties[party] = { total: stat.total, lines: stat.lines };
        }
      }
      return out;
    });
    franchises.push(entry);
  }

  const PART = 2500;
  const parts = [];
  for (let i = 0; i < FIGURES.length; i += PART) {
    const rel = `figures/parts/${String(parts.length).padStart(2, "0")}.json`;
    parts.push(rel);
    await writeJson(rel, FIGURES.slice(i, i + PART));
  }

  const figBuckets = new Map();
  for (const figure of FIGURES) {
    const rel = figureBucketPath(figure.id);
    const list = figBuckets.get(rel) ?? [];
    list.push(figure);
    figBuckets.set(rel, list);
  }
  await pool([...figBuckets.entries()], 24, async ([rel, rows]) => {
    await writeJson(rel, rows);
  });

  const sets = new Map();
  for (const figure of FIGURES) {
    const setId = figure.setId?.trim();
    if (!setId) continue;
    const list = sets.get(setId) ?? [];
    list.push(figure);
    sets.set(setId, list);
  }
  let setFiles = 0;
  for (const [setId, members] of sets) {
    if (members.length < 2) continue;
    await writeJson(figureSetPath(setId), members);
    setFiles += 1;
  }
  console.log(`[shard-catalog] ${setFiles} figure sets`);

  const aliases = buildAliasToFigureId(aliasDoc);
  for (const figure of FIGURES) {
    const sku = (figure.sku ?? "").trim();
    if (!sku) continue;
    const key = sku.toUpperCase();
    if (!aliases[key]) aliases[key] = figure.id;
  }
  await writeJson("figures/aliases.json", aliases);

  const ids = [];
  const skus = [];
  const keys = [];
  const skuSeen = new Set();
  for (const figure of FIGURES) {
    ids.push(figure.id);
    const sku = (figure.sku ?? "").trim().toLowerCase();
    if (sku && !skuSeen.has(sku)) {
      skuSeen.add(sku);
      skus.push(sku);
    }
    keys.push(`${figure.name}|${figure.subtitle}|${figure.line}|${figure.company}`.toLowerCase());
  }
  await writeJson("figures/identity.json", { ids, skus, keys });

  await writeJson("figures/browse.json", {
    total: FIGURES.length,
    companies,
    franchises,
    parts,
  });

  return { figureCount: FIGURES.length, companyCount: byCompany.size };
}

async function build() {
  bytesWritten = 0;
  fs.rmSync(outStaging, { recursive: true, force: true });
  fs.mkdirSync(outStaging, { recursive: true });
  const started = Date.now();
  const comic = await shardComics();
  const figures = await shardFigures();
  const manifest = {
    generatedAt: new Date().toISOString(),
    figures: figures.figureCount,
    comics: comic.comicCount,
    companies: figures.companyCount,
    recentComics: comic.recentComics,
    figureBrowse: "figures/browse.json",
    publishers: "comics/publishers.json",
    noteworthy: "comics/noteworthy.json",
    comicSearch: comic.comicSearch,
    figureAliases: "figures/aliases.json",
  };
  await writeJson("manifest.json", manifest);
  fs.rmSync(outFinal, { recursive: true, force: true });
  fs.renameSync(outStaging, outFinal);
  const sec = ((Date.now() - started) / 1000).toFixed(1);
  console.log(
    `[shard-catalog] done in ${sec}s — ${figures.figureCount} figures, ${comic.comicCount} comics, ${(bytesWritten / 1e6).toFixed(1)} MB json`,
  );
}

await withLock(async () => {
  if (await catalogInputsAreFresh(root, path.join(outFinal, "manifest.json"))) {
    console.log("[shard-catalog] fresh — skipping");
    return;
  }
  await build();
});

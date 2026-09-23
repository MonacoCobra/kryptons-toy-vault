/**
 * Densify Blokees Transformers parents from the official store collection
 * and link TFWiki-sourced blind-box members as set children.
 *
 * Does not invent SKUs. Children ship without photos.
 * Removes fake Blokees Gundam rows.
 *
 *   node scripts/densify-blokees-tf.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const oneshotPath = join(root, "src/data/figure-archive/oneshot.json");
const aliasPath = join(root, "src/data/figure-sku-aliases.json");
const store = JSON.parse(readFileSync(join(root, "scripts/figure_oneshot/blokees-tf-store.json"), "utf8"));
const wavesDoc = JSON.parse(readFileSync(join(root, "scripts/figure_oneshot/blokees-tf-waves.json"), "utf8"));

function parentId(handle) {
  return `sf-blokees-${handle}`.slice(0, 80);
}

function slug(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48);
}

function normName(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function lineFor(title, handle) {
  const t = `${title} ${handle}`.toLowerCase();
  if (t.includes("action edition")) return "Blokees Action Edition";
  if (t.includes("champion class")) return "Blokees Champion Class";
  if (t.includes("classic class")) return "Blokees Classic Class";
  if (t.includes("galaxy version")) return "Blokees Galaxy Version";
  if (t.includes("shining version")) return "Blokees Shining Version";
  if (t.includes("defender version")) return "Blokees Defender Version";
  if (t.includes("wheels")) return "Blokees Wheels";
  return "Blokees Transformers";
}

function scaleFor(line) {
  if (line.includes("Action")) return '6"';
  if (line.includes("Classic") || line.includes("Champion")) return '4.5"';
  if (line.includes("Defender")) return '2"';
  if (line.includes("Wheels")) return "1:64";
  return '4"';
}

function splitTitle(title) {
  const cleaned = title.replace(/^Blokees\s+/i, "").trim();
  const parts = cleaned.split("|").map((part) => part.trim()).filter(Boolean);
  if (parts.length >= 2) {
    return { name: parts[parts.length - 1].slice(0, 120), subtitle: parts.slice(0, -1).join(" · ").slice(0, 120) };
  }
  return { name: cleaned.slice(0, 120), subtitle: "Transformers" };
}

function ensureTag(row, tag) {
  if (!Array.isArray(row.tags)) row.tags = [];
  if (!row.tags.includes(tag)) row.tags.push(tag);
}

function formatRow(obj, indentFirst = false) {
  return JSON.stringify(obj, null, 2)
    .split("\n")
    .map((line, index) => (index === 0 && !indentFirst ? line : `  ${line}`))
    .join("\n");
}

function objectBounds(text, id) {
  const needle = `"id": ${JSON.stringify(id)}`;
  const idAt = text.indexOf(needle);
  if (idAt < 0) return null;
  const start = text.lastIndexOf("{", idAt);
  if (start < 0) return null;
  let depth = 0;
  for (let i = start; i < text.length; i++) {
    const ch = text[i];
    if (ch === "{") depth += 1;
    else if (ch === "}") {
      depth -= 1;
      if (depth === 0) return { start, end: i + 1 };
    }
  }
  return null;
}

function removeSpan(text, start, end) {
  const before = text.slice(0, start);
  const commaBefore = before.match(/,(\s*)$/);
  if (commaBefore) return text.slice(0, start - commaBefore[0].length) + text.slice(end);
  const after = text.slice(end);
  const commaAfter = after.match(/^(\s*),/);
  if (commaAfter) return text.slice(0, start) + text.slice(end + commaAfter[0].length);
  return text.slice(0, start) + text.slice(end);
}

const raw = readFileSync(oneshotPath, "utf8");
const rows = JSON.parse(raw);
const byId = new Map(rows.map((row) => [row.id, row]));

const gundamIds = rows
  .filter((row) => row.company === "blokees" && /gundam/i.test(`${row.line} ${row.name} ${row.subtitle} ${row.id}`))
  .map((row) => row.id);

const stats = {
  storeProducts: store.products.length,
  parentsExisting: 0,
  parentsAdded: [],
  gundamRemoved: gundamIds,
  childrenAdded: 0,
  childrenReused: 0,
  waves: [],
};

const parentByHandle = new Map();

for (const product of store.products) {
  const id = parentId(product.handle);
  const line = lineFor(product.title, product.handle);
  const { name, subtitle } = splitTitle(product.title);
  let row = byId.get(id);
  if (row && row.company === "blokees") {
    stats.parentsExisting += 1;
  } else {
    row = {
      id,
      name,
      subtitle: subtitle || line,
      line,
      company: "blokees",
      kind: "kit",
      releaseDate: product.created && product.created >= "1980-01-01" ? product.created : "2024-01-01",
      msrp: Number(product.price) || 19.99,
      scale: scaleFor(line),
      demand: 1,
      tags: ["blokees", "transformers", "archive", "shopify", "densify-blokees-tf", "kit"],
      source: "blokees-store",
    };
    if (product.sku) row.sku = String(product.sku);
    if (product.image) row.imageUrl = product.image;
    rows.push(row);
    byId.set(id, row);
    stats.parentsAdded.push(id);
  }
  row.setId = id;
  row.setRole = "parent";
  ensureTag(row, "blokees");
  ensureTag(row, "transformers");
  ensureTag(row, "set-parent");
  if (!row.sku && product.sku) row.sku = String(product.sku);
  if (!row.imageUrl && product.image) row.imageUrl = product.image;
  parentByHandle.set(product.handle, row);
}

const lineGroup = (waveId) => waveId.replace(/\d+$/, "");

const reusePool = rows.filter((row) => row.company === "blokees" && !gundamIds.includes(row.id) && !row.setId);
function rowGroup(row) {
  const blob = `${row.line} ${row.subtitle} ${(row.tags || []).join(" ")}`.toLowerCase();
  if (blob.includes("wheels")) return "C";
  if (blob.includes("defender")) return "DV";
  if (blob.includes("shining")) return "SV";
  if (blob.includes("galaxy")) return "GV";
  return "";
}

for (const wave of wavesDoc.waves) {
  const parent = parentByHandle.get(wave.handle);
  if (!parent) {
    stats.waves.push({ id: wave.id, missingParent: true });
    continue;
  }
  const group = lineGroup(wave.id);
  const nameCounts = new Map();
  for (const member of wave.members) {
    const key = normName(member);
    nameCounts.set(key, (nameCounts.get(key) || 0) + 1);
  }
  // Uniqueness across waves in the same line, not just inside one wave.
  const siblingNames = new Map();
  for (const other of wavesDoc.waves) {
    if (lineGroup(other.id) !== group) continue;
    for (const member of other.members) {
      const key = normName(member);
      siblingNames.set(key, (siblingNames.get(key) || 0) + 1);
    }
  }

  let added = 0;
  let reused = 0;
  for (const member of wave.members) {
    const key = normName(member);
    const childId = `blk-m-${wave.id.toLowerCase()}-${slug(member)}`.slice(0, 80);
    if (byId.has(childId)) {
      const existing = byId.get(childId);
      existing.setId = parent.id;
      existing.setRole = "member";
      ensureTag(existing, "transformers");
      ensureTag(existing, "set-member");
      continue;
    }
    const uniqueInLine = siblingNames.get(key) === 1 && nameCounts.get(key) === 1;
    const reusable = uniqueInLine
      ? reusePool.find((row) => !row.setId && rowGroup(row) === group && normName(row.name) === key)
      : undefined;
    if (reusable) {
      reusable.setId = parent.id;
      reusable.setRole = "member";
      reusable.subtitle = wave.title;
      ensureTag(reusable, "transformers");
      ensureTag(reusable, "set-member");
      reused += 1;
      stats.childrenReused += 1;
      continue;
    }
    const child = {
      id: childId,
      name: member.slice(0, 120),
      subtitle: wave.title.slice(0, 120),
      line: parent.line,
      company: "blokees",
      kind: "kit",
      releaseDate: parent.releaseDate || "2024-01-01",
      msrp: parent.msrp || 8.99,
      scale: parent.scale || '4"',
      demand: 1,
      tags: ["blokees", "transformers", "set-member", "tfwiki", wave.id.toLowerCase(), "kit"],
      source: "tfwiki-blokees",
      setId: parent.id,
      setRole: "member",
    };
    rows.push(child);
    byId.set(childId, child);
    added += 1;
    stats.childrenAdded += 1;
  }
  stats.waves.push({ id: wave.id, handle: wave.handle, members: wave.members.length, added, reused });
}

const kept = rows.filter((row) => !gundamIds.includes(row.id));

let text = raw;
const edits = [];
for (const id of gundamIds) {
  const bounds = objectBounds(text, id);
  if (bounds) edits.push({ kind: "delete", ...bounds, id });
}
for (const row of kept) {
  if (!row.setId) continue;
  const bounds = objectBounds(text, row.id);
  if (!bounds) continue;
  edits.push({ kind: "replace", ...bounds, id: row.id, text: formatRow(row) });
}
edits.sort((a, b) => b.start - a.start);
for (const edit of edits) {
  if (edit.kind === "delete") text = removeSpan(text, edit.start, edit.end);
  else text = text.slice(0, edit.start) + edit.text + text.slice(edit.end);
}

const fresh = kept.filter((row) => !objectBounds(raw, row.id));
if (fresh.length) {
  const block = fresh.map((row) => formatRow(row, true)).join(",\n");
  const close = text.lastIndexOf("]");
  const before = text.slice(0, close).replace(/\s*$/, "");
  const needsComma = !before.endsWith("[");
  text = `${before}${needsComma ? ",\n" : "\n"}${block}\n]\n`;
}
writeFileSync(oneshotPath, text.endsWith("\n") ? text : `${text}\n`);

let aliasText = readFileSync(aliasPath, "utf8");
let aliasRetargets = 0;
const escapeRe = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
for (const product of store.products) {
  const id = parentId(product.handle);
  const codes = [...new Set([product.sku, ...(product.variantSkus || [])].filter(Boolean).map(String))];
  for (const code of codes) {
    const re = new RegExp(`("${escapeRe(code)}"\\s*:\\s*")([^"]*)(")`);
    if (re.test(aliasText)) {
      aliasText = aliasText.replace(re, (_match, open, prev, close) => {
        if (prev !== id) aliasRetargets += 1;
        return `${open}${id}${close}`;
      });
      continue;
    }
    const marker = `"aliasToFigureId": {`;
    const at = aliasText.indexOf(marker);
    if (at < 0) continue;
    const insertAt = at + marker.length;
    aliasText = `${aliasText.slice(0, insertAt)}\n    ${JSON.stringify(code)}: ${JSON.stringify(id)},${aliasText.slice(insertAt)}`;
    aliasRetargets += 1;
  }
}
writeFileSync(aliasPath, aliasText.endsWith("\n") ? aliasText : `${aliasText}\n`);

const parents = kept.filter((row) => row.company === "blokees" && row.setRole === "parent" && store.products.some((product) => parentId(product.handle) === row.id));
stats.aliasRetargets = aliasRetargets;
stats.parentCount = parents.length;
stats.childCount = kept.filter((row) => row.company === "blokees" && row.setRole === "member").length;
stats.blokeesRemaining = kept.filter((row) => row.company === "blokees").length;
stats.note = "Children have no imageUrl. Parents use the official store photo when the row had none. Alias file rewritten so the 71 store SKUs resolve to those parents.";

writeFileSync(join(root, "src/data/figure-archive/blokees-tf-densify-stats.json"), `${JSON.stringify(stats, null, 2)}\n`);
console.log(JSON.stringify({
  storeProducts: stats.storeProducts,
  parentsExisting: stats.parentsExisting,
  parentsAdded: stats.parentsAdded.length,
  parentCount: stats.parentCount,
  gundamRemoved: stats.gundamRemoved.length,
  childrenAdded: stats.childrenAdded,
  childrenReused: stats.childrenReused,
  childCount: stats.childCount,
  aliasRetargets,
  blokeesRemaining: stats.blokeesRemaining,
}, null, 2));

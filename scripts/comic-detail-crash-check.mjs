/**
 * Regression: live/DB extras (numeric issue, CSV writers, null series fields,
 * noteworthy-only ids) must not crash detail lookup, family indexing, or helpers.
 */
import assert from "node:assert/strict";

const { mergeComics, comicById, comicLabel } = await import("../src/data/comics.ts");
const {
  getComicVariants,
  indexComicsByFamily,
  normalizeComicPart,
  variantDisplayLabel,
  isPrimaryCover,
} = await import("../src/lib/comic-variants.ts");
const { libraryCatalogRows } = await import("../src/lib/comic-catalog.ts");
const { formatMonthYear, formatDate, usd } = await import("../src/lib/format.ts");
const seed = (await import("../src/data/weekly-seed.json", { with: { type: "json" } })).default;
const { slug } = await import("../src/lib/utils.ts");

assert.equal(normalizeComicPart(13), "13");
assert.equal(normalizeComicPart(null), "");
assert.equal(variantDisplayLabel({ variant: 2 }), "2");
assert.equal(isPrimaryCover({ variant: 1 }), false);
assert.equal(formatMonthYear(20260901), "20260901"); // invalid numeric date → stringified fallback
assert.equal(formatMonthYear(null), "—");
assert.equal(formatDate(""), "—");
assert.match(usd("3.90"), /\$3\.90/);

const week = seed.week || "2026-W36";
function normalizeSeedComic(row, weekKey) {
  const series = String(row.series ?? "").trim();
  const issue = String(row.issue ?? "").replace(/^#/, "").trim() || "1";
  const publisher = String(row.publisher ?? "Unknown").trim();
  const variant = String(row.variant ?? "").trim();
  const street = String(row.streetDate ?? row.coverDate ?? "2026-09-02").trim();
  return {
    id: `live-c-${weekKey}-${slug(series)}-${slug(issue)}${variant ? `-${slug(variant)}` : ""}`.slice(0, 80),
    series,
    issue,
    publisher,
    coverDate: street,
    streetDate: street,
    writers: typeof row.writers === "string" ? row.writers : row.writers,
    artists: typeof row.artists === "string" ? row.artists : row.artists,
    description: row.description || `Street date ${street}.`,
    msrp: Number(row.msrp) || 4.99,
    format: row.format || "single",
    variant: variant || undefined,
    demand: 1,
    key: false,
    palette: ["#111827", "#f8fafc", "#e30613"],
    cover: row.coverUrl || undefined,
  };
}

// Simulate messy live extras (pre-coerce shapes that used to reach the client).
const messyExtras = (seed.comics || []).map((row, i) => {
  const base = normalizeSeedComic(row, week);
  if (i === 0) {
    return { ...base, issue: Number(base.issue) || 1, writers: "Matt Fraction", artists: "Matteo Scalera" };
  }
  if (i === 1) {
    return { ...base, variant: 1, upc: 75960612345600111, coverDate: "2026-09-03\u0000" };
  }
  return base;
});

const crow = messyExtras.find((c) => /crowbound/i.test(c.series));
assert.ok(crow, "Crowbound must be in weekly seed");
console.log("Crowbound id:", crow.id);

const badExtras = [
  {
    id: "live-bad-1",
    series: "Batman",
    issue: 13,
    publisher: "DC Comics",
    writers: "Matt Fraction",
    artists: "Matteo Scalera",
    coverDate: "2026-01-01",
    msrp: 4.99,
    format: "single",
    demand: 1,
    description: "x",
    palette: ["#1", "#2", "#3"],
  },
  ...messyExtras,
];

// Library shape: noteworthy holds live-drop titles; archive does not (yet).
const fakeLibrary = {
  noteworthy: messyExtras,
  archive: [],
  promoted: 0,
  week,
};
const libraryRows = libraryCatalogRows(fakeLibrary);
assert.ok(libraryRows.some((c) => c.id === crow.id), "libraryCatalogRows includes Crowbound");

// BUG REPRO: archive-only lookup misses noteworthy (was Live detail crash / notFound-as-error).
assert.equal(comicById(crow.id, [], fakeLibrary.archive), undefined);
const found = comicById(crow.id, [], libraryRows);
assert.ok(found, "detail lookup with noteworthy+archive finds Crowbound");
assert.equal(found.series, "Crowbound");

const catalog = mergeComics([], libraryRows);
const familyIndex = indexComicsByFamily(catalog);

const sampleIds = [
  "mv-asm-300",
  "dc-abs-batman-1",
  "live-bad-1",
  crow.id,
  ...messyExtras.slice(0, 8).map((c) => c.id),
  ...messyExtras.filter((c) => /escape|mask|queen|absolute/i.test(c.series)).map((c) => c.id),
];

for (const id of [...new Set(sampleIds)]) {
  const comic = comicById(id, badExtras, libraryRows) || badExtras.find((c) => c.id === id);
  assert.ok(comic, `missing ${id}`);
  // Coerce like a hardened boundary would before UI helpers:
  const safe = {
    ...comic,
    issue: String(comic.issue ?? ""),
    series: String(comic.series ?? ""),
    publisher: String(comic.publisher ?? ""),
    variant: comic.variant == null || comic.variant === "" ? undefined : String(comic.variant),
    upc: comic.upc == null || comic.upc === "" ? undefined : String(comic.upc),
    coverDate: String(comic.coverDate ?? "").replace(/\u0000/g, ""),
    writers: comic.writers,
    artists: comic.artists,
  };
  const variants = getComicVariants(safe, catalog, familyIndex);
  assert.ok(Array.isArray(variants));
  assert.ok(comicLabel(safe).length > 0);
  assert.ok(variantDisplayLabel(safe).length > 0);
  assert.ok(typeof formatMonthYear(safe.coverDate) === "string");
  assert.ok(typeof usd(safe.msrp) === "string");
}

console.log("comic-detail-crash-check: ok", {
  crowboundId: crow.id,
  noteworthyCount: fakeLibrary.noteworthy.length,
});

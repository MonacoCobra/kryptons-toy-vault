/**
 * Regression: numeric issue / CSV writers in live extras must not crash
 * family indexing or comic detail helpers (was: s.trim is not a function).
 */
import assert from "node:assert/strict";

const { mergeComics, comicById, comicLabel } = await import("../src/data/comics.ts");
const { getComicVariants, indexComicsByFamily, normalizeComicPart } = await import("../src/lib/comic-variants.ts");

assert.equal(normalizeComicPart(13), "13");
assert.equal(normalizeComicPart(null), "");

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
];

const catalog = mergeComics(badExtras, []);
const familyIndex = indexComicsByFamily(catalog);
for (const id of ["mv-asm-300", "dc-abs-batman-1", "mv-spm-supes-1", "live-bad-1"]) {
  const comic = comicById(id, badExtras) || badExtras.find((c) => c.id === id);
  assert.ok(comic, id);
  const variants = getComicVariants(comic, catalog, familyIndex);
  assert.ok(Array.isArray(variants));
  assert.ok(comicLabel(comic).length > 0);
}
console.log("comic-detail-crash-check: ok");

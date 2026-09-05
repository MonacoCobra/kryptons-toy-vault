/**
 * Self-check for LOCG import matching against the real user export + sample CSV.
 * Run: node --experimental-strip-types scripts/locg-import-check.mjs
 * (imports TS via strip-types from src)
 */
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

// Dynamic import of TS module
const mod = await import("../src/lib/locg-import.ts");
const comicsMod = await import("../src/data/comics.ts");

const {
  parseLocgSpreadsheet,
  matchLocgRows,
  parseSeriesMeta,
  parseFullTitle,
  normalizeIssue,
  publishersMatch,
} = mod;
const { mergeComics } = comicsMod;

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

// --- unit checks ---
{
  const m = parseSeriesMeta("Action Comics (Vol. 3) (2016 - Present)");
  assert(m.base === "Action Comics", `base got ${m.base}`);
  assert(m.year === 2016, `year got ${m.year}`);
  assert(m.vol === 3, `vol got ${m.vol}`);
}
{
  const m = parseSeriesMeta("Batman (Vol. 3) (2016 - 2026)");
  assert(m.base === "Batman" && m.year === 2016 && m.vol === 3, JSON.stringify(m));
}
{
  const m = parseSeriesMeta("The Adventures of Superman (Vol. 1) (1987 - 2006)");
  assert(m.base === "The Adventures of Superman", m.base);
  assert(m.baseNorm === "adventures of superman", m.baseNorm);
}
{
  const m = parseSeriesMeta("All-Star Superman (2005 - 2008)");
  assert(m.base === "All-Star Superman" && m.year === 2005, JSON.stringify(m));
}
{
  const t = parseFullTitle(
    "Action Comics #1032 Cover B Julian Totino Tedesco Variant",
    "Action Comics",
  );
  assert(t.issue === "1032", `issue ${t.issue}`);
  assert(/cover b/i.test(t.variant ?? ""), `variant ${t.variant}`);
}
{
  const t = parseFullTitle("Batman #1 2nd Printing", "Batman");
  assert(t.issue === "1", t.issue);
}
{
  const t = parseFullTitle("The Amazing Spider-Man #129 Facsimile Edition 2026", "The Amazing Spider-Man");
  assert(t.issue === "129", t.issue);
  assert(t.facsimile === true, "facsimile");
}
assert(normalizeIssue("#300") === "300", "issue #");
assert(normalizeIssue("0300") === "300", "leading zero");
assert(publishersMatch("DC", "DC Comics"), "DC alias");
assert(publishersMatch("Marvel Comics", "Marvel"), "Marvel alias");

// --- sample CSV (legacy columns) ---
const sampleText = readFileSync(
  new URL("../public/samples/locg-sample-export.csv", import.meta.url),
  "utf8",
);
const sample = parseLocgSpreadsheet(sampleText);
const sampleMatch = matchLocgRows(sample.rows);
console.log(
  `sample CSV: ${sample.rows.length} rows → ${sampleMatch.matched} catalog / ${sampleMatch.unmatched} custom`,
);
const sampleCustomSeries = sampleMatch.matches
  .filter((m) => m.kind === "custom")
  .map((m) => m.row.series);
console.log("  sample customs:", sampleCustomSeries);

// Expect known keys to match
for (const name of ["Absolute Batman", "The Amazing Spider-Man", "Saga", "Invincible", "Action Comics"]) {
  const row = sampleMatch.matches.find((m) => m.row.series === name);
  assert(row, `missing sample row ${name}`);
  if (name === "Weird Al vs Batman Hypothetical") continue;
  assert(row.kind === "catalog", `${name} should catalog-match, got ${row.kind}`);
}
const weird = sampleMatch.matches.find((m) => m.row.series.includes("Weird Al"));
assert(weird?.kind === "custom", "hypothetical should stay custom");

// --- real user export ---
const userText = readFileSync(
  new URL("../public/samples/locg-user-export.csv", import.meta.url),
  "utf8",
);
const user = parseLocgSpreadsheet(userText);
assert(user.headers.includes("Publisher Name"), "publisher name header");
assert(user.rows.length >= 200, `expected ~251 rows, got ${user.rows.length}`);

// Spot-check parse
const ac1032 = user.rows.find((r) => (r.title ?? "").includes("Action Comics #1032"));
assert(ac1032, "ac1032 row");
assert(ac1032.publisher === "DC Comics", `pub ${ac1032.publisher}`);
assert(ac1032.issue === "1032", `issue ${ac1032.issue}`);
assert(ac1032.seriesBase === "Action Comics", `base ${ac1032.seriesBase}`);
assert(ac1032.seriesYear === 2016, `year ${ac1032.seriesYear}`);

const bat163 = user.rows.find((r) => r.title === "Batman #163");
assert(bat163?.issue === "163" && bat163.seriesYear === 2016, JSON.stringify(bat163));

const catalog = mergeComics();
console.log(`catalog size: ${catalog.length}`);

const userMatch = matchLocgRows(user.rows);
const rate = Math.round((userMatch.matched / user.rows.length) * 100);
console.log(
  `user CSV: ${user.rows.length} rows → ${userMatch.matched} catalog (${rate}%) / ${userMatch.unmatched} custom`,
);

// Show a few matched / unmatched examples
const matchedEx = userMatch.matches.filter((m) => m.kind === "catalog").slice(0, 8);
for (const m of matchedEx) {
  console.log(
    `  ✓ ${m.row.seriesBase} #${m.row.issue} → ${m.comic.series} #${m.comic.issue} [${m.comic.id}]`,
  );
}
const customEx = userMatch.matches.filter((m) => m.kind === "custom").slice(0, 12);
for (const m of customEx) {
  console.log(`  ✗ custom: ${m.row.seriesBase} #${m.row.issue} (${m.row.title})`);
}

// Batman #163 should hit Batman (2016)
const m163 = userMatch.matches.find((m) => m.row.title === "Batman #163");
assert(m163?.kind === "catalog", `Batman #163 should match, got ${m163?.kind}`);
assert(
  m163.comic.series === "Batman (2016)",
  `Batman #163 expected Batman (2016), got ${m163.comic.series}`,
);

// Action Comics #1032 should match
const m1032 = userMatch.matches.find((m) => (m.row.title ?? "").includes("#1032"));
assert(m1032?.kind === "catalog", `AC #1032 should match, got ${m1032?.kind}`);

// Facsimile Edition titles must not bind to the original non-facsimile key
const asm129fac = userMatch.matches.find((m) => (m.row.title ?? "").includes("Spider-Man #129 Facsimile"));
if (asm129fac?.kind === "catalog") {
  assert(asm129fac.comic.format === "facsimile", "ASM 129 fac should be facsimile format");
} else {
  assert(asm129fac?.kind === "custom", "ASM 129 fac unmatched ok when no fac in catalog");
}

const bat1 = userMatch.matches.find((m) => m.row.title === "Batman #1 2nd Printing");
assert(bat1?.kind === "catalog", "Batman #1 2nd Printing should match Court of Owls era");
assert(bat1.comic.format !== "facsimile", "2nd printing should not bind facsimile");

const dd2026 = userMatch.matches.find(
  (m) => m.row.seriesBase === "Daredevil" && m.row.issue === "1" && m.row.seriesYear === 2026,
);
if (dd2026?.kind === "catalog") {
  assert(
    !String(dd2026.comic.coverDate || "").startsWith("1964"),
    "Daredevil 2026 must not bind 1964 #1",
  );
}

// Expect a healthy match rate on this collection (seed covers many DC/Marvel keys)
assert(userMatch.matched >= 40, `expected >=40 catalog hits, got ${userMatch.matched}`);
assert(rate >= 15, `expected >=15% match rate, got ${rate}%`);

// Before fix: Publisher Name / missing Issue → every row became custom (0 catalog).
console.log(
  `before/after: prior importer treated real LOCG exports as ~0% catalog (publisher/issue parse miss); now ${rate}% (${userMatch.matched}/${user.rows.length})`,
);

console.log("locg-import-check: OK");

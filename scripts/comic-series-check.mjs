import { assignSeriesRunYears, buildSeriesList, seriesDisplayLabel } from "../src/lib/comic-series.ts";
import { COMICS } from "../src/data/comics.ts";

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

const yearById = assignSeriesRunYears(COMICS);
const marvelSeries = buildSeriesList(COMICS, yearById, "Marvel Comics");
const asm = marvelSeries.filter((s) => /amazing spider-man/i.test(s.title));
console.log(
  "ASM runs:",
  asm.map((s) => seriesDisplayLabel(s.title, s.year) + ` ×${s.issueCount}`),
);

// Expect at least two ASM runs when both classic keys and 2022 #1 exist
assert(asm.length >= 2, `expected ≥2 ASM runs, got ${asm.length}: ${JSON.stringify(asm)}`);
const years = new Set(asm.map((s) => s.year));
assert(years.has(2022), "missing 2022 ASM run");
assert([...years].some((y) => y > 0 && y < 2022), "missing classic ASM run");

const secret = marvelSeries.filter((s) => /^secret wars$/i.test(s.title));
if (secret.length) {
  const sy = new Set(secret.map((s) => s.year));
  assert(sy.has(1984) && sy.has(2015), `Secret Wars years ${[...sy]}`);
}

console.log("comic-series-check: ok");

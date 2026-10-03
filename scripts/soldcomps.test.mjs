import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  buildFigureSoldComps,
  figureKeyword,
  rejectReason,
} from "../src/lib/soldcomps.ts";

const snarl = {
  id: "tfaotp-selects-g2-universe-dinobot-snarl-g2-universe-dinobo",
  name: "G2 Universe Dinobot Snarl / G2 Universe Dinobot Slug",
  line: "Transformers Age of the Primes",
  subtitle: "Age of the Primes · Generations Selects",
  scale: "Multipack",
};
const sample = JSON.parse(readFileSync(new URL("./fixtures/soldcomps/snarl.json", import.meta.url), "utf8"));

test("tight keyword for a multipack", () => {
  assert.equal(figureKeyword(snarl), "age of the primes snarl slug");
});

test("Snarl/Slug pack: avg of 5 newest new 2-pack sales = 78.80", () => {
  const out = buildFigureSoldComps(snarl, "age of the primes snarl slug", sample, "2026-10-03T20:11:43.302Z");
  assert.equal(out.status, "ok");
  assert.equal(out.conditionBasis, "new");
  assert.deepEqual(out.comps.map((c) => c.price), [75, 74.99, 79, 81.99, 83]);
  assert.equal(out.estimate, 78.8);
  assert.equal(out.bestOfferInAvg, 1);
  assert.ok(out.comps.every((c) => c.url?.startsWith("https://www.ebay.com/itm/")));
});

test("rejects single from a multipack, lots, customs, cards, non-USD", () => {
  const base = { soldPrice: "50", soldCurrency: "USD", endedAt: "2026-10-01" };
  assert.match(rejectReason(snarl, { ...base, title: "Transformers Age of the Primes G2 Dinobot Slug *Used*" }), /missing/);
  assert.equal(rejectReason(snarl, { ...base, title: "Age of the Primes Snarl Slug lot of 3" }), "lot-partial-custom");
  assert.equal(rejectReason(snarl, { ...base, title: "Custom Age of the Primes Snarl Slug" }), "lot-partial-custom");
  assert.equal(rejectReason(snarl, { ...base, title: "Age of the Primes Trading Cards - Dinobot Snarl & Slug" }), "lot-partial-custom");
  assert.equal(rejectReason(snarl, { ...base, soldCurrency: "GBP", title: "Age of the Primes Snarl and Slug 2 Pack" }), "non-usd");
  assert.equal(rejectReason(snarl, { ...base, title: "Age of the Primes Snarl and Slug 2 Pack" }), null);
});

test("fewer than 3 passing → insufficient, no comps", () => {
  const out = buildFigureSoldComps(snarl, "k", { items: sample.items.slice(0, 1) }, "2026-10-03T00:00:00Z");
  assert.equal(out.status, "insufficient");
  assert.equal(out.estimate, null);
  assert.deepEqual(out.comps, []);
});

import assert from "node:assert/strict";
import test from "node:test";
import { itemValue, summarizeVault } from "../src/lib/vault-math.ts";

test("item value: paid, else MSRP, else null (never $0/$4 placeholders)", () => {
  assert.equal(itemValue(60, 109.99), 60);
  assert.equal(itemValue(undefined, 109.99), 109.99);
  assert.equal(itemValue(0, 24.99), 0); // gift
  assert.equal(itemValue(undefined, 0), null);
  assert.equal(itemValue(undefined, undefined), null);
});

test("vault totals: Paid, MSRP, combined total and missing count", () => {
  const figures = [
    { id: "a", msrp: 109.99 },
    { id: "b", msrp: 24.99 },
    { id: "c", msrp: 0 },
  ];
  const comics = [{ id: "x", msrp: 4.99 }];
  const stats = summarizeVault(
    {
      ownedFigures: {
        a: { figureId: "a", acquiredPrice: 80 },
        b: { figureId: "b" },
        c: { figureId: "c" },
      },
      ownedComics: {
        o1: { id: "o1", catalogId: "x", acquiredPrice: 3 },
        o2: { id: "o2", custom: { msrp: 7.99 } },
      },
    },
    { figures, comics },
  );
  assert.equal(stats.figureCount, 3);
  assert.equal(stats.comicCount, 2);
  assert.equal(stats.all.paid, 83);
  assert.equal(stats.all.paidCount, 2);
  assert.equal(stats.all.msrp, 147.96); // 109.99 + 24.99 + 4.99 + 7.99
  assert.equal(stats.all.msrpCount, 4);
  assert.equal(stats.all.total, 115.98); // 80 + 24.99 + 3 + 7.99
  assert.equal(stats.all.missing, 1);
  assert.equal(stats.figures.total, 104.99);
});

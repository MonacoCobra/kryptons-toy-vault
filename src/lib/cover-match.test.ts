import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  normalizeIssue,
  rankComicsFromGuess,
  scoreCoverGuess,
  searchCatalogLimited,
  type CoverGuess,
} from "@/lib/cover-match";
import type { CatalogComic } from "@/lib/types";

function comic(partial: Partial<CatalogComic> & Pick<CatalogComic, "id" | "series" | "issue">): CatalogComic {
  return {
    publisher: "Image Comics",
    coverDate: "2012-03-14",
    writers: [],
    artists: [],
    description: "",
    msrp: 2.99,
    format: "single",
    demand: 0,
    palette: ["111827", "7f1d1d", "eab308"],
    ...partial,
  };
}

const saga1 = comic({ id: "im-saga-1", series: "Saga", issue: "1" });
const saga1B = comic({
  id: "im-saga-1-b",
  series: "Saga",
  issue: "1",
  variant: "Cover B",
});
const saga13 = comic({ id: "im-saga-13", series: "Saga", issue: "13" });
const walking = comic({ id: "im-twd-1", series: "The Walking Dead", issue: "1" });

const catalog = [saga1, saga1B, saga13, walking];

describe("normalizeIssue", () => {
  it("treats hashed and zero-padded issue numbers as the same", () => {
    assert.equal(normalizeIssue("#001"), "1");
    assert.equal(normalizeIssue("13"), "13");
  });
});

describe("rankComicsFromGuess", () => {
  it("returns only existing catalog rows for a cover guess", () => {
    const guess: CoverGuess = { series: "Saga", issue: "1", publisher: "Image Comics" };
    const ranked = rankComicsFromGuess(guess, catalog, 5);
    assert.deepEqual(
      ranked.map((c) => c.id).slice(0, 2),
      ["im-saga-1", "im-saga-1-b"],
    );
    assert.ok(ranked.every((c) => catalog.some((row) => row.id === c.id)));
    assert.ok(ranked.every((c) => c.series === "Saga"));
  });

  it("prefers the matching issue over a later issue in the same series", () => {
    const guess: CoverGuess = { series: "Saga", issue: "13" };
    const ranked = rankComicsFromGuess(guess, catalog, 3);
    assert.equal(ranked[0]?.id, "im-saga-13");
    assert.ok(scoreCoverGuess(saga13, guess) > scoreCoverGuess(saga1, guess));
  });

  it("returns an empty list when nothing in the catalog scores", () => {
    const ranked = rankComicsFromGuess({ series: "Unlisted Mini Series", issue: "1" }, catalog, 5);
    assert.deepEqual(ranked, []);
  });
});

describe("searchCatalogLimited", () => {
  it("returns only existing rows and stops at the limit", () => {
    const found = searchCatalogLimited("Saga 1", [catalog], 2);
    assert.equal(found.length, 2);
    assert.ok(found.every((c) => catalog.some((row) => row.id === c.id)));
    assert.ok(found.every((c) => c.series === "Saga"));
  });
});

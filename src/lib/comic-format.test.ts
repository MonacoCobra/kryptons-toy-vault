import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { COMICS } from "@/data/comics";
import {
  catalogFromCustom,
  comicFormatLabel,
  filterCollectedComics,
  filterIssueComics,
  isCollectedComic,
  isCollectedFormat,
  normalizeComicFormat,
} from "@/lib/comic-format";
import { collectedForPublisher } from "@/lib/comic-series";
import type { CustomComic } from "@/lib/types";

describe("normalizeComicFormat", () => {
  it("keeps canonical ComicFormat values", () => {
    assert.equal(normalizeComicFormat("tpb"), "tpb");
    assert.equal(normalizeComicFormat("hc"), "hc");
    assert.equal(normalizeComicFormat("omnibus"), "omnibus");
    assert.equal(normalizeComicFormat("single"), "single");
    assert.equal(normalizeComicFormat("annual"), "annual");
    assert.equal(normalizeComicFormat("facsimile"), "facsimile");
  });

  it("maps hardcover aliases to hc", () => {
    assert.equal(normalizeComicFormat("hardcover"), "hc");
    assert.equal(normalizeComicFormat("Hard Cover"), "hc");
    assert.equal(normalizeComicFormat("hard-cover"), "hc");
    assert.equal(normalizeComicFormat("hardback"), "hc");
  });

  it("maps trade aliases to tpb", () => {
    assert.equal(normalizeComicFormat("trade"), "tpb");
    assert.equal(normalizeComicFormat("Trade Paperback"), "tpb");
    assert.equal(normalizeComicFormat("tp"), "tpb");
  });
});

describe("collected vs issues", () => {
  it("treats tpb / hc / omnibus as collected", () => {
    assert.equal(isCollectedFormat("tpb"), true);
    assert.equal(isCollectedFormat("hardcover"), true);
    assert.equal(isCollectedFormat("omnibus"), true);
    assert.equal(isCollectedFormat("single"), false);
    assert.equal(isCollectedFormat("annual"), false);
    assert.equal(isCollectedFormat("facsimile"), false);
  });

  it("labels collected formats for badges", () => {
    assert.equal(comicFormatLabel("tpb"), "TPB");
    assert.equal(comicFormatLabel("hardcover"), "HC");
    assert.equal(comicFormatLabel("omnibus"), "Omnibus");
  });

  it("splits the static catalog without inventing rows", () => {
    const collected = filterCollectedComics(COMICS);
    const issues = filterIssueComics(COMICS);
    assert.equal(collected.length + issues.length, COMICS.length);
    assert.ok(collected.every(isCollectedComic));
    assert.ok(issues.every((c) => !isCollectedComic(c)));
    assert.ok(collected.some((c) => c.id === "dc-hush-tpb"));
    assert.ok(collected.some((c) => c.id === "dc-yl-batman"));
    assert.ok(collected.some((c) => c.id === "im-rat-queens-deluxe-hardcover-1"));
    assert.ok(collected.some((c) => c.id === "dc-superman-death-and-return-of-superman-nn"));
    assert.ok(collected.some((c) => c.id === "im-invincible-compendium-1"));
    assert.ok(collected.some((c) => c.id === "dc-elseworlds-superman-1-2024-edition"));
    assert.ok(issues.every((c) => c.id !== "dc-hush-tpb"));
    assert.ok(issues.every((c) => c.id !== "dc-superman-death-and-return-of-superman-nn"));
  });

  it("lists collected editions for one publisher only", () => {
    const dc = collectedForPublisher(COMICS, "DC Comics");
    assert.ok(dc.some((c) => c.id === "dc-superman-death-and-return-of-superman-nn"));
    assert.ok(dc.every((c) => isCollectedComic(c)));
    assert.ok(!dc.some((c) => c.id === "im-invincible-compendium-1"));
  });

  it("normalizes hardcover catalog rows to hc", () => {
    const rat = COMICS.find((c) => c.id === "im-rat-queens-deluxe-hardcover-1");
    assert.ok(rat);
    assert.equal(rat.format, "hc");
  });
});

describe("catalogFromCustom", () => {
  it("projects a custom collected book", () => {
    const custom: CustomComic = {
      id: "custom-death-return",
      series: "Superman: The Death and Return of Superman Compendium",
      issue: "nn",
      publisher: "DC Comics",
      format: "tpb",
      upc: "978-1-79950-149-7",
    };
    const row = catalogFromCustom(custom);
    assert.equal(row.id, custom.id);
    assert.equal(row.format, "tpb");
    assert.equal(isCollectedComic(row), true);
  });
});

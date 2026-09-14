import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  assignSeriesRunYears,
  buildPublisherList,
  buildSeriesList,
  compareIsoDateDesc,
  sortCatalogComics,
  sortPublisherList,
  sortSeriesList,
  type CatalogComicSortable,
  type PublisherRef,
  type SeriesRef,
} from "@/lib/comic-series";
import type { CatalogComic } from "@/lib/types";

function comic(partial: Partial<CatalogComic> & Pick<CatalogComic, "id" | "series" | "issue">): CatalogComic {
  return {
    publisher: "Marvel Comics",
    coverDate: "2020-01-01",
    writers: [],
    artists: [],
    description: "",
    msrp: 4.99,
    format: "single",
    demand: 0,
    palette: ["111827", "dc2626", "f8fafc"],
    ...partial,
  };
}

function series(partial: Partial<SeriesRef> & Pick<SeriesRef, "key" | "title">): SeriesRef {
  return {
    publisher: "Marvel Comics",
    titleNorm: partial.title.toLowerCase(),
    year: 2020,
    issueCount: 1,
    latestDate: "2020-01-01",
    ...partial,
  };
}

describe("compareIsoDateDesc", () => {
  it("orders newest first and sinks missing dates", () => {
    assert.equal(compareIsoDateDesc("2024-06-01", "2020-01-01"), -1);
    assert.equal(compareIsoDateDesc("2020-01-01", "2024-06-01"), 1);
    assert.equal(compareIsoDateDesc("", "2024-06-01"), 1);
    assert.equal(compareIsoDateDesc("2024-06-01", ""), -1);
    assert.equal(compareIsoDateDesc("2024-06-01", "2024-06-01"), 0);
  });
});

describe("sortCatalogComics", () => {
  const list: CatalogComicSortable[] = [
    { id: "z", series: "Zatanna", issue: "1", coverDate: "2025-01-01" },
    { id: "a", series: "Action Comics", issue: "1000", coverDate: "2018-06-01", streetDate: "2018-06-06" },
    { id: "b", series: "Batman", issue: "1", coverDate: "2016-08-01" },
  ];

  it("sorts A–Z by series then issue", () => {
    const out = sortCatalogComics(list, "name");
    assert.deepEqual(
      out.map((c) => c.id),
      ["a", "b", "z"],
    );
  });

  it("sorts release date newest first (not A–Z)", () => {
    const out = sortCatalogComics(list, "release");
    assert.deepEqual(
      out.map((c) => c.id),
      ["z", "a", "b"],
    );
  });

  it("sorts issue numbers numerically", () => {
    const issues: CatalogComicSortable[] = [
      { id: "10", series: "X", issue: "10", coverDate: "2020-01-01" },
      { id: "2", series: "X", issue: "2", coverDate: "2020-02-01" },
      { id: "1", series: "X", issue: "1", coverDate: "2020-03-01" },
    ];
    assert.deepEqual(
      sortCatalogComics(issues, "issue").map((c) => c.id),
      ["1", "2", "10"],
    );
  });

  it("sorts acquired with unowned titles last", () => {
    const owned = new Map([
      ["z", { addedAt: "2026-01-01T00:00:00.000Z" }],
      ["b", { addedAt: "2026-06-01T00:00:00.000Z" }],
    ]);
    const out = sortCatalogComics(list, "acquired", { ownedByCatalog: owned });
    assert.deepEqual(
      out.map((c) => c.id),
      ["b", "z", "a"],
    );
  });
});

describe("sortSeriesList", () => {
  const list: SeriesRef[] = [
    series({ key: "m|wolverine|2020", title: "Wolverine", year: 2020, latestDate: "2024-01-01" }),
    series({ key: "m|amazing|1963", title: "Amazing Spider-Man", year: 1963, latestDate: "2022-01-01" }),
    series({ key: "m|amazing|2022", title: "Amazing Spider-Man", year: 2022, latestDate: "2025-09-01" }),
  ];

  it("A–Z groups title then newest run year", () => {
    const out = sortSeriesList(list, "name");
    assert.deepEqual(
      out.map((s) => s.key),
      ["m|amazing|2022", "m|amazing|1963", "m|wolverine|2020"],
    );
  });

  it("release date uses latestDate newest first", () => {
    const out = sortSeriesList(list, "release");
    assert.deepEqual(
      out.map((s) => s.key),
      ["m|amazing|2022", "m|wolverine|2020", "m|amazing|1963"],
    );
  });

  it("acquired uses owned timestamps then falls back to name", () => {
    const acquired = new Map([["m|wolverine|2020", "2026-08-01T00:00:00.000Z"]]);
    const out = sortSeriesList(list, "acquired", acquired);
    assert.equal(out[0]?.key, "m|wolverine|2020");
  });
});

describe("sortPublisherList", () => {
  const list: PublisherRef[] = [
    { publisher: "Marvel Comics", seriesCount: 2, issueCount: 10, latestDate: "2020-01-01" },
    { publisher: "Image", seriesCount: 1, issueCount: 4, latestDate: "2025-01-01" },
    { publisher: "DC Comics", seriesCount: 3, issueCount: 8, latestDate: "2024-06-01" },
  ];

  it("A–Z is alphabetical", () => {
    assert.deepEqual(
      sortPublisherList(list, "name").map((p) => p.publisher),
      ["DC Comics", "Image", "Marvel Comics"],
    );
  });

  it("release date is newest publisher activity first", () => {
    assert.deepEqual(
      sortPublisherList(list, "release").map((p) => p.publisher),
      ["Image", "DC Comics", "Marvel Comics"],
    );
  });
});

describe("buildSeriesList latestDate", () => {
  it("tracks the newest street/cover date in a run", () => {
    const comics = [
      comic({ id: "asm-1", series: "Amazing Spider-Man", issue: "1", coverDate: "2022-01-01", streetDate: "2022-01-12" }),
      comic({ id: "asm-2", series: "Amazing Spider-Man", issue: "2", coverDate: "2022-02-01", streetDate: "2022-02-09" }),
      comic({ id: "wolv-1", series: "Wolverine", issue: "1", coverDate: "2020-01-01" }),
    ];
    const yearById = assignSeriesRunYears(comics);
    const seriesList = buildSeriesList(comics, yearById, "Marvel Comics");
    const asm = seriesList.find((s) => /amazing/i.test(s.title));
    const wolv = seriesList.find((s) => /wolverine/i.test(s.title));
    assert.equal(asm?.latestDate, "2022-02-09");
    assert.equal(wolv?.latestDate, "2020-01-01");

    const pubs = buildPublisherList(comics, yearById);
    assert.equal(pubs[0]?.latestDate, "2022-02-09");
  });
});

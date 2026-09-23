import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { collapseFigureSets, getFigureSetMembers } from "@/lib/figure-sets";
import type { CatalogFigure } from "@/lib/types";

function fig(partial: Partial<CatalogFigure> & Pick<CatalogFigure, "id" | "name">): CatalogFigure {
  return {
    subtitle: "",
    line: "Blokees Galaxy Version",
    company: "blokees",
    kind: "kit",
    releaseDate: "2024-01-01",
    msrp: 8.99,
    scale: '4"',
    demand: 1,
    tags: ["transformers"],
    ...partial,
  };
}

describe("collapseFigureSets", () => {
  it("hides children when a parent shares the set", () => {
    const parent = fig({ id: "parent", name: "Galaxy Version 01", setId: "gv01", setRole: "parent" });
    const jazz = fig({ id: "jazz", name: "Jazz", setId: "gv01", setRole: "member" });
    const bee = fig({ id: "bee", name: "Bumblebee", setId: "gv01", setRole: "member" });
    const solo = fig({ id: "tarn", name: "Tarn", line: "Blokees Action Edition" });
    const collapsed = collapseFigureSets([jazz, solo, parent, bee]);
    assert.deepEqual(
      collapsed.map((row) => row.id),
      ["parent", "tarn"],
    );
  });

  it("keeps a lone child when the rest of the family is filtered out", () => {
    const jazz = fig({ id: "jazz", name: "Jazz", setId: "gv01", setRole: "member" });
    assert.deepEqual(collapseFigureSets([jazz]).map((row) => row.id), ["jazz"]);
  });

  it("does not collapse rows that have no set id", () => {
    const a = fig({ id: "a", name: "Optimus Prime" });
    const b = fig({ id: "b", name: "Megatron" });
    assert.equal(collapseFigureSets([a, b]).length, 2);
  });
});

describe("getFigureSetMembers", () => {
  it("returns the family only when more than one catalog row shares the set", () => {
    const parent = fig({ id: "parent", name: "Set", setId: "gv01", setRole: "parent" });
    const jazz = fig({ id: "jazz", name: "Jazz", setId: "gv01", setRole: "member" });
    const other = fig({ id: "other", name: "Other", setId: "gv02", setRole: "parent" });
    const members = getFigureSetMembers(jazz, [other, jazz, parent]);
    assert.deepEqual(members.map((row) => row.id), ["parent", "jazz"]);
  });

  it("returns just the figure for a single-figure SKU", () => {
    const tarn = fig({ id: "tarn", name: "Tarn" });
    assert.deepEqual(getFigureSetMembers(tarn, [tarn]).map((row) => row.id), ["tarn"]);
  });
});

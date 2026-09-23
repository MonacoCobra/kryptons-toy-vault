import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { figureMatchesFranchise, matchFigureProperty, matchTransformersParty } from "@/lib/figure-property";
import type { FigureFranchiseInput } from "@/lib/figure-property";

function row(partial: Partial<FigureFranchiseInput> & Pick<FigureFranchiseInput, "name" | "company" | "line">): FigureFranchiseInput {
  return { id: partial.id ?? partial.name.toLowerCase().replace(/\s+/g, "-"), subtitle: "", tags: [], ...partial };
}

describe("transformers parties", () => {
  it("tags Hasbro and Takara Transformers as 1P", () => {
    assert.equal(matchTransformersParty(row({ name: "Optimus Prime", line: "Transformers Studio Series", company: "hasbro", tags: ["transformers"] })), "1p");
    assert.equal(matchTransformersParty(row({ name: "Optimus Prime", line: "Transformers MPG", company: "takaratomy" })), "1p");
    assert.equal(matchFigureProperty(row({ name: "Megatron", line: "Marvel Legends", company: "hasbro", tags: ["marvel"] })), "marvel");
  });

  it("does not treat Diaclone or Kenner Super Powers as Transformers", () => {
    assert.equal(matchTransformersParty(row({ name: "Dia-Battles", line: "Diaclone Reboot", company: "takaratomy" })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Batman", line: "Kenner Super Powers", company: "kenner" })), "dc");
    assert.equal(matchTransformersParty(row({ name: "Megatron", line: "Super7 ReAction", company: "kenner", tags: ["transformers"] })), "1p");
  });

  it("gates Blokees by Transformers in the title and excludes Gundam, Herospire, and Legend Edition", () => {
    const prime = row({ name: "Optimus Prime", subtitle: "Transformers Galaxy Version", line: "Blokees Galaxy Version", company: "blokees" });
    assert.equal(matchTransformersParty(prime), "2p");
    assert.equal(matchFigureProperty(prime), "transformers");
    assert.equal(matchFigureProperty(row({ name: "RX-78-2 Gundam", subtitle: "Gundam Galaxy Version", line: "Blokees Gundam", company: "blokees", id: "blk-rx78" })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Sun Wukong", line: "Blokees Herospire Warrior", company: "blokees" })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Evangelion", line: "Blokees Legend Edition", company: "blokees" })), undefined);
    assert.equal(matchTransformersParty(row({ name: "Batman", line: "Blokees Champion Class", company: "blokees", tags: ["dc"] })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Batman", line: "Blokees Champion Class", company: "blokees" })), "dc");
    assert.equal(matchTransformersParty(row({ name: "CT03 Motormaster", subtitle: "Blokees Wheels Transformers", line: "Blokees Wheels", company: "blokees", id: "blokees-wheels-transformers-ct03-motormaster" })), "2p");
  });

  it("gates threezero, Yolopark, Flame Toys, and Super7", () => {
    assert.equal(matchTransformersParty(row({ name: "Elita-1", subtitle: "Transformers One DLX", line: "threezero DLX", company: "threezero" })), "2p");
    assert.equal(matchTransformersParty(row({ name: "Sojourn", subtitle: "Overwatch 2", line: "threezero Overwatch", company: "threezero" })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Snake Eyes", subtitle: "G.I. Joe DLX", line: "threezero DLX", company: "threezero" })), "gi-joe");
    assert.equal(matchTransformersParty(row({ name: "Voltes V Mech", subtitle: "Voltes V", line: "Yolopark AMK", company: "yolopark" })), undefined);
    assert.equal(matchTransformersParty(row({ name: "Optimus Prime", subtitle: "The Last Knight", line: "Yolopark AMK", company: "yolopark" })), "2p");
    assert.equal(matchTransformersParty(row({ name: "Arcee", subtitle: "Kuro Kara Kuri", line: "Kuro Kara Kuri", company: "flametoys" })), "2p");
    assert.equal(matchTransformersParty(row({ name: "Flame Metallic Set", subtitle: "Special", line: "Flame Toys Special", company: "flametoys" })), undefined);
    assert.equal(matchTransformersParty(row({ name: "Megatron", subtitle: "ReAction", line: "Super7 ReAction", company: "super7", tags: ["transformers"] })), "2p");
    assert.equal(matchTransformersParty(row({ name: "He-Man", line: "Super7 ULTIMATES!", company: "super7", tags: ["motu"] })), undefined);
  });

  it("puts known KO companies in 3P and leaves Beast Kingdom out", () => {
    assert.equal(matchTransformersParty(row({ name: "MS-B36", line: "B Series", company: "magicsquare" })), "3p");
    assert.equal(matchTransformersParty(row({ name: "Dynamic Action Heroes Batman", line: "Dynamic Action Heroes", company: "beastkingdom" })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Batman", line: "Dynamic Action Heroes", company: "beastkingdom" })), "dc");
  });
});

describe("other franchises", () => {
  it("keeps Gunpla and rejects 30MM unless the kit is Gundam-named", () => {
    assert.equal(matchFigureProperty(row({ name: "RX-78-2 Gundam", line: "High Grade", company: "bandai" })), "gundam");
    assert.equal(matchFigureProperty(row({ name: "Alto", line: "30 Minutes Missions", company: "bandai" })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Gundam Barbatos", line: "30 Minutes Missions", company: "bandai" })), "gundam");
  });

  it("does not let a dirty WWE tag pull Masterverse into WWE", () => {
    const heman = row({ name: "He-Man", line: "Masters of the Universe Masterverse", company: "mattel", tags: ["wwe", "motu"] });
    assert.equal(matchFigureProperty(heman), "motu");
    assert.equal(matchFigureProperty(row({ name: "Stone Cold", line: "WWE Elite", company: "mattel", tags: ["wwe"] })), "wwe");
  });

  it("does not treat Spawn-only rows as DC", () => {
    assert.equal(matchFigureProperty(row({ name: "Spawn", line: "Spawn", company: "mcfarlane", tags: ["spawn"] })), undefined);
    assert.equal(matchFigureProperty(row({ name: "Batman", line: "DC Multiverse", company: "mcfarlane" })), "dc");
  });

  it("filters a Transformers party without matching Marvel rows", () => {
    const tf = row({ name: "Jazz", line: "Transformers Legacy", company: "hasbro", tags: ["transformers"] });
    const marvel = row({ name: "Wolverine", line: "Marvel Legends", company: "hasbro", tags: ["marvel"] });
    assert.equal(figureMatchesFranchise(tf, "transformers", "1p"), true);
    assert.equal(figureMatchesFranchise(tf, "transformers", "3p"), false);
    assert.equal(figureMatchesFranchise(marvel, "transformers"), false);
    assert.equal(figureMatchesFranchise(marvel, "marvel"), true);
  });
});

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  figureMatchesFranchise,
  indexFranchiseBrowse,
  matchFigureProperty,
  matchTransformersParty,
  reclassifyUnbrandedKoCompany,
  reconcileBrowseSelection,
  stampFigureFranchise,
  textIsUnbrandedTransformersKo,
} from "@/lib/figure-property";
import { COMPANIES } from "@/data/companies";
import { FIGURES } from "@/data/figures";
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

  it("puts Unbranded and legacy unknown catch-alls in Transformers 3P", () => {
    const mp10 = row({
      name: "Optimus Prime",
      subtitle: "Unbranded knockoff",
      line: "MP10 KO",
      company: "unbranded",
      tags: ["transformers", "ko"],
    });
    const deformation = row({
      name: "Optimus Prime",
      subtitle: "No maker",
      line: "Deformation",
      company: "unknown",
      tags: ["transformers", "ko"],
    });
    assert.equal(matchTransformersParty(mp10), "3p");
    assert.equal(matchFigureProperty(mp10), "transformers");
    assert.equal(matchTransformersParty(deformation), "3p");
    assert.equal(reclassifyUnbrandedKoCompany(deformation), "unbranded");
    assert.equal(reclassifyUnbrandedKoCompany(mp10), "unbranded");

    const stamped = stampFigureFranchise({
      ...deformation,
      subtitle: deformation.subtitle ?? "",
      kind: "figure",
      releaseDate: "2016-01-01",
      msrp: 40,
      scale: "MP",
      demand: 1,
      tags: deformation.tags ?? [],
    });
    assert.equal(stamped.company, "unbranded");
    assert.equal(stamped.line, "Deformation");
    assert.equal(stamped.party, "3p");

    const legacy = stampFigureFranchise({
      id: "tf-def",
      name: "Megatron",
      subtitle: "KO",
      line: "Deformation",
      company: "other",
      kind: "figure",
      releaseDate: "2016-01-01",
      msrp: 40,
      scale: "MP",
      demand: 1,
      tags: ["transformers", "ko"],
    });
    assert.equal(legacy.company, "unbranded");
    assert.equal(legacy.line, "Deformation");

    const figures = [
      row({ id: "tf-op", name: "Optimus Prime", line: "Transformers Studio Series", company: "hasbro", tags: ["transformers"] }),
      row({ id: "tf-blk", name: "Optimus Prime", subtitle: "Transformers Galaxy Version", line: "Blokees Galaxy Version", company: "blokees" }),
      row({ id: "tf-ko", name: "MS-B36", line: "B Series", company: "magicsquare" }),
      mp10,
      legacy,
      row({ id: "marvel", name: "Wolverine", line: "Marvel Legends", company: "hasbro", tags: ["marvel"] }),
      row({ id: "tb", name: "Spider-Man", line: "Marvel Legends", company: "toybiz", tags: ["marvel"] }),
      row({ id: "wwe", name: "Stone Cold", line: "WWE Elite", company: "mattel", tags: ["wwe"] }),
    ];
    const third = indexFranchiseBrowse(figures, "transformers", "3p");
    assert.deepEqual([...third.byCompany.keys()], ["magicsquare", "unbranded"]);
    assert.equal(third.byCompany.has("hasbro"), false);
    assert.equal(third.byCompany.has("blokees"), false);
    assert.equal(third.byCompany.has("toybiz"), false);
    assert.equal(third.byCompany.has("mattel"), false);
    assert.equal(third.byCompany.has("other"), false);
    assert.equal(third.byCompany.get("unbranded")?.total, 2);
    assert.deepEqual(third.byCompany.get("unbranded")?.lines, ["MP10 KO", "Deformation"]);
  });

  it("does not sweep branded 3P or official 1P/2P into Unbranded", () => {
    const magic = row({ name: "MS-B36", line: "B Series", company: "magicsquare" });
    const wei = row({
      name: "Battle Commander",
      subtitle: "WJ-MPP10 — MP Optimus Prime homage",
      line: "Robot Force",
      company: "weijiang",
      tags: ["transformers", "ko"],
    });
    const bmb = row({
      name: "4th Party No Brand Bmb T-11",
      subtitle: "T-11",
      line: "BMB",
      company: "blackmamba",
      tags: ["ko"],
    });
    const official = row({
      name: "Optimus Prime",
      subtitle: "MP-10 Convoy",
      line: "Transformers Masterpiece",
      company: "hasbro",
      tags: ["transformers"],
    });
    const licensee = row({
      name: "Optimus Prime",
      subtitle: "Transformers Galaxy Version",
      line: "Blokees Galaxy Version",
      company: "blokees",
    });
    const misfiledNamed = row({
      name: "Magic Square MS-B36",
      line: "B Series",
      company: "other",
      tags: ["transformers"],
    });
    assert.equal(reclassifyUnbrandedKoCompany(magic), "magicsquare");
    assert.equal(reclassifyUnbrandedKoCompany(wei), "weijiang");
    assert.equal(reclassifyUnbrandedKoCompany(bmb), "blackmamba");
    assert.equal(reclassifyUnbrandedKoCompany(official), "hasbro");
    assert.equal(matchTransformersParty(official), "1p");
    assert.equal(reclassifyUnbrandedKoCompany(licensee), "blokees");
    assert.equal(matchTransformersParty(licensee), "2p");
    assert.equal(reclassifyUnbrandedKoCompany(misfiledNamed), "other");
    assert.equal(textIsUnbrandedTransformersKo("wei jiang mpp10 deformation era battle commander"), false);
    assert.equal(textIsUnbrandedTransformersKo("hasbro transformers masterpiece mp-10 convoy"), false);
    assert.equal(textIsUnbrandedTransformersKo("optimus prime mp10 ko deformation"), true);

    const mistag = row({
      name: "Optimus Prime",
      subtitle: "MP10 KO",
      line: "MP10 KO",
      company: "hasbro",
      tags: ["transformers", "ko"],
    });
    assert.equal(reclassifyUnbrandedKoCompany(mistag), "unbranded");
    assert.equal(mistag.line, "MP10 KO");
    const moved = stampFigureFranchise({
      ...mistag,
      subtitle: mistag.subtitle ?? "",
      kind: "figure",
      releaseDate: "2016-01-01",
      msrp: 30,
      scale: "MP",
      demand: 1,
      tags: mistag.tags ?? [],
    });
    assert.equal(moved.company, "unbranded");
    assert.equal(moved.party, "3p");
    assert.equal(moved.line, "MP10 KO");
  });

  it("keeps the live catalog's branded makers off the Unbranded card", () => {
    assert.equal(COMPANIES.some((c) => c.id === "unbranded" && c.short === "Unbranded"), true);
    const third = indexFranchiseBrowse(FIGURES, "transformers", "3p");
    assert.equal(third.byCompany.has("hasbro"), false);
    assert.equal(third.byCompany.has("takaratomy"), false);
    assert.equal(third.byCompany.has("blokees"), false);
    assert.equal(third.byCompany.has("threezero"), false);
    assert.equal(third.byCompany.has("yolopark"), false);
    assert.equal(third.byCompany.has("toybiz"), false);
    assert.equal(third.byCompany.has("mattel"), false);
    assert.equal(third.byCompany.has("magicsquare"), true);
    assert.equal(third.byCompany.has("weijiang"), true);
    assert.equal(third.byCompany.has("blackmamba"), true);

    const unbranded = FIGURES.filter((f) => f.company === "unbranded");
    assert.ok(unbranded.length >= 28);
    assert.equal(third.byCompany.get("unbranded")?.total, unbranded.length);
    for (const figure of unbranded) {
      assert.equal(figure.property, "transformers");
      assert.equal(figure.party, "3p");
      assert.equal(figure.sku, undefined);
    }
    const mp10 = FIGURES.find((f) => f.id === "unbranded-mp10-mp44-color");
    assert.equal(mp10?.name, "MP10 Optimus Prime");
    assert.equal(mp10?.line, "MP10 KO");
    assert.equal(mp10?.company, "unbranded");
    assert.equal(mp10?.party, "3p");
    assert.equal(mp10?.property, "transformers");
    assert.match(mp10?.imageUrl ?? "", /^https:\/\/cdn\.shopify\.com\//);
    const legends = FIGURES.find((f) => f.id === "unbranded-sd-01");
    assert.equal(legends?.line, "Legends KO");
    assert.equal(legends?.company, "unbranded");
    assert.equal(FIGURES.find((f) => f.id === "tfmp-mp10")?.company, "hasbro");
    assert.equal(FIGURES.find((f) => f.id === "tfmp-mp10")?.party, "1p");
    assert.equal(FIGURES.find((f) => f.id === "weijiang-wj-mpp10")?.company, "weijiang");
    assert.equal(FIGURES.find((f) => f.id === "weijiang-wj-mpp10")?.party, "3p");
    assert.equal(FIGURES.find((f) => f.id === "lewin-lwh-01-spike")?.company, "lewin");
    assert.equal(FIGURES.find((f) => f.id === "blackmamba-t-11")?.company, "blackmamba");
    assert.equal(FIGURES.find((f) => f.id === "blackmamba-jh01")?.company, "blackmamba");
  });

  it("keeps Show.Z third-party makers on the Transformers 3P rail", () => {
    for (const id of ["galaxytoys", "badcube", "01studio", "metagate", "dreamstartoys"]) {
      assert.equal(COMPANIES.some((c) => c.id === id), true);
      const sample = row({ name: "Optimus Prime", line: "Show.Z", company: id, tags: ["transformers", "3p"] });
      assert.equal(matchTransformersParty(sample), "3p");
      assert.equal(matchFigureProperty(sample), "transformers");
    }
    assert.equal(
      matchTransformersParty(row({ name: "Skybreaker", line: "Brave General", company: "djs", tags: ["transformers"] })),
      "3p",
    );
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

  it("limits company rails to makers that have the selected franchise", () => {
    const figures = [
      row({ id: "tf-op", name: "Optimus Prime", line: "Transformers Studio Series", company: "hasbro", tags: ["transformers"] }),
      row({ id: "tf-blk", name: "Optimus Prime", subtitle: "Transformers Galaxy Version", line: "Blokees Galaxy Version", company: "blokees" }),
      row({ id: "tf-ko", name: "MS-B36", line: "B Series", company: "magicsquare" }),
      row({ id: "marvel", name: "Wolverine", line: "Marvel Legends", company: "hasbro", tags: ["marvel"] }),
      row({ id: "tb", name: "Spider-Man", line: "Marvel Legends", company: "toybiz", tags: ["marvel"] }),
      row({ id: "wwe", name: "Stone Cold", line: "WWE Elite", company: "mattel", tags: ["wwe"] }),
    ];
    const transformers = indexFranchiseBrowse(figures, "transformers", undefined, (id) => id === "tf-op");
    assert.deepEqual([...transformers.byCompany.keys()], ["hasbro", "blokees", "magicsquare"]);
    assert.equal(transformers.byCompany.has("toybiz"), false);
    assert.equal(transformers.byCompany.has("mattel"), false);
    assert.equal(transformers.byCompany.get("hasbro")?.owned, 1);
    assert.equal(transformers.byCompany.get("hasbro")?.total, 1);
    assert.deepEqual(transformers.byCompany.get("hasbro")?.lines, ["Transformers Studio Series"]);

    const firstParty = indexFranchiseBrowse(figures, "transformers", "1p");
    assert.deepEqual([...firstParty.byCompany.keys()], ["hasbro"]);

    const thirdParty = indexFranchiseBrowse(figures, "transformers", "3p");
    assert.deepEqual([...thirdParty.byCompany.keys()], ["magicsquare"]);

    const marvel = indexFranchiseBrowse(figures, "marvel");
    assert.deepEqual([...marvel.byCompany.keys()], ["hasbro", "toybiz"]);
    assert.equal(marvel.byCompany.has("mattel"), false);

    const all = indexFranchiseBrowse(figures);
    assert.equal(all.byCompany.has("toybiz"), true);
    assert.equal(all.byCompany.has("mattel"), true);

    assert.deepEqual(
      reconcileBrowseSelection(figures, { company: "mattel", line: "WWE Elite" }, "transformers"),
      { company: undefined, line: undefined },
    );
    assert.deepEqual(
      reconcileBrowseSelection(figures, { company: "hasbro", line: "Marvel Legends" }, "transformers", "1p"),
      { company: "hasbro", line: undefined },
    );
    assert.deepEqual(
      reconcileBrowseSelection(figures, { company: "hasbro", line: "Transformers Studio Series" }, "transformers", "1p"),
      { company: "hasbro", line: "Transformers Studio Series" },
    );
    assert.deepEqual(
      reconcileBrowseSelection(figures, { company: "mattel", line: "WWE Elite" }),
      { company: "mattel", line: "WWE Elite" },
    );
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

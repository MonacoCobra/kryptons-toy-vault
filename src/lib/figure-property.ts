import type { CatalogFigure, FigureProperty, TransformersParty } from "@/lib/types";

/**
 * High-precision franchise tagging for figure browse.
 * Match order: hard excludes → line / tag → company allowlists → name lexicon.
 * A miss stays untagged. Company name alone is not a franchise.
 */

export type FigureFranchiseInput = {
  id: string;
  name: string;
  subtitle?: string;
  line: string;
  company: string;
  tags?: string[];
};

export const POPULAR_FRANCHISES: { id: FigureProperty; label: string }[] = [
  { id: "dc", label: "DC" },
  { id: "marvel", label: "Marvel" },
  { id: "transformers", label: "Transformers" },
  { id: "gundam", label: "Gundam" },
  { id: "gi-joe", label: "G.I. Joe" },
  { id: "tmnt", label: "TMNT" },
  { id: "star-wars", label: "Star Wars" },
  { id: "motu", label: "Masters of the Universe" },
  { id: "wwe", label: "WWE" },
  { id: "power-rangers", label: "Power Rangers" },
  { id: "naruto", label: "Naruto" },
  { id: "demon-slayer", label: "Demon Slayer" },
  { id: "dragon-ball", label: "Dragon Ball" },
  { id: "one-piece", label: "One Piece" },
];

export const TRANSFORMERS_PARTIES: { id: TransformersParty; label: string }[] = [
  { id: "1p", label: "1P Hasbro / Takara" },
  { id: "2p", label: "2P Licensees" },
  { id: "3p", label: "3P / KO" },
];

const PROPERTY_IDS = new Set<string>(POPULAR_FRANCHISES.map((p) => p.id));

export function isFigureProperty(value: unknown): value is FigureProperty {
  return typeof value === "string" && PROPERTY_IDS.has(value);
}

export function isTransformersParty(value: unknown): value is TransformersParty {
  return value === "1p" || value === "2p" || value === "3p";
}

/** Known Transformers-only third-party / KO makers. Never used for Super7 or Beast Kingdom. */
const TF_3P = new Set([
  "magicsquare",
  "weijiang",
  "blackmamba",
  "newage",
  "fanstoys",
  "ironfactory",
  "uniquetoys",
  "toyworld",
  "perfecteffect",
  "robotparadise",
  "apctoys",
  "moonstudio",
  "jxjiang",
  "toyhousefactory",
  "bpf",
  "dx9",
  "mastermind",
  "maketoys",
  "planetx",
  "kfc",
  "xtransbots",
  "tfc",
  "gcreation",
  "generationtoy",
  "zeta",
  "mechfans",
  "toywolf",
  "evolutiontoy",
  "fanshobby",
  "fansproject",
  "transart",
  "bingotoys",
  "cangtoys",
  "drwu",
]);

const GUNDAM_LINES =
  /^(high grade|gunpla|sd gundam|master grade|real grade|entry grade|perfect grade)\b/i;

const DC_PHRASES = [
  "batman",
  "superman",
  "wonder woman",
  "aquaman",
  "green lantern",
  "green arrow",
  "black adam",
  "shazam",
  "harley quinn",
  "catwoman",
  "nightwing",
  "batgirl",
  "batwoman",
  "red hood",
  "deathstroke",
  "darkseid",
  "brainiac",
  "doomsday",
  "lex luthor",
  "zatanna",
  "john constantine",
  "constantine",
  "swamp thing",
  "hawkman",
  "hawkgirl",
  "martian manhunter",
  "starfire",
  "beast boy",
  "peacemaker",
  "black canary",
  "supergirl",
  "superboy",
  "power girl",
  "blue beetle",
  "booster gold",
  "sinestro",
  "black manta",
  "ocean master",
  "lobo",
  "alfred pennyworth",
  "bruce wayne",
  "clark kent",
  "hal jordan",
  "barry allen",
  "dick grayson",
  "jason todd",
  "damian wayne",
  "barbara gordon",
  "tim drake",
  "justice league",
  "teen titans",
  "suicide squad",
  "arkham",
  "gotham",
  "dark knight",
  "man of steel",
  "the flash",
  "reverse-flash",
  "reverse flash",
  "wally west",
  "kyle rayner",
  "john stewart",
  "two-face",
  "scarecrow",
  "riddler",
  "the penguin",
  "poison ivy",
  "mr. freeze",
  "mister freeze",
  "killer croc",
  "ra's al ghul",
  "ras al ghul",
  "black mask",
  "deadshot",
  "king shark",
  "joker",
  "damian wayne",
  "tim drake",
  "dick grayson",
  "jason todd",
  "cyborg",
];

const MARVEL_PHRASES = [
  "spider-man",
  "spiderman",
  "wolverine",
  "deadpool",
  "iron man",
  "captain america",
  "black widow",
  "hawkeye",
  "thanos",
  "venom",
  "carnage",
  "magneto",
  "cyclops",
  "jean grey",
  "gambit",
  "rogue",
  "nightcrawler",
  "colossus",
  "professor x",
  "charles xavier",
  "mystique",
  "sabretooth",
  "apocalypse",
  "galactus",
  "silver surfer",
  "doctor doom",
  "fantastic four",
  "black panther",
  "doctor strange",
  "scarlet witch",
  "ant-man",
  "captain marvel",
  "ms. marvel",
  "she-hulk",
  "moon knight",
  "punisher",
  "ghost rider",
  "daredevil",
  "elektra",
  "jessica jones",
  "luke cage",
  "iron fist",
  "x-men",
  "avengers",
  "star-lord",
  "gamora",
  "rocket raccoon",
  "drax",
  "nebula",
  "winter soldier",
  "war machine",
  "nick fury",
  "miles morales",
  "peter parker",
  "green goblin",
  "doctor octopus",
  "doc ock",
  "hobgoblin",
  "mysterio",
  "kraven",
  "morbius",
  "knull",
  "kingpin",
  "psylocke",
  "emma frost",
  "cable",
  "domino",
  "spider-gwen",
  "black bolt",
  "silver samurai",
  "omega red",
  "lady deathstrike",
  "hulk",
  "thor",
  "loki",
  "ultron",
  "groot",
  "venom",
];

const STAR_WARS_PHRASES = [
  "star wars",
  "darth vader",
  "darth maul",
  "luke skywalker",
  "anakin",
  "obi-wan",
  "kenobi",
  "yoda",
  "mandalorian",
  "din djarin",
  "grogu",
  "ahsoka",
  "boba fett",
  "jango fett",
  "chewbacca",
  "han solo",
  "princess leia",
  "leia organa",
  "palpatine",
  "emperor palpatine",
  "stormtrooper",
  "clone trooper",
  "kylo ren",
  "poe dameron",
  "cassian andor",
  "grand admiral thrawn",
  "thrawn",
  "moff gideon",
  "bo-katan",
  "the armorer",
  "ig-11",
  "ig-88",
  "r2-d2",
  "c-3po",
  "bb-8",
  "general grievous",
  "count dooku",
  "mace windu",
  "qui-gon",
  "padme",
  "captain rex",
  "captain phasma",
  "poe dameron",
  "x-wing",
  "tie fighter",
];

const MOTU_PHRASES = [
  "he-man",
  "skeletor",
  "she-ra",
  "masters of the universe",
  "masterverse",
  "beast man",
  "man-at-arms",
  "teela",
  "evil-lyn",
  "hordak",
  "orko",
  "stratos",
  "trap jaw",
  "tri-klops",
  "ram man",
  "fisto",
  "grayskull",
  "snake mountain",
];

const TMNT_PHRASES = [
  "teenage mutant",
  "ninja turtle",
  "tmnt",
  "leonardo",
  "donatello",
  "michelangelo",
  "raphael",
  "shredder",
  "splinter",
  "bebop",
  "rocksteady",
  "krang",
  "april o'neil",
  "casey jones",
  "foot clan",
];

const GI_JOE_PHRASES = [
  "g.i. joe",
  "gi joe",
  "g.i joe",
  "snake eyes",
  "storm shadow",
  "cobra commander",
  "destro",
  "baroness",
  "zarana",
  "roadblock",
  "lady jaye",
  "sergeant slaughter",
];

function textOf(f: FigureFranchiseInput): string {
  return [f.name, f.subtitle ?? "", f.line, f.id, ...(f.tags ?? [])].join(" ").toLowerCase();
}

function hasPhrase(blob: string, phrase: string): boolean {
  const esc = phrase.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(?:^|[^a-z0-9])${esc}(?:[^a-z0-9]|$)`).test(blob);
}

function hasAny(blob: string, phrases: string[]): boolean {
  return phrases.some((p) => hasPhrase(blob, p));
}

function tagHas(f: FigureFranchiseInput, tag: string): boolean {
  return (f.tags ?? []).some((t) => t.toLowerCase() === tag);
}

function isMotu(f: FigureFranchiseInput, blob: string): boolean {
  const line = `${f.line} ${f.subtitle ?? ""}`;
  if (/masters of the universe|masterverse|\bmotu\b|primal age/i.test(line)) return true;
  if (tagHas(f, "motu")) return true;
  if (/mondo/i.test(f.line) && /motu|masters of the universe|he-man/i.test(blob)) return true;
  return false;
}

function isWwe(f: FigureFranchiseInput, blob: string): boolean {
  if (isMotu(f, blob)) return false;
  if (/\bwwe\b/i.test(f.line)) return true;
  if ((f.company === "mattel" || f.company === "jakks") && tagHas(f, "wwe") && !/masterverse|masters of the universe/i.test(blob)) {
    return true;
  }
  return false;
}

function blokeesBlocked(f: FigureFranchiseInput): boolean {
  if (f.company !== "blokees") return false;
  return /herospire|legend edition|gundam/i.test(`${f.line} ${f.name} ${f.subtitle ?? ""} ${f.id}`);
}

function isGundam(f: FigureFranchiseInput, blob: string): boolean {
  if (f.company === "blokees" || blokeesBlocked(f)) return false;
  const line = f.line;
  if (/30\s?minutes|30mm|30ms|30mf/i.test(line) && !/gundam/i.test(`${f.name} ${f.subtitle ?? ""} ${f.id}`)) {
    return false;
  }
  if (GUNDAM_LINES.test(line)) return true;
  if (/\bsd gundam\b/i.test(line)) return true;
  if (/gundam|gunpla/i.test(`${f.name} ${f.subtitle ?? ""} ${f.id} ${line}`)) return true;
  if ((/robot spirits|figure-rise/i.test(line) || f.company === "bandai") && /gundam|gunpla|\bzaku\b|\bsazabi\b/i.test(blob)) {
    return true;
  }
  return false;
}

export function matchTransformersParty(f: FigureFranchiseInput): TransformersParty | undefined {
  const blob = textOf(f);
  if (f.company === "blokees" && blokeesBlocked(f)) return undefined;

  if (f.company === "kenner") {
    return /transformers/i.test(blob) ? "1p" : undefined;
  }
  if (f.company === "hasbro" || f.company === "takaratomy") {
    if (/transformers/i.test(blob)) return "1p";
    if (f.company === "takaratomy" && /\bmpg\b/i.test(f.line)) return "1p";
    return undefined;
  }

  if (f.company === "blokees") {
    if (/transformers/i.test(blob)) return "2p";
    if (/wheels/i.test(`${f.line} ${f.name} ${f.subtitle ?? ""}`) && /transformers|\bct0\d\b|\bc0\d\b/i.test(blob)) {
      return "2p";
    }
    return undefined;
  }

  if (f.company === "threezero") {
    if (/overwatch|pacific rim/i.test(blob) && !/transformers/i.test(blob)) return undefined;
    return /transformers/i.test(blob) ? "2p" : undefined;
  }

  if (f.company === "yolopark") {
    if (/voltes|shurato|evangelion|\beva-\d|metal slug|minion/i.test(blob) && !/transformers/i.test(blob)) {
      return undefined;
    }
    return /transformers|beast wars|rise of the beasts|the last knight|dark of the moon|generation 1|\bg1\b|bumblebee|optimus|megatron|starscream|soundwave|shockwave|ironhide|mirage|arcee|blackarachnia/i.test(blob)
      ? "2p"
      : undefined;
  }

  if (f.company === "robosen") {
    if (/transformers/i.test(blob)) return "2p";
    if (/optimus|megatron|bumblebee|soundwave|starscream|elita|jazz/i.test(`${f.name} ${f.subtitle ?? ""}`)) return "2p";
    return undefined;
  }

  if (f.company === "flametoys") {
    if (/kuro kara kuri|furai model/i.test(f.line)) return "2p";
    if (/\bkkk\b|transformers|furai/i.test(blob)) return "2p";
    return undefined;
  }

  if (f.company === "super7") {
    return /transformers/i.test(`${f.name} ${f.subtitle ?? ""} ${f.id} ${(f.tags ?? []).join(" ")} ${f.line}`)
      ? "2p"
      : undefined;
  }

  if (TF_3P.has(f.company)) {
    if (/gundam|star wars|naruto|ultraman|one piece|dragon ball/i.test(blob) && !/transformers|optimus|megatron|bumblebee/i.test(blob)) {
      return undefined;
    }
    return "3p";
  }

  return undefined;
}

function marvelLine(f: FigureFranchiseInput): boolean {
  return /marvel legends|marvel select|s\.h\.figuarts marvel|jada marvel|mego marvel/i.test(f.line);
}

function dcLine(f: FigureFranchiseInput): boolean {
  if (/^spawn\b|\bmcfarlane spawn\b/i.test(f.line)) return false;
  if (f.company === "kenner" && /batman|super powers|dark knight/i.test(f.line)) return true;
  if (
    /\bdc\b|dc multiverse|dc direct|dc universe|dc infinite|dc collect|dc designer|dc essentials|dc super powers|justice league|page punchers|batman the brave|super powers|jada dc|s\.h\.figuarts dc|mondo btas/i.test(
      f.line,
    )
  ) {
    return true;
  }
  return false;
}

/** Character names are only trusted on mixed lines (Mezco, Hot Toys, MAFEX, SHF, Super7, …). */
function allowNameLexicon(f: FigureFranchiseInput): boolean {
  return (
    f.company === "mezco" ||
    f.company === "hottoys" ||
    f.company === "mafex" ||
    f.company === "shfiguarts" ||
    f.company === "beastkingdom" ||
    f.company === "storm" ||
    f.company === "mondo" ||
    f.company === "super7" ||
    f.company === "threezero" ||
    f.company === "neca" ||
    f.company === "figma" ||
    f.company === "sentinel" ||
    f.company === "blokees" ||
    f.company === "diamondselect" ||
    f.company === "medicom" ||
    f.company === "bandai" ||
    /one:12|mafex|hot toys|figuarts|dynamic action|ultimates|reaction|^figures$/i.test(f.line)
  );
}

function nameProperty(f: FigureFranchiseInput, blob: string): FigureProperty | undefined {
  if (!allowNameLexicon(f)) return undefined;
  if (isGundam(f, blob)) return "gundam";
  if (hasAny(blob, ["star wars"]) || hasAny(blob, STAR_WARS_PHRASES)) return "star-wars";
  if (hasAny(blob, MOTU_PHRASES)) return "motu";
  if (hasAny(blob, TMNT_PHRASES)) return "tmnt";
  if (hasAny(blob, GI_JOE_PHRASES)) return "gi-joe";
  if (/power rangers|mighty morphin/i.test(blob)) return "power-rangers";
  if (/one piece/i.test(blob) || hasAny(blob, ["monkey d. luffy", "roronoa zoro", "straw hat"])) return "one-piece";
  if (/naruto|shippuden/i.test(blob) || hasAny(blob, ["naruto uzumaki", "sasuke uchiha", "hatake kakashi", "itachi"])) return "naruto";
  if (/demon slayer|kimetsu/i.test(blob) || hasAny(blob, ["tanjiro", "nezuko", "zenitsu", "inosuke", "rengoku"])) {
    return "demon-slayer";
  }
  if (/dragon ball|dragonball/i.test(blob) || hasAny(blob, ["son goku", "goku", "vegeta", "piccolo", "frieza", "gohan", "broly"])) {
    return "dragon-ball";
  }
  if (hasAny(blob, MARVEL_PHRASES) || tagHas(f, "marvel")) return "marvel";
  if (/\bspawn\b/i.test(`${f.name} ${f.line}`) && !hasAny(blob, DC_PHRASES)) return undefined;
  if (hasAny(blob, DC_PHRASES) || tagHas(f, "dc")) return "dc";
  return undefined;
}

export function matchFigureProperty(f: FigureFranchiseInput): FigureProperty | undefined {
  const blob = textOf(f);

  if (isMotu(f, blob)) return "motu";
  if (isWwe(f, blob)) return "wwe";

  const party = matchTransformersParty(f);
  if (party) return "transformers";

  if (isGundam(f, blob)) return "gundam";

  if (/g\.?\s*i\.?\s*joe/i.test(f.line) || (f.company === "hasbro" && /gi joe classified/i.test(f.line))) return "gi-joe";
  if (/tmnt|teenage mutant|ninja turtle/i.test(f.line) || tagHas(f, "tmnt")) return "tmnt";
  if (/star wars|black series/i.test(f.line) || tagHas(f, "star-wars")) return "star-wars";
  if (/power rangers|mighty morphin/i.test(blob) || (f.company === "hasbro" && /lightning collection/i.test(f.line)) || tagHas(f, "power-rangers")) {
    return "power-rangers";
  }
  if (marvelLine(f)) return "marvel";
  if (dcLine(f)) return "dc";

  if (/s\.h\.figuarts naruto|naruto/i.test(f.line)) return "naruto";
  if (/demon slayer|kimetsu/i.test(f.line)) return "demon-slayer";
  if (/dragon ball|dragonball/i.test(f.line)) return "dragon-ball";
  if (/one piece/i.test(f.line)) return "one-piece";

  return nameProperty(f, blob);
}

export function figureMatchesFranchise(
  figure: FigureFranchiseInput & { property?: FigureProperty; party?: TransformersParty },
  property: FigureProperty,
  party?: TransformersParty,
): boolean {
  const tagged = figure.property ?? matchFigureProperty(figure);
  if (tagged !== property) return false;
  if (property === "transformers" && party) {
    const p = figure.party ?? matchTransformersParty(figure);
    return p === party;
  }
  return true;
}

type BrowseFigure = FigureFranchiseInput & {
  id: string;
  property?: FigureProperty;
  party?: TransformersParty;
};

export type FranchiseCompanyCount = {
  total: number;
  owned: number;
  lines: string[];
};

export type FranchiseBrowseIndex = {
  /** Rows in the franchise scope. The full catalog when no franchise is selected. */
  total: number;
  byCompany: Map<string, FranchiseCompanyCount>;
};

/**
 * Company totals and lines for the browse rail.
 * No franchise → every row. A franchise (and Transformers party, when set)
 * keeps only matching rows, so makers with zero hits drop out of `byCompany`.
 */
export function indexFranchiseBrowse(
  figures: readonly BrowseFigure[],
  property?: FigureProperty,
  party?: TransformersParty,
  isOwned?: (id: string) => boolean,
): FranchiseBrowseIndex {
  const activeParty = property === "transformers" ? party : undefined;
  const byCompany = new Map<string, FranchiseCompanyCount>();
  let total = 0;
  for (const figure of figures) {
    if (property && !figureMatchesFranchise(figure, property, activeParty)) continue;
    total += 1;
    let bucket = byCompany.get(figure.company);
    if (!bucket) {
      bucket = { total: 0, owned: 0, lines: [] };
      byCompany.set(figure.company, bucket);
    }
    bucket.total += 1;
    if (isOwned?.(figure.id)) bucket.owned += 1;
    if (!bucket.lines.includes(figure.line)) bucket.lines.push(figure.line);
  }
  return { total, byCompany };
}

/**
 * Drop a company or line that has no rows in the active franchise.
 * With no franchise selected, the selection is left as-is.
 */
export function reconcileBrowseSelection<C extends string>(
  figures: readonly BrowseFigure[],
  selection: { company?: C; line?: string },
  property?: FigureProperty,
  party?: TransformersParty,
): { company?: C; line?: string } {
  if (!property) return { company: selection.company, line: selection.line };
  if (!selection.company) return { company: undefined, line: undefined };
  const activeParty = property === "transformers" ? party : undefined;
  let companyOk = false;
  let lineOk = !selection.line;
  for (const figure of figures) {
    if (figure.company !== selection.company) continue;
    if (!figureMatchesFranchise(figure, property, activeParty)) continue;
    companyOk = true;
    if (selection.line && figure.line === selection.line) lineOk = true;
    if (companyOk && lineOk) break;
  }
  if (!companyOk) return { company: undefined, line: undefined };
  return { company: selection.company, line: lineOk ? selection.line : undefined };
}

/** Stamp property / party onto a catalog row. Does not invent set membership. */
export function stampFigureFranchise<T extends CatalogFigure>(figure: T): T {
  const property = matchFigureProperty(figure);
  const party = property === "transformers" ? matchTransformersParty(figure) : undefined;
  if (figure.property === property && figure.party === party) return figure;
  const next: T = { ...figure };
  if (property) next.property = property;
  else delete next.property;
  if (party) next.party = party;
  else delete next.party;
  return next;
}

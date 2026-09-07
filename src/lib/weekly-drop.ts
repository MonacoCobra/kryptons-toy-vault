import { createServerFn } from "@tanstack/react-start";
import seed from "@/data/weekly-seed.json";
import { fetchStorefrontFigures } from "@/lib/figure-storefronts";
import type { CatalogComic, CatalogFigure, ComicFormat, CompanyId, ItemKind, WeeklyDrop } from "@/lib/types";
import { slug, weekKey } from "@/lib/utils";

const COMPANIES: CompanyId[] = [
  "hasbro",
  "toybiz",
  "mattel",
  "mcfarlane",
  "mafex",
  "mezco",
  "bandai",
  "shfiguarts",
  "neca",
  "super7",
  "hottoys",
  "figma",
  "kotobukiya",
  "storm",
  "bossfight",
  "loyalsubjects",
  "premiumdna",
  "hiya",
  "mondo",
  "threezero",
  "dcdirect",
  "kenner",
  "valaverse",
  "jakks",
  "takaratomy",
  "playmates",
  "kaiyodo",
  "jazwares",
  "diamondselect",
  "joytoy",
  "beastkingdom",
  "enterbay",
  "funko",
  "fourhorsemen",
  "spinmaster",
  "sentinel",
  "thousandtoys",
  "acidrain",
  "freshmonkey",
  "jada",
  "blokees",
  "robosen",
  "newage",
  "fanstoys",
  "tunshi",
  "damtoys",
  "easysimple",
  "soldierstory",
  "minitimes",
  "verycool",
  "ironfactory",
  "magicsquare",
  "cangtoys",
  "medicom",
  "drwu",
  "dx9",
  "mastermind",
  "maketoys",
  "planetx",
  "kfc",
  "xtransbots",
  "flametoys",
  "tfc",
  "gcreation",
  "generationtoy",
  "zeta",
  "mechfans",
  "toywolf",
  "evolutiontoy",
  "starace",
  "exo6",
  "blitzway",
  "toynami",
  "creativebeast",
  "alertline",
  "snailshell",
  "asmus",
  "herocross",
  "fanshobby",
  "fansproject",
  "transart",
  "bingotoys",
  "heatboys",
  "ccstoys",
  "tbleague",
  "coomodel",
  "did",
  "moshow",
  "mego",
  "worldbox",
  "kaustic",
  "poptoys",
  "deviltoys",
  "kingarts",
  "jtstudio",
  "artspirits",
  "artstorm",
  "fiftytwo",
  "actiontoys",
  "underverse",
  "haoyu",
  "bigchief",
  "iconiq",
  "figurestoy",
  "toynotch",
  "actoys",
  "newwave",
  "flirtygirl",
  "firegirl",
  "i8toys",
  "nanmu",
  "vtoys",
];

const FORMATS: ComicFormat[] = ["single", "annual", "tpb", "hc", "omnibus", "facsimile"];

type DropRow = {
  week: string;
  fetched_at: string;
  comics: unknown;
  figures: unknown;
  status: string;
  error: string | null;
};

type MemSlot = { week: string; drop: WeeklyDrop };

const memRef = globalThis as typeof globalThis & { __kryptonWeeklyDrop__?: MemSlot };

function neonConfigured(): boolean {
  return Boolean(typeof process !== "undefined" && process.env.DATABASE_URL?.trim());
}

function hasItems(drop: WeeklyDrop | null | undefined): drop is WeeklyDrop {
  return Boolean(drop && (drop.comics.length || drop.figures.length));
}

function readMem(week: string): WeeklyDrop | null {
  const slot = memRef.__kryptonWeeklyDrop__;
  if (!slot || slot.week !== week) return null;
  return slot.drop;
}

function writeMem(drop: WeeklyDrop): void {
  memRef.__kryptonWeeklyDrop__ = { week: drop.week, drop };
}

function emptyDrop(week: string, error?: string): WeeklyDrop {
  return {
    week,
    fetchedAt: new Date().toISOString(),
    comics: [],
    figures: [],
    status: error ? "error" : "ok",
    error,
  };
}

function asArray(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value) as unknown;
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

function str(value: unknown): string {
  const s = typeof value === "string" ? value : value == null ? "" : String(value);
  return s.replace(/\u0000/g, "").trim();
}

function num(value: unknown, fallback: number): number {
  const n = typeof value === "number" ? value : Number.parseFloat(str(value).replace(/[^0-9.]/g, ""));
  return Number.isFinite(n) ? n : fallback;
}

function dateish(value: unknown, fallback: string): string {
  const s = str(value);
  const m = s.match(/(\d{4}-\d{2}-\d{2})/);
  if (m) return m[1]!;
  const md = s.match(/([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})/);
  if (md) {
    const d = new Date(`${md[1]} ${md[2]}, ${md[3]}`);
    if (!Number.isNaN(d.getTime())) return d.toISOString().slice(0, 10);
  }
  return fallback;
}

function issueNo(value: unknown): string {
  const s = str(value).replace(/^#/, "").trim();
  return s || "1";
}

function asFormat(value: unknown, series: string): ComicFormat {
  const hay = `${str(value)} ${series}`.toLowerCase();
  if (hay.includes("omnibus")) return "omnibus";
  if (hay.includes("hardcover") || hay.includes(" hc")) return "hc";
  if (hay.includes("tpb") || hay.includes("trade")) return "tpb";
  if (hay.includes("facsimile")) return "facsimile";
  if (hay.includes("annual")) return "annual";
  if (FORMATS.includes(str(value) as ComicFormat)) return str(value) as ComicFormat;
  return "single";
}

function people(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(str).filter(Boolean);
  return str(value)
    .split(/,|&| and /i)
    .map((p) => p.trim())
    .filter(Boolean);
}

function paletteFor(publisher: string): [string, string, string] {
  const p = publisher.toLowerCase();
  if (p.includes("dc")) return ["#1e3a8a", "#e30613", "#ffd200"];
  if (p.includes("marvel")) return ["#e30613", "#1e3a8a", "#f8fafc"];
  if (p.includes("image")) return ["#111827", "#f8fafc", "#e30613"];
  if (p.includes("dark horse")) return ["#111827", "#f59e0b", "#f8fafc"];
  if (p.includes("idw")) return ["#0ea5e9", "#111827", "#f8fafc"];
  if (p.includes("boom")) return ["#f97316", "#111827", "#f8fafc"];
  if (p.includes("dynamite")) return ["#7c2d12", "#eab308", "#f8fafc"];
  if (p.includes("valiant")) return ["#1d4ed8", "#f8fafc", "#111827"];
  return ["#1e4fa3", "#e30613", "#f8fafc"];
}

function asCompany(raw: string, line: string, name: string): CompanyId | null {
  const s = `${raw} ${line} ${name}`.toLowerCase();
  const direct = COMPANIES.find((id) => s.includes(id));
  if (direct) return direct;
  if (/takara|\bmpg\b|masterpiece g/.test(s)) return "takaratomy";
  if (/marvel legends|black series|classified|transformers|studio series|gi joe|power rangers|hasbro|pulse/.test(s)) {
    return "hasbro";
  }
  if (/dc multiverse|spawn|mcfarlane/.test(s)) return "mcfarlane";
  if (/\bmafex\b/.test(s)) return "mafex";
  if (/one:?12|mezco/.test(s)) return "mezco";
  if (/figuarts|\bshf\b/.test(s)) return "shfiguarts";
  if (/gunpla|\brg\b|\bmg\b|\bpg\b|\bhg\b|bandai|gundam/.test(s)) return "bandai";
  if (/\bneca\b/.test(s)) return "neca";
  if (/super7|ultimates/.test(s)) return "super7";
  if (/hot toys|\bmms\b|sixth scale|1\/6/.test(s)) return "hottoys";
  if (/\bfigma\b/.test(s)) return "figma";
  if (/kotobukiya|bishoujo|artfx|frame arms|hexa gear/.test(s)) return "kotobukiya";
  if (/storm collect/.test(s)) return "storm";
  if (/boss fight|h\.?a\.?c\.?k\.?s/.test(s)) return "bossfight";
  if (/loyal subjects|bst axn/.test(s)) return "loyalsubjects";
  if (/premium dna/.test(s)) return "premiumdna";
  if (/\bhiya\b/.test(s)) return "hiya";
  if (/\bmondo\b/.test(s)) return "mondo";
  if (/\bthreezero\b/.test(s)) return "threezero";
  if (/masterverse|origins|mattel|wwe elite/.test(s)) return "mattel";
  if (/jakks|primal age|sonic the hedgehog/.test(s)) return "jakks";
  if (/playmates/.test(s)) return "playmates";
  if (/kaiyodo|revoltech|amazing yamaguchi/.test(s)) return "kaiyodo";
  if (/jazwares|\bfortnite\b|\baew\b|unrivaled/.test(s)) return "jazwares";
  if (/diamond select|marvel select|\bdst\b/.test(s)) return "diamondselect";
  if (/joytoy|warhammer 40|dark source/.test(s)) return "joytoy";
  if (/beast kingdom|dynamic action heroes|\bdah\b/.test(s)) return "beastkingdom";
  if (/enterbay/.test(s)) return "enterbay";
  if (/funko legacy|funko.*action/.test(s)) return "funko";
  if (/toy ?biz/.test(s)) return "toybiz";
  if (/four horsemen|mythic legions|cosmic legions|figura obscura/.test(s)) return "fourhorsemen";
  if (/spin master|bakugan/.test(s)) return "spinmaster";
  if (/\bsentinel\b|fighting armor|\briobot\b|wonderful acts/.test(s)) return "sentinel";
  if (/1000toys|thousandtoys|tough guys|synthetic human/.test(s)) return "thousandtoys";
  if (/acid rain|toys alliance/.test(s)) return "acidrain";
  if (/fresh monkey|fresh retro/.test(s)) return "freshmonkey";
  if (/\bjada\b|street fighter.*jada/.test(s)) return "jada";
  if (/\bblokees\b|galaxy version/.test(s)) return "blokees";
  if (/\brobosen\b/.test(s)) return "robosen";
  if (/\bnewage\b/.test(s)) return "newage";
  if (/fans toys|fanstoys/.test(s)) return "fanstoys";
  if (/tunshi/.test(s)) return "tunshi";
  if (/damtoys|dam toys|gangsters kingdom|pocket elite/.test(s)) return "damtoys";
  if (/easy & simple|easy and simple|easysimple/.test(s)) return "easysimple";
  if (/soldier story|soldierstory/.test(s)) return "soldierstory";
  if (/mini times|minitimes/.test(s)) return "minitimes";
  if (/very cool|verycool/.test(s)) return "verycool";
  if (/iron factory|ironfactory/.test(s)) return "ironfactory";
  if (/magic square|magicsquare/.test(s)) return "magicsquare";
  if (/cang toys|cangtoys|\bcang\b/.test(s)) return "cangtoys";
  if (/real action heroes|\brah\b|medicom toy/.test(s)) return "medicom";
  if (/dr\.?\s*wu|drwu/.test(s)) return "drwu";
  if (/\bdx9\b/.test(s)) return "dx9";
  if (/mastermind creations|\bmmc\b|reformatted|ocular max/.test(s)) return "mastermind";
  if (/maketoys|make toys|\bmtrm\b|\bmtcm\b/.test(s)) return "maketoys";
  if (/planet x|planetx/.test(s)) return "planetx";
  if (/keiths fantasy|\bkfc\b/.test(s)) return "kfc";
  if (/xtransbots|x-?transbots/.test(s)) return "xtransbots";
  if (/flame toys|flametoys|kuro kara kuri/.test(s)) return "flametoys";
  if (/\btfc toys\b|\btfc\b/.test(s)) return "tfc";
  if (/gcreation|g-?creation|shuraking/.test(s)) return "gcreation";
  if (/generation toy|generationtoy|gravity builder/.test(s)) return "generationtoy";
  if (/\bzeta toys\b|\bzeta\b/.test(s)) return "zeta";
  if (/mech fans|mechfans/.test(s)) return "mechfans";
  if (/toywolf|toy wolf/.test(s)) return "toywolf";
  if (/evolution-?toy|evolutiontoy/.test(s)) return "evolutiontoy";
  if (/star ace|starace/.test(s)) return "starace";
  if (/\bexo-?6\b|exo6/.test(s)) return "exo6";
  if (/\bblitzway\b/.test(s)) return "blitzway";
  if (/\btoynami\b|robotech.*toynami/.test(s)) return "toynami";
  if (/creative beast|beasts of the mesozoic/.test(s)) return "creativebeast";
  if (/alert line|alertline/.test(s)) return "alertline";
  if (/snail shell|snailshell/.test(s)) return "snailshell";
  if (/asmus toys|\basmus\b|lord of the rings.*asmus/.test(s)) return "asmus";
  if (/herocross|hybrid metal figuration/.test(s)) return "herocross";
  if (/fans hobby|fanshobby/.test(s)) return "fanshobby";
  if (/fansproject|fans project/.test(s)) return "fansproject";
  if (/transart|trans art|beast wars metal/.test(s)) return "transart";
  if (/bingotoys|bingo toys/.test(s)) return "bingotoys";
  if (/heatboys|heat boys/.test(s)) return "heatboys";
  if (/ccs toys|ccstoys/.test(s)) return "ccstoys";
  if (/tbleague|tb league|phicen/.test(s)) return "tbleague";
  if (/coo model|coomodel/.test(s)) return "coomodel";
  if (/\bdid\b|dragon in dream/.test(s)) return "did";
  if (/moshow|mo show|progenitor effect/.test(s)) return "moshow";
  if (/\bmego\b|world.?s greatest super/.test(s)) return "mego";
  if (/world box|worldbox/.test(s)) return "worldbox";
  if (/kaustic plastik|kaustic/.test(s)) return "kaustic";
  if (/\bpop toys\b|poptoys/.test(s)) return "poptoys";
  if (/devil toys|deviltoys|devilman.*devil toys/.test(s)) return "deviltoys";
  if (/king arts|kingarts/.test(s)) return "kingarts";
  if (/\bjt studio\b|jtstudio/.test(s)) return "jtstudio";
  if (/art spirits|artspirits/.test(s)) return "artspirits";
  if (/art storm|artstorm/.test(s)) return "artstorm";
  if (/\b52toys\b|beastbox|megabox/.test(s)) return "fiftytwo";
  if (/action toys|actiontoys|es gokin/.test(s)) return "actiontoys";
  if (/underverse/.test(s)) return "underverse";
  if (/haoyu|hao yu toys/.test(s)) return "haoyu";
  if (/big chief studios|bigchief/.test(s)) return "bigchief";
  if (/iconiq studios|\biconiq\b/.test(s)) return "iconiq";
  if (/figures toy company|figurestoy/.test(s)) return "figurestoy";
  if (/toy notch|toynotch/.test(s)) return "toynotch";
  if (/\bactoys\b|ac toys/.test(s)) return "actoys";
  if (/new wave toys|newwave|replicade/.test(s)) return "newwave";
  if (/flirty girl/.test(s)) return "flirtygirl";
  if (/fire girl toys|firegirl/.test(s)) return "firegirl";
  if (/\bi8toys\b|i8 toys/.test(s)) return "i8toys";
  if (/nanmu studio|\bnanmu\b/.test(s)) return "nanmu";
  if (/\bvtoys\b|v toys/.test(s)) return "vtoys";
  if (/valaverse|action force/.test(s)) return "valaverse";
  return null;
}

function asKind(value: unknown, line: string): ItemKind {
  const hay = `${str(value)} ${line}`.toLowerCase();
  if (hay.includes("kit") || hay.includes("gunpla") || /\b(rg|mg|pg|hg)\b/.test(hay)) return "kit";
  return "figure";
}

function extractJson(text: string): { comics?: unknown[]; figures?: unknown[] } {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const raw = fenced?.[1] ?? text;
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start < 0 || end <= start) return {};
  try {
    return JSON.parse(raw.slice(start, end + 1)) as { comics?: unknown[]; figures?: unknown[] };
  } catch {
    return {};
  }
}

function outputText(payload: { output?: unknown }): string {
  const output = payload.output;
  if (!Array.isArray(output)) return "";
  const chunks: string[] = [];
  for (const item of output) {
    if (!item || typeof item !== "object") continue;
    const rec = item as { type?: string; content?: unknown };
    if (rec.type !== "message") continue;
    if (!Array.isArray(rec.content)) continue;
    for (const part of rec.content) {
      if (part && typeof part === "object" && "text" in part) {
        const text = (part as { text?: unknown }).text;
        if (typeof text === "string") chunks.push(text);
      }
    }
  }
  return chunks.join("\n");
}

function normalizeComics(rows: unknown[], week: string, fallbackDate: string): CatalogComic[] {
  const seen = new Set<string>();
  const out: CatalogComic[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const r = row as Record<string, unknown>;
    const series = str(r.series);
    if (!series) continue;
    const issue = issueNo(r.issue);
    const publisher = str(r.publisher) || "Unknown";
    const key = `${series}|${issue}|${publisher}|${str(r.variant)}`.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    const street = dateish(r.streetDate ?? r.coverDate, fallbackDate);
    const variant = str(r.variant);
    const cover = str(r.coverUrl ?? r.cover);
    out.push({
      id: `live-c-${week}-${slug(series)}-${slug(issue)}${variant ? `-${slug(variant)}` : ""}`.slice(0, 80),
      series,
      issue,
      publisher,
      coverDate: street,
      streetDate: street,
      writers: people(r.writers),
      artists: people(r.artists),
      description: str(r.description) || `Street date ${street}.`,
      msrp: num(r.msrp, 4.99),
      format: asFormat(r.format, series),
      variant: variant || undefined,
      demand: 1,
      key: false,
      palette: paletteFor(publisher),
      cover: cover.startsWith("http") ? cover : undefined,
    });
    if (out.length >= 28) break;
  }
  return out;
}

function normalizeFigures(rows: unknown[], week: string, fallbackDate: string): CatalogFigure[] {
  const seen = new Set<string>();
  const out: CatalogFigure[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const r = row as Record<string, unknown>;
    const name = str(r.name);
    const line = str(r.line) || str(r.brand) || "Collector line";
    if (!name) continue;
    const company = asCompany(str(r.company), line, name);
    if (!company) continue;
    const subtitle = str(r.subtitle);
    const key = `${name}|${subtitle}|${line}|${company}`.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    const kind = asKind(r.kind, line);
    out.push({
      id: `live-f-${week}-${slug(line)}-${slug(name)}-${slug(subtitle || "std")}`.slice(0, 80),
      name,
      subtitle: subtitle || line,
      line,
      company,
      kind,
      releaseDate: dateish(r.releaseDate, fallbackDate),
      msrp: num(r.msrp, kind === "kit" ? 49.99 : 24.99),
      scale: str(r.scale) || (kind === "kit" ? "1/144" : '6"'),
      exclusive: str(r.exclusive) || undefined,
      imageUrl: (() => {
        const img = str(r.imageUrl ?? r.image);
        return img.startsWith("http") ? img : undefined;
      })(),
      demand: 1,
      tags: ["this-week", company, kind],
    });
    if (out.length >= 18) break;
  }
  return out;
}

function coerceCachedComics(rows: unknown[], week: string): CatalogComic[] {
  // Preserve stored ids; only repair shape (numeric issue, CSV writers, etc.).
  const out: CatalogComic[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const r = row as Record<string, unknown>;
    const id = str(r.id) || undefined;
    const series = str(r.series);
    if (!series) continue;
    const issue = issueNo(r.issue);
    const publisher = str(r.publisher) || "Unknown";
    const variant = str(r.variant);
    const cover = str(r.coverUrl ?? r.cover);
    const street = dateish(r.streetDate ?? r.coverDate, new Date().toISOString().slice(0, 10));
    out.push({
      id: (id || `live-c-${week}-${slug(series)}-${slug(issue)}${variant ? `-${slug(variant)}` : ""}`).slice(0, 80),
      series,
      issue,
      publisher,
      coverDate: str(r.coverDate) || street,
      streetDate: str(r.streetDate) || street,
      writers: people(r.writers),
      artists: people(r.artists),
      description: str(r.description) || `Street date ${street}.`,
      msrp: num(r.msrp, 4.99),
      format: asFormat(r.format, series),
      variant: variant || undefined,
      demand: num(r.demand, 1),
      key: Boolean(r.key),
      palette: Array.isArray(r.palette) && r.palette.length >= 3
        ? [String(r.palette[0]), String(r.palette[1]), String(r.palette[2])]
        : paletteFor(publisher),
      cover: cover.startsWith("http") ? cover : undefined,
    });
  }
  return out;
}

function coerceCachedFigures(rows: unknown[]): CatalogFigure[] {
  const out: CatalogFigure[] = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const f = row as CatalogFigure;
    if (!f.id || !f.name || !f.company) continue;
    out.push(f);
  }
  return out;
}

async function readCached(week: string): Promise<WeeklyDrop | null> {
  // Production preview has no DATABASE_URL; importing @/lib/db there boots PGLite
  // and the WASM payload is missing from the Vercel output — that crash kills Node.
  // Deployed, Neon is injected and this path is safe.
  if (!neonConfigured()) return null;
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    const rows = await sql.query<DropRow>(
      "select week, fetched_at, comics, figures, status, error from weekly_drops where week = $1",
      [week],
    );
    const row = rows[0];
    if (!row) return null;
    return {
      week: row.week,
      fetchedAt: row.fetched_at,
      comics: coerceCachedComics(asArray(row.comics), row.week),
      figures: coerceCachedFigures(asArray(row.figures)),
      status: row.status === "error" ? "error" : "ok",
      error: row.error ?? undefined,
    };
  } catch {
    return null;
  }
}

async function writeCached(drop: WeeklyDrop): Promise<void> {
  if (!neonConfigured()) return;
  try {
    const { getSql } = await import("@/lib/db");
    const sql = await getSql();
    await sql.query(
      `insert into weekly_drops (week, fetched_at, comics, figures, status, error)
       values ($1, $2, $3::jsonb, $4::jsonb, $5, $6)
       on conflict (week) do update set
         fetched_at = excluded.fetched_at,
         comics = excluded.comics,
         figures = excluded.figures,
         status = excluded.status,
         error = excluded.error`,
      [
        drop.week,
        drop.fetchedAt,
        JSON.stringify(drop.comics),
        JSON.stringify(drop.figures),
        drop.status,
        drop.error ?? null,
      ],
    );
  } catch {
    /* seed still serves if the store is unavailable */
  }
}

function stale(drop: WeeklyDrop, hours: number): boolean {
  const t = Date.parse(drop.fetchedAt);
  if (!Number.isFinite(t)) return true;
  return Date.now() - t > hours * 3600 * 1000;
}

function dropFromSeed(week: string, today: string): WeeklyDrop | null {
  const bundled = seed as { week?: string; comics?: unknown[]; figures?: unknown[] };
  if (bundled.week !== week) return null;
  const comics = normalizeComics(bundled.comics ?? [], week, today);
  const figures = normalizeFigures(bundled.figures ?? [], week, today);
  if (!comics.length && !figures.length) return null;
  return {
    week,
    fetchedAt: new Date().toISOString(),
    comics,
    figures,
    status: "ok",
  };
}

async function ingestWeek(week: string, today: string): Promise<WeeklyDrop> {
  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    return emptyDrop(week, "unavailable");
  }

  const body = {
    model: "grok-4.5",
    max_tool_calls: 6,
    tools: [
      {
        type: "web_search",
        filters: {
          allowed_domains: [
            "leagueofcomicgeeks.com",
            "comicbook.com",
            "marvel.com",
            "dc.com",
            "imagecomics.com",
            "darkhorse.com",
            "idwpublishing.com",
            "boom-studios.com",
            "dynamite.com",
            "previewsworld.com",
            "bigbadtoystore.com",
            "hasbropulse.com",
            "mcfarlane.com",
            "mattel.com",
            "mezcotoyz.com",
            "necaonline.com",
            "super7.com",
            "hottoys.com.hk",
            "goodsmile.info",
            "bandai.com",
            "tamashiinations.com",
            "kotobukiya.co.jp",
            "entertainmentearth.com",
          ],
        },
      },
    ],
    input: [
      {
        role: "user",
        content: `Today is ${today} (ISO week ${week}). US comics street on Wednesday.

Extract CURRENT releases only — do not invent titles.

Comics (major publishers): Marvel, DC, Image, Dark Horse, IDW, BOOM!, Dynamite, Valiant.
Primary list: https://leagueofcomicgeeks.com/comics/new-comics
Cross-check publisher new-release / solicitations pages when useful.

Figures / kits (major manufacturers): Hasbro Pulse, Mattel, McFarlane Toys, MAFEX/Medicom, Mezco One:12, Bandai / S.H.Figuarts, NECA, Super7, Hot Toys, figma (Good Smile), Kotobukiya, Storm Collectibles.
Use manufacturer new-release pages plus BBTS / Entertainment Earth new arrivals for collector lines (Marvel Legends, Black Series, DC Multiverse, MAFEX, Figuarts, Gunpla, NECA, Super7, Hot Toys, figma, etc.).

Return ONLY JSON:
{"comics":[{"series":"","issue":"","publisher":"","streetDate":"YYYY-MM-DD","msrp":0,"writers":"","artists":"","format":"single","variant":"","coverUrl":""}],"figures":[{"name":"","subtitle":"","line":"","company":"hasbro","kind":"figure","releaseDate":"YYYY-MM-DD","msrp":0,"scale":"6\\"","exclusive":""}]}

Comics: this week's main covers only (skip 1:25+ ratio variants). Max 28. Issue without #.
Figures: newly in-stock or newly announced matching those companies. Max 18.
company must be one of: hasbro,toybiz,mattel,mcfarlane,mafex,mezco,bandai,shfiguarts,neca,super7,hottoys,figma,kotobukiya,storm.`,
      },
    ],
  };

  const res = await fetch("https://api.x.ai/v1/responses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(90_000),
  });

  if (!res.ok) {
    return emptyDrop(week, `ingest ${res.status}`);
  }

  const payload = (await res.json()) as { output?: unknown };
  const parsed = extractJson(outputText(payload));
  const comics = normalizeComics(parsed.comics ?? [], week, today);
  let figures = normalizeFigures(parsed.figures ?? [], week, today);
  try {
    const storefront = await fetchStorefrontFigures({ week, today, max: 18 });
    if (storefront.length) {
      // Prefer live storefront products (real images) over LLM figure guesses.
      const seen = new Set(storefront.map((f) => f.id));
      figures = [...storefront, ...figures.filter((f) => !seen.has(f.id))].slice(0, 18);
    }
  } catch {
    /* keep LLM/seed figures */
  }
  return {
    week,
    fetchedAt: new Date().toISOString(),
    comics,
    figures,
    status: comics.length || figures.length ? "ok" : "error",
    error: comics.length || figures.length ? undefined : "empty",
  };
}

function remember(drop: WeeklyDrop): WeeklyDrop {
  writeMem(drop);
  return drop;
}

export const getWeeklyDrop = createServerFn({ method: "POST" })
  .validator((data: unknown) => {
    const force = Boolean(data && typeof data === "object" && "force" in data && (data as { force?: unknown }).force);
    return { force };
  })
  .handler(async ({ data }): Promise<WeeklyDrop> => {
    const week = weekKey();
    const today = new Date().toISOString().slice(0, 10);

    const mem = readMem(week);
    if (mem && !data.force) {
      if (mem.status === "ok" && hasItems(mem) && !stale(mem, 72)) return mem;
    }

    const cached = await readCached(week);
    if (cached && !data.force) {
      if (cached.status === "ok" && hasItems(cached) && !stale(cached, 72)) {
        return remember(cached);
      }
    }

    const seeded = dropFromSeed(week, today);
    if (seeded && !data.force) {
      if (!hasItems(cached)) void writeCached(seeded);
      return remember(seeded);
    }

    if (!data.force) {
      if (hasItems(cached)) return remember(cached);
      if (hasItems(mem)) return mem;
      // New ISO week with no seed/cache: attempt live ingest when configured.
      if (!process.env.XAI_API_KEY?.trim()) {
        return remember(emptyDrop(week));
      }
    }

    if (cached && cached.status === "error" && !hasItems(cached) && !stale(cached, 0.05)) {
      return cached;
    }
    if (mem && mem.status === "error" && !hasItems(mem) && !stale(mem, 0.05)) {
      return mem;
    }

    try {
      const drop = await ingestWeek(week, today);
      if (drop.status === "error" && hasItems(cached)) return remember(cached);
      if (drop.status === "error" && seeded) return remember(seeded);
      await writeCached(drop);
      return remember(drop);
    } catch (err) {
      const fallback: WeeklyDrop =
        seeded ??
        (hasItems(cached) ? cached : null) ??
        emptyDrop(week, err instanceof Error ? err.message : "ingest failed");
      if (!cached) void writeCached(fallback);
      return remember(fallback);
    }
  });

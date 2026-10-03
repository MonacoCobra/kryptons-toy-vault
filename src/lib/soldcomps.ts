/**
 * SoldComps (api.sold-comps.com) helpers: keyword builder, relevance filter and
 * "avg of 5 most recent sold" estimate. Pure — no imports — so the server
 * function (src/lib/soldcomps-market.ts) and the box script
 * (scripts/soldcomps-refresh.mjs) share the exact same logic.
 */

export type SoldCompsItem = {
  itemId?: string | null;
  url?: string | null;
  title?: string | null;
  condition?: string | null;
  bestOfferAccepted?: boolean | null;
  endedAt?: string | null;
  soldPrice?: string | number | null;
  soldCurrency?: string | null;
};

export type SoldCompsResponse = {
  keyword?: string;
  totalItems?: number;
  hasNextPage?: boolean;
  items?: SoldCompsItem[];
};

export type FigureLike = {
  id: string;
  name: string;
  line: string;
  subtitle?: string;
  scale?: string;
  tags?: string[];
};

export type RealComp = {
  price: number;
  date: string;
  condition: string;
  title: string;
  url?: string;
  /** Best offer accepted: eBay shows the asking price, so the real sale was ≤ price. */
  bestOffer?: boolean;
};

export type FigureSoldComps = {
  figureId: string;
  source: "soldcomps";
  keyword: string;
  fetchedAt: string;
  /** ok = ≥ MIN_PASSING matching sales; insufficient = fewer; error = lookup failed. */
  status: "ok" | "insufficient" | "error";
  estimate: number | null;
  /** The (up to) 5 sales the estimate averages, newest first. */
  comps: RealComp[];
  passing: number;
  totalItems: number;
  bestOfferInAvg: number;
  conditionBasis: "new" | "mixed" | "none";
  error?: string;
};

export const SOLDCOMPS_URL = "https://api.sold-comps.com/v1/scrape";
export const MIN_PASSING = 3;
export const AVG_COUNT = 5;
export const CACHE_DAYS = 30;
/** Stop calling SoldComps when x-usage-remaining drops to this. */
export const BUDGET_FLOOR = 10;

const STOP = new Set([
  "the", "of", "and", "a", "an", "with", "for", "in", "on", "by", "to",
  "figure", "figures", "action", "class", "edition", "exclusive", "pack", "set",
  "universe", "g1", "g2", "series", "wave", "new", "version", "ver",
]);
const BRAND_PREFIX = /^(?:transformers|hasbro|mcfarlane(?:\s+toys)?|neca|mattel|bandai)\s+/i;

function words(s: string): string[] {
  return (s || "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

/** "Transformers Age of the Primes" -> "age of the primes". */
export function lineKey(line: string): string {
  const raw = (line || "").trim();
  const stripped = raw.replace(BRAND_PREFIX, "");
  const base = words(stripped).length >= 2 ? stripped : raw;
  return words(base).slice(0, 5).join(" ");
}

function nameParts(name: string): string[] {
  return (name || "")
    .split(/\s*(?:\/|&|\+|\bvs\.?\b|\band\b|,)\s*/i)
    .map((p) => p.trim())
    .filter(Boolean);
}

/** Distinctive name tokens; for multipacks one+ per member ("snarl", "slug"). */
export function nameTokens(name: string): string[] {
  const parts = nameParts(name).map((p) => words(p).filter((w) => !STOP.has(w)));
  if (!parts.length) return [];
  if (parts.length === 1) {
    const toks = parts[0]!;
    return toks.slice(-3);
  }
  const common = parts.reduce<Set<string>>(
    (acc, p) => new Set([...acc].filter((w) => p.includes(w))),
    new Set(parts[0]),
  );
  const out: string[] = [];
  for (const p of parts) {
    const own = p.filter((w) => !common.has(w));
    const pick = own.length ? own.slice(-1) : p.slice(-1);
    for (const w of pick) if (!out.includes(w)) out.push(w);
  }
  return out.slice(0, 4);
}

function studioNumber(subtitle: string | undefined): string | null {
  const m = (subtitle || "").match(/\b(\d{2,3}-\d{2}|ss\s?-?\s?\d{2,3})\b/i);
  return m ? m[1]!.toLowerCase().replace(/\s+/g, "") : null;
}

/** Tight eBay keyword, e.g. "age of the primes snarl slug". */
export function figureKeyword(f: FigureLike): string {
  const parts = [lineKey(f.line), ...nameTokens(f.name)];
  const ss = studioNumber(f.subtitle);
  if (ss && /studio\s+series/i.test(f.line)) parts.push(ss);
  return parts.join(" ").replace(/\s+/g, " ").trim().slice(0, 120);
}

const EXCLUDE_RE = new RegExp(
  [
    "\\blots?\\b", "\\bbundle\\b", "\\bbulk\\b", "\\bjob\\s+lot\\b", "\\bset\\s+of\\s+\\d",
    "\\bcustom\\b", "\\bko\\b", "\\bknock[\\s-]?off\\b", "\\bbootleg\\b", "\\brepro(?:duction)?\\b",
    "\\breplica\\b", "\\bfake\\b", "\\b3rd\\s+party\\b", "\\bthird\\s+party\\b",
    "\\bfor\\s+parts\\b", "\\bparts\\s+only\\b", "\\bincomplete\\b", "\\bmissing\\b", "\\bbroken\\b",
    "\\bbox\\s+only\\b", "\\bempty\\s+box\\b", "\\bno\\s+(?:figure|box)\\b",
    "\\b(?:accessor(?:y|ies)|weapons?|head|manual|instructions?)\\s+only\\b",
    "\\btrading\\s+cards?\\b", "\\bcard\\s+only\\b", "\\bsticker\\b", "\\bposter\\b", "\\bdecals?\\b",
  ].join("|"),
  "i",
);
const USED_RE = /\b(?:used|loose|pre[\s-]?owned|opened|open\s+box)\b/i;

export function isUsedSale(item: SoldCompsItem): boolean {
  return USED_RE.test(item.condition || "") || USED_RE.test(item.title || "");
}

function hasToken(titleWords: string[], tok: string): boolean {
  return titleWords.some((w) => w === tok || w === `${tok}s` || (tok.length >= 5 && w.startsWith(tok)));
}

function acronym(key: string): string {
  return words(key).map((w) => w[0]).join("");
}

/** Why a sale doesn't count for this figure (null = it passes). */
export function rejectReason(f: FigureLike, item: SoldCompsItem): string | null {
  const title = (item.title || "").trim();
  if (!title) return "no-title";
  const price = Number(item.soldPrice);
  if (!Number.isFinite(price) || price <= 0) return "no-price";
  if ((item.soldCurrency || "").toUpperCase() !== "USD") return "non-usd";
  if (!/^\d{4}-\d{2}-\d{2}/.test(item.endedAt || "")) return "no-date";
  if (EXCLUDE_RE.test(title)) return "lot-partial-custom";
  const tw = words(title);
  for (const tok of nameTokens(f.name)) if (!hasToken(tw, tok)) return `missing:${tok}`;
  const lk = lineKey(f.line);
  const lineToks = words(lk).filter((w) => !STOP.has(w));
  const ac = acronym(lk);
  const lineOk = lineToks.every((t) => hasToken(tw, t)) || (ac.length >= 3 && tw.includes(ac));
  if (!lineOk) return "line-mismatch";
  return null;
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

export function buildFigureSoldComps(
  f: FigureLike,
  keyword: string,
  res: SoldCompsResponse,
  fetchedAt: string,
): FigureSoldComps {
  const items = Array.isArray(res.items) ? res.items : [];
  const passing = items.filter((it) => rejectReason(f, it) === null);
  const fresh = passing.filter((it) => !isUsedSale(it));
  const basis: FigureSoldComps["conditionBasis"] =
    fresh.length >= MIN_PASSING ? "new" : passing.length >= MIN_PASSING ? "mixed" : "none";
  const pool = basis === "new" ? fresh : passing;
  // Newest first; stable for same-day sales (API order).
  const sorted = pool
    .map((it, i) => ({ it, i }))
    .sort((a, b) => {
      const d = String(b.it.endedAt).slice(0, 10).localeCompare(String(a.it.endedAt).slice(0, 10));
      return d || a.i - b.i;
    })
    .map((x) => x.it);
  const used = sorted.slice(0, AVG_COUNT);
  const comps: RealComp[] = used.map((it) => ({
    price: round2(Number(it.soldPrice)),
    date: String(it.endedAt).slice(0, 10),
    condition: (it.condition || "").trim() || (isUsedSale(it) ? "Used" : "Sold"),
    title: (it.title || "").trim(),
    url: it.url && /^https:\/\/(?:www\.)?ebay\.com\//.test(it.url) ? it.url : undefined,
    bestOffer: Boolean(it.bestOfferAccepted),
  }));
  const ok = basis !== "none";
  return {
    figureId: f.id,
    source: "soldcomps",
    keyword,
    fetchedAt,
    status: ok ? "ok" : "insufficient",
    estimate: ok ? round2(comps.reduce((s, c) => s + c.price, 0) / comps.length) : null,
    comps: ok ? comps : [],
    passing: pool.length,
    totalItems: Number(res.totalItems ?? items.length) || items.length,
    bestOfferInAvg: ok ? comps.filter((c) => c.bestOffer).length : 0,
    conditionBasis: basis,
  };
}

export function cacheAgeDays(fetchedAt: string | undefined, now = Date.now()): number {
  const t = Date.parse(fetchedAt || "");
  return Number.isFinite(t) ? (now - t) / 86400000 : Number.POSITIVE_INFINITY;
}

export function soldCompsRequestUrl(keyword: string): string {
  const q = new URLSearchParams({ keyword, ebaySite: "ebay.com", count: "40" });
  return `${SOLDCOMPS_URL}?${q.toString()}`;
}

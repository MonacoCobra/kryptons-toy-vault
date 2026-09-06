/**
 * Live figure ingest from brand Shopify storefront product JSON.
 * Prefer real CDN product images — never generative art.
 *
 * Focus: articulated action figures (not pins, dolls, or statue lines).
 * Hasbro Pulse / BBTS / EE / Mezco / McFarlane Toys official still lack stable public JSON.
 * NECA: store.necaonline.com; shop.dc.com McFarlane Multiverse; Valaverse; Blokees/Blitzway/EXO-6/Star Ace/DamToys verified open JSON.
 */

import type { CatalogFigure, CompanyId, ItemKind } from "@/lib/types";
import { slug } from "@/lib/utils";

export type StorefrontSource = {
  id: string;
  /** Origin only, e.g. https://super7.com */
  baseUrl: string;
  company: CompanyId;
  /** Optional collection path; default /products.json */
  productsPath?: string;
  /** Extra title/tag filter for noisy catalogs (e.g. Mattel dolls). */
  requireHint?: RegExp;
};

/** Shops verified to return Shopify `{ products: [...] }` JSON. */
export const FIGURE_STOREFRONTS: StorefrontSource[] = [
  { id: "super7", baseUrl: "https://super7.com", company: "super7" },
  { id: "goodsmile-us", baseUrl: "https://goodsmileus.com", company: "figma" },
  { id: "bossfight", baseUrl: "https://bossfightstudio.com", company: "bossfight" },
  { id: "loyalsubjects", baseUrl: "https://theloyalsubjects.com", company: "loyalsubjects" },
  {
    id: "mattel-creations",
    baseUrl: "https://creations.mattel.com",
    company: "mattel",
    requireHint:
      /masterverse|masters of the universe|wwe|elite|jurassic|monster high|dc universe|hammond|action figure/i,
  },
  { id: "premiumdna", baseUrl: "https://www.premiumdnatoys.com", company: "premiumdna" },
  { id: "hiya", baseUrl: "https://www.hiyatoys.com", company: "hiya" },
  { id: "mondo", baseUrl: "https://www.mondoshop.com", company: "mondo" },
  {
    id: "shop-dc",
    baseUrl: "https://shop.dc.com",
    company: "mcfarlane",
    requireHint: /action figure|dc multiverse|mcfarlane collector/i,
  },
  {
    id: "valaverse",
    baseUrl: "https://www.valaverse.com",
    company: "valaverse",
    requireHint: /action force|figure|trooper|gear/i,
  },
  {
    id: "neca-store",
    baseUrl: "https://store.necaonline.com",
    company: "neca",
    requireHint: /action figure|figure|ultimate|scale|tmnt|predator|alien|horror/i,
  },
  {
    id: "blokees",
    baseUrl: "https://blokees.com",
    company: "blokees",
    requireHint: /blokees|champion|galaxy|defender|transformers|ultraman|mega man|saint seiya|figure/i,
  },
  {
    id: "blitzway",
    baseUrl: "https://blitzway.com",
    company: "blitzway",
    requireHint: /action figure|figure|carbote|mazinger|voltron|getter|scale/i,
  },
  {
    id: "exo6",
    baseUrl: "https://exo-6.com",
    company: "exo6",
    requireHint: /star trek|spock|kirk|picard|janeway|figure|1:?6|scale/i,
  },
  {
    id: "starace",
    baseUrl: "https://www.staracetoys.com",
    company: "starace",
    requireHint: /1\/?6|action figure|figure|harry potter|wonder woman|elvis|pacific rim|defostyle/i,
  },
  {
    id: "damtoys",
    baseUrl: "https://shop.damtoys.com",
    company: "damtoys",
    requireHint: /damtoys|1\/?6|1\/?12|figure|gangsters|pocket elite|vertex/i,
  },
];

type ShopifyImage = { src?: string };
type ShopifyVariant = { price?: string; sku?: string; available?: boolean };
type ShopifyProduct = {
  id?: number | string;
  title?: string;
  handle?: string;
  vendor?: string;
  product_type?: string;
  tags?: string[] | string;
  published_at?: string;
  updated_at?: string;
  created_at?: string;
  body_html?: string;
  images?: ShopifyImage[];
  variants?: ShopifyVariant[];
};

const UA = "KryptonsToyVault/1.0 (personal collection; weekly figure ingest)";

const SKIP_TYPE =
  /\b(apparel|shirt|hoodie|hat|cap|sock|sticker|figpin|enamel|poster|print|mug|bag|wallet|blanket|keychain|lanyard|gift.?card|digital|barbie|doll|little people|plush|soft toy|board game|vinyl art|minico|statue only)\b/i;
const FIGURE_HINT =
  /\b(figure|figurine|statue|mafex|figuarts|figma|mezco|legends|classified|black series|model kit|gunpla|plamo|soft.?vinyl|sofubi|reactors|ultimates|reaction|h\.?a\.?c\.?k\.?s|bst axn|masterverse)\b/i;

function tagList(tags: ShopifyProduct["tags"]): string[] {
  if (Array.isArray(tags)) return tags.map((t) => String(t));
  if (typeof tags === "string")
    return tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
  return [];
}

function isFigureLike(p: ShopifyProduct, source: StorefrontSource): boolean {
  const type = p.product_type ?? "";
  const title = p.title ?? "";
  const tags = tagList(p.tags).join(" ");
  const blob = `${type} ${title} ${tags}`;
  if (SKIP_TYPE.test(type) || SKIP_TYPE.test(title)) return false;
  if (source.requireHint && !source.requireHint.test(blob)) return false;
  if (FIGURE_HINT.test(blob) || FIGURE_HINT.test(type)) return true;
  // Collector shops are mostly figures; allow generic "Figures" types
  if (/figures?/i.test(type) || /statue/i.test(type) || /model/i.test(type)) return true;
  // Boss Fight / TLS / Super7: if not skipped, keep
  if (
    source.company === "bossfight" ||
    source.company === "loyalsubjects" ||
    source.company === "super7" ||
    source.company === "valaverse" ||
    source.company === "neca" ||
    source.company === "blokees" ||
    source.company === "blitzway" ||
    source.company === "exo6" ||
    source.company === "starace" ||
    source.company === "damtoys"
  ) {
    return true;
  }
  return false;
}

function kindFor(p: ShopifyProduct): ItemKind {
  const blob = `${p.product_type ?? ""} ${p.title ?? ""} ${tagList(p.tags).join(" ")}`;
  if (/\b(gunpla|plamo|model kit|hguc|rg |mg |pg )\b/i.test(blob)) return "kit";
  return "figure";
}

function scaleFor(p: ShopifyProduct, kind: ItemKind): string {
  const blob = `${p.title ?? ""} ${tagList(p.tags).join(" ")} ${p.body_html ?? ""}`;
  const m = blob.match(/\b(1\/\d+)\b/) || blob.match(/\b(\d+(?:\.\d+)?")\b/);
  if (m) return m[1]!;
  return kind === "kit" ? "1/144" : '6"';
}

function parseMoney(v: unknown): number {
  const n = typeof v === "number" ? v : Number.parseFloat(String(v ?? "").replace(/[^0-9.]/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function dateFrom(p: ShopifyProduct, fallback: string): string {
  for (const raw of [p.published_at, p.created_at, p.updated_at]) {
    if (!raw) continue;
    const d = String(raw).slice(0, 10);
    if (/^\d{4}-\d{2}-\d{2}$/.test(d)) return d;
  }
  return fallback;
}

function splitTitle(title: string): { name: string; subtitle: string } {
  const cleaned = title.replace(/\s+/g, " ").trim();
  if (cleaned.includes(" | ")) {
    const segs = cleaned.split(" | ").map((s) => s.trim()).filter(Boolean);
    const right = segs[segs.length - 1]!;
    const left = segs.slice(0, -1).join(" | ");
    const name = (right.split(":")[0] || right).trim();
    return { name, subtitle: left || right };
  }
  const parts = cleaned.split(/\s+[—–-]\s+/);
  if (parts.length >= 2) {
    return { name: parts[0]!.trim(), subtitle: parts.slice(1).join(" - ").trim() };
  }
  const colon = cleaned.split(":");
  if (colon.length >= 2 && colon[0]!.length < 48) {
    return { name: colon[0]!.trim(), subtitle: colon.slice(1).join(":").trim() };
  }
  return { name: cleaned, subtitle: "" };
}

async function fetchProductsPage(baseUrl: string, path: string, page: number): Promise<ShopifyProduct[]> {
  const url = new URL(path, baseUrl);
  url.searchParams.set("limit", "50");
  url.searchParams.set("page", String(page));
  const res = await fetch(url.toString(), {
    headers: { Accept: "application/json", "User-Agent": UA },
    signal: AbortSignal.timeout(20_000),
  });
  if (!res.ok) return [];
  const text = await res.text();
  if (text.trimStart().startsWith("<")) return [];
  try {
    const data = JSON.parse(text) as { products?: ShopifyProduct[] };
    return Array.isArray(data.products) ? data.products : [];
  } catch {
    return [];
  }
}

function mapProduct(
  p: ShopifyProduct,
  source: StorefrontSource,
  week: string,
  fallbackDate: string,
): CatalogFigure | null {
  if (!p.title || !isFigureLike(p, source)) return null;
  const { name, subtitle } = splitTitle(p.title);
  if (!name) return null;
  const kind = kindFor(p);
  const variant = p.variants?.[0];
  const msrp = parseMoney(variant?.price) || (kind === "kit" ? 49.99 : 24.99);
  const imageUrl = p.images?.find((i) => i.src)?.src;
  const tags = new Set<string>(["this-week", "storefront", source.id, source.company, kind]);
  for (const t of tagList(p.tags).slice(0, 8)) tags.add(t.toLowerCase());
  const exclusiveTag = tagList(p.tags).find((t) => /exclusive/i.test(t));
  const handle = p.handle || slug(name);
  return {
    id: `sf-${source.id}-${handle}`.slice(0, 80),
    name,
    subtitle: subtitle || p.product_type || source.id,
    line: p.product_type || p.vendor || source.id,
    company: source.company,
    kind,
    releaseDate: dateFrom(p, fallbackDate),
    msrp,
    scale: scaleFor(p, kind),
    sku: variant?.sku || undefined,
    exclusive: exclusiveTag || undefined,
    imageUrl: imageUrl?.startsWith("http") ? imageUrl : undefined,
    demand: 1,
    tags: [...tags],
  };
}

/** Fetch recent figure-like products from configured Shopify storefronts. */
export async function fetchStorefrontFigures(opts: {
  week: string;
  today: string;
  max?: number;
  sources?: StorefrontSource[];
}): Promise<CatalogFigure[]> {
  const max = opts.max ?? 18;
  const sources = opts.sources ?? FIGURE_STOREFRONTS;
  const out: CatalogFigure[] = [];
  const seen = new Set<string>();

  for (const source of sources) {
    if (out.length >= max) break;
    const path = source.productsPath ?? "/products.json";
    // First pages are newest on most Shopify shops
    for (let page = 1; page <= 3 && out.length < max; page++) {
      let products: ShopifyProduct[] = [];
      try {
        products = await fetchProductsPage(source.baseUrl, path, page);
      } catch {
        break;
      }
      if (!products.length) break;
      for (const p of products) {
        const fig = mapProduct(p, source, opts.week, opts.today);
        if (!fig) continue;
        const key = fig.id.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(fig);
        if (out.length >= max) break;
      }
    }
  }
  return out;
}

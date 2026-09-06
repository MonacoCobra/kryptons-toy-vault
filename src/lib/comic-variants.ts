import type { CatalogComic } from "@/lib/types";

/** Normalize series / issue / publisher for variant family matching. */
export function normalizeComicPart(s: string): string {
  return s.trim().toLowerCase().replace(/\s+/g, " ");
}

/** Family key: series + issue + publisher (no variant). */
export function comicFamilyKey(c: { series: string; issue: string; publisher: string }): string {
  return `${normalizeComicPart(c.series)}|${normalizeComicPart(c.issue)}|${normalizeComicPart(c.publisher)}`;
}

/** UI label for a cover row (Cover A when unset). */
export function variantDisplayLabel(c: { variant?: string }): string {
  const v = c.variant?.trim();
  return v || "Cover A";
}

/** True for standard / Cover A / regular / main (empty variant counts as primary). */
export function isPrimaryCover(c: { variant?: string }): boolean {
  const v = (c.variant ?? "").trim().toLowerCase();
  if (!v) return true;
  return (
    /^(cover\s*)?a\b/.test(v) ||
    v === "standard" ||
    v === "regular" ||
    v === "main" ||
    v === "main cover" ||
    v === "direct edition"
  );
}

function sortVariants(a: CatalogComic, b: CatalogComic): number {
  const pa = isPrimaryCover(a) ? 0 : 1;
  const pb = isPrimaryCover(b) ? 0 : 1;
  if (pa !== pb) return pa - pb;
  const la = variantDisplayLabel(a).localeCompare(variantDisplayLabel(b), undefined, { sensitivity: "base" });
  if (la !== 0) return la;
  return a.id.localeCompare(b.id);
}

/**
 * Open-order / variant covers for the same series+issue+publisher family.
 * Only returns real catalog rows — never invents variants.
 * Ambiguous reboot/facsimile collisions (same family, no variant/UPC differentiation)
 * collapse to the current comic so the strip stays honest.
 */
export function getComicVariants(comic: CatalogComic, catalog: CatalogComic[]): CatalogComic[] {
  const key = comicFamilyKey(comic);
  const byId = new Map<string, CatalogComic>();
  for (const c of catalog) {
    if (comicFamilyKey(c) !== key) continue;
    byId.set(c.id, c);
  }
  if (!byId.has(comic.id)) byId.set(comic.id, comic);

  let list = [...byId.values()];

  // Prefer same format (single with single, TPB with TPB, …)
  const sameFormat = list.filter((c) => c.format === comic.format);
  if (sameFormat.length) list = sameFormat;

  // Open-order variants share a cover year; keeps reboot/facsimile eras from mixing
  const year = comic.coverDate?.slice(0, 4);
  if (year) {
    const sameYear = list.filter((c) => c.coverDate?.slice(0, 4) === year);
    if (sameYear.length) list = sameYear;
  }

  if (list.length > 1) {
    const variants = new Set(list.map((c) => (c.variant ?? "").trim().toLowerCase()));
    const upcs = new Set(list.map((c) => c.upc?.trim()).filter(Boolean));
    // Reboots / facsimiles sharing series+# without variant or UPC signal — not open-order variants
    if (variants.size <= 1 && upcs.size <= 1) {
      return [comic];
    }
  }

  list.sort(sortVariants);
  return list;
}

/** Pick Cover A / primary from a variant family. */
export function pickPrimaryComic(comics: CatalogComic[]): CatalogComic {
  const sorted = [...comics].sort(sortVariants);
  return sorted.find(isPrimaryCover) ?? sorted[0]!;
}

/**
 * Catalog/list collapse: one card per family (primary / Cover A).
 * Families that are not true variant sets (no variant/UPC differentiation) are left intact.
 */
export function collapseComicVariants(catalog: CatalogComic[]): CatalogComic[] {
  const seen = new Set<string>();
  const out: CatalogComic[] = [];

  for (const c of catalog) {
    if (seen.has(c.id)) continue;
    const family = getComicVariants(c, catalog);
    if (family.length <= 1) {
      out.push(c);
      seen.add(c.id);
      continue;
    }
    const primary = pickPrimaryComic(family);
    if (seen.has(primary.id)) {
      for (const v of family) seen.add(v.id);
      continue;
    }
    out.push(primary);
    for (const v of family) seen.add(v.id);
  }

  return out;
}

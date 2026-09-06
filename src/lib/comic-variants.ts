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
  const la = variantDisplayLabel(a).localeCompare(variantDisplayLabel(b), undefined, {
    sensitivity: "base",
  });
  if (la !== 0) return la;
  return a.id.localeCompare(b.id);
}

/** Group key used for open-order collapse (family + format + cover year). */
function collapseGroupKey(c: CatalogComic): string {
  const year = c.coverDate?.slice(0, 4) || "";
  return `${comicFamilyKey(c)}|${c.format}|${year}`;
}

function isTrueVariantSet(list: CatalogComic[]): boolean {
  if (list.length <= 1) return false;
  const variants = new Set(list.map((c) => (c.variant ?? "").trim().toLowerCase()));
  const upcs = new Set(list.map((c) => c.upc?.trim()).filter(Boolean));
  return variants.size > 1 || upcs.size > 1;
}

function refineFamily(comic: CatalogComic, siblings: CatalogComic[]): CatalogComic[] {
  let list = siblings;
  const sameFormat = list.filter((c) => c.format === comic.format);
  if (sameFormat.length) list = sameFormat;
  const year = comic.coverDate?.slice(0, 4);
  if (year) {
    const sameYear = list.filter((c) => c.coverDate?.slice(0, 4) === year);
    if (sameYear.length) list = sameYear;
  }
  return list;
}

/**
 * Open-order / variant covers for the same series+issue+publisher family.
 * Only returns real catalog rows — never invents variants.
 * Ambiguous reboot/facsimile collisions (same family, no variant/UPC differentiation)
 * collapse to the current comic so the strip stays honest.
 *
 * Pass an optional index from `indexComicsByFamily` for O(family) lookup on large catalogs.
 */
export function getComicVariants(
  comic: CatalogComic,
  catalog: CatalogComic[],
  familyIndex?: Map<string, CatalogComic[]>,
): CatalogComic[] {
  const key = comicFamilyKey(comic);
  const siblings = familyIndex?.get(key);
  const byId = new Map<string, CatalogComic>();
  if (siblings) {
    for (const c of siblings) byId.set(c.id, c);
  } else {
    for (const c of catalog) {
      if (comicFamilyKey(c) !== key) continue;
      byId.set(c.id, c);
    }
  }
  if (!byId.has(comic.id)) byId.set(comic.id, comic);

  let list = refineFamily(comic, [...byId.values()]);

  if (list.length > 1 && !isTrueVariantSet(list)) {
    return [comic];
  }

  list.sort(sortVariants);
  return list;
}

/** Build series|issue|publisher → comics index (one O(n) pass). */
export function indexComicsByFamily(catalog: CatalogComic[]): Map<string, CatalogComic[]> {
  const index = new Map<string, CatalogComic[]>();
  for (const c of catalog) {
    const key = comicFamilyKey(c);
    const bucket = index.get(key);
    if (bucket) bucket.push(c);
    else index.set(key, [c]);
  }
  return index;
}

/** Pick Cover A / primary from a variant family. */
export function pickPrimaryComic(comics: CatalogComic[]): CatalogComic {
  const sorted = [...comics].sort(sortVariants);
  return sorted.find(isPrimaryCover) ?? sorted[0]!;
}

/**
 * Catalog/list collapse: one card per true variant family (primary / Cover A).
 * Families that are not true variant sets (no variant/UPC differentiation) are left intact.
 * O(n) — groups once; does not rescan the catalog per row.
 */
export function collapseComicVariants(catalog: CatalogComic[]): CatalogComic[] {
  const groups = new Map<string, CatalogComic[]>();
  for (const c of catalog) {
    const key = collapseGroupKey(c);
    const bucket = groups.get(key);
    if (bucket) bucket.push(c);
    else groups.set(key, [c]);
  }

  const out: CatalogComic[] = [];
  for (const list of groups.values()) {
    if (!isTrueVariantSet(list)) {
      // Preserve encounter order within non-variant collisions (reboots/facsimiles).
      out.push(...list);
      continue;
    }
    out.push(pickPrimaryComic(list));
  }
  return out;
}

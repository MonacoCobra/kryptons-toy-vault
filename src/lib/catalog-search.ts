import type { CatalogComic, CatalogFigure } from "@/lib/types";

function normSku(sku: string | undefined): string | undefined {
  const s = (sku ?? "").trim();
  return s ? s.toLowerCase() : undefined;
}

function figureKey(f: { name: string; subtitle: string; line: string; company: string }) {
  return `${f.name}|${f.subtitle}|${f.line}|${f.company}`.toLowerCase();
}

function comicKey(c: { series: string; issue: string; publisher: string; variant?: string }) {
  return `${c.series}|${c.issue}|${c.publisher}|${c.variant ?? ""}`.toLowerCase();
}

/** Merge live extras onto a loaded shard. Same preference as the baked catalog: sku → id → name key. */
export function mergeFiguresInto(base: CatalogFigure[], extras: CatalogFigure[] = []): CatalogFigure[] {
  if (!extras.length) return base;
  const skus = new Set<string>();
  const ids = new Set<string>();
  const keys = new Set<string>();
  for (const f of base) {
    ids.add(f.id);
    keys.add(figureKey(f));
    const s = normSku(f.sku);
    if (s) skus.add(s);
  }
  const add: CatalogFigure[] = [];
  for (const f of extras) {
    const s = normSku(f.sku);
    if (s && skus.has(s)) continue;
    if (ids.has(f.id)) continue;
    if (keys.has(figureKey(f))) continue;
    add.push(f);
    if (s) skus.add(s);
    ids.add(f.id);
    keys.add(figureKey(f));
  }
  return add.length ? [...base, ...add] : base;
}

export function searchFigureList(list: CatalogFigure[], query: string): CatalogFigure[] {
  const q = query.trim().toLowerCase();
  if (!q) return list;
  return list.filter((f) => {
    const hay =
      `${f.name} ${f.subtitle} ${f.line} ${f.company} ${f.property ?? ""} ${f.party ?? ""} ${f.sku ?? ""} ${f.exclusive ?? ""} ${f.tags.join(" ")}`.toLowerCase();
    return hay.includes(q);
  });
}

export function mergeComicsInto(base: CatalogComic[], extras: CatalogComic[] = []): CatalogComic[] {
  if (!extras.length) return base;
  const seen = new Set(base.map(comicKey));
  const out = [...base];
  for (const c of extras) {
    const k = comicKey(c);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(c);
  }
  return out;
}

/** Same match rules as the baked `searchComics` helper. */
export function searchComicList(list: CatalogComic[], query: string): CatalogComic[] {
  const q = query.trim().toLowerCase();
  if (!q) return list;
  const issueMatch = q.match(/#?\s*(\d+[a-z]?)$/i);
  return list.filter((c) => {
    const writers = Array.isArray(c.writers) ? c.writers.join(" ") : String(c.writers ?? "");
    const artists = Array.isArray(c.artists) ? c.artists.join(" ") : String(c.artists ?? "");
    const hay =
      `${c.series} ${c.issue} ${c.publisher} ${writers} ${artists} ${c.variant ?? ""} ${c.upc ?? ""} ${c.format ?? ""} ${c.description ?? ""}`.toLowerCase();
    if (hay.includes(q)) return true;
    if (issueMatch && c.issue === issueMatch[1] && hay.includes(q.replace(issueMatch[0], "").trim())) {
      return true;
    }
    return false;
  });
}

export function comicByIdIn(
  id: string,
  lists: CatalogComic[][],
): CatalogComic | undefined {
  for (const list of lists) {
    const hit = list.find((c) => c.id === id);
    if (hit) return hit;
  }
  return undefined;
}

export function figureByIdIn(id: string, lists: CatalogFigure[][]): CatalogFigure | undefined {
  for (const list of lists) {
    const hit = list.find((f) => f.id === id);
    if (hit) return hit;
  }
  const q = id.trim().toLowerCase();
  if (!q) return undefined;
  for (const list of lists) {
    const bySku = list.find((f) => normSku(f.sku) === q);
    if (bySku) return bySku;
  }
  return undefined;
}

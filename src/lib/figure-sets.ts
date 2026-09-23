import type { CatalogFigure } from "@/lib/types";

function familyKey(figure: { setId?: string; id: string }): string {
  const setId = figure.setId?.trim();
  return setId ? `set:${setId}` : `solo:${figure.id}`;
}

function compareMembers(a: CatalogFigure, b: CatalogFigure): number {
  const pa = a.setRole === "parent" ? 0 : 1;
  const pb = b.setRole === "parent" ? 0 : 1;
  if (pa !== pb) return pa - pb;
  const byName = a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
  if (byName !== 0) return byName;
  return a.id.localeCompare(b.id);
}

/**
 * Browse collapse: one card per set family when the current list contains
 * more than one member. Families of one stay as-is, so a search that hits
 * only a child still shows that child.
 */
export function collapseFigureSets(list: CatalogFigure[]): CatalogFigure[] {
  const groups = new Map<string, CatalogFigure[]>();
  const order: string[] = [];
  for (const figure of list) {
    const key = familyKey(figure);
    const bucket = groups.get(key);
    if (bucket) bucket.push(figure);
    else {
      groups.set(key, [figure]);
      order.push(key);
    }
  }

  const out: CatalogFigure[] = [];
  for (const key of order) {
    const bucket = groups.get(key)!;
    if (bucket.length <= 1) {
      out.push(bucket[0]!);
      continue;
    }
    const parent = bucket.find((figure) => figure.setRole === "parent") ?? bucket[0]!;
    out.push(parent);
  }
  return out;
}

/** Members of this figure's set, including the parent. Single-figure SKUs return one row. */
export function getFigureSetMembers(figure: CatalogFigure, catalog: CatalogFigure[]): CatalogFigure[] {
  const setId = figure.setId?.trim();
  if (!setId) return [figure];
  const members = catalog.filter((row) => row.setId?.trim() === setId);
  if (!members.some((row) => row.id === figure.id)) members.push(figure);
  if (members.length <= 1) return [figure];
  members.sort(compareMembers);
  return members;
}

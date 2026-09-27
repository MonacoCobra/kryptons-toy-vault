type FigureIdentity = { ids: string[]; skus: string[]; keys: string[] };

const EMPTY: FigureIdentity = { ids: [], skus: [], keys: [] };

/** Baked figure identity for upsert dedupe. Read from the build-time shard, not the client bundle. */
export async function readFigureIdentity(): Promise<FigureIdentity> {
  try {
    const { readFile } = await import("node:fs/promises");
    const { join } = await import("node:path");
    const raw = await readFile(join(process.cwd(), "public", "catalog", "figures", "identity.json"), "utf8");
    const parsed = JSON.parse(raw) as FigureIdentity;
    if (!parsed || !Array.isArray(parsed.ids)) return EMPTY;
    return {
      ids: parsed.ids,
      skus: Array.isArray(parsed.skus) ? parsed.skus : [],
      keys: Array.isArray(parsed.keys) ? parsed.keys : [],
    };
  } catch {
    // Preview hosts serve public/ even when the function filesystem does not.
  }
  try {
    const { getRequest } = await import("@tanstack/react-start/server");
    const origin = new URL(getRequest().url).origin;
    const res = await fetch(`${origin}/catalog/figures/identity.json`);
    if (!res.ok) return EMPTY;
    const parsed = (await res.json()) as FigureIdentity;
    if (!parsed || !Array.isArray(parsed.ids)) return EMPTY;
    return {
      ids: parsed.ids,
      skus: Array.isArray(parsed.skus) ? parsed.skus : [],
      keys: Array.isArray(parsed.keys) ? parsed.keys : [],
    };
  } catch {
    return EMPTY;
  }
}

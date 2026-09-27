import { upcBucketPath } from "@/lib/catalog-shard";

type UpcMapEntry = {
  upc?: string;
  locgId?: string;
  coverUrl?: string;
  source?: string;
};

/** One UPC-map bucket. The full map is not imported into the client bundle. */
export async function readUpcEntry(comicId: string): Promise<UpcMapEntry | null> {
  const rel = upcBucketPath(comicId);
  try {
    const { readFile } = await import("node:fs/promises");
    const { join } = await import("node:path");
    const raw = await readFile(join(process.cwd(), "public", "catalog", rel), "utf8");
    const map = JSON.parse(raw) as Record<string, UpcMapEntry>;
    return map[comicId] ?? null;
  } catch {
    // Static file is served by the host when the function filesystem does not have public/.
  }
  try {
    const { getRequest } = await import("@tanstack/react-start/server");
    const origin = new URL(getRequest().url).origin;
    const res = await fetch(`${origin}/catalog/${rel}`);
    if (!res.ok) return null;
    const map = (await res.json()) as Record<string, UpcMapEntry>;
    return map[comicId] ?? null;
  } catch {
    return null;
  }
}

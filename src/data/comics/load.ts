import { SHARDS } from "./shard-list.ts";

export type ComicShardEntry = { seq: number; row: unknown[] };
export type ComicShard = { entries: ComicShardEntry[] };

/** Catalog rows in original order. Shards are assigned by id, not by publisher. */
export function loadComicRows(): unknown[][] {
  const packed: ComicShardEntry[] = [];
  for (const shard of SHARDS as ComicShard[]) {
    for (const entry of shard.entries) packed.push(entry);
  }
  packed.sort((a, b) => a.seq - b.seq);
  return packed.map((entry) => entry.row);
}

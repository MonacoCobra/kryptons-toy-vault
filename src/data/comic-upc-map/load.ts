import { SHARDS } from "./shard-list.ts";

export type UpcMapEntry = {
  upc?: string;
  isbn?: string;
  coverUrl?: string;
  locgId?: string;
  gcdIssueId?: string;
  sourceId?: string;
  source?: string;
  title?: string;
  url?: string;
  fetchedAt?: string;
  coverSource?: string;
  coverSourceId?: string;
};

type UpcShard = { entries: Record<string, UpcMapEntry> };

const merged: Record<string, UpcMapEntry> = {};
for (const shard of SHARDS as UpcShard[]) {
  Object.assign(merged, shard.entries);
}

export const UPC_MAP: Record<string, UpcMapEntry> = merged;

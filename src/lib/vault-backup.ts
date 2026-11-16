import type { VaultState } from "@/lib/types";

/** Current Zustand persist key used by the live app (old site and new site). */
export const CURRENT_VAULT_STORAGE_KEY = "krypton-toy-vault-v4";

/** Older persist keys that may still be sitting in a browser from earlier versions. */
export const LEGACY_VAULT_STORAGE_KEYS = ["krypton-toy-vault-v3"] as const;

export const VAULT_STORAGE_PREFIX = "krypton-toy-vault";
export const VAULT_BACKUP_KIND = "vault-backup";
export const VAULT_BACKUP_VERSION = 1;
export const OLD_SITE_URL = "https://kryptons-toy-vault.grok.me";
export const IMPORT_PATH = "/import";

export type VaultCounts = {
  ownedFigures: number;
  wantedFigures: number;
  ownedComics: number;
  wantedComics: number;
  customComics: number;
  displays: number;
  pulseBaselines: number;
  totalItems: number;
};

export type VaultBackup = {
  app: "kryptons-toy-vault";
  kind: typeof VAULT_BACKUP_KIND;
  version: number;
  exportedAt: string;
  sourceOrigin?: string;
  keys?: Record<string, unknown>;
  state: VaultState;
};

export type ParseBackupResult =
  | { ok: true; backup: VaultBackup; counts: VaultCounts; warnings: string[] }
  | { ok: false; error: string };

export type StorageLike = {
  length: number;
  key(index: number): string | null;
  getItem(key: string): string | null;
};

export function emptyVaultState(): VaultState {
  return {
    ownedFigures: {},
    wantedFigures: {},
    ownedComics: {},
    wantedComics: {},
    customComics: {},
    displays: {},
    pulseBaselines: {},
    lastPulseNoticeWeek: null,
  };
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asMap<T>(value: unknown): Record<string, T> {
  return isRecord(value) ? (value as Record<string, T>) : {};
}

/** True when a value looks like saved vault data (any of the collection maps). */
export function normalizeVaultState(value: unknown): VaultState | null {
  if (!isRecord(value)) return null;
  const hasAny =
    isRecord(value.ownedFigures) ||
    isRecord(value.wantedFigures) ||
    isRecord(value.ownedComics) ||
    isRecord(value.wantedComics) ||
    isRecord(value.customComics) ||
    isRecord(value.displays);
  if (!hasAny) return null;
  return {
    ownedFigures: asMap(value.ownedFigures),
    wantedFigures: asMap(value.wantedFigures),
    ownedComics: asMap(value.ownedComics),
    wantedComics: asMap(value.wantedComics),
    customComics: asMap(value.customComics),
    displays: asMap(value.displays),
    pulseBaselines: asMap(value.pulseBaselines),
    lastPulseNoticeWeek:
      typeof value.lastPulseNoticeWeek === "string" ? value.lastPulseNoticeWeek : null,
  };
}

function parseJsonValue(value: unknown): unknown {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function stateFromPersistOrState(value: unknown): VaultState | null {
  const parsed = parseJsonValue(value);
  if (isRecord(parsed) && parsed.state) {
    const fromPersist = normalizeVaultState(parsed.state);
    if (fromPersist) return fromPersist;
  }
  return normalizeVaultState(parsed);
}

/** Prefer v4, then v3, then any other krypton-toy-vault* key (newest name first). */
export function stateFromKeyMap(keys: Record<string, unknown>): VaultState | null {
  const preferred = keys[CURRENT_VAULT_STORAGE_KEY];
  if (preferred != null) {
    const state = stateFromPersistOrState(preferred);
    if (state) return state;
  }
  const legacy = keys["krypton-toy-vault-v3"];
  if (legacy != null) {
    const state = stateFromPersistOrState(legacy);
    if (state) return state;
  }
  const rest = Object.entries(keys)
    .filter(([key]) => key.startsWith(VAULT_STORAGE_PREFIX))
    .sort(([a], [b]) => b.localeCompare(a));
  for (const [, value] of rest) {
    const state = stateFromPersistOrState(value);
    if (state) return state;
  }
  return null;
}

export function extractStateFromUnknown(value: unknown): VaultState | null {
  if (!isRecord(value)) return null;
  if (value.kind === VAULT_BACKUP_KIND || value.app === "kryptons-toy-vault") {
    if (value.state) {
      const fromState = stateFromPersistOrState(value.state);
      if (fromState) return fromState;
    }
    if (isRecord(value.keys)) {
      const fromKeys = stateFromKeyMap(value.keys);
      if (fromKeys) return fromKeys;
    }
  }
  if (isRecord(value.keys)) {
    const fromKeys = stateFromKeyMap(value.keys);
    if (fromKeys) return fromKeys;
  }
  return stateFromPersistOrState(value);
}

export function collectStorageKeys(storage: StorageLike): Record<string, unknown> {
  const found = new Set<string>([CURRENT_VAULT_STORAGE_KEY, ...LEGACY_VAULT_STORAGE_KEYS]);
  try {
    for (let i = 0; i < storage.length; i += 1) {
      const key = storage.key(i);
      if (key && key.startsWith(VAULT_STORAGE_PREFIX)) found.add(key);
    }
  } catch {
    // Some browsers throw if storage is blocked.
  }
  const keys: Record<string, unknown> = {};
  for (const key of found) {
    try {
      const raw = storage.getItem(key);
      if (raw) keys[key] = parseJsonValue(raw) ?? raw;
    } catch {
      // Skip unreadable keys.
    }
  }
  return keys;
}

export function buildBackupFromState(
  state: VaultState,
  options?: { origin?: string; keys?: Record<string, unknown>; exportedAt?: string },
): VaultBackup {
  const backup: VaultBackup = {
    app: "kryptons-toy-vault",
    kind: VAULT_BACKUP_KIND,
    version: VAULT_BACKUP_VERSION,
    exportedAt: options?.exportedAt ?? new Date().toISOString(),
    state,
  };
  if (options?.origin) backup.sourceOrigin = options.origin;
  if (options?.keys) backup.keys = options.keys;
  return backup;
}

export function buildBackupFromStorage(storage: StorageLike, origin?: string): VaultBackup | null {
  const keys = collectStorageKeys(storage);
  const state = stateFromKeyMap(keys);
  if (!state) return null;
  return buildBackupFromState(state, { origin, keys });
}

export function parseVaultBackup(input: string | unknown): ParseBackupResult {
  let value: unknown = input;
  if (typeof input === "string") {
    const trimmed = input.trim();
    if (!trimmed) return { ok: false, error: "The backup is empty." };
    try {
      value = JSON.parse(trimmed);
    } catch {
      return {
        ok: false,
        error: "That file isn't valid JSON. Export again from the old site and try the new file.",
      };
    }
  }
  const state = extractStateFromUnknown(value);
  if (!state) {
    return { ok: false, error: "That JSON doesn't look like a Krypton's Toy Vault backup." };
  }
  const counts = countVault(state);
  if (counts.totalItems === 0) {
    return {
      ok: false,
      error: "That backup has no saved figures, comics, wishlist items, or displays.",
    };
  }
  const origin =
    isRecord(value) && typeof value.sourceOrigin === "string" ? value.sourceOrigin : undefined;
  const exportedAt =
    isRecord(value) && typeof value.exportedAt === "string"
      ? value.exportedAt
      : new Date().toISOString();
  const keys = isRecord(value) && isRecord(value.keys) ? value.keys : undefined;
  return {
    ok: true,
    backup: buildBackupFromState(state, { origin, keys, exportedAt }),
    counts,
    warnings: [],
  };
}

export function countVault(state: VaultState): VaultCounts {
  const ownedFigures = Object.keys(state.ownedFigures ?? {}).length;
  const wantedFigures = Object.keys(state.wantedFigures ?? {}).length;
  const ownedComics = Object.keys(state.ownedComics ?? {}).length;
  const wantedComics = Object.keys(state.wantedComics ?? {}).length;
  const customComics = Object.keys(state.customComics ?? {}).length;
  const displays = Object.keys(state.displays ?? {}).length;
  const pulseBaselines = Object.keys(state.pulseBaselines ?? {}).length;
  return {
    ownedFigures,
    wantedFigures,
    ownedComics,
    wantedComics,
    customComics,
    displays,
    pulseBaselines,
    totalItems:
      ownedFigures + wantedFigures + ownedComics + wantedComics + customComics + displays,
  };
}

export function formatVaultCounts(counts: VaultCounts): string {
  const parts = [
    `${counts.ownedFigures} owned figure${counts.ownedFigures === 1 ? "" : "s"}`,
    `${counts.ownedComics} owned comic${counts.ownedComics === 1 ? "" : "s"}`,
  ];
  const wished = counts.wantedFigures + counts.wantedComics;
  if (wished) parts.push(`${wished} wishlist item${wished === 1 ? "" : "s"}`);
  if (counts.customComics) {
    parts.push(`${counts.customComics} custom title${counts.customComics === 1 ? "" : "s"}`);
  }
  if (counts.displays) {
    parts.push(`${counts.displays} display photo${counts.displays === 1 ? "" : "s"}`);
  }
  return parts.join(", ");
}

/** Drop wishlist rows that are already owned, matching add-to-collection behavior. */
export function pruneOwnedFromWishlist(state: VaultState): VaultState {
  const wantedFigures = { ...state.wantedFigures };
  for (const id of Object.keys(state.ownedFigures)) delete wantedFigures[id];

  const wantedComics = { ...state.wantedComics };
  for (const owned of Object.values(state.ownedComics)) {
    if (owned.catalogId) delete wantedComics[owned.catalogId];
    if (owned.custom?.id) delete wantedComics[owned.custom.id];
    delete wantedComics[owned.id];
  }
  return { ...state, wantedFigures, wantedComics };
}

export function mergeVault(current: VaultState, incoming: VaultState): VaultState {
  return pruneOwnedFromWishlist({
    ownedFigures: { ...current.ownedFigures, ...incoming.ownedFigures },
    wantedFigures: { ...current.wantedFigures, ...incoming.wantedFigures },
    ownedComics: { ...current.ownedComics, ...incoming.ownedComics },
    wantedComics: { ...current.wantedComics, ...incoming.wantedComics },
    customComics: { ...current.customComics, ...incoming.customComics },
    displays: { ...current.displays, ...incoming.displays },
    pulseBaselines: { ...current.pulseBaselines, ...incoming.pulseBaselines },
    lastPulseNoticeWeek: incoming.lastPulseNoticeWeek ?? current.lastPulseNoticeWeek,
  });
}

export function replaceVault(_current: VaultState, incoming: VaultState): VaultState {
  return pruneOwnedFromWishlist({ ...emptyVaultState(), ...incoming });
}

export function pickVaultState(source: VaultState): VaultState {
  return {
    ownedFigures: source.ownedFigures ?? {},
    wantedFigures: source.wantedFigures ?? {},
    ownedComics: source.ownedComics ?? {},
    wantedComics: source.wantedComics ?? {},
    customComics: source.customComics ?? {},
    displays: source.displays ?? {},
    pulseBaselines: source.pulseBaselines ?? {},
    lastPulseNoticeWeek: source.lastPulseNoticeWeek ?? null,
  };
}

export function backupFilename(date = new Date()): string {
  return `kryptons-toy-vault-backup-${date.toISOString().slice(0, 10)}.json`;
}

export function stringifyBackup(backup: VaultBackup): string {
  return `${JSON.stringify(backup, null, 2)}\n`;
}

export function downloadJsonFile(filename: string, json: string): void {
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/**
 * Self-contained script to run in the console (or as a bookmarklet) on the old
 * site. It cannot live on the old site, so this string is what the user pastes.
 * Keep the key names and backup shape in sync with the helpers above.
 */
export const VAULT_EXPORT_SNIPPET = `(function(){
  var PREFIX="krypton-toy-vault";
  var PREFERRED=["krypton-toy-vault-v4","krypton-toy-vault-v3"];
  var keys={};
  function parse(s){try{return JSON.parse(s)}catch(e){return s}}
  try{
    for(var i=0;i<localStorage.length;i++){
      var k=localStorage.key(i);
      if(k&&k.indexOf(PREFIX)===0){
        var raw=localStorage.getItem(k);
        if(raw) keys[k]=parse(raw);
      }
    }
  }catch(e){}
  for(var p=0;p<PREFERRED.length;p++){
    if(!keys[PREFERRED[p]]){
      try{
        var r=localStorage.getItem(PREFERRED[p]);
        if(r) keys[PREFERRED[p]]=parse(r);
      }catch(e){}
    }
  }
  function pick(){
    for(var p=0;p<PREFERRED.length;p++){
      if(keys[PREFERRED[p]]){
        var v=keys[PREFERRED[p]];
        return v&&v.state?v.state:v;
      }
    }
    for(var k in keys){
      if(Object.prototype.hasOwnProperty.call(keys,k)){
        var v=keys[k];
        return v&&v.state?v.state:v;
      }
    }
    return null;
  }
  var state=pick();
  if(!state){
    alert("No Krypton's Toy Vault collection was found in this browser for this site.");
    return;
  }
  function size(o){return o&&typeof o==="object"?Object.keys(o).length:0}
  var ownedFigures=size(state.ownedFigures);
  var ownedComics=size(state.ownedComics);
  var wished=size(state.wantedFigures)+size(state.wantedComics);
  var displays=size(state.displays);
  var backup={
    app:"kryptons-toy-vault",
    kind:"vault-backup",
    version:1,
    exportedAt:new Date().toISOString(),
    sourceOrigin:location.origin,
    keys:keys,
    state:state
  };
  var json=JSON.stringify(backup,null,2);
  try{
    var blob=new Blob([json],{type:"application/json"});
    var url=URL.createObjectURL(blob);
    var a=document.createElement("a");
    a.href=url;
    a.download="kryptons-toy-vault-backup.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function(){URL.revokeObjectURL(url)},2000);
  }catch(e){}
  var old=document.getElementById("ktv-export-overlay");
  if(old) old.remove();
  var wrap=document.createElement("div");
  wrap.id="ktv-export-overlay";
  wrap.setAttribute("style","position:fixed;inset:0;z-index:2147483647;background:rgba(0,0,0,.72);display:flex;align-items:center;justify-content:center;padding:16px;font-family:system-ui,sans-serif");
  var box=document.createElement("div");
  box.setAttribute("style","background:#111827;color:#f8fafc;max-width:640px;width:100%;max-height:90vh;overflow:auto;border-radius:12px;padding:20px;box-shadow:0 10px 40px rgba(0,0,0,.4)");
  var summary=ownedFigures+" owned figures, "+ownedComics+" owned comics, "+wished+" wishlist items, "+displays+" display photos.";
  var heading=document.createElement("h2");
  heading.textContent="Collection backup ready";
  heading.setAttribute("style","margin:0 0 8px;font-size:20px");
  var p=document.createElement("p");
  p.setAttribute("style","margin:0 0 12px;line-height:1.45");
  p.textContent=summary+" A file should also have downloaded. If it didn't, use Copy or select the text below, then paste it on KryptonsToyVault.com/import.";
  var ta=document.createElement("textarea");
  ta.value=json;
  ta.readOnly=true;
  ta.setAttribute("style","width:100%;height:180px;box-sizing:border-box;margin:0 0 12px;font:12px/1.4 ui-monospace,monospace;background:#0b1220;color:#e2e8f0;border:1px solid #334155;border-radius:8px;padding:8px");
  function btn(label,primary,fn){
    var b=document.createElement("button");
    b.type="button";
    b.textContent=label;
    b.setAttribute("style","margin:0 8px 8px 0;padding:10px 14px;border:0;border-radius:8px;background:"+(primary?"#e30613":"#334155")+";color:#fff;font-weight:600;cursor:pointer");
    b.onclick=fn;
    return b;
  }
  var row=document.createElement("div");
  row.appendChild(btn("Copy backup",true,function(){
    function ok(){alert("Copied. Open KryptonsToyVault.com/import and paste it there.");}
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(json).then(ok).catch(function(){ta.select();document.execCommand("copy");ok();});
    }else{ta.select();document.execCommand("copy");ok();}
  }));
  row.appendChild(btn("Close",false,function(){wrap.remove();}));
  box.appendChild(heading);
  box.appendChild(p);
  box.appendChild(ta);
  box.appendChild(row);
  wrap.appendChild(box);
  wrap.addEventListener("click",function(e){if(e.target===wrap)wrap.remove();});
  document.body.appendChild(wrap);
  ta.focus();
  ta.select();
})();`;

export function vaultExportBookmarklet(): string {
  return `javascript:${encodeURIComponent(VAULT_EXPORT_SNIPPET)}`;
}

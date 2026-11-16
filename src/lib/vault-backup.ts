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

/** Short loader bookmarklet for phones. The real export script lives at /x.js. */
export const NEW_SITE_ORIGIN = "https://kryptonstoyvault.com";
export const VAULT_EXPORT_SCRIPT_PATH = "/x.js";
export const VAULT_HANDOFF_PATH = "/api/vault-handoff";
export const HANDOFF_STORAGE_KEY = "ktv-vault-handoff";
export const HANDOFF_IDB_NAME = "ktv-handoff";
export const BOOKMARKLET_NAME = "Move vault";

/**
 * 110-character loader. The old site has no Content-Security-Policy, so it can
 * load this script from the new site. Do not lengthen it — phone bookmark
 * fields rejected the previous long bookmarklet.
 */
export const SHORT_VAULT_BOOKMARKLET =
  "javascript:document.head.appendChild(document.createElement('script')).src='https://kryptonstoyvault.com/x.js'";

/** Console-friendly loader (same as the bookmarklet, without the javascript: prefix). */
export const VAULT_CONSOLE_LOADER =
  "document.head.appendChild(document.createElement('script')).src='https://kryptonstoyvault.com/x.js'";

export function vaultExportBookmarklet(): string {
  return SHORT_VAULT_BOOKMARKLET;
}

/** Escape JSON so it can sit inside a <script type="application/json"> tag. */
export function escapeJsonForScript(json: string): string {
  return json
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}

export async function readBackupFromRequest(request: Request): Promise<string> {
  const contentType = request.headers.get("content-type") ?? "";
  if (contentType.includes("multipart/form-data") || contentType.includes("application/x-www-form-urlencoded")) {
    const form = await request.formData();
    const value = form.get("backup");
    return typeof value === "string" ? value : "";
  }
  return request.text();
}

/** HTML returned to the same tab after a form POST from the old site. Nothing is stored on the server. */
export function renderHandoffPage(json: string): string {
  const escaped = escapeJsonForScript(json);
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Moving your collection…</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0b1220; color: #f8fafc; margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px; }
    p { max-width: 28rem; line-height: 1.5; text-align: center; }
  </style>
</head>
<body>
  <p id="msg">Moving your collection to the new site…</p>
  <script type="application/json" id="ktv-backup">${escaped}</script>
  <script>
  (function () {
    var rawEl = document.getElementById("ktv-backup");
    var raw = rawEl ? rawEl.textContent : "";
    var msg = document.getElementById("msg");
    function fail(text) {
      if (msg) msg.textContent = text;
    }
    function go() {
      location.replace("/import?handoff=1");
    }
    function saveIdb(value, done) {
      try {
        var req = indexedDB.open("ktv-handoff", 1);
        req.onupgradeneeded = function () {
          var db = req.result;
          if (!db.objectStoreNames.contains("data")) db.createObjectStore("data");
        };
        req.onsuccess = function () {
          var db = req.result;
          var tx = db.transaction("data", "readwrite");
          tx.objectStore("data").put(value, "backup");
          tx.oncomplete = function () { db.close(); done(true); };
          tx.onerror = function () { db.close(); done(false); };
        };
        req.onerror = function () { done(false); };
      } catch (e) {
        done(false);
      }
    }
    if (!raw) {
      fail("The backup was empty. Go back to the old site and try the bookmark again.");
      return;
    }
    try { JSON.parse(raw); } catch (e) {
      fail("That backup could not be read. Go back to the old site and try the bookmark again.");
      return;
    }
    try {
      sessionStorage.setItem("ktv-vault-handoff", raw);
      go();
      return;
    } catch (e) {}
    saveIdb(raw, function (ok) {
      if (ok) go();
      else fail("This backup is too large to keep in the browser. Try again, or use the import page to paste a file without display photos.");
    });
  })();
  </script>
</body>
</html>
`;
}

export function renderHandoffError(message: string): string {
  const safe = message.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Could not move the collection</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0b1220; color: #f8fafc; margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px; }
    p { max-width: 28rem; line-height: 1.5; text-align: center; }
    a { color: #f8fafc; }
  </style>
</head>
<body>
  <p>${safe} You can go to <a href="/import">kryptonstoyvault.com/import</a> and try again.</p>
</body>
</html>
`;
}

/**
 * Hosted at /x.js and loaded by the short bookmarklet on the old site.
 * Collects the vault, then POSTs it in the same tab to the new site so the
 * user lands on the import page with the backup already loaded. No server
 * storage: the POST is echoed back as a page on the new origin.
 */
export const VAULT_EXPORT_SCRIPT = `(function(){
  var PREFIX="krypton-toy-vault";
  var PREFERRED=["krypton-toy-vault-v4","krypton-toy-vault-v3"];
  var DEFAULT_ORIGIN="https://kryptonstoyvault.com";
  var origin=DEFAULT_ORIGIN;
  try{
    var cur=document.currentScript;
    if(cur&&cur.src) origin=new URL(cur.src).origin;
  }catch(e){}
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
    alert("No Krypton's Toy Vault collection was found in this browser for this site. Open the old site in Chrome (not the installed app) and try again.");
    return;
  }
  function size(o){return o&&typeof o==="object"?Object.keys(o).length:0}
  var summary=size(state.ownedFigures)+" owned figures, "+size(state.ownedComics)+" owned comics.";
  var backup={
    app:"kryptons-toy-vault",
    kind:"vault-backup",
    version:1,
    exportedAt:new Date().toISOString(),
    sourceOrigin:location.origin,
    keys:keys,
    state:state
  };
  var json=JSON.stringify(backup);
  var old=document.getElementById("ktv-export-overlay");
  if(old) old.remove();
  var wrap=document.createElement("div");
  wrap.id="ktv-export-overlay";
  wrap.setAttribute("style","position:fixed;inset:0;z-index:2147483647;background:rgba(0,0,0,.72);display:flex;align-items:center;justify-content:center;padding:16px;font-family:system-ui,sans-serif");
  var box=document.createElement("div");
  box.setAttribute("style","background:#111827;color:#f8fafc;max-width:480px;width:100%;border-radius:12px;padding:20px;text-align:center");
  box.textContent="Found "+summary+" Sending you to the new site…";
  wrap.appendChild(box);
  document.body.appendChild(wrap);
  var form=document.createElement("form");
  form.method="POST";
  form.action=origin+"/api/vault-handoff";
  form.enctype="multipart/form-data";
  form.acceptCharset="UTF-8";
  form.style.display="none";
  var input=document.createElement("textarea");
  input.name="backup";
  input.value=json;
  form.appendChild(input);
  document.body.appendChild(form);
  form.submit();
})();
`;


export async function readHandoffBackup(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  try {
    const fromSession = window.sessionStorage.getItem(HANDOFF_STORAGE_KEY);
    if (fromSession) return fromSession;
  } catch {
    // sessionStorage may be blocked
  }
  try {
    return await new Promise((resolve) => {
      const req = window.indexedDB.open(HANDOFF_IDB_NAME, 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains("data")) db.createObjectStore("data");
      };
      req.onsuccess = () => {
        const db = req.result;
        try {
          const tx = db.transaction("data", "readonly");
          const get = tx.objectStore("data").get("backup");
          get.onsuccess = () => {
            const value = get.result;
            db.close();
            resolve(typeof value === "string" && value ? value : null);
          };
          get.onerror = () => {
            db.close();
            resolve(null);
          };
        } catch {
          db.close();
          resolve(null);
        }
      };
      req.onerror = () => resolve(null);
    });
  } catch {
    return null;
  }
}

export async function clearHandoffBackup(): Promise<void> {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(HANDOFF_STORAGE_KEY);
  } catch {
    // ignore
  }
  try {
    await new Promise<void>((resolve) => {
      const req = window.indexedDB.open(HANDOFF_IDB_NAME, 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains("data")) db.createObjectStore("data");
      };
      req.onsuccess = () => {
        const db = req.result;
        try {
          const tx = db.transaction("data", "readwrite");
          tx.objectStore("data").delete("backup");
          tx.oncomplete = () => {
            db.close();
            resolve();
          };
          tx.onerror = () => {
            db.close();
            resolve();
          };
        } catch {
          db.close();
          resolve();
        }
      };
      req.onerror = () => resolve();
    });
  } catch {
    // ignore
  }
}

import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { createContext, runInContext } from "node:vm";
import type { OwnedComic, OwnedFigure, VaultState, WishlistItem } from "@/lib/types";
import {
  CURRENT_VAULT_STORAGE_KEY,
  VAULT_EXPORT_SNIPPET,
  buildBackupFromState,
  buildBackupFromStorage,
  countVault,
  formatVaultCounts,
  mergeVault,
  SHORT_VAULT_BOOKMARKLET,
  VAULT_EXPORT_SCRIPT,
  escapeJsonForScript,
  parseVaultBackup,
  renderHandoffPage,
  replaceVault,
  stringifyBackup,
  vaultExportBookmarklet,
} from "@/lib/vault-backup";

function figure(id: string, extra: Partial<OwnedFigure> = {}): OwnedFigure {
  return {
    figureId: id,
    condition: "opened",
    addedAt: "2026-01-01T00:00:00.000Z",
    acquiredPrice: 25,
    ...extra,
  };
}

function comic(id: string, extra: Partial<OwnedComic> = {}): OwnedComic {
  return {
    id,
    catalogId: id,
    grade: "raw",
    addedAt: "2026-01-01T00:00:00.000Z",
    acquiredPrice: 8,
    ...extra,
  };
}

function want(id: string): WishlistItem {
  return { id, addedAt: "2026-01-02T00:00:00.000Z" };
}

function sampleState(overrides: Partial<VaultState> = {}): VaultState {
  return {
    ownedFigures: { "fig-1": figure("fig-1") },
    wantedFigures: { "fig-2": want("fig-2") },
    ownedComics: { "own-c1": comic("own-c1", { catalogId: "c1" }) },
    wantedComics: { c2: want("c2") },
    customComics: {},
    displays: {},
    pulseBaselines: {},
    lastPulseNoticeWeek: null,
    ...overrides,
  };
}

class MemoryStorage {
  private data: Record<string, string>;
  constructor(data: Record<string, string> = {}) {
    this.data = { ...data };
  }
  get length() {
    return Object.keys(this.data).length;
  }
  key(index: number) {
    return Object.keys(this.data)[index] ?? null;
  }
  getItem(key: string) {
    return this.data[key] ?? null;
  }
  setItem(key: string, value: string) {
    this.data[key] = value;
  }
}

describe("parseVaultBackup", () => {
  it("accepts a vault-backup wrapper", () => {
    const state = sampleState();
    const backup = buildBackupFromState(state, { origin: "https://kryptons-toy-vault.grok.me" });
    const parsed = parseVaultBackup(stringifyBackup(backup));
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;
    assert.equal(parsed.counts.ownedFigures, 1);
    assert.equal(parsed.counts.ownedComics, 1);
    assert.equal(parsed.counts.wantedFigures, 1);
    assert.equal(parsed.counts.wantedComics, 1);
    assert.equal(parsed.backup.state.ownedFigures["fig-1"]?.acquiredPrice, 25);
    assert.equal(parsed.backup.sourceOrigin, "https://kryptons-toy-vault.grok.me");
  });

  it("accepts a raw Zustand persist blob", () => {
    const persist = { state: sampleState(), version: 0 };
    const parsed = parseVaultBackup(JSON.stringify(persist));
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;
    assert.equal(parsed.counts.ownedFigures, 1);
    assert.equal(parsed.backup.state.ownedComics["own-c1"]?.catalogId, "c1");
  });

  it("accepts a raw vault state object", () => {
    const parsed = parseVaultBackup(sampleState());
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;
    assert.equal(parsed.counts.totalItems, 4);
  });

  it("prefers v4 over v3 when both keys are present", () => {
    const v3 = {
      state: sampleState({ ownedFigures: { old: figure("old", { notes: "legacy" }) } }),
      version: 0,
    };
    const v4 = { state: sampleState({ ownedFigures: { neu: figure("neu", { notes: "current" }) } }), version: 0 };
    const parsed = parseVaultBackup({
      keys: {
        "krypton-toy-vault-v3": v3,
        "krypton-toy-vault-v4": v4,
      },
    });
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;
    assert.equal(parsed.backup.state.ownedFigures.neu?.notes, "current");
    assert.equal(parsed.backup.state.ownedFigures.old, undefined);
  });

  it("rejects empty, invalid, or unrelated JSON", () => {
    assert.equal(parseVaultBackup("").ok, false);
    assert.equal(parseVaultBackup("{not json").ok, false);
    assert.equal(parseVaultBackup('{"hello":"world"}').ok, false);
    assert.equal(parseVaultBackup(sampleState({ ownedFigures: {}, wantedFigures: {}, ownedComics: {}, wantedComics: {} })).ok, false);
  });
});

describe("merge and replace", () => {
  it("merges incoming items over the current vault and drops owned wishlist rows", () => {
    const current = sampleState({
      ownedFigures: { keep: figure("keep", { acquiredPrice: 10 }) },
      wantedFigures: { "fig-1": want("fig-1"), other: want("other") },
    });
    const incoming = sampleState({
      ownedFigures: { "fig-1": figure("fig-1", { acquiredPrice: 40, notes: "paid forty" }) },
      wantedFigures: {},
    });
    const merged = mergeVault(current, incoming);
    assert.equal(merged.ownedFigures.keep?.acquiredPrice, 10);
    assert.equal(merged.ownedFigures["fig-1"]?.acquiredPrice, 40);
    assert.equal(merged.ownedFigures["fig-1"]?.notes, "paid forty");
    assert.equal(merged.wantedFigures["fig-1"], undefined);
    assert.equal(merged.wantedFigures.other?.id, "other");
    assert.equal(merged.ownedComics["own-c1"]?.acquiredPrice, 8);
  });

  it("replace keeps only the incoming collection", () => {
    const current = sampleState();
    const incoming = sampleState({
      ownedFigures: { only: figure("only") },
      wantedFigures: {},
      ownedComics: {},
      wantedComics: {},
    });
    const next = replaceVault(current, incoming);
    assert.deepEqual(Object.keys(next.ownedFigures), ["only"]);
    assert.deepEqual(Object.keys(next.ownedComics), []);
    assert.deepEqual(Object.keys(next.wantedComics), []);
  });
});

describe("buildBackupFromStorage", () => {
  it("collects the current persist key from a storage mock", () => {
    const state = sampleState();
    const storage = new MemoryStorage({
      [CURRENT_VAULT_STORAGE_KEY]: JSON.stringify({ state, version: 0 }),
      unrelated: "ignore me",
    });
    const backup = buildBackupFromStorage(storage, "https://kryptons-toy-vault.grok.me");
    assert.ok(backup);
    assert.equal(backup?.state.ownedFigures["fig-1"]?.figureId, "fig-1");
    assert.ok(backup?.keys?.[CURRENT_VAULT_STORAGE_KEY]);
  });
});

describe("formatVaultCounts", () => {
  it("summarizes counts in plain language", () => {
    const text = formatVaultCounts(countVault(sampleState({ displays: { d1: { id: "d1", photoDataUrl: "data:image/jpeg;base64,xx", addedAt: "2026-01-01T00:00:00.000Z" } } })));
    assert.match(text, /1 owned figure/);
    assert.match(text, /1 owned comic/);
    assert.match(text, /2 wishlist items/);
    assert.match(text, /1 display photo/);
  });
});

describe("export snippet", () => {
  const originalDoc = (globalThis as { document?: unknown }).document;

  afterEach(() => {
    if (originalDoc === undefined) delete (globalThis as { document?: unknown }).document;
    else (globalThis as { document?: unknown }).document = originalDoc;
  });

  it("builds a short javascript: bookmarklet that loads /x.js", () => {
    assert.equal(vaultExportBookmarklet(), SHORT_VAULT_BOOKMARKLET);
    assert.equal(SHORT_VAULT_BOOKMARKLET.startsWith("javascript:"), true);
    assert.ok(SHORT_VAULT_BOOKMARKLET.length <= 120, `bookmarklet is ${SHORT_VAULT_BOOKMARKLET.length} chars`);
    assert.match(SHORT_VAULT_BOOKMARKLET, /https:\/\/kryptonstoyvault\.com\/x\.js/);
    assert.match(VAULT_EXPORT_SNIPPET, /krypton-toy-vault-v4/);
  });

  it("reads v4 storage, downloads JSON, and produces a parseable backup", () => {
    const state = sampleState({ ownedFigures: { prime: figure("prime", { notes: "from old site" }) } });
    const persist = JSON.stringify({ state, version: 0 });
    const data: Record<string, string> = { [CURRENT_VAULT_STORAGE_KEY]: persist };
    const keys = Object.keys(data);
    const downloaded: string[] = [];
    const created: { id?: string; children: unknown[] }[] = [];

    const storage = {
      get length() {
        return keys.length;
      },
      key(index: number) {
        return keys[index] ?? null;
      },
      getItem(key: string) {
        return data[key] ?? null;
      },
    };

    const textarea = {
      value: "",
      readOnly: false,
      style: "",
      focus() {},
      select() {},
      setAttribute() {},
    };

    const documentMock = {
      getElementById() {
        return null;
      },
      createElement(tag: string) {
        if (tag === "textarea") return textarea;
        const node: {
          id?: string;
          type?: string;
          href?: string;
          download?: string;
          textContent?: string;
          value?: string;
          readOnly?: boolean;
          style?: string;
          children: unknown[];
          onclick?: (() => void) | null;
          appendChild(child: unknown): unknown;
          remove(): void;
          setAttribute(name: string, value: string): void;
          addEventListener(): void;
          click(): void;
          focus(): void;
          select(): void;
        } = {
          children: [],
          onclick: null,
          appendChild(child) {
            this.children.push(child);
            created.push(this);
            return child;
          },
          remove() {},
          setAttribute(name, value) {
            if (name === "style") this.style = value;
            if (name === "id") this.id = value;
          },
          addEventListener() {},
          click() {
            if (this.download && this.href) downloaded.push(this.href);
          },
          focus() {},
          select() {},
        };
        return node;
      },
      body: {
        appendChild(child: unknown) {
          created.push(child as { id?: string; children: unknown[] });
          return child;
        },
      },
    };
    (globalThis as { document?: unknown }).document = documentMock;

    const context = createContext({
      localStorage: storage,
      location: { origin: "https://kryptons-toy-vault.grok.me" },
      document: documentMock,
      alert() {},
      navigator: {},
      Blob: class MockBlob {
        parts: string[];
        constructor(parts: string[]) {
          this.parts = parts;
        }
      },
      URL: {
        createObjectURL() {
          return "blob:backup";
        },
        revokeObjectURL() {},
      },
      setTimeout(fn: () => void) {
        fn();
        return 0;
      },
    });

    runInContext(VAULT_EXPORT_SNIPPET, context);
    assert.ok(downloaded.includes("blob:backup"));
    assert.ok(textarea.value.length > 0);
    const parsed = parseVaultBackup(textarea.value);
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;
    assert.equal(parsed.backup.state.ownedFigures.prime?.notes, "from old site");
    assert.equal(parsed.backup.sourceOrigin, "https://kryptons-toy-vault.grok.me");
    assert.equal(parsed.counts.ownedFigures, 1);
  });
});

describe("short bookmarklet and hosted script", () => {
  const originalDoc = (globalThis as { document?: unknown }).document;

  afterEach(() => {
    if (originalDoc === undefined) delete (globalThis as { document?: unknown }).document;
    else (globalThis as { document?: unknown }).document = originalDoc;
  });

  it("keeps the phone bookmarklet under 120 characters", () => {
    assert.equal(SHORT_VAULT_BOOKMARKLET.length, 110);
  });

  it("posts a parseable backup to the new-site handoff path", () => {
    const state = sampleState({ ownedFigures: { prime: figure("prime", { notes: "from phone" }) } });
    const persist = JSON.stringify({ state, version: 0 });
    const data: Record<string, string> = { [CURRENT_VAULT_STORAGE_KEY]: persist };
    const keys = Object.keys(data);
    const submitted: { action?: string; enctype?: string; backup?: string }[] = [];

    const storage = {
      get length() {
        return keys.length;
      },
      key(index: number) {
        return keys[index] ?? null;
      },
      getItem(key: string) {
        return data[key] ?? null;
      },
    };

    function el() {
      const node: Record<string, unknown> & {
        children: unknown[];
        appendChild(child: unknown): unknown;
        remove(): void;
        setAttribute(name: string, value: string): void;
        submit(): void;
      } = {
        children: [],
        style: {},
        appendChild(child) {
          this.children.push(child);
          return child;
        },
        remove() {},
        setAttribute(name, value) {
          this[name] = value;
        },
        submit() {
          const backup = (this.children as Array<{ name?: string; value?: string }>).find((c) => c.name === "backup");
          submitted.push({
            action: String(this.action ?? ""),
            enctype: String(this.enctype ?? ""),
            backup: backup?.value,
          });
        },
      };
      return node;
    }

    const documentMock = {
      currentScript: { src: "https://kryptonstoyvault.com/x.js" },
      getElementById() {
        return null;
      },
      createElement(_tag: string) {
        return el();
      },
      body: {
        appendChild(child: unknown) {
          return child;
        },
      },
    };
    (globalThis as { document?: unknown }).document = documentMock;

    const context = createContext({
      localStorage: storage,
      location: { origin: "https://kryptons-toy-vault.grok.me" },
      document: documentMock,
      alert() {},
      URL,
      Date,
    });
    runInContext(VAULT_EXPORT_SCRIPT, context);
    assert.equal(submitted.length, 1);
    assert.equal(submitted[0]?.action, "https://kryptonstoyvault.com/api/vault-handoff");
    assert.equal(submitted[0]?.enctype, "multipart/form-data");
    const parsed = parseVaultBackup(submitted[0]?.backup ?? "");
    assert.equal(parsed.ok, true);
    if (!parsed.ok) return;
    assert.equal(parsed.backup.state.ownedFigures.prime?.notes, "from phone");
    assert.equal(parsed.backup.sourceOrigin, "https://kryptons-toy-vault.grok.me");
  });

  it("escapes HTML in the handoff page so a backup cannot break out of the script tag", () => {
    const sneaky = '{"kind":"vault-backup","state":{},"evil":"</script><script>alert(1)"}';
    const escaped = escapeJsonForScript(sneaky);
    assert.equal(escaped.includes("</script>"), false);
    assert.match(escaped, /\\u003c\/script/);
    const page = renderHandoffPage(sneaky);
    assert.equal(page.includes("</script><script>alert(1)"), false);
    const marker = 'id="ktv-backup">';
    const start = page.indexOf(marker) + marker.length;
    const end = page.indexOf("</script>", start);
    const body = page.slice(start, end);
    assert.equal(JSON.parse(body).evil, "</script><script>alert(1)");
  });
});

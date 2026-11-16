import { useEffect, useMemo, useState } from "react";
import { Copy, Download, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  BOOKMARKLET_NAME,
  OLD_SITE_URL,
  SHORT_VAULT_BOOKMARKLET,
  VAULT_CONSOLE_LOADER,
  backupFilename,
  buildBackupFromState,
  clearHandoffBackup,
  countVault,
  downloadJsonFile,
  formatVaultCounts,
  mergeVault,
  parseVaultBackup,
  pickVaultState,
  readHandoffBackup,
  replaceVault,
  stringifyBackup,
  vaultExportBookmarklet,
  type VaultCounts,
} from "@/lib/vault-backup";
import { useHydrated, useVault } from "@/lib/store";
import type { VaultState } from "@/lib/types";

type Mode = "merge" | "replace";

function currentVaultFromStore(): VaultState {
  return pickVaultState(useVault.getState());
}

function applyVault(incoming: VaultState, mode: Mode) {
  const current = currentVaultFromStore();
  const next = mode === "replace" ? replaceVault(current, incoming) : mergeVault(current, incoming);
  useVault.setState(next);
}

export function exportCurrentVault(): boolean {
  const state = currentVaultFromStore();
  const counts = countVault(state);
  if (counts.totalItems === 0) {
    toast.error("There's nothing in this browser's vault to export yet.");
    return false;
  }
  const backup = buildBackupFromState(state, {
    origin: typeof window === "undefined" ? undefined : window.location.origin,
  });
  downloadJsonFile(backupFilename(), stringifyBackup(backup));
  toast.success(`Saved a backup of ${formatVaultCounts(counts)}.`);
  return true;
}

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("style", "position:fixed;left:-9999px;top:0");
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      return ok;
    } catch {
      return false;
    }
  }
}

function CountsList({ counts }: { counts: VaultCounts }) {
  return <p className="text-sm text-muted">{formatVaultCounts(counts)}</p>;
}

export function VaultBackupPanel() {
  const hydrated = useHydrated();
  const ownedFigures = useVault((s) => s.ownedFigures);
  const ownedComics = useVault((s) => s.ownedComics);
  const wantedFigures = useVault((s) => s.wantedFigures);
  const wantedComics = useVault((s) => s.wantedComics);
  const customComics = useVault((s) => s.customComics);
  const displays = useVault((s) => s.displays ?? {});

  const currentCounts = useMemo(
    () =>
      countVault({
        ownedFigures,
        wantedFigures,
        ownedComics,
        wantedComics,
        customComics,
        displays,
        pulseBaselines: {},
        lastPulseNoticeWeek: null,
      }),
    [ownedFigures, wantedFigures, ownedComics, wantedComics, customComics, displays],
  );

  const [raw, setRaw] = useState("");
  const [fileName, setFileName] = useState("");
  const [replaceAck, setReplaceAck] = useState(false);
  const [busy, setBusy] = useState(false);

  const parsed = useMemo(() => {
    const trimmed = raw.trim();
    if (!trimmed) return null;
    return parseVaultBackup(trimmed);
  }, [raw]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("handoff") !== "1") return;
    let cancelled = false;
    void (async () => {
      const rawBackup = await readHandoffBackup();
      if (cancelled) return;
      if (!rawBackup) {
        toast.error("The transfer was lost. Open the old site in Chrome and use the bookmark again.");
        return;
      }
      setRaw(rawBackup);
      setFileName("Transferred from the old site");
      const result = parseVaultBackup(rawBackup);
      if (result.ok) toast.success(`Ready to import ${formatVaultCounts(result.counts)}.`);
      else toast.error(result.error);
      const url = new URL(window.location.href);
      url.searchParams.delete("handoff");
      window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onFile(file?: File) {
    if (!file) return;
    const name = file.name.toLowerCase();
    if (!name.endsWith(".json") && file.type && file.type !== "application/json" && file.type !== "text/plain") {
      toast.error("Please choose the JSON backup file from the old site.");
      return;
    }
    try {
      const text = await file.text();
      setRaw(text);
      setFileName(file.name);
      const result = parseVaultBackup(text);
      if (result.ok) toast.success(`Ready to import ${formatVaultCounts(result.counts)}.`);
      else toast.error(result.error);
    } catch {
      toast.error("Could not read that file.");
    }
  }

  async function copyBookmarklet() {
    const ok = await copyText(vaultExportBookmarklet());
    if (ok) toast.success("Copied. Paste it into the bookmark address field.");
    else toast.error("Could not copy. Select the short bookmark text and copy it yourself.");
  }

  async function copyConsoleLoader() {
    const ok = await copyText(VAULT_CONSOLE_LOADER);
    if (ok) toast.success("Copied. Paste it in the console on the old site and press Enter.");
    else toast.error("Could not copy. Select the console line and copy it yourself.");
  }

  function runImport(mode: Mode) {
    if (!parsed || !parsed.ok) return;
    if (mode === "replace" && !replaceAck) {
      toast.error("Check the box first if you want to replace everything currently on this site.");
      return;
    }
    setBusy(true);
    try {
      applyVault(parsed.backup.state, mode);
      void clearHandoffBackup();
      const next = countVault(currentVaultFromStore());
      toast.success(
        mode === "replace"
          ? `Replaced this site's vault with ${formatVaultCounts(next)}.`
          : `Merged the backup in. This site now has ${formatVaultCounts(next)}.`,
      );
      setReplaceAck(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <section
        id="move"
        className="scroll-mt-24 rounded-xl bg-bg-elevated p-5 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]"
      >
        <h2 className="font-display text-lg tracking-wide uppercase">Move your collection from the old site</h2>
        <p className="mt-2 text-sm text-muted">
          Your collection is saved in this browser, on this website address. If it only shows on
          your phone, you need to export it from that phone. The bookmark below is short so it will
          fit in the bookmark address field. After you use it on the old site, this page should open
          with your collection already loaded — no file or paste required.
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button type="button" onClick={() => void copyBookmarklet()}>
            <Copy /> Copy the short bookmark
          </Button>
        </div>
        <label className="mt-3 block text-xs font-medium text-muted" htmlFor="short-bookmarklet">
          Bookmark address ({SHORT_VAULT_BOOKMARKLET.length} characters). Name it “{BOOKMARKLET_NAME}”.
        </label>
        <textarea
          id="short-bookmarklet"
          readOnly
          value={SHORT_VAULT_BOOKMARKLET}
          rows={3}
          className="mt-1 w-full resize-y rounded-md bg-surface px-3 py-2 font-mono text-xs text-fg shadow-[0_0_0_1px_rgba(214,230,255,0.12)]"
          onFocus={(e) => e.currentTarget.select()}
        />

        <h3 className="mt-5 text-sm font-medium">On an Android phone, in Chrome</h3>
        <ol className="mt-2 list-decimal space-y-2 pl-5 text-sm text-muted">
          <li>
            Open Chrome — not the installed app window. The bookmark will not run inside the app,
            but Chrome uses the same saved collection. In Chrome, go to{" "}
            <a
              href={OLD_SITE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-fg underline-offset-2 hover:underline"
            >
              kryptons-toy-vault.grok.me
            </a>{" "}
            and confirm your collection is there.
          </li>
          <li>Bookmark any page (the star or the menu item Add bookmark is fine).</li>
          <li>
            Open your bookmarks, edit that bookmark, and paste the short bookmark you copied into
            the URL or address field. Name it {BOOKMARKLET_NAME}. Save it.
          </li>
          <li>
            Go back to the old site, tap the address bar, type {BOOKMARKLET_NAME}, and tap it in the
            suggestions. You should be sent here with your collection ready to import.
          </li>
        </ol>

        <details className="mt-4 rounded-md bg-surface p-3">
          <summary className="cursor-pointer text-sm font-medium">On a computer instead</summary>
          <p className="mt-2 text-sm text-muted">
            Open the old site in the same browser where the collection shows, press F12 (or
            Cmd+Option+I), click Console, paste the line below, and press Enter. You will be sent to
            this page with the backup already loaded.
          </p>
          <div className="mt-3">
            <Button type="button" variant="secondary" size="sm" onClick={() => void copyConsoleLoader()}>
              <Copy /> Copy the console line
            </Button>
          </div>
          <textarea
            readOnly
            value={VAULT_CONSOLE_LOADER}
            className="mt-3 h-20 w-full resize-y rounded-md bg-bg px-3 py-2 font-mono text-xs text-fg"
            onFocus={(e) => e.currentTarget.select()}
          />
        </details>
      </section>

      <section className="rounded-xl bg-bg-elevated p-5 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
        <h2 className="font-display text-lg tracking-wide uppercase">2. Import the backup here</h2>
        <p className="mt-2 text-sm text-muted">
          Upload the JSON file, or paste the backup text. You'll see a count of what's in the file
          before anything is saved. Merge keeps what's already on this site and adds or updates from
          the backup. Replace throws out what's here and uses only the backup — useful if this site
          still shows the sample comic.
        </p>

        <label className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border px-4 py-10 text-center transition-colors hover:border-primary/50">
          <Upload className="size-8 text-gold" />
          <span className="text-sm font-medium">Drop your backup JSON here or click to browse</span>
          <span className="text-xs text-muted">.json file from the old site</span>
          <input
            type="file"
            accept=".json,application/json,text/plain"
            className="sr-only"
            onChange={(e) => void onFile(e.target.files?.[0])}
          />
        </label>
        {fileName ? <p className="mt-3 text-xs text-muted">Loaded: {fileName}</p> : null}

        <label className="mt-4 block text-sm font-medium" htmlFor="vault-backup-paste">
          Or paste the backup text
        </label>
        <textarea
          id="vault-backup-paste"
          value={raw}
          onChange={(e) => {
            setRaw(e.target.value);
            setFileName("");
          }}
          spellCheck={false}
          placeholder="Paste the backup JSON here"
          className="mt-2 h-36 w-full resize-y rounded-md bg-surface px-3 py-2 font-mono text-xs text-fg shadow-[0_0_0_1px_rgba(214,230,255,0.12)]"
        />

        {parsed && !parsed.ok ? <p className="mt-3 text-sm text-primary">{parsed.error}</p> : null}

        {parsed?.ok ? (
          <div className="mt-4 flex flex-col gap-3 rounded-md bg-surface p-4">
            <div>
              <h3 className="text-sm font-medium">In this backup</h3>
              <CountsList counts={parsed.counts} />
            </div>
            <div>
              <h3 className="text-sm font-medium">Already on this site</h3>
              {hydrated ? (
                currentCounts.totalItems ? (
                  <CountsList counts={currentCounts} />
                ) : (
                  <p className="text-sm text-muted">This site's vault is empty in this browser.</p>
                )
              ) : (
                <p className="text-sm text-muted">Checking this browser…</p>
              )}
            </div>
            <label className="flex items-start gap-2 text-sm text-muted">
              <input
                type="checkbox"
                className="mt-1"
                checked={replaceAck}
                onChange={(e) => setReplaceAck(e.target.checked)}
              />
              <span>I understand that Replace will remove what's currently saved on this site and leave only the backup.</span>
            </label>
            <div className="flex flex-wrap gap-2">
              <Button type="button" disabled={busy} onClick={() => runImport("merge")}>
                Merge into this site
              </Button>
              <Button
                type="button"
                variant="danger"
                disabled={busy || !replaceAck}
                onClick={() => runImport("replace")}
              >
                Replace this site's vault
              </Button>
            </div>
          </div>
        ) : null}
      </section>

      <section className="rounded-xl bg-bg-elevated p-5 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
        <h2 className="font-display text-lg tracking-wide uppercase">Download a backup of this site</h2>
        <p className="mt-2 text-sm text-muted">
          Save a JSON copy of whatever is stored in this browser on KryptonsToyVault.com, including
          owned items, prices you entered, wishlist, notes, custom titles, and display photos. Keep
          it somewhere safe so you can restore it later.
        </p>
        {hydrated ? (
          currentCounts.totalItems ? (
            <p className="mt-2 text-sm text-muted">Currently saved here: {formatVaultCounts(currentCounts)}.</p>
          ) : (
            <p className="mt-2 text-sm text-muted">Nothing is saved in this browser on this site yet.</p>
          )
        ) : null}
        <div className="mt-4">
          <Button type="button" variant="secondary" onClick={() => exportCurrentVault()}>
            <Download /> Download backup
          </Button>
        </div>
      </section>
    </div>
  );
}

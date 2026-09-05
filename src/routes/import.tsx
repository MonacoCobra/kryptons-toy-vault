import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { FileUp, Upload } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useEnsureComicLibrary, useLiveComics } from "@/lib/live-store";
import {
  buildOwnedFromMatch,
  matchLocgRows,
  parseLocgSpreadsheet,
  type LocgMatch,
  type LocgParseResult,
} from "@/lib/locg-import";
import { useVault } from "@/lib/store";

export const Route = createFileRoute("/import")({
  component: ImportPage,
});

function ImportPage() {
  const extras = useLiveComics();
  const library = useEnsureComicLibrary(extras);
  const addComic = useVault((s) => s.addComic);
  const addCustomComic = useVault((s) => s.addCustomComic);
  const toggleWantComic = useVault((s) => s.toggleWantComic);
  const owned = useVault((s) => s.ownedComics);
  const wanted = useVault((s) => s.wantedComics);

  const [parsed, setParsed] = useState<LocgParseResult | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [busy, setBusy] = useState(false);

  const matched = useMemo(() => {
    if (!parsed) return null;
    // Full seed + weekly extras + permanent archive promotions
    return matchLocgRows(parsed.rows, extras, library?.archive ?? []);
  }, [parsed, extras, library]);

  async function onFile(file?: File) {
    if (!file) return;
    const name = file.name.toLowerCase();
    if (name.endsWith(".xlsx") || name.endsWith(".xls")) {
      toast.error("Save the LOCG Excel export as CSV first (File → Save As → CSV), then drop that here.");
      return;
    }
    try {
      const text = await file.text();
      const result = parseLocgSpreadsheet(text);
      setParsed(result);
      setFileName(file.name);
      if (result.warnings.length) result.warnings.forEach((w) => toast.message(w));
      if (!result.rows.length) toast.error("No comic rows found in that file.");
      else toast.success(`Parsed ${result.rows.length} rows from ${file.name}`);
    } catch {
      toast.error("Could not read that file.");
    }
  }

  function applyImport() {
    if (!matched) return;
    setBusy(true);
    try {
      let added = 0;
      let wished = 0;
      let skippedOwned = 0;
      const ownedCatalog = new Set(
        Object.values(owned)
          .map((o) => o.catalogId)
          .filter(Boolean) as string[],
      );

      for (const m of matched.matches) {
        if (m.kind === "skip") continue;
        const built = buildOwnedFromMatch(m as Extract<LocgMatch, { kind: "catalog" | "custom" }>);
        if (built.custom) addCustomComic(built.custom);
        if (built.wantId) {
          if (!wanted[built.wantId] && !(built.wantId && ownedCatalog.has(built.wantId))) {
            toggleWantComic(built.wantId);
            wished += 1;
          }
          continue;
        }
        if (built.owned) {
          const cat = built.owned.catalogId;
          if (cat && ownedCatalog.has(cat)) {
            skippedOwned += 1;
            continue;
          }
          addComic(built.owned);
          if (cat) ownedCatalog.add(cat);
          added += 1;
        }
      }
      toast.success(
        `Imported ${added} owned` +
          (wished ? `, ${wished} wishlist` : "") +
          (skippedOwned ? ` (${skippedOwned} already owned skipped)` : ""),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex flex-col gap-6">
      <header>
        <p className="text-xs tracking-[0.28em] text-gold uppercase">Migration</p>
        <h1 className="mt-1 font-display text-3xl tracking-wide uppercase">Import collection</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Bring comics from{" "}
          <a
            href="https://leagueofcomicgeeks.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-fg underline-offset-2 hover:underline"
          >
            League of Comic Geeks
          </a>{" "}
          via their Bulk Import/Export CSV. Matched titles link to the vault catalog; everything else lands as
          custom issues.
        </p>
      </header>

      <section className="rounded-xl bg-bg-elevated p-5 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
        <h2 className="font-display text-lg tracking-wide uppercase">1. Export from LOCG</h2>
        <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-muted">
          <li>Open your LOCG profile → Comics → Bulk Import/Export</li>
          <li>Click Export My Comics</li>
          <li>If you get Excel, Save As → CSV UTF-8, then upload below</li>
        </ol>
      </section>

      <section className="rounded-xl bg-bg-elevated p-5 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
        <h2 className="font-display text-lg tracking-wide uppercase">2. Upload CSV</h2>
        <label className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border px-4 py-10 text-center transition-colors hover:border-primary/50">
          <FileUp className="size-8 text-gold" />
          <span className="text-sm font-medium">Drop LOCG CSV here or click to browse</span>
          <span className="text-xs text-muted">.csv only for now</span>
          <input
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            onChange={(e) => void onFile(e.target.files?.[0])}
          />
        </label>
        {fileName ? <p className="mt-3 text-xs text-muted">Loaded: {fileName}</p> : null}
      </section>

      {matched && parsed ? (
        <section className="flex flex-col gap-4 rounded-xl bg-bg-elevated p-5 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-display text-lg tracking-wide uppercase">3. Review &amp; import</h2>
              <p className="mt-1 text-sm text-muted">
                {parsed.rows.length} rows · {matched.matched} catalog matches (
                {parsed.rows.length
                  ? Math.round((matched.matched / parsed.rows.length) * 100)
                  : 0}
                %) · {matched.owned} collection · {matched.wanted} wishlist · {matched.unmatched}{" "}
                custom (not in catalog yet)
              </p>
            </div>
            <Button disabled={busy || !matched.matches.length} onClick={applyImport}>
              <Upload /> Import into vault
            </Button>
          </div>

          <ul className="max-h-96 space-y-2 overflow-y-auto text-sm">
            {matched.matches.slice(0, 80).map((m, i) => (
              <li
                key={i}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-surface px-3 py-2"
              >
                <span className="min-w-0 truncate">
                  {m.row.series} #{m.row.issue}
                  <span className="text-muted"> · {m.row.publisher}</span>
                </span>
                <span className="flex gap-1">
                  {m.row.inCollection ? <Badge tone="gain">Own</Badge> : null}
                  {m.row.inWishlist ? <Badge tone="gold">Want</Badge> : null}
                  {m.kind === "catalog" ? <Badge>Matched</Badge> : null}
                  {m.kind === "custom" ? <Badge tone="red">Custom</Badge> : null}
                  {m.kind === "skip" ? <Badge tone="red">Skip</Badge> : null}
                </span>
              </li>
            ))}
          </ul>
          {matched.matches.length > 80 ? (
            <p className="text-xs text-muted">Showing first 80 of {matched.matches.length}…</p>
          ) : null}
        </section>
      ) : null}

      <p className="text-sm text-muted">
        Prefer browsing the catalog first?{" "}
        <Link to="/comics" className="text-fg underline-offset-2 hover:underline">
          Open comics
        </Link>
      </p>
    </main>
  );
}

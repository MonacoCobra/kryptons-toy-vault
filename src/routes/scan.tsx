import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Camera, ImagePlus, Loader2, Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { COMICS } from "@/data/comics";
import { AddComicDialog } from "@/components/add-comic-dialog";
import { ScanMatchList } from "@/components/scan-match-list";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { libraryCatalogRows } from "@/lib/comic-catalog";
import { searchCatalogLimited } from "@/lib/cover-match";
import { identifyCover } from "@/lib/identify-cover";
import { compressImage } from "@/lib/image";
import { useEnsureComicLibrary, useLiveComics } from "@/lib/live-store";
import { matchComicsFromGuess, type CoverGuess } from "@/lib/match";
import { useVault } from "@/lib/store";
import type { CatalogComic, CustomComic } from "@/lib/types";
import { slug } from "@/lib/utils";

type ScanSearch = { q?: string };

export const Route = createFileRoute("/scan")({
  validateSearch: (s: Record<string, unknown>): ScanSearch => ({
    q: typeof s.q === "string" && s.q.trim() ? s.q : undefined,
  }),
  component: ScanPage,
});

function ScanPage() {
  const navigate = useNavigate();
  const urlSearch = Route.useSearch();
  const cameraRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const extras = useLiveComics();
  const library = useEnsureComicLibrary(extras);
  const libraryRows = useMemo(() => libraryCatalogRows(library), [library]);
  const ownedComics = useVault((s) => s.ownedComics);
  const ownedIds = useMemo(() => {
    const ids = new Set<string>();
    for (const entry of Object.values(ownedComics)) {
      if (entry.catalogId) ids.add(entry.catalogId);
    }
    return ids;
  }, [ownedComics]);

  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [guess, setGuess] = useState<CoverGuess | null>(null);
  const [matches, setMatches] = useState<CatalogComic[]>([]);
  const [query, setQuery] = useState(urlSearch.q ?? "");
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState<CatalogComic | null>(null);
  const [custom, setCustom] = useState<CustomComic | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [listMode, setListMode] = useState<"scan" | "search">("search");
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
    document.body.dataset.scanReady = "1";
  }, []);

  async function onFile(file: File) {
    setBusy(true);
    setError(null);
    setGuess(null);
    setMatches([]);
    setSelectedId(null);
    setListMode("search");
    try {
      const dataUrl = await compressImage(file, 960, 0.78);
      setPreview(dataUrl);
      const base64 = dataUrl.split(",")[1] ?? "";
      const result = await identifyCover({
        data: { imageBase64: base64, mimeType: "image/jpeg" },
      });
      if (!result.ok) {
        setError(result.error);
        toast.error(result.error);
        return;
      }
      const g: CoverGuess = {
        series: result.series,
        issue: result.issue,
        publisher: result.publisher,
        year: result.year,
        variant: result.variant,
        writers: result.writers,
        artists: result.artists,
      };
      setGuess(g);
      const ranked = matchComicsFromGuess(g, 5, extras, libraryRows);
      setMatches(ranked);
      setSelectedId(ranked[0]?.id ?? null);
      setListMode("scan");
      setQuery(`${result.series} ${result.issue}`);
    } catch {
      setError("Could not read that image.");
      toast.error("Scan failed.");
    } finally {
      setBusy(false);
    }
  }

  function handlePick(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) void onFile(file);
  }

  const qDebounced = useDebouncedValue(query, 200);
  const searched = useMemo(
    () => searchCatalogLimited(qDebounced, [COMICS, extras, libraryRows], 8),
    [qDebounced, extras, libraryRows],
  );
  /** Prefer AI cover matches; fall back to catalog search from the query. */
  const shown = listMode === "scan" && matches.length ? matches : searched;
  const shownKey = shown.map((c) => c.id).join("|");
  const ambiguous = matches.length > 1;
  const selected = shown.find((c) => c.id === selectedId) ?? shown[0] ?? null;
  const topMatch = matches[0] ?? (shown.length === 1 ? shown[0] : null);

  useEffect(() => {
    if (!guess || listMode !== "scan") return;
    const ranked = matchComicsFromGuess(guess, 5, extras, libraryRows);
    setMatches((prev) => {
      const same =
        prev.length === ranked.length && prev.every((comic, i) => comic.id === ranked[i]?.id);
      return same ? prev : ranked;
    });
  }, [guess, extras, libraryRows, listMode]);

  useEffect(() => {
    const ids = shownKey ? shownKey.split("|") : [];
    if (!ids.length) {
      setSelectedId((prev) => (prev ? null : prev));
      return;
    }
    setSelectedId((prev) => (prev && ids.includes(prev) ? prev : ids[0]));
  }, [shownKey]);

  function asCustom(): CustomComic | null {
    if (!guess?.series) return null;
    return {
      id: `custom-${slug(guess.series)}-${slug(guess.issue)}-${Date.now()}`,
      series: guess.series,
      issue: guess.issue,
      publisher: guess.publisher || "Unknown",
      coverDate: guess.year ? `${guess.year}-01-01` : undefined,
      writers: guess.writers,
      artists: guess.artists,
      format: "single",
      variant: guess.variant,
    };
  }

  function requestAdd(comic: CatalogComic) {
    setSelectedId(comic.id);
    setAdding(comic);
  }

  function goAfterSave(info: { catalogId?: string; customId?: string }) {
    if (info.catalogId) {
      void navigate({ to: "/comics/$comicId", params: { comicId: info.catalogId } });
      return;
    }
    void navigate({ to: "/collection" });
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 pb-24">
      <header>
        <h1 className="font-display text-3xl tracking-wide uppercase">Scan a comic</h1>
        <p className="mt-2 text-sm text-muted">
          Photograph a cover to match it in the catalog, then add it to your collection. If it
          isn&apos;t there, save it as a custom issue.
        </p>
      </header>

      <div
        className={`relative flex flex-col items-center justify-center overflow-hidden rounded-xl bg-bg-elevated shadow-[0_0_0_1px_rgba(214,230,255,0.1)] ${
          preview || !shown.length ? "min-h-64" : "min-h-0 py-5"
        }`}
      >
        {preview ? (
          <img
            src={preview}
            alt="Scanned cover"
            className={shown.length ? "max-h-40 object-contain" : "max-h-80 object-contain"}
          />
        ) : (
          <>
            <Camera className="size-8 text-gold" />
            <p className="mt-3 text-sm text-muted">Take a photo or upload an existing cover</p>
          </>
        )}
        {busy ? (
          <div className="absolute inset-0 flex items-center justify-center bg-bg/70">
            <Loader2 className="size-6 animate-spin text-gold" />
          </div>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <Button
          type="button"
          variant="default"
          disabled={busy}
          onClick={() => cameraRef.current?.click()}
          className="min-h-11 w-full"
        >
          <Camera className="size-4" />
          Take photo
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={busy}
          onClick={() => galleryRef.current?.click()}
          className="min-h-11 w-full"
        >
          <ImagePlus className="size-4" />
          Upload existing photo
        </Button>
      </div>

      {/* Camera: capture forces rear camera on mobile */}
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handlePick}
        suppressHydrationWarning
      />
      {/* Gallery: no capture attribute so Android offers the photo picker */}
      <input
        ref={galleryRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handlePick}
        suppressHydrationWarning
      />

      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" />
        <Input
          value={query}
          placeholder="Or search the catalog — Saga 13, Batman 608…"
          className="pl-10"
          onChange={(e) => {
            setQuery(e.target.value);
            setListMode("search");
          }}
          aria-label="Search catalog"
          suppressHydrationWarning
        />
      </div>

      {error ? <p className="text-sm text-loss">{error}</p> : null}

      {guess ? (
        <div className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
          <p className="text-xs tracking-[0.18em] text-gold uppercase">Read as</p>
          <p className="mt-1 font-display text-2xl tracking-wide uppercase">
            {guess.series} #{guess.issue}
          </p>
          <p className="mt-1 text-sm text-muted">
            {guess.publisher}
            {guess.variant ? ` · ${guess.variant}` : ""}
          </p>
          {selected || topMatch ? (
            <Button
              type="button"
              className="mt-4 min-h-11 w-full"
              onClick={() => {
                const comic = selected ?? topMatch;
                if (comic) requestAdd(comic);
              }}
            >
              <Plus className="size-4" />
              Add to collection
            </Button>
          ) : null}
          {ambiguous ? (
            <p className="mt-3 text-sm text-muted">
              Several catalog matches — tap a card or Add to collection to put that issue in
              your vault.
            </p>
          ) : null}
        </div>
      ) : null}

      {mounted ? (
        <ScanMatchList
          comics={shown}
          selectedId={selected?.id ?? null}
          ownedIds={ownedIds}
          source={listMode === "scan" && matches.length ? "matches" : "search"}
          onSelect={(comic) => setSelectedId(comic.id)}
          onAdd={requestAdd}
        />
      ) : null}

      {guess && !shown.length ? (
        <div className="flex flex-wrap gap-2">
          <Button
            className="min-h-11"
            onClick={() => {
              const c = asCustom();
              if (c) setCustom(c);
            }}
          >
            <Plus className="size-4" />
            Add as custom issue
          </Button>
          <Button asChild variant="secondary" className="min-h-11">
            <Link to="/comics">Search catalog</Link>
          </Button>
        </div>
      ) : null}

      {guess && shown.length ? (
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            className="min-h-11"
            onClick={() => {
              const c = asCustom();
              if (c) setCustom(c);
            }}
          >
            Not listed — add as custom
          </Button>
          <Button asChild variant="ghost" className="min-h-11">
            <Link to="/comics">Browse catalog</Link>
          </Button>
        </div>
      ) : null}

      <AddComicDialog
        comic={adding ?? undefined}
        photo={preview ?? undefined}
        open={adding !== null}
        confirmLabel="Add to collection"
        onOpenChange={(v) => {
          if (!v) setAdding(null);
        }}
        onSaved={goAfterSave}
      />
      <AddComicDialog
        custom={custom ?? undefined}
        photo={preview ?? undefined}
        open={custom !== null}
        confirmLabel="Add to collection"
        onOpenChange={(v) => {
          if (!v) setCustom(null);
        }}
        onSaved={goAfterSave}
      />
    </main>
  );
}

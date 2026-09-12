import { useRef, useState, type ChangeEvent } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Camera, ImagePlus, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { comicLabel, searchComics } from "@/data/comics";
import { AddComicDialog } from "@/components/add-comic-dialog";
import { ComicCover } from "@/components/comic-cover";
import { Button } from "@/components/ui/button";
import { identifyCover } from "@/lib/identify-cover";
import { compressImage } from "@/lib/image";
import { useLiveComics } from "@/lib/live-store";
import { matchComicsFromGuess, type CoverGuess } from "@/lib/match";
import type { CatalogComic, CustomComic } from "@/lib/types";
import { slug } from "@/lib/utils";

export const Route = createFileRoute("/scan")({ component: ScanPage });

function ScanPage() {
  const navigate = useNavigate();
  const cameraRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const extras = useLiveComics();
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [guess, setGuess] = useState<CoverGuess | null>(null);
  const [matches, setMatches] = useState<CatalogComic[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState<CatalogComic | null>(null);
  const [custom, setCustom] = useState<CustomComic | null>(null);

  async function onFile(file: File) {
    setBusy(true);
    setError(null);
    setGuess(null);
    setMatches([]);
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
      setMatches(matchComicsFromGuess(g, 5, extras));
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

  const searched = query.trim() ? searchComics(query, extras).slice(0, 8) : [];
  /** Prefer AI matches; fall back to catalog search from the guess query. */
  const shown = matches.length ? matches : searched;
  const ambiguous = matches.length > 1;
  const topMatch = matches[0] ?? (shown.length === 1 ? shown[0] : null);

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

  function goAfterSave(info: { catalogId?: string; customId?: string }) {
    if (info.catalogId) {
      void navigate({ to: "/comics/$comicId", params: { comicId: info.catalogId } });
      return;
    }
    void navigate({ to: "/collection" });
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6">
      <header>
        <h1 className="font-display text-3xl tracking-wide uppercase">Scan a comic</h1>
        <p className="mt-2 text-sm text-muted">
          Photograph a cover to match it in the catalog, then add it to your collection. If it
          isn&apos;t there, save it as a custom issue.
        </p>
      </header>

      <div className="relative flex min-h-64 flex-col items-center justify-center overflow-hidden rounded-xl bg-bg-elevated shadow-[0_0_0_1px_rgba(214,230,255,0.1)]">
        {preview ? (
          <img src={preview} alt="Scanned cover" className="max-h-80 object-contain" />
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
      />
      {/* Gallery: no capture attribute so Android offers the photo picker */}
      <input
        ref={galleryRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handlePick}
      />

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
          {topMatch && matches.length === 1 ? (
            <Button
              type="button"
              className="mt-4 min-h-11 w-full"
              onClick={() => setAdding(topMatch)}
            >
              <Plus className="size-4" />
              Add to collection
            </Button>
          ) : null}
          {ambiguous ? (
            <p className="mt-3 text-sm text-muted">
              Several catalog matches — pick the right issue below, then add it.
            </p>
          ) : null}
        </div>
      ) : null}

      {shown.length ? (
        <section className="grid gap-2">
          <div className="flex items-baseline justify-between gap-2">
            <h2 className="text-xs tracking-[0.18em] text-gold uppercase">
              {matches.length ? "Catalog matches" : "Search results"}
            </h2>
            <span className="text-xs text-muted">{shown.length} found</span>
          </div>
          <ul className="grid gap-2">
            {shown.map((comic, i) => (
              <li key={comic.id}>
                <div className="flex items-center gap-3 rounded-lg bg-bg-elevated p-2 shadow-[var(--shadow-border)]">
                  <ComicCover comic={comic} className="h-20 w-14 shrink-0 rounded-sm" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{comicLabel(comic)}</p>
                    <p className="truncate text-xs text-muted">
                      {comic.publisher}
                      {i === 0 && matches.length ? " · best match" : ""}
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant={i === 0 && matches.length ? "default" : "secondary"}
                    className="min-h-11 shrink-0 px-3"
                    onClick={() => setAdding(comic)}
                  >
                    <Plus className="size-4" />
                    <span className="hidden sm:inline">Add to collection</span>
                    <span className="sm:hidden">Add</span>
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </section>
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

      {adding ? (
        <AddComicDialog
          comic={adding}
          photo={preview ?? undefined}
          open
          confirmLabel="Add to collection"
          onOpenChange={(v) => !v && setAdding(null)}
          onSaved={goAfterSave}
        />
      ) : null}
      {custom ? (
        <AddComicDialog
          custom={custom}
          photo={preview ?? undefined}
          open
          confirmLabel="Add to collection"
          onOpenChange={(v) => !v && setCustom(null)}
          onSaved={goAfterSave}
        />
      ) : null}
    </main>
  );
}

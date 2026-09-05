import { useRef, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Camera, Loader2 } from "lucide-react";
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
  const inputRef = useRef<HTMLInputElement>(null);
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

  const searched = query.trim() ? searchComics(query, extras).slice(0, 8) : [];
  const shown = matches.length ? matches : searched;

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

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6">
      <header>
        <h1 className="font-display text-3xl tracking-wide uppercase">Scan a comic</h1>
        <p className="mt-2 text-sm text-muted">
          Photograph a cover to match it in the catalog. If it isn't there, save it as a custom issue.
        </p>
      </header>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="relative flex min-h-64 flex-col items-center justify-center overflow-hidden rounded-xl bg-bg-elevated shadow-[0_0_0_1px_rgba(214,230,255,0.1)]"
      >
        {preview ? (
          <img src={preview} alt="Scanned cover" className="max-h-80 object-contain" />
        ) : (
          <>
            <Camera className="size-8 text-gold" />
            <p className="mt-3 text-sm text-muted">Tap to photograph or upload a cover</p>
          </>
        )}
        {busy ? (
          <div className="absolute inset-0 flex items-center justify-center bg-bg/70">
            <Loader2 className="size-6 animate-spin text-gold" />
          </div>
        ) : null}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void onFile(file);
        }}
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
        </div>
      ) : null}

      {shown.length ? (
        <ul className="grid gap-2">
          {shown.map((comic) => (
            <li key={comic.id}>
              <button
                type="button"
                onClick={() => setAdding(comic)}
                className="flex w-full items-center gap-3 rounded-lg bg-bg-elevated p-2 text-left shadow-[var(--shadow-border)]"
              >
                <ComicCover comic={comic} className="h-20 w-14 shrink-0 rounded-sm" />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{comicLabel(comic)}</span>
                  <span className="block text-xs text-muted">{comic.publisher}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {guess && !shown.length ? (
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={() => {
              const c = asCustom();
              if (c) setCustom(c);
            }}
          >
            Add as custom issue
          </Button>
          <Button asChild variant="secondary">
            <Link to="/comics">Search catalog</Link>
          </Button>
        </div>
      ) : null}

      {adding ? (
        <AddComicDialog
          comic={adding}
          photo={preview ?? undefined}
          open
          onOpenChange={(v) => !v && setAdding(null)}
        />
      ) : null}
      {custom ? (
        <AddComicDialog
          custom={custom}
          photo={preview ?? undefined}
          open
          onOpenChange={(v) => !v && setCustom(null)}
        />
      ) : null}
    </main>
  );
}

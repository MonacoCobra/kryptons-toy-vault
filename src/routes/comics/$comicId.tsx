import { useEffect, useMemo, useState } from "react";
import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { ArrowLeft, ChevronRight, Heart, Trash2 } from "lucide-react";
import { loadComicBundle } from "@/lib/catalog-client";
import { comicLabel } from "@/lib/comic-label";
import { AddComicDialog } from "@/components/add-comic-dialog";
import { ComicCover } from "@/components/comic-cover";
import { ComicVariantScroller } from "@/components/comic-variant-scroller";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { libraryCatalogRows } from "@/lib/comic-catalog";
import { comicFormatLabel, isCollectedComic } from "@/lib/comic-format";
import { seriesBaseTitle, seriesDisplayLabel, seriesRunYearFor } from "@/lib/comic-series";
import { getComicVariants } from "@/lib/comic-variants";
import { formatMonthYear, usdOrDash } from "@/lib/format";
import { useComicLib, useEnsureComicLibrary, useLiveComics, useLiveDrop } from "@/lib/live-store";
import { itemValue, msrpPrice, paidPrice } from "@/lib/vault-math";
import { GRADES, useVault } from "@/lib/store";
import type { CatalogComic } from "@/lib/types";

export const Route = createFileRoute("/comics/$comicId")({
  component: ComicDetail,
});

function ComicDetail() {
  const { comicId } = Route.useParams();
  const extras = useLiveComics();
  const library = useEnsureComicLibrary(extras);
  const loading = useLiveDrop((s) => s.loading);
  const libLoading = useComicLib((s) => s.loading);
  const libraryRows = useMemo(() => libraryCatalogRows(library), [library]);
  const [bundle, setBundle] = useState<Awaited<ReturnType<typeof loadComicBundle>> | undefined>(undefined);
  const [edit, setEdit] = useState(false);
  const ownedList = useVault((s) => s.ownedComics);
  const toggleWant = useVault((s) => s.toggleWantComic);
  const removeComic = useVault((s) => s.removeComic);

  useEffect(() => {
    let cancel = false;
    setBundle(undefined);
    loadComicBundle(comicId)
      .then((next) => {
        if (!cancel) setBundle(next);
      })
      .catch(() => {
        if (!cancel) setBundle(null);
      });
    return () => {
      cancel = true;
    };
  }, [comicId]);

  const comic = useMemo(() => {
    if (bundle?.comic) return bundle.comic;
    return extras.find((row) => row.id === comicId) ?? libraryRows.find((row) => row.id === comicId);
  }, [bundle, comicId, extras, libraryRows]);
  const yearById = useMemo(() => {
    const years = new Map<string, number>();
    if (bundle?.run) {
      for (const [id, year] of Object.entries(bundle.run.years)) years.set(id, year);
    } else if (bundle?.comic) {
      years.set(bundle.comic.id, bundle.year);
    }
    return years;
  }, [bundle]);
  const variants = useMemo(() => {
    if (!comic) return [];
    const catalog = [...(bundle?.run?.comics ?? []), ...(bundle?.run?.related ?? []), ...extras, ...libraryRows];
    return getComicVariants(comic, catalog);
  }, [bundle, comic, extras, libraryRows]);
  const owned = useMemo(
    () => (comic ? Object.values(ownedList).find((entry) => entry.catalogId === comic.id) : undefined),
    [ownedList, comic],
  );
  const wanted = useVault((s) => (comic ? s.wantedComics[comic.id] : undefined));

  if (!comic) {
    if (bundle === undefined || loading || libLoading || library == null) {
      return <p className="py-16 text-center text-sm text-muted">Loading catalog…</p>;
    }
    throw notFound();
  }

  const cover = msrpPrice(comic.msrp);
  const paid = paidPrice(owned?.acquiredPrice);
  const gradeLabel = GRADES.find((g) => g.id === owned?.grade)?.label;

  return (
    <main className="grid min-w-0 max-w-full gap-8 overflow-x-hidden lg:grid-cols-[minmax(0,16rem)_1fr]">
      <div className="mx-auto w-full min-w-0 max-w-[16rem] overflow-hidden lg:mx-0">
        <ComicCover comic={comic} photo={owned?.photoDataUrl} resolveRemote className="aspect-2/3 w-full max-w-full overflow-hidden rounded-xl" />
        <ComicVariantScroller comic={comic} variants={variants} />
        <div className="mt-4 grid gap-2">
          <Button onClick={() => setEdit(true)}>{owned ? "Edit copy" : "Add to vault"}</Button>
          <Button variant="secondary" onClick={() => toggleWant(comic.id)} disabled={Boolean(owned)}>
            <Heart className={wanted ? "fill-gold text-gold" : ""} />
            {owned ? "Already owned" : wanted ? "Remove from want list" : "Add to want list"}
          </Button>
          {owned ? (
            <Button variant="outline" onClick={() => removeComic(owned.id)}>
              <Trash2 />
              Remove from vault
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-6">
        <div>
          <ComicLadderCrumbs comic={comic} yearById={yearById} />
          <h1 className="mt-1 font-display text-4xl tracking-wide uppercase">{comicLabel(comic)}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">{comic.description}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {owned ? <Badge tone="gain">Owned</Badge> : null}
            {wanted && !owned ? <Badge tone="gold">Wanted</Badge> : null}
            {comic.key ? <Badge tone="red">Key issue</Badge> : null}
            {comic.variant ? <Badge tone="gold">{comic.variant}</Badge> : null}
            <Badge tone={isCollectedComic(comic) ? "ice" : "default"}>{comicFormatLabel(comic.format)}</Badge>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Meta label="Cover date" value={formatMonthYear(comic.coverDate)} />
          <Meta label="Cover price" value={usdOrDash(cover)} />
          <Meta label="Writer" value={peopleList(comic.writers)} />
          <Meta label="Artist" value={peopleList(comic.artists)} />
          <Meta label="UPC / ISBN" value={comic.upc ?? "—"} />
        </dl>

        {owned ? (
          <section className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
            <h2 className="font-display text-xl tracking-wide uppercase">Your copy</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Meta label="Acquired" value={owned.acquiredDate ?? "—"} />
              <Meta label="You paid" value={usdOrDash(paid)} />
              <Meta label="Grade" value={gradeLabel ?? "Raw"} />
              <Meta label="Counts as" value={usdOrDash(itemValue(paid, cover))} />
            </dl>
            {owned.notes ? <p className="mt-3 text-sm text-muted">{owned.notes}</p> : null}
          </section>
        ) : null}

        <AddComicDialog comic={comic} open={edit} onOpenChange={setEdit} />
      </div>
    </main>
  );
}


function ComicLadderCrumbs({
  comic,
  yearById,
}: {
  comic: CatalogComic;
  yearById: Map<string, number>;
}) {
  const year = seriesRunYearFor(comic, yearById);
  const title = seriesBaseTitle(comic.series);
  const collected = isCollectedComic(comic);
  return (
    <nav aria-label="Comic breadcrumb" className="flex flex-wrap items-center gap-1 text-xs tracking-[0.2em] uppercase">
      <Link to="/comics" search={{}} className="inline-flex items-center gap-1 text-gold hover:underline">
        <ArrowLeft className="size-3" /> Comics
      </Link>
      <ChevronRight className="size-3 text-muted" />
      <Link
        to="/comics"
        search={{ publisher: comic.publisher }}
        className="text-gold hover:underline"
      >
        {comic.publisher}
      </Link>
      <ChevronRight className="size-3 text-muted" />
      {collected ? (
        <>
          <Link
            to="/comics"
            search={{ publisher: comic.publisher, section: "collected" }}
            className="text-gold hover:underline"
          >
            Collected Editions
          </Link>
          <ChevronRight className="size-3 text-muted" />
          <Link
            to="/comics"
            search={{ publisher: comic.publisher, section: "collected", series: title }}
            className="min-w-0 break-words text-gold hover:underline"
          >
            {title || "Series unknown"}
          </Link>
        </>
      ) : (
        <Link
          to="/comics"
          search={{ publisher: comic.publisher, series: title, year }}
          className="text-gold hover:underline"
        >
          {seriesDisplayLabel(title, year)}
        </Link>
      )}
    </nav>
  );
}

/** Coerce writers/artists whether the row arrived as string[] or a CSV string. */
function peopleList(value: unknown): string {
  if (Array.isArray(value)) {
    const parts = value.map((v) => String(v ?? "").trim()).filter(Boolean);
    return parts.length ? parts.join(", ") : "—";
  }
  if (value == null || value === "") return "—";
  const s = String(value).trim();
  return s || "—";
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-surface p-3">
      <dt className="text-[11px] tracking-[0.16em] text-muted uppercase">{label}</dt>
      <dd className="mt-1 text-sm">{value}</dd>
    </div>
  );
}

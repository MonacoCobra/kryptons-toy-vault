import { useMemo, useState } from "react";
import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { Heart, Trash2 } from "lucide-react";
import { comicById, comicLabel, mergeComics } from "@/data/comics";
import { AddComicDialog } from "@/components/add-comic-dialog";
import { ComicCover } from "@/components/comic-cover";
import { ComicVariantScroller } from "@/components/comic-variant-scroller";
import { MarketEstimate } from "@/components/market-estimate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getComicVariants, indexComicsByFamily } from "@/lib/comic-variants";
import { formatMonthYear, usd } from "@/lib/format";
import { useComicLib, useEnsureComicLibrary, useLiveComics, useLiveDrop } from "@/lib/live-store";
import { comicHistory, comicMarket } from "@/lib/market";
import { GRADES, useVault } from "@/lib/store";

export const Route = createFileRoute("/comics/$comicId")({
  component: ComicDetail,
});

function ComicDetail() {
  const { comicId } = Route.useParams();
  const extras = useLiveComics();
  const library = useEnsureComicLibrary(extras);
  const loading = useLiveDrop((s) => s.loading);
  const libLoading = useComicLib((s) => s.loading);
  const comic = comicById(comicId, extras, library?.archive ?? []);

  const catalog = useMemo(
    () => mergeComics(extras, library?.archive ?? []),
    [extras, library],
  );
  const familyIndex = useMemo(() => indexComicsByFamily(catalog), [catalog]);
  const variants = useMemo(
    () => (comic ? getComicVariants(comic, catalog, familyIndex) : []),
    [comic, catalog, familyIndex],
  );

  const ownedList = useVault((s) => s.ownedComics);
  const owned = useMemo(
    () => (comic ? Object.values(ownedList).find((o) => o.catalogId === comic.id) : undefined),
    [ownedList, comic],
  );
  const wanted = useVault((s) => (comic ? s.wantedComics[comic.id] : undefined));
  const toggleWant = useVault((s) => s.toggleWantComic);
  const removeComic = useVault((s) => s.removeComic);
  const [edit, setEdit] = useState(false);

  if (!comic) {
    if ((comicId.startsWith("live-") && loading) || libLoading) {
      return <p className="py-16 text-center text-sm text-muted">Loading catalog…</p>;
    }
    throw notFound();
  }

  const market = comicMarket(comic);
  const prev = comicMarket(comic, -1).estimate;
  const deltaPct = prev ? ((market.estimate - prev) / prev) * 100 : 0;
  const history = comicHistory(comic, 12);
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
          <Link to="/comics" search={{ publisher: comic.publisher }} className="text-xs tracking-[0.2em] text-gold uppercase">
            {comic.publisher}
          </Link>
          <h1 className="mt-1 font-display text-4xl tracking-wide uppercase">{comicLabel(comic)}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">{comic.description}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {owned ? <Badge tone="gain">Owned</Badge> : null}
            {wanted && !owned ? <Badge tone="gold">Wanted</Badge> : null}
            {comic.key ? <Badge tone="red">Key issue</Badge> : null}
            {comic.variant ? <Badge tone="gold">{comic.variant}</Badge> : null}
            <Badge>{comic.format}</Badge>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Meta label="Cover date" value={formatMonthYear(comic.coverDate)} />
          <Meta label="Cover price" value={usd(comic.msrp)} />
          <Meta label="Writer" value={comic.writers.join(", ")} />
          <Meta label="Artist" value={comic.artists.join(", ")} />
          <Meta label="UPC / ISBN" value={comic.upc ?? "—"} />
        </dl>

        <MarketEstimate
          kind="comic"
          item={comic}
          fallbackComps={market.comps}
          fallbackEstimate={market.estimate}
          history={history}
          deltaPct={deltaPct}
        />

        {owned ? (
          <section className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
            <h2 className="font-display text-xl tracking-wide uppercase">Your copy</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
              <Meta label="Acquired" value={owned.acquiredDate ?? "—"} />
              <Meta label="You paid" value={owned.acquiredPrice != null ? usd(owned.acquiredPrice) : "—"} />
              <Meta label="Grade" value={gradeLabel ?? "Raw"} />
            </dl>
            {owned.notes ? <p className="mt-3 text-sm text-muted">{owned.notes}</p> : null}
          </section>
        ) : null}

        <AddComicDialog comic={comic} open={edit} onOpenChange={setEdit} />
      </div>
    </main>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-surface p-3">
      <dt className="text-[11px] tracking-[0.16em] text-muted uppercase">{label}</dt>
      <dd className="mt-1 text-sm">{value}</dd>
    </div>
  );
}

import { useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { COMIC_BY_ID, comicLabel } from "@/data/comics";
import { FIGURE_BY_ID } from "@/data/figures";
import { ComicCover } from "@/components/comic-cover";
import { FigureArt } from "@/components/figure-art";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatDate, usd } from "@/lib/format";
import { useFigureExtras, useLiveComics } from "@/lib/live-store";
import { comicEstimate, figureMarket } from "@/lib/market";
import { useVault } from "@/lib/store";
import { DisplaysGallery } from "@/components/displays-gallery";
import { summarizeVault } from "@/lib/vault-math";

export const Route = createFileRoute("/collection")({ component: CollectionPage });

function CollectionPage() {
  const ownedFigures = useVault((s) => s.ownedFigures);
  const ownedComics = useVault((s) => s.ownedComics);
  const displays = useVault((s) => s.displays ?? {});
  const displayCount = Object.keys(displays).length;
  const liveFigures = useFigureExtras();
  const liveComics = useLiveComics();
  const clearVault = useVault((s) => s.clearVault);
  const [tab, setTab] = useState<string | null>(null);
  const stats = summarizeVault({ ownedFigures, ownedComics }, { figures: liveFigures, comics: liveComics });

  const figures = useMemo(
    () =>
      Object.values(ownedFigures)
        .map((o) => ({ owned: o, figure: FIGURE_BY_ID[o.figureId] ?? liveFigures.find((f) => f.id === o.figureId) }))
        .filter((x) => x.figure)
        .sort((a, b) => (a.owned.addedAt < b.owned.addedAt ? 1 : -1)),
    [ownedFigures, liveFigures],
  );

  const comics = useMemo(
    () =>
      Object.values(ownedComics)
        .map((o) => ({ owned: o, comic: o.catalogId ? COMIC_BY_ID[o.catalogId] ?? liveComics.find((c) => c.id === o.catalogId) : o.custom }))
        .filter((x) => x.comic)
        .sort((a, b) => (a.owned.addedAt < b.owned.addedAt ? 1 : -1)),
    [ownedComics, liveComics],
  );

  const activeTab = tab ?? (figures.length === 0 && comics.length > 0 ? "comics" : "figures");

  return (
    <main className="flex flex-col gap-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-display text-3xl tracking-wide uppercase">Collection</h1>
          <p className="mt-2 text-sm text-muted">
            {stats.figureCount} figures · {stats.comicCount} comics · {usd(stats.value, 0)} estimated
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" asChild>
            <Link to="/import">Import LOCG</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link to="/displays">Displays</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link to="/wishlist">Want list</Link>
          </Button>
          <Button variant="ghost" onClick={() => clearVault()}>
            Clear vault
          </Button>
        </div>
      </header>

      <Tabs value={activeTab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="figures">Figures ({figures.length})</TabsTrigger>
          <TabsTrigger value="comics">Comics ({comics.length})</TabsTrigger>
          <TabsTrigger value="displays">Displays ({displayCount})</TabsTrigger>
        </TabsList>
        <TabsContent value="figures">
          {figures.length === 0 ? (
            <Empty to="/figures" label="Browse checklists" />
          ) : (
            <ul className="grid gap-2">
              {figures.map(({ owned, figure }) => {
                if (!figure) return null;
                const est = figureMarket(figure).estimate;
                return (
                  <li
                    key={owned.figureId}
                    className="flex gap-3 rounded-lg bg-bg-elevated p-2 shadow-[var(--shadow-border)]"
                  >
                    <Link to="/figures/$figureId" params={{ figureId: figure.id }} className="shrink-0">
                      <FigureArt figure={figure} photo={owned.photoDataUrl} className="h-24 w-20 rounded-sm" />
                    </Link>
                    <div className="min-w-0 flex-1">
                      <Link to="/figures/$figureId" params={{ figureId: figure.id }} className="font-medium">
                        {figure.name}
                      </Link>
                      <p className="text-xs text-muted">
                        {figure.line} · acquired {formatDate(owned.acquiredDate)}
                      </p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <Badge>{owned.condition}</Badge>
                        {owned.photoDataUrl ? <Badge tone="ice">Photo</Badge> : null}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="tabular text-sm text-gold">{usd(est)}</p>
                      <p className="tabular text-xs text-subtle">
                        paid {owned.acquiredPrice != null ? usd(owned.acquiredPrice) : "—"}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </TabsContent>
        <TabsContent value="comics">
          {comics.length === 0 ? (
            <Empty to="/comics" label="Browse the catalog" />
          ) : (
            <ul className="grid gap-2">
              {comics.map(({ owned, comic }) => {
                if (!comic) return null;
                const catalog = owned.catalogId
                  ? COMIC_BY_ID[owned.catalogId] ?? liveComics.find((c) => c.id === owned.catalogId)
                  : undefined;
                const est = catalog ? comicEstimate(catalog) : owned.acquiredPrice ?? 0;
                return (
                  <li
                    key={owned.id}
                    className="flex gap-3 rounded-lg bg-bg-elevated p-2 shadow-[var(--shadow-border)]"
                  >
                    {owned.catalogId ? (
                      <Link to="/comics/$comicId" params={{ comicId: owned.catalogId }} className="shrink-0">
                        <ComicCover comic={comic} photo={owned.photoDataUrl} resolveRemote className="h-24 w-16 rounded-sm" />
                      </Link>
                    ) : (
                      <ComicCover comic={comic} photo={owned.photoDataUrl} resolveRemote className="h-24 w-16 shrink-0 rounded-sm" />
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="font-medium">{comicLabel(comic)}</p>
                      <p className="text-xs text-muted">
                        {comic.publisher} · {owned.grade === "raw" ? "Raw" : owned.grade}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="tabular text-sm text-gold">{usd(est)}</p>
                      <p className="tabular text-xs text-subtle">
                        paid {owned.acquiredPrice != null ? usd(owned.acquiredPrice) : "—"}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </TabsContent>
        <TabsContent value="displays">
          <DisplaysGallery />
        </TabsContent>
      </Tabs>
    </main>
  );
}

function Empty({ to, label }: { to: "/figures" | "/comics"; label: string }) {
  return (
    <div className="rounded-xl bg-bg-elevated p-10 text-center shadow-[var(--shadow-border)]">
      <p className="font-display text-xl tracking-wide uppercase">Nothing here yet</p>
      <Button asChild className="mt-4">
        <Link to={to}>{label}</Link>
      </Button>
    </div>
  );
}

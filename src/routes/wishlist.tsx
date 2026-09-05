import { createFileRoute, Link } from "@tanstack/react-router";
import { COMIC_BY_ID, comicLabel } from "@/data/comics";
import { FIGURE_BY_ID } from "@/data/figures";
import { ComicCover } from "@/components/comic-cover";
import { FigureArt } from "@/components/figure-art";
import { Button } from "@/components/ui/button";
import { usd } from "@/lib/format";
import { useLiveComics, useLiveFigures } from "@/lib/live-store";
import { comicEstimate, figureMarket } from "@/lib/market";
import { useVault } from "@/lib/store";

export const Route = createFileRoute("/wishlist")({ component: WishlistPage });

function WishlistPage() {
  const wantedFigures = useVault((s) => s.wantedFigures);
  const wantedComics = useVault((s) => s.wantedComics);
  const liveFigures = useLiveFigures();
  const liveComics = useLiveComics();
  const toggleWantFigure = useVault((s) => s.toggleWantFigure);
  const toggleWantComic = useVault((s) => s.toggleWantComic);

  const figures = Object.keys(wantedFigures)
    .map((id) => FIGURE_BY_ID[id] ?? liveFigures.find((f) => f.id === id))
    .filter(Boolean);
  const comics = Object.keys(wantedComics)
    .map((id) => COMIC_BY_ID[id] ?? liveComics.find((c) => c.id === id))
    .filter(Boolean);

  return (
    <main className="flex flex-col gap-8">
      <header>
        <p className="text-xs tracking-[0.28em] text-gold uppercase">The hunt</p>
        <h1 className="mt-1 font-display text-3xl tracking-wide uppercase">Want list</h1>
        <p className="mt-2 text-sm text-muted">
          {figures.length} figures · {comics.length} issues still outside the vault.
        </p>
      </header>

      <section>
        <h2 className="font-display text-xl tracking-wide uppercase">Figures</h2>
        {figures.length === 0 ? (
          <p className="mt-3 text-sm text-muted">No figures on the list.</p>
        ) : (
          <ul className="mt-3 grid gap-2">
            {figures.map((f) =>
              f ? (
                <li
                  key={f.id}
                  className="flex items-center gap-3 rounded-lg bg-bg-elevated p-2 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]"
                >
                  <Link to="/figures/$figureId" params={{ figureId: f.id }}>
                    <FigureArt figure={f} className="h-16 w-14 rounded-sm" />
                  </Link>
                  <div className="min-w-0 flex-1">
                    <Link to="/figures/$figureId" params={{ figureId: f.id }} className="font-medium">
                      {f.name}
                    </Link>
                    <p className="text-xs text-muted">{f.line}</p>
                  </div>
                  <p className="tabular text-sm text-gold">{usd(figureMarket(f).estimate)}</p>
                  <Button size="sm" variant="ghost" onClick={() => toggleWantFigure(f.id)}>
                    Drop
                  </Button>
                </li>
              ) : null,
            )}
          </ul>
        )}
      </section>

      <section>
        <h2 className="font-display text-xl tracking-wide uppercase">Comics</h2>
        {comics.length === 0 ? (
          <p className="mt-3 text-sm text-muted">No issues on the list.</p>
        ) : (
          <ul className="mt-3 grid gap-2">
            {comics.map((c) =>
              c ? (
                <li
                  key={c.id}
                  className="flex items-center gap-3 rounded-lg bg-bg-elevated p-2 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]"
                >
                  <Link to="/comics/$comicId" params={{ comicId: c.id }}>
                    <ComicCover comic={c} resolveRemote className="h-16 w-11 rounded-sm" />
                  </Link>
                  <div className="min-w-0 flex-1">
                    <Link to="/comics/$comicId" params={{ comicId: c.id }} className="font-medium">
                      {comicLabel(c)}
                    </Link>
                    <p className="text-xs text-muted">{c.publisher}</p>
                  </div>
                  <p className="tabular text-sm text-gold">{usd(comicEstimate(c))}</p>
                  <Button size="sm" variant="ghost" onClick={() => toggleWantComic(c.id)}>
                    Drop
                  </Button>
                </li>
              ) : null,
            )}
          </ul>
        )}
      </section>
    </main>
  );
}

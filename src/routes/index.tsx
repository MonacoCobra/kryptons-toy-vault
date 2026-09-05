import { createFileRoute, Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { comicLabel, recentComics } from "@/data/comics";
import { FigureArt } from "@/components/figure-art";
import { ComicCover } from "@/components/comic-cover";
import { pct, usd } from "@/lib/format";
import { useLiveComics, useLiveDrop, useLiveFigures } from "@/lib/live-store";
import { catalogStats } from "@/lib/market";
import { useVault } from "@/lib/store";
import { weekKey } from "@/lib/utils";
import { summarizeVault } from "@/lib/vault-math";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  const ownedFigures = useVault((s) => s.ownedFigures);
  const ownedComics = useVault((s) => s.ownedComics);
  const liveComics = useLiveComics();
  const liveFigures = useLiveFigures();
  const liveLoading = useLiveDrop((s) => s.loading);
  const stats = summarizeVault({ ownedFigures, ownedComics }, { comics: liveComics, figures: liveFigures });
  const catalog = catalogStats();
  const gainUp = stats.gain >= 0;
  const week = weekKey();
  const newFigures = liveFigures.slice(0, 8);
  const newComics = liveComics.length ? liveComics.slice(0, 10) : recentComics(10);

  return (
    <main className="flex flex-col gap-8">
      <section className="flex flex-col items-center pt-2 text-center md:pt-4">
        <img
          src="/krypton-logo.png"
          alt="Krypton's Toy Vault shield"
          className="mark w-64 md:w-80 lg:w-96"
        />
        <h1 className="mt-5 font-display text-3xl tracking-wide text-fg uppercase md:text-4xl">
          <Link
            to="/collection"
            className="text-fg transition-colors duration-150 hover:text-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold/60"
          >
            Personal vault
          </Link>
        </h1>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Vault estimate"
          value={usd(stats.value, 0)}
          hint="Median of recent sold comps"
        />
        <StatCard
          label="Cost basis"
          value={usd(stats.cost, 0)}
          hint={
            <span className={gainUp ? "text-gain" : "text-loss"}>
              {gainUp ? <ArrowUpRight className="inline size-3.5" /> : <ArrowDownRight className="inline size-3.5" />}{" "}
              {usd(Math.abs(stats.gain), 0)} ({pct(stats.gainPct)})
            </span>
          }
        />
        <StatCard
          label="Action Figures"
          value={String(stats.figureCount)}
          hint={`${catalog.figures} in the checklists`}
        />
        <StatCard
          label="Comics"
          value={String(stats.comicCount)}
          hint={`${catalog.comics} issues in the catalog`}
        />
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-xl tracking-wide uppercase">New figure releases</h2>
            <p className="text-sm text-muted">
              {liveFigures.length
                ? `This week's action figures · ${week}`
                : liveLoading
                  ? "Checking this week's figure drop…"
                  : "Live weekly figures will land here."}
            </p>
          </div>
          <Link to="/figures" className="shrink-0 text-sm text-ice hover:text-fg">
            All figures
          </Link>
        </div>
        {liveLoading && !newFigures.length ? (
          <p className="rounded-xl bg-bg-elevated px-4 py-8 text-center text-sm text-muted shadow-[var(--shadow-border)]">
            Pulling this week's figure releases…
          </p>
        ) : newFigures.length ? (
          <ul className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {newFigures.map((figure) => (
              <li key={figure.id}>
                <Link
                  to="/figures/$figureId"
                  params={{ figureId: figure.id }}
                  className="block overflow-hidden rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]"
                >
                  <FigureArt figure={figure} className="aspect-4/5" />
                  <div className="p-2.5">
                    <p className="line-clamp-2 text-xs font-medium">{figure.name}</p>
                    <p className="truncate text-[11px] text-muted">{figure.line}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rounded-xl bg-bg-elevated px-4 py-8 text-center text-sm text-muted shadow-[var(--shadow-border)]">
            No new figure releases this week yet.
          </p>
        )}
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-xl tracking-wide uppercase">New comic releases</h2>
            <p className="text-sm text-muted">
              {liveComics.length
                ? `Street dates for ${week}`
                : liveLoading
                  ? "Checking this week's street list…"
                  : "Newest issues in the catalog."}
            </p>
          </div>
          <Link to="/comics" className="shrink-0 text-sm text-ice hover:text-fg">
            All comics
          </Link>
        </div>
        {liveLoading && !liveComics.length ? (
          <p className="rounded-xl bg-bg-elevated px-4 py-8 text-center text-sm text-muted shadow-[var(--shadow-border)]">
            Pulling this week's comic releases…
          </p>
        ) : (
          <ul className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {newComics.map((comic) => (
              <li key={comic.id}>
                <Link
                  to="/comics/$comicId"
                  params={{ comicId: comic.id }}
                  className="block overflow-hidden rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]"
                >
                  <ComicCover comic={comic} className="aspect-2/3" />
                  <div className="p-2.5">
                    <p className="line-clamp-2 text-xs font-medium">{comicLabel(comic)}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: ReactNode;
}) {
  return (
    <div className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
      <p className="text-xs tracking-[0.18em] text-muted uppercase">{label}</p>
      <p className="mt-2 font-display text-3xl tracking-wide tabular">{value}</p>
      <p className="mt-1 text-xs text-muted">{hint}</p>
    </div>
  );
}

import { createFileRoute, Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight, Camera, Star } from "lucide-react";
import { COMPANIES } from "@/data/companies";
import { FIGURE_BY_ID } from "@/data/figures";
import { COMIC_BY_ID, comicLabel, recentComics } from "@/data/comics";
import { FigureArt } from "@/components/figure-art";
import { ComicCover } from "@/components/comic-cover";
import { ValueChart } from "@/components/value-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { pct, usd } from "@/lib/format";
import { useLiveComics, useLiveDrop, useLiveFigures } from "@/lib/live-store";
import { catalogStats, topMovers } from "@/lib/market";
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
  const movers = topMovers(4);
  const gainUp = stats.gain >= 0;
  const week = weekKey();
  const pull = liveComics.length ? liveComics.slice(0, 5) : recentComics(5);
  const newFigures = liveFigures.slice(0, 4);

  const recentlyVaulted = [
    ...Object.values(ownedFigures)
      .map((owned) => {
        const figure = FIGURE_BY_ID[owned.figureId] ?? liveFigures.find((f) => f.id === owned.figureId);
        return figure ? { kind: "figure" as const, addedAt: owned.addedAt, owned, figure } : null;
      })
      .filter((x) => x !== null),
    ...Object.values(ownedComics).map((owned) => ({
      kind: "comic" as const,
      addedAt: owned.addedAt,
      owned,
    })),
  ]
    .sort((a, b) => (a.addedAt < b.addedAt ? 1 : -1))
    .slice(0, 4);

  return (
    <main className="flex flex-col gap-8">
      <section className="grid items-center gap-6 md:grid-cols-[1.15fr_0.85fr]">
        <div>
          <p className="text-xs tracking-[0.28em] text-gold uppercase">Collector archive</p>
          <h1 className="mt-2 font-display text-4xl tracking-wide text-fg uppercase md:text-5xl">
            The vault
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted">
            Figures, kits, and comics — logged with photos, tracked against recent sold comps.
            New releases land here every week.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            <Button asChild>
              <Link to="/figures">Browse figures</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/comics">Browse comics</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/scan">
                <Camera className="size-4" />
                Scan a cover
              </Link>
            </Button>
          </div>
        </div>
        <div className="flex justify-center md:justify-end">
          <img
            src="/krypton-logo.png"
            alt="Krypton's Toy Vault shield"
            className="mark w-52 md:w-72"
          />
        </div>
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
          label="Figures & kits"
          value={String(stats.figureCount)}
          hint={`${catalog.figures} in the checklists`}
        />
        <StatCard
          label="Comics"
          value={String(stats.comicCount)}
          hint={`${catalog.comics} issues in the catalog`}
        />
      </section>

      <section className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)] md:p-5">
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <h2 className="font-display text-xl tracking-wide uppercase">Twelve-week market</h2>
            <p className="text-sm text-muted">Sold-comp median, week by week.</p>
          </div>
          <Badge tone="gold">Updates {week}</Badge>
        </div>
        {stats.history.length ? (
          <ValueChart data={stats.history} />
        ) : (
          <p className="py-10 text-center text-sm text-muted">Add pieces to see the market line.</p>
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-xl tracking-wide uppercase">Company checklists</h2>
            <Link to="/figures" className="text-sm text-ice hover:text-fg">
              All lines
            </Link>
          </div>
          <ul className="grid gap-3">
            {COMPANIES.slice(0, 8).map((c) => {
              const row = stats.byCompany[c.id] ?? { total: 0, owned: 0 };
              const pctOwned = row.total ? (row.owned / row.total) * 100 : 0;
              return (
                <li key={c.id}>
                  <Link
                    to="/figures"
                    search={{ company: c.id }}
                    className="grid grid-cols-[auto_1fr_auto] items-center gap-3"
                  >
                    <span className="size-2.5 rounded-full" style={{ background: c.accent }} />
                    <span>
                      <span className="block text-sm font-medium">{c.name}</span>
                      <Progress value={pctOwned} className="mt-1.5" />
                    </span>
                    <span className="tabular text-xs text-muted">
                      {row.owned}/{row.total}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
          <div className="mb-4 flex items-center gap-2">
            <Star className="size-4 text-gold" />
            <h2 className="font-display text-xl tracking-wide uppercase">Weekly movers</h2>
          </div>
          <ul className="grid gap-3">
            {movers.map((m) => (
              <li key={m.figure.id}>
                <Link to="/figures/$figureId" params={{ figureId: m.figure.id }} className="flex items-center gap-3">
                  <div className="size-14 overflow-hidden rounded-sm">
                    <FigureArt figure={m.figure} caption={false} className="size-14" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{m.figure.name}</p>
                    <p className="truncate text-xs text-muted">{m.figure.line}</p>
                  </div>
                  <div className="text-right">
                    <p className="tabular text-sm">{usd(m.now)}</p>
                    <p className={`tabular text-xs ${m.delta >= 0 ? "text-gain" : "text-loss"}`}>
                      {pct(m.pct)}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-xl tracking-wide uppercase">Recently vaulted</h2>
          <Link to="/collection" className="text-sm text-ice hover:text-fg">
            Full collection
          </Link>
        </div>
        {recentlyVaulted.length ? (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {recentlyVaulted.map((item) => {
            if (item.kind === "figure" && item.figure) {
              return (
                <Link
                  key={item.figure.id}
                  to="/figures/$figureId"
                  params={{ figureId: item.figure.id }}
                  className="overflow-hidden rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]"
                >
                  <FigureArt
                    figure={item.figure}
                    photo={item.owned.photoDataUrl}
                    className="aspect-4/5"
                  />
                </Link>
              );
            }
            if (item.kind === "comic") {
              const o = item.owned;
      const c = o.catalogId ? COMIC_BY_ID[o.catalogId] ?? liveComics.find((x) => x.id === o.catalogId) : o.custom;
              if (!c) return null;
              if (o.catalogId) {
                return (
                  <Link
                    key={o.id}
                    to="/comics/$comicId"
                    params={{ comicId: o.catalogId }}
                    className="overflow-hidden rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]"
                  >
                    <ComicCover comic={c} photo={o.photoDataUrl} className="aspect-2/3" />
                  </Link>
                );
              }
              return (
                <Link
                  key={o.id}
                  to="/collection"
                  className="overflow-hidden rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]"
                >
                  <ComicCover comic={c} photo={o.photoDataUrl} className="aspect-2/3" />
                </Link>
              );
            }
            return null;
          })}
          </div>
        ) : (
          <p className="rounded-xl bg-bg-elevated px-4 py-8 text-center text-sm text-muted shadow-[var(--shadow-border)]">
            Nothing vaulted yet. Scan a cover or add a figure from the checklists.
          </p>
        )}
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-xl tracking-wide uppercase">This week's drop</h2>
            <p className="text-sm text-muted">
              {liveComics.length || liveFigures.length
                ? `Street dates and new figures for ${week}.`
                : liveLoading
                  ? "Checking this week's street list…"
                  : "Newest issues in the catalog."}
            </p>
          </div>
          <Link to="/comics" className="text-sm text-ice hover:text-fg">
            Full catalog
          </Link>
        </div>
        {liveLoading && !liveComics.length && !liveFigures.length ? (
          <p className="mb-4 rounded-xl bg-bg-elevated px-4 py-8 text-center text-sm text-muted shadow-[var(--shadow-border)]">
            Pulling this week's street list. New issues will appear here.
          </p>
        ) : null}
        {newFigures.length ? (
          <ul className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
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
        ) : null}
        {liveComics.length || !liveLoading ? (
        <ul className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {pull.map((comic) => (
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
        ) : null}
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

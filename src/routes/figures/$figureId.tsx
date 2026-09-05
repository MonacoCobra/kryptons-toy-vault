import { useState } from "react";
import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { Heart, Trash2 } from "lucide-react";
import { COMPANY_BY_ID } from "@/data/companies";
import { figureById } from "@/data/figures";
import { AddFigureDialog } from "@/components/add-figure-dialog";
import { FigureArt } from "@/components/figure-art";
import { MarketEstimate } from "@/components/market-estimate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate, usd } from "@/lib/format";
import { useLiveDrop, useLiveFigures } from "@/lib/live-store";
import { figureHistory, figureMarket } from "@/lib/market";
import { CONDITIONS, useVault } from "@/lib/store";

export const Route = createFileRoute("/figures/$figureId")({
  component: FigureDetail,
});

function FigureDetail() {
  const { figureId } = Route.useParams();
  const extras = useLiveFigures();
  const loading = useLiveDrop((s) => s.loading);
  const figure = figureById(figureId, extras);
  if (!figure) {
    if (figureId.startsWith("live-") && loading) {
      return <p className="py-16 text-center text-sm text-muted">Loading this week's drop…</p>;
    }
    throw notFound();
  }

  const owned = useVault((s) => s.ownedFigures[figure.id]);
  const wanted = useVault((s) => s.wantedFigures[figure.id]);
  const toggleWant = useVault((s) => s.toggleWantFigure);
  const removeFigure = useVault((s) => s.removeFigure);
  const [edit, setEdit] = useState(false);

  const company = COMPANY_BY_ID[figure.company];
  const market = figureMarket(figure);
  const prev = figureMarket(figure, -1).estimate;
  const deltaPct = prev ? ((market.estimate - prev) / prev) * 100 : 0;
  const history = figureHistory(figure, 12);
  const condLabel = CONDITIONS.find((c) => c.id === owned?.condition)?.label;

  return (
    <main className="grid gap-8 lg:grid-cols-[minmax(0,18rem)_1fr]">
      <div>
        <FigureArt
          figure={figure}
          photo={owned?.photoDataUrl}
          className="aspect-4/5 overflow-hidden rounded-xl"
        />
        <div className="mt-4 grid gap-2">
          <Button onClick={() => setEdit(true)}>{owned ? "Edit vault entry" : "Add to vault"}</Button>
          <Button variant="secondary" onClick={() => toggleWant(figure.id)} disabled={Boolean(owned)}>
            <Heart className={wanted ? "fill-gold text-gold" : ""} />
            {owned ? "Already owned" : wanted ? "Remove from want list" : "Add to want list"}
          </Button>
          {owned ? (
            <Button variant="outline" onClick={() => removeFigure(figure.id)}>
              <Trash2 />
              Remove from vault
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-6">
        <div>
          <Link
            to="/figures"
            search={{ company: figure.company }}
            className="text-xs tracking-[0.2em] text-gold uppercase"
          >
            {company.name} · {figure.line}
          </Link>
          <h1 className="mt-1 font-display text-4xl tracking-wide uppercase">{figure.name}</h1>
          <p className="mt-1 text-muted">{figure.subtitle}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {owned ? <Badge tone="gain">In vault</Badge> : null}
            {wanted && !owned ? <Badge tone="gold">Wanted</Badge> : null}
            {figure.exclusive ? <Badge tone="ice">{figure.exclusive}</Badge> : null}
            {figure.kind === "kit" ? <Badge>Model kit</Badge> : <Badge>{figure.scale}</Badge>}
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Meta label="Release" value={formatDate(figure.releaseDate)} />
          <Meta label="MSRP" value={usd(figure.msrp)} />
          <Meta label="SKU" value={figure.sku ?? "—"} />
          <Meta label="Scale" value={figure.scale} />
        </dl>

        <MarketEstimate
          kind="figure"
          item={figure}
          fallbackComps={market.comps}
          fallbackEstimate={market.estimate}
          history={history}
          deltaPct={deltaPct}
        />

        {owned ? (
          <section className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
            <h2 className="font-display text-xl tracking-wide uppercase">Your copy</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Meta label="Acquired" value={formatDate(owned.acquiredDate)} />
              <Meta label="You paid" value={owned.acquiredPrice != null ? usd(owned.acquiredPrice) : "—"} />
              <Meta label="Condition" value={condLabel ?? "—"} />
              <Meta
                label="Spread"
                value={
                  owned.acquiredPrice != null
                    ? usd(market.estimate - owned.acquiredPrice)
                    : "—"
                }
              />
            </dl>
            {owned.notes ? <p className="mt-3 text-sm text-muted">{owned.notes}</p> : null}
          </section>
        ) : null}

        <AddFigureDialog figure={figure} open={edit} onOpenChange={setEdit} />
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

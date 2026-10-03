import { useEffect, useState } from "react";
import { SoldListings } from "@/components/sold-listings";
import { ValueChart } from "@/components/value-chart";
import { Badge } from "@/components/ui/badge";
import { formatDate, usd } from "@/lib/format";
import { cachedFigureComps } from "@/lib/market-comps-cache";
import { getFigureSoldComps, type SoldCompsLookup } from "@/lib/soldcomps-market";
import type { FigureSoldComps } from "@/lib/soldcomps";
import type { CatalogComic, CatalogFigure, SoldComp } from "@/lib/types";

type Props = {
  kind: "figure" | "comic";
  item: CatalogFigure | CatalogComic;
  /** Modeled comps — never rendered as sales. Kept for API compatibility. */
  fallbackComps: SoldComp[];
  fallbackEstimate: number;
  history: { label: string; value: number }[];
  deltaPct: number;
};

function shortDate(iso: string): string {
  const [, m, d] = iso.split("-");
  return m && d ? `${Number(m)}/${Number(d)}` : iso;
}

export function MarketEstimate(props: Props) {
  const isFigure = props.kind === "figure";
  const fig = isFigure ? (props.item as CatalogFigure) : null;
  const itemId = props.item.id;
  const [lookup, setLookup] = useState<SoldCompsLookup | null>(() =>
    fig ? { result: cachedFigureComps(fig.id) ?? null } : null,
  );
  const [loading, setLoading] = useState(isFigure);

  useEffect(() => {
    if (!fig) return;
    let cancelled = false;
    setLookup({ result: cachedFigureComps(fig.id) ?? null });
    setLoading(true);
    void getFigureSoldComps({
      data: { id: fig.id, name: fig.name, line: fig.line, subtitle: fig.subtitle, scale: fig.scale },
    })
      .then((res) => {
        if (!cancelled) setLookup(res);
      })
      .catch(() => {
        /* keep the repo cache result */
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemId]);

  const result: FigureSoldComps | null = lookup?.result ?? null;
  const real = Boolean(result && result.status === "ok" && result.comps.length && result.estimate);

  if (real && result) {
    const comps: SoldComp[] = result.comps.map((c) => ({ ...c, source: "soldcomps" }));
    const chart = [...comps]
      .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0))
      .map((c) => ({ label: shortDate(c.date), value: c.price }));
    return (
      <section className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-xs tracking-[0.18em] text-muted uppercase">Current value</p>
            <p className="mt-1 font-display text-4xl tracking-wide text-gold tabular">{usd(result.estimate!)}</p>
            <p className="text-sm text-muted">
              Avg of {comps.length} most recent eBay sales
              {result.conditionBasis === "new" ? " (new)" : ""}
            </p>
          </div>
          <Badge tone="gold">eBay sold</Badge>
        </div>
        <p className="mt-3 text-xs text-muted">
          Average of the {comps.length} most recent matching sold listings on eBay ({result.passing} matching
          sales found for “{result.keyword}”). Updated {formatDate(result.fetchedAt.slice(0, 10))}; refreshed at most
          every 30 days.
          {result.bestOfferInAvg
            ? ` ${result.bestOfferInAvg} of these took a best offer — eBay shows the asking price, so those sold at or below it.`
            : ""}
        </p>
        <div className="mt-4">
          <ValueChart data={chart} />
        </div>
        <div className="mt-4">
          <SoldListings comps={comps} />
        </div>
      </section>
    );
  }

  let why = "";
  if (loading && isFigure) why = "Checking eBay sold listings… ";
  else if (result?.status === "insufficient")
    why = `Not enough matching eBay sales yet (${result.passing} found, need 3). `;
  else if (lookup?.note === "budget") why = "Monthly sales-lookup budget reached. ";
  else if (lookup?.note === "daily-cap") why = "Daily sales-lookup limit reached; try again tomorrow. ";
  else if (lookup?.note === "error" || result?.status === "error") why = "eBay sales lookup failed. ";
  else if (isFigure) why = "No eBay sales data cached for this figure yet. ";

  return (
    <section className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.18em] text-muted uppercase">Estimated value</p>
          <p className="mt-1 font-display text-4xl tracking-wide text-gold tabular">{usd(props.fallbackEstimate)}</p>
          <p className="text-sm text-muted">Estimate · not based on sales</p>
        </div>
        <Badge tone="default">{loading && isFigure ? "Checking…" : "Estimate"}</Badge>
      </div>
      <p className="mt-3 text-xs text-muted">
        {why}
        This is a modeled estimate from {isFigure ? "MSRP" : "cover price"} and demand, not actual sold listings.
      </p>
      <div className="mt-4">
        <p className="mb-1 text-xs tracking-wide text-muted uppercase">Modeled trend</p>
        <ValueChart data={props.history} />
      </div>
    </section>
  );
}

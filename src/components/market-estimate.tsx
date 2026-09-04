import { useEffect, useState } from "react";
import { SoldListings } from "@/components/sold-listings";
import { ValueChart } from "@/components/value-chart";
import { Badge } from "@/components/ui/badge";
import { usd } from "@/lib/format";
import {
  comicEbayQuery,
  figureEbayQuery,
  getEbayMarket,
  type EbayMarketResult,
} from "@/lib/ebay-market";
import { estimateFromComps } from "@/lib/market";
import type { CatalogComic, CatalogFigure, SoldComp } from "@/lib/types";
import { weekKey } from "@/lib/utils";

type Props = {
  kind: "figure" | "comic";
  item: CatalogFigure | CatalogComic;
  fallbackComps: SoldComp[];
  fallbackEstimate: number;
  history: { label: string; value: number }[];
  deltaPct: number;
};

export function MarketEstimate(props: Props) {
  const query =
    props.kind === "figure"
      ? figureEbayQuery(props.item as CatalogFigure)
      : comicEbayQuery(props.item as CatalogComic);
  const itemId = props.item.id;
  const [live, setLive] = useState<EbayMarketResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void getEbayMarket({
      data: {
        kind: props.kind,
        itemId,
        query,
        force: false,
      },
    })
      .then((result) => {
        if (!cancelled) setLive(result);
      })
      .catch(() => {
        if (!cancelled) setLive(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [props.kind, itemId, query]);

  const ebayReady = Boolean(live?.status === "ok" && live.comps.length);
  const comps = ebayReady ? live!.comps : props.fallbackComps;
  const estimate = ebayReady ? live!.estimate : estimateFromComps(comps) || props.fallbackEstimate;
  const sourceLabel = ebayReady
    ? "Avg of 5 most recent eBay sold"
    : loading
      ? "Loading eBay sold comps…"
      : live?.status === "unavailable"
        ? "Provisional estimate (eBay refresh unavailable here)"
        : "Provisional estimate — eBay solds unavailable";

  return (
    <section className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.18em] text-muted uppercase">
            {props.kind === "figure" ? "Current estimate" : "Market estimate"}
          </p>
          <p className="mt-1 font-display text-4xl tracking-wide text-gold tabular">{usd(estimate)}</p>
          <p className={`text-sm ${props.deltaPct >= 0 ? "text-gain" : "text-loss"}`}>
            {props.deltaPct >= 0 ? "+" : ""}
            {props.deltaPct.toFixed(1)}% vs last week
          </p>
        </div>
        <Badge tone="gold">{ebayReady ? "eBay · 5 sold avg" : loading ? "Fetching…" : "5 sold comps"}</Badge>
      </div>
      <p className="mt-3 text-xs text-muted">
        {sourceLabel}. Method: average of the five most recent matching sold listings on eBay
        {ebayReady ? "" : " (fallback model until live solds load)"}. Week {weekKey()}.
      </p>
      <div className="mt-4">
        <ValueChart data={props.history} />
      </div>
      <div className="mt-4">
        {comps.length ? (
          <SoldListings comps={comps} />
        ) : (
          <p className="text-sm text-muted">No sold comps yet.</p>
        )}
      </div>
    </section>
  );
}

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { LayoutGrid, List, Search } from "lucide-react";
import { COMPANIES } from "@/data/companies";
import { mergeFigures, searchFigures } from "@/data/figures";
import { AddFigureDialog } from "@/components/add-figure-dialog";
import { FigureArt } from "@/components/figure-art";
import { VirtualGrid } from "@/components/virtual-grid";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { usd } from "@/lib/format";
import { useLiveFigures } from "@/lib/live-store";
import { figureMarket } from "@/lib/market";
import { useVault } from "@/lib/store";
import type { CatalogFigure, CompanyId } from "@/lib/types";
import { cn } from "@/lib/utils";

type Search = {
  company?: CompanyId;
  q?: string;
  line?: string;
  view?: "all" | "owned" | "missing" | "kits";
  sort?: "release" | "name" | "acquired";
  layout?: "grid" | "list";
};

export const Route = createFileRoute("/figures/")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    company: typeof s.company === "string" ? (s.company as CompanyId) : undefined,
    q: typeof s.q === "string" ? s.q : undefined,
    line: typeof s.line === "string" ? s.line : undefined,
    view: s.view === "owned" || s.view === "missing" || s.view === "kits" || s.view === "all" ? s.view : undefined,
    sort: s.sort === "name" || s.sort === "acquired" || s.sort === "release" ? s.sort : undefined,
    layout: s.layout === "list" || s.layout === "grid" ? s.layout : undefined,
  }),
  component: FiguresPage,
});

const VIEW_LABEL: Record<NonNullable<Search["view"]> | "all", string> = {
  all: "All",
  owned: "Owned",
  missing: "Missing",
  kits: "Kits",
};

const SORT_LABEL: Record<NonNullable<Search["sort"]> | "release", string> = {
  release: "Release date",
  name: "A–Z",
  acquired: "Recently acquired",
};

const FIGURE_GRID_COLUMNS = { base: 2, md: 3, lg: 4 } as const;
const FIGURE_LIST_COLUMNS = { base: 1, md: 1, lg: 1 } as const;

function FiguresPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const owned = useVault((s) => s.ownedFigures);
  const wanted = useVault((s) => s.wantedFigures);
  const extras = useLiveFigures();
  const [adding, setAdding] = useState<CatalogFigure | null>(null);

  const catalog = useMemo(() => mergeFigures(extras), [extras]);
  const company = COMPANIES.find((c) => c.id === search.company);
  const lines = company
    ? [...new Set(catalog.filter((f) => f.company === company.id).map((f) => f.line))]
    : [];
  const layout = search.layout ?? "grid";
  const sort = search.sort ?? "release";

  const [qDraft, setQDraft] = useState(search.q ?? "");
  useEffect(() => {
    setQDraft(search.q ?? "");
  }, [search.q]);
  const qDebounced = useDebouncedValue(qDraft, 250);
  useEffect(() => {
    const next = qDebounced.trim() ? qDebounced : undefined;
    if (next === search.q) return;
    void navigate({ search: (prev) => ({ ...prev, q: next }), replace: true });
  }, [qDebounced, navigate, search.q]);

  const filtered = useMemo(() => {
    let list = search.q ? searchFigures(search.q, extras) : [...catalog];
    if (search.company) list = list.filter((f) => f.company === search.company);
    if (search.line) list = list.filter((f) => f.line === search.line);
    if (search.view === "owned") list = list.filter((f) => owned[f.id]);
    if (search.view === "missing") list = list.filter((f) => !owned[f.id]);
    if (search.view === "kits") list = list.filter((f) => f.kind === "kit");
    list.sort((a, b) => {
      if (sort === "name") {
        const byName = a.name.localeCompare(b.name);
        if (byName !== 0) return byName;
        const bySubtitle = a.subtitle.localeCompare(b.subtitle);
        if (bySubtitle !== 0) return bySubtitle;
        return a.line.localeCompare(b.line);
      }
      if (sort === "acquired") {
        const oa = owned[a.id];
        const ob = owned[b.id];
        if (!oa && !ob) return a.releaseDate < b.releaseDate ? 1 : -1;
        if (!oa) return 1;
        if (!ob) return -1;
        if (oa.addedAt !== ob.addedAt) return oa.addedAt < ob.addedAt ? 1 : -1;
        const aa = oa.acquiredDate || "";
        const ab = ob.acquiredDate || "";
        if (aa !== ab) return aa < ab ? 1 : -1;
        return a.name.localeCompare(b.name);
      }
      return a.releaseDate < b.releaseDate ? 1 : -1;
    });
    return list;
  }, [search, owned, sort, extras, catalog]);

  const ownedCount = filtered.filter((f) => owned[f.id]).length;

  return (
    <main className="flex flex-col gap-6">
      <header>
        <p className="text-xs tracking-[0.28em] text-gold uppercase">Release checklists</p>
        <h1 className="mt-1 font-display text-3xl tracking-wide uppercase">Figures & kits</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Tick what you own, add a shelf photo, and follow the weekly sold-comp estimate.
          New figures fold in automatically.
        </p>
      </header>

      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" />
        <Input
          value={qDraft}
          placeholder="Search name, line, SKU, exclusive…"
          className="pl-10"
          onChange={(e) => setQDraft(e.target.value)}
        />
      </div>

      <div className="hide-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 pb-1 md:mx-0 md:grid md:grid-cols-5 md:overflow-visible md:px-0 lg:grid-cols-8">
        <button
          type="button"
          onClick={() => navigate({ search: (prev) => ({ ...prev, company: undefined, line: undefined }) })}
          className={cn(
            "min-w-28 rounded-md px-3 py-3 text-left text-sm shadow-[var(--shadow-border)] md:min-w-0",
            !search.company ? "bg-surface text-fg" : "bg-bg-elevated text-muted",
          )}
        >
          All
          <span className="mt-1 block tabular text-xs">{catalog.length}</span>
        </button>
        {COMPANIES.map((c) => {
          const total = catalog.filter((f) => f.company === c.id).length;
          const have = catalog.filter((f) => f.company === c.id && owned[f.id]).length;
          return (
            <button
              key={c.id}
              type="button"
              onClick={() =>
                navigate({
                  search: (prev) => ({
                    ...prev,
                    company: prev.company === c.id ? undefined : c.id,
                    line: undefined,
                  }),
                })
              }
              className={cn(
                "min-w-28 rounded-md px-3 py-3 text-left shadow-[var(--shadow-border)] md:min-w-0",
                search.company === c.id ? "bg-surface text-fg" : "bg-bg-elevated text-muted",
              )}
            >
              <span className="flex items-center gap-2 text-sm font-medium text-fg">
                <span className="size-2 rounded-full" style={{ background: c.accent }} />
                {c.short}
              </span>
              <span className="mt-1 block tabular text-xs">
                {have}/{total}
              </span>
            </button>
          );
        })}
      </div>

      {company ? (
        <div className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
          <p className="text-sm text-muted">{company.blurb}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <FilterChip
              active={!search.line}
              onClick={() => navigate({ search: (prev) => ({ ...prev, line: undefined }) })}
            >
              All lines
            </FilterChip>
            {lines.map((line) => (
              <FilterChip
                key={line}
                active={search.line === line}
                onClick={() =>
                  navigate({ search: (prev) => ({ ...prev, line: prev.line === line ? undefined : line }) })
                }
              >
                {line}
              </FilterChip>
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        {(["all", "owned", "missing", "kits"] as const).map((view) => (
          <FilterChip
            key={view}
            active={(search.view ?? "all") === view}
            onClick={() =>
              navigate({ search: (prev) => ({ ...prev, view: view === "all" ? undefined : view }) })
            }
          >
            {VIEW_LABEL[view]}
          </FilterChip>
        ))}
        <span className="hidden h-5 w-px bg-border sm:block" />
        {(["release", "name", "acquired"] as const).map((s) => (
          <FilterChip
            key={s}
            active={sort === s}
            onClick={() => navigate({ search: (prev) => ({ ...prev, sort: s === "release" ? undefined : s }) })}
          >
            {SORT_LABEL[s]}
          </FilterChip>
        ))}
        <div className="ml-auto flex items-center gap-1">
          <button
            type="button"
            aria-label="Grid"
            onClick={() => navigate({ search: (prev) => ({ ...prev, layout: undefined }) })}
            className={cn(
              "inline-flex size-11 items-center justify-center rounded-sm",
              layout === "grid" ? "bg-surface text-fg" : "text-muted",
            )}
          >
            <LayoutGrid className="size-4" />
          </button>
          <button
            type="button"
            aria-label="Checklist"
            onClick={() => navigate({ search: (prev) => ({ ...prev, layout: "list" }) })}
            className={cn(
              "inline-flex size-11 items-center justify-center rounded-sm",
              layout === "list" ? "bg-surface text-fg" : "text-muted",
            )}
          >
            <List className="size-4" />
          </button>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Progress value={filtered.length ? (ownedCount / filtered.length) * 100 : 0} />
        <span className="shrink-0 text-xs text-muted tabular">
          {ownedCount} of {filtered.length}
        </span>
      </div>

      {layout === "list" ? (
        <VirtualGrid
          items={filtered}
          getKey={(figure) => figure.id}
          columns={FIGURE_LIST_COLUMNS}
          estimateRowHeight={80}
          gapClassName="gap-2"
          renderItem={(figure) => {
            const have = Boolean(owned[figure.id]);
            const est = figureMarket(figure).estimate;
            return (
              <div className="flex items-center gap-3 rounded-lg bg-bg-elevated p-2 shadow-[var(--shadow-border)]">
                <Link to="/figures/$figureId" params={{ figureId: figure.id }} className="shrink-0">
                  <FigureArt figure={figure} photo={owned[figure.id]?.photoDataUrl} caption={false} className="h-16 w-14 rounded-sm" />
                </Link>
                <div className="min-w-0 flex-1">
                  <Link to="/figures/$figureId" params={{ figureId: figure.id }} className="font-medium">
                    {figure.name}
                  </Link>
                  <p className="truncate text-xs text-muted">
                    {figure.line} · {figure.subtitle}
                  </p>
                </div>
                <p className="hidden tabular text-sm text-gold sm:block">{usd(est)}</p>
                <Button size="sm" variant={have ? "secondary" : "default"} onClick={() => setAdding(figure)}>
                  {have ? "Edit" : "Add"}
                </Button>
              </div>
            );
          }}
        />
      ) : (
        <VirtualGrid
          items={filtered}
          getKey={(figure) => figure.id}
          columns={FIGURE_GRID_COLUMNS}
          estimateRowHeight={420}
          renderItem={(figure) => {
            const have = Boolean(owned[figure.id]);
            const want = Boolean(wanted[figure.id]);
            const est = figureMarket(figure).estimate;
            return (
              <div className="overflow-hidden rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]">
                <Link to="/figures/$figureId" params={{ figureId: figure.id }} className="block">
                  <FigureArt figure={figure} photo={owned[figure.id]?.photoDataUrl} caption={false} className="aspect-4/5" />
                </Link>
                <div className="grid gap-2 p-3">
                  <div className="flex flex-wrap gap-1">
                    {have ? <Badge tone="gain">In vault</Badge> : null}
                    {want && !have ? <Badge tone="gold">Wanted</Badge> : null}
                    {figure.kind === "kit" ? <Badge>Kit</Badge> : null}
                  </div>
                  <div>
                    <p className="text-xs text-muted">{figure.line}</p>
                    <p className="font-medium leading-snug">{figure.name}</p>
                    <p className="text-xs text-subtle">{figure.subtitle}</p>
                  </div>
                  <div className="flex items-end justify-between gap-2">
                    <p className="tabular text-sm text-gold">{usd(est)}</p>
                    <p className="tabular text-xs text-subtle">MSRP {usd(figure.msrp)}</p>
                  </div>
                  <Button size="sm" variant={have ? "secondary" : "default"} onClick={() => setAdding(figure)}>
                    {have ? "Edit entry" : "Add to vault"}
                  </Button>
                </div>
              </div>
            );
          }}
        />
      )}

      {filtered.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted">No releases match those filters.</p>
      ) : null}

      {adding ? (
        <AddFigureDialog figure={adding} open onOpenChange={(v) => !v && setAdding(null)} />
      ) : null}
    </main>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "h-10 rounded-full px-3 text-xs font-medium tracking-wide uppercase",
        active ? "bg-primary text-primary-fg" : "bg-surface text-muted",
      )}
    >
      {children}
    </button>
  );
}

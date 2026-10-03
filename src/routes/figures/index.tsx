import { useEffect, useMemo, useState, type ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { LayoutGrid, List, Search } from "lucide-react";
import { COMPANIES } from "@/data/companies";
import { AddFigureDialog } from "@/components/add-figure-dialog";
import { loadCatalogJson, loadFigureBrowse } from "@/lib/catalog-client";
import { mergeFiguresInto, searchFigureList } from "@/lib/catalog-search";
import type { FigureBrowseIndex } from "@/lib/catalog-shard";
import { collapseFigureSets } from "@/lib/figure-sets";
import {
  POPULAR_FRANCHISES,
  TRANSFORMERS_PARTIES,
  figureMatchesFranchise,
  isFigureProperty,
  isTransformersParty,
  type FranchiseBrowseIndex,
} from "@/lib/figure-property";
import { FigureArt } from "@/components/figure-art";
import { VirtualGrid } from "@/components/virtual-grid";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { usdOrDash } from "@/lib/format";
import { useEnsureFigureLibrary, useFigureExtras, useLiveFigures } from "@/lib/live-store";
import { msrpPrice } from "@/lib/vault-math";
import { useVault } from "@/lib/store";
import type { CatalogFigure, CompanyId, FigureProperty, TransformersParty } from "@/lib/types";
import { cn } from "@/lib/utils";

type Search = {
  company?: CompanyId;
  q?: string;
  line?: string;
  view?: "all" | "owned" | "missing" | "kits";
  sort?: "release" | "name" | "acquired";
  layout?: "grid" | "list";
  property?: FigureProperty;
  party?: TransformersParty;
};

export const Route = createFileRoute("/figures/")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    company: typeof s.company === "string" ? (s.company as CompanyId) : undefined,
    q: typeof s.q === "string" ? s.q : undefined,
    line: typeof s.line === "string" ? s.line : undefined,
    view: s.view === "owned" || s.view === "missing" || s.view === "kits" || s.view === "all" ? s.view : undefined,
    sort: s.sort === "name" || s.sort === "acquired" || s.sort === "release" ? s.sort : undefined,
    layout: s.layout === "list" || s.layout === "grid" ? s.layout : undefined,
    property: isFigureProperty(s.property) ? s.property : undefined,
    party: isTransformersParty(s.party) ? s.party : undefined,
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
  const live = useLiveFigures();
  useEnsureFigureLibrary(live);
  const extras = useFigureExtras();
  const [adding, setAdding] = useState<CatalogFigure | null>(null);
  const [browseIndex, setBrowseIndex] = useState<FigureBrowseIndex | null>(null);
  const [scopeFigures, setScopeFigures] = useState<CatalogFigure[] | null>(null);
  const [loadedScope, setLoadedScope] = useState("");

  useEffect(() => {
    let cancel = false;
    loadFigureBrowse()
      .then((index) => {
        if (cancel) return;
        if (!index || Array.isArray(index) || !Array.isArray(index.companies)) {
          setBrowseIndex({ total: 0, companies: [], franchises: [], parts: [] });
          return;
        }
        setBrowseIndex(index);
      })
      .catch(() => {
        if (!cancel) setBrowseIndex({ total: 0, companies: [], franchises: [], parts: [] });
      });
    return () => {
      cancel = true;
    };
  }, []);

  const scopePaths = useMemo(() => figureScopePaths(browseIndex, search), [browseIndex, search]);
  const scopeKey = scopePaths?.join("|") ?? "";

  useEffect(() => {
    if (!scopePaths) return;
    let cancel = false;
    const key = scopePaths.join("|");
    Promise.all(scopePaths.map((path) => loadCatalogJson<CatalogFigure[]>(path))).then((parts) => {
      if (cancel) return;
      setScopeFigures(parts.flatMap((part) => (Array.isArray(part) ? part : [])));
      setLoadedScope(key);
    });
    return () => {
      cancel = true;
    };
  }, [scopePaths]);

  const scopeReady = Boolean(scopeFigures && loadedScope === scopeKey);
  const catalog = useMemo(
    () => (scopeReady && scopeFigures ? mergeFiguresInto(scopeFigures, extras) : []),
    [scopeReady, scopeFigures, extras],
  );
  const franchiseCounts = useMemo(() => {
    const counts = new Map<FigureProperty, number>();
    for (const franchise of browseIndex?.franchises ?? []) {
      counts.set(franchise.id as FigureProperty, franchise.count);
    }
    return counts;
  }, [browseIndex]);
  const browseParty = search.property === "transformers" ? search.party : undefined;
  const ownedByCompany = useMemo(() => {
    const map = new Map<string, number>();
    if (!scopeReady) return map;
    for (const figure of catalog) {
      if (!owned[figure.id]) continue;
      map.set(figure.company, (map.get(figure.company) ?? 0) + 1);
    }
    return map;
  }, [catalog, owned, scopeReady]);
  const browse = useMemo(
    () =>
      browseIndex
        ? railsFromBrowse(browseIndex, search.property, browseParty, ownedByCompany)
        : {
            total: 0,
            byCompany: new Map<string, { total: number; owned: number; lines: string[] }>(),
          },
    [browseIndex, browseParty, ownedByCompany, search.property],
  );
  const visibleCompanies = useMemo(() => {
    const withRows = (c: (typeof COMPANIES)[number]) => (browse.byCompany.get(c.id)?.total ?? 0) > 0;
    if (!search.property) {
      return COMPANIES.filter((c) => c.id !== "unbranded" || withRows(c));
    }
    return COMPANIES.filter(withRows);
  }, [browse, search.property]);
  const company = (search.property ? visibleCompanies : COMPANIES).find((c) => c.id === search.company);
  const lines = company ? (browse.byCompany.get(company.id)?.lines ?? []) : [];

  useEffect(() => {
    if (!browseIndex) return;
    const kept = reconcileFromBrowse(
      browseIndex,
      { company: search.company, line: search.line },
      search.property,
      browseParty,
    );
    if (kept.company === search.company && kept.line === search.line) return;
    void navigate({
      search: (prev) => {
        const party = prev.property === "transformers" ? prev.party : undefined;
        const next = reconcileFromBrowse(
          browseIndex,
          { company: prev.company, line: prev.line },
          prev.property,
          party,
        );
        if (next.company === prev.company && next.line === prev.line) return prev;
        return { ...prev, company: next.company, line: next.line };
      },
      replace: true,
    });
  }, [browseIndex, browseParty, navigate, search.company, search.line, search.property]);
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
    if (!scopeReady) return [];
    let list = search.q ? searchFigureList(catalog, search.q) : [...catalog];
    if (search.company) list = list.filter((f) => f.company === search.company);
    if (search.line) list = list.filter((f) => f.line === search.line);
    if (search.view === "owned") list = list.filter((f) => owned[f.id]);
    if (search.view === "missing") list = list.filter((f) => !owned[f.id]);
    if (search.view === "kits") list = list.filter((f) => f.kind === "kit");
    if (search.property) {
      const party = search.property === "transformers" ? search.party : undefined;
      list = list.filter((f) => figureMatchesFranchise(f, search.property!, party));
    }
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
        if (!oa && !ob) {
          const byDate = a.releaseDate === b.releaseDate ? 0 : a.releaseDate < b.releaseDate ? 1 : -1;
          if (byDate !== 0) return byDate;
          return a.name.localeCompare(b.name);
        }
        if (!oa) return 1;
        if (!ob) return -1;
        if (oa.addedAt !== ob.addedAt) return oa.addedAt < ob.addedAt ? 1 : -1;
        const aa = oa.acquiredDate || "";
        const ab = ob.acquiredDate || "";
        if (aa !== ab) return aa < ab ? 1 : -1;
        return a.name.localeCompare(b.name);
      }
      if (a.releaseDate !== b.releaseDate) return a.releaseDate < b.releaseDate ? 1 : -1;
      return a.name.localeCompare(b.name);
    });
    return collapseFigureSets(list);
  }, [search, owned, sort, catalog, scopeReady]);

  const ownedCount = filtered.filter((f) => owned[f.id]).length;

  return (
    <main className="flex flex-col gap-6">
      <header>
        <h1 className="font-display text-3xl tracking-wide uppercase">Action Figures</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Tick what you own, note what you paid, and add a shelf photo.
          New action figures fold in automatically.
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

      <section className="flex flex-col gap-2" aria-label="Popular franchises">
        <h2 className="text-xs tracking-widest text-muted uppercase">Popular franchises</h2>
        <div className="hide-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
          {POPULAR_FRANCHISES.filter((franchise) => (franchiseCounts.get(franchise.id) ?? 0) > 0).map((franchise) => (
            <FilterChip
              key={franchise.id}
              active={search.property === franchise.id}
              onClick={() =>
                navigate({
                  search: (prev) => {
                    const next = prev.property === franchise.id ? undefined : franchise.id;
                    const party = next === "transformers" ? prev.party : undefined;
                    const kept = browseIndex
                      ? reconcileFromBrowse(
                          browseIndex,
                          { company: prev.company, line: undefined },
                          next,
                          party,
                        )
                      : { company: prev.company, line: undefined };
                    return {
                      ...prev,
                      property: next,
                      party,
                      company: kept.company,
                      line: undefined,
                    };
                  },
                })
              }
            >
              {franchise.label}
              <span className="ml-1 tabular opacity-80">{franchiseCounts.get(franchise.id)}</span>
            </FilterChip>
          ))}
        </div>
        {search.property === "transformers" ? (
          <div className="flex flex-wrap gap-2" aria-label="Transformers party">
            <FilterChip
              active={!search.party}
              onClick={() =>
                navigate({
                  search: (prev) => {
                    const kept = browseIndex
                      ? reconcileFromBrowse(browseIndex, { company: prev.company, line: prev.line }, "transformers")
                      : { company: prev.company, line: prev.line };
                    return { ...prev, party: undefined, company: kept.company, line: kept.line };
                  },
                })
              }
            >
              All Transformers
            </FilterChip>
            {TRANSFORMERS_PARTIES.map((party) => (
              <FilterChip
                key={party.id}
                active={search.party === party.id}
                onClick={() =>
                  navigate({
                    search: (prev) => {
                      const nextParty = prev.party === party.id ? undefined : party.id;
                      const kept = browseIndex
                        ? reconcileFromBrowse(
                            browseIndex,
                            { company: prev.company, line: prev.line },
                            "transformers",
                            nextParty,
                          )
                        : { company: prev.company, line: prev.line };
                      return {
                        ...prev,
                        property: "transformers",
                        party: nextParty,
                        company: kept.company,
                        line: kept.line,
                      };
                    },
                  })
                }
              >
                {party.label}
              </FilterChip>
            ))}
          </div>
        ) : null}
      </section>

      <div className="hide-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 pb-1 md:mx-0 md:grid md:grid-cols-5 md:overflow-visible md:px-0 lg:grid-cols-8">
        <button
          type="button"
          onClick={() =>
            navigate({
              search: (prev) => ({ ...prev, company: undefined, line: undefined }),
            })
          }
          className={cn(
            "min-w-28 rounded-md px-3 py-3 text-left text-sm shadow-[var(--shadow-border)] md:min-w-0",
            !search.company ? "bg-surface text-fg" : "bg-bg-elevated text-muted",
          )}
        >
          All
          <span className="mt-1 block tabular text-xs">{browse.total}</span>
        </button>
        {visibleCompanies.map((c) => {
          const stats = browse.byCompany.get(c.id);
          const total = stats?.total ?? 0;
          const have = stats?.owned ?? 0;
          const countsReady =
            scopeReady && (Boolean(search.property) || !search.company || search.company === c.id);
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
              {c.id === "unbranded" ? (
                <span className="mt-0.5 block text-[10px] uppercase tracking-wide text-muted">Other / KO</span>
              ) : null}
              <span className="mt-1 block tabular text-xs">
                {countsReady ? `${have}/${total}` : total}
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
          {scopeReady ? `${ownedCount} of ${filtered.length}` : "Loading releases…"}
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
                <p className="hidden tabular text-sm text-gold sm:block">MSRP {usdOrDash(msrpPrice(figure.msrp))}</p>
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
                    {figure.setRole === "parent" ? <Badge>Set</Badge> : null}
                  </div>
                  <div>
                    <p className="text-xs text-muted">{figure.line}</p>
                    <p className="font-medium leading-snug">{figure.name}</p>
                    <p className="text-xs text-subtle">{figure.subtitle}</p>
                  </div>
                  <p className="tabular text-sm text-gold">MSRP {usdOrDash(msrpPrice(figure.msrp))}</p>
                  <Button size="sm" variant={have ? "secondary" : "default"} onClick={() => setAdding(figure)}>
                    {have ? "Edit entry" : "Add to vault"}
                  </Button>
                </div>
              </div>
            );
          }}
        />
      )}

      {scopeReady && filtered.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted">No releases match those filters.</p>
      ) : null}

      {adding ? (
        <AddFigureDialog figure={adding} open onOpenChange={(v) => !v && setAdding(null)} />
      ) : null}
    </main>
  );
}

function figureScopePaths(index: FigureBrowseIndex | null, search: Search): string[] | null {
  if (!index) return null;
  if (search.property) {
    const franchise = index.franchises.find((item) => item.id === search.property);
    if (!franchise) return [];
    if (search.property === "transformers" && search.party) {
      const path = franchise.partyShards?.[search.party];
      return path ? [path] : [];
    }
    return [franchise.shard];
  }
  if (search.company) {
    const company = index.companies.find((item) => item.id === search.company);
    return company ? [company.shard] : [];
  }
  return index.parts;
}

function railsFromBrowse(
  index: FigureBrowseIndex,
  property: FigureProperty | undefined,
  party: TransformersParty | undefined,
  ownedByCompany: Map<string, number>,
): FranchiseBrowseIndex {
  const byCompany = new Map<string, { total: number; owned: number; lines: string[] }>();
  if (!property) {
    for (const company of index.companies) {
      byCompany.set(company.id, {
        total: company.total,
        owned: ownedByCompany.get(company.id) ?? 0,
        lines: company.lines.map((line) => line.name),
      });
    }
    return { total: index.total, byCompany };
  }
  const franchise = index.franchises.find((item) => item.id === property);
  if (!franchise) return { total: 0, byCompany };
  for (const company of franchise.companies) {
    const partyStat = property === "transformers" && party ? company.parties?.[party] : undefined;
    if (property === "transformers" && party && !partyStat?.total) continue;
    byCompany.set(company.id, {
      total: partyStat ? partyStat.total : company.total,
      owned: ownedByCompany.get(company.id) ?? 0,
      lines: partyStat ? partyStat.lines : company.lines,
    });
  }
  let total = 0;
  for (const row of byCompany.values()) total += row.total;
  return { total, byCompany };
}

function reconcileFromBrowse(
  index: FigureBrowseIndex,
  selection: { company?: CompanyId; line?: string },
  property?: FigureProperty,
  party?: TransformersParty,
): { company?: CompanyId; line?: string } {
  if (!property) return { company: selection.company, line: selection.line };
  if (!selection.company) return { company: undefined, line: undefined };
  const franchise = index.franchises.find((item) => item.id === property);
  const company = franchise?.companies.find((item) => item.id === selection.company);
  if (!company) return { company: undefined, line: undefined };
  if (property === "transformers" && party) {
    const partyStat = company.parties?.[party];
    if (!partyStat?.total) return { company: undefined, line: undefined };
    const lineOk = !selection.line || partyStat.lines.includes(selection.line);
    return { company: selection.company, line: lineOk ? selection.line : undefined };
  }
  const lineOk = !selection.line || company.lines.includes(selection.line);
  return { company: selection.company, line: lineOk ? selection.line : undefined };
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
      aria-pressed={active}
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

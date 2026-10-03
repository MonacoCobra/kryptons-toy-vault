import { useEffect, useMemo, useState, type ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, Camera, ChevronRight, Plus, Search } from "lucide-react";
import { comicLabel } from "@/lib/comic-label";
import { AddComicDialog } from "@/components/add-comic-dialog";
import { ComicCover } from "@/components/comic-cover";
import { VirtualGrid } from "@/components/virtual-grid";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { COMIC_FORMAT_LABELS, comicFormatLabel, isCollectedComic } from "@/lib/comic-format";
import { collectedSeriesIdentity, seriesDisplayLabel, seriesRunYearFor, type LadderSortMode } from "@/lib/comic-series";
import { useComicsLadder } from "@/lib/use-comics-ladder";
import { formatMonthYear, usdOrDash } from "@/lib/format";
import { normalizePublisher } from "@/lib/locg-import";
import { useEnsureComicLibrary, useLiveComics } from "@/lib/live-store";
import { msrpPrice } from "@/lib/vault-math";
import { useVault } from "@/lib/store";
import type { CatalogComic, ComicFormat, CustomComic } from "@/lib/types";
import { cn, slug } from "@/lib/utils";

type Search = {
  q?: string;
  publisher?: string;
  /** Series base title (display), paired with year for a run. */
  series?: string;
  /** Series run year (see src/lib/comic-series.ts). */
  year?: number;
  keys?: boolean;
  sort?: "release" | "name" | "acquired" | "issue";
  /** Publisher-scoped collected editions list (tpb / hc / omnibus). */
  section?: "collected";
};

export const Route = createFileRoute("/comics/")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    q: typeof s.q === "string" ? s.q : undefined,
    publisher: typeof s.publisher === "string" ? s.publisher : undefined,
    series: typeof s.series === "string" ? s.series : undefined,
    year:
      typeof s.year === "number" && Number.isFinite(s.year)
        ? s.year
        : typeof s.year === "string" && /^\d{1,4}$/.test(s.year)
          ? Number(s.year)
          : undefined,
    keys: s.keys === true || s.keys === "true",
    sort:
      s.sort === "name" || s.sort === "acquired" || s.sort === "release" || s.sort === "issue"
        ? s.sort
        : undefined,
    section: s.section === "collected" ? "collected" : undefined,
  }),
  component: ComicsPage,
});

const SORT_LABEL: Record<NonNullable<Search["sort"]> | "release", string> = {
  release: "Release date",
  name: "A–Z",
  acquired: "Recently acquired",
  issue: "Issue #",
};

type LadderLevel = "publishers" | "series" | "issues" | "collected" | "collected-volumes" | "search";

function ComicsPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const owned = useVault((s) => s.ownedComics);
  const wanted = useVault((s) => s.wantedComics);
  const customComics = useVault((s) => s.customComics);
  const extras = useLiveComics();
  const library = useEnsureComicLibrary(extras);
  const [adding, setAdding] = useState<CatalogComic | null>(null);
  const [customOpen, setCustomOpen] = useState(false);

  const ownedIds = useMemo(() => {
    const ids = new Set<string>();
    for (const entry of Object.values(owned)) {
      if (entry.catalogId) ids.add(entry.catalogId);
      if (entry.custom?.id) ids.add(entry.custom.id);
    }
    return ids;
  }, [owned]);

  const ownedByCatalog = useMemo(() => {
    const map = new Map<string, (typeof owned)[string]>();
    for (const entry of Object.values(owned)) {
      const key = entry.catalogId ?? entry.custom?.id ?? entry.id;
      if (!key) continue;
      const prev = map.get(key);
      if (!prev || entry.addedAt > prev.addedAt) map.set(key, entry);
    }
    return map;
  }, [owned]);

  const inCollected = search.section === "collected" && Boolean(search.publisher);
  const viewingCollectedVolumes = inCollected && Boolean(search.series);
  const sort = viewingCollectedVolumes
    ? (search.sort ?? "issue")
    : inCollected && search.sort === "issue"
      ? "release"
      : (search.sort ??
        (search.publisher && search.series && search.year != null && !inCollected ? "issue" : "release"));
  const ladderSort: LadderSortMode = sort === "name" || sort === "acquired" ? sort : "release";
  const sortDefault =
    viewingCollectedVolumes || (!inCollected && (search.publisher && search.series && search.year != null && !search.q))
      ? "issue"
      : "release";

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

  const level: LadderLevel = search.q
    ? "search"
    : viewingCollectedVolumes
      ? "collected-volumes"
      : search.publisher && search.section === "collected"
        ? "collected"
        : search.publisher && search.series && search.year != null
          ? "issues"
          : search.publisher
            ? "series"
            : "publishers";

  const {
    publishers,
    collectedCounts,
    seriesList,
    collectedSeries,
    collectedEditionCount,
    collectedFormatLabels,
    collectedSample,
    issueComics,
    collectedComics,
    filteredSearch,
    filteredNoteworthy,
    yearById,
    loadingPublishers,
    loadingDetail,
    loadingRun,
  } = useComicsLadder({
    search,
    extras,
    library,
    customComics,
    owned,
    ownedByCatalog,
    ladderSort,
    sort,
    level,
  });

  /** Volume # belongs on issue lists and inside a collected series, not on the series index. */
  const showIssueSort =
    viewingCollectedVolumes || ((level === "issues" || level === "search") && !inCollected);

  function goUp() {
    if (level === "collected-volumes") {
      void navigate({
        search: (prev) => ({
          ...prev,
          series: undefined,
          year: undefined,
          sort: undefined,
        }),
      });
      return;
    }
    if (level === "issues" || level === "collected") {
      void navigate({
        search: (prev) => ({
          ...prev,
          series: undefined,
          year: undefined,
          section: undefined,
          sort: undefined,
        }),
      });
      return;
    }
    if (level === "series") {
      void navigate({
        search: (prev) => ({
          ...prev,
          publisher: undefined,
          series: undefined,
          year: undefined,
          section: undefined,
        }),
      });
      return;
    }
    if (level === "search") {
      void navigate({ search: (prev) => ({ ...prev, q: undefined }) });
      setQDraft("");
    }
  }

  const activeCollectedSeries =
    viewingCollectedVolumes && search.series
      ? collectedSeries.find((s) => s.titleNorm === collectedSeriesIdentity(search.series).titleNorm)
      : undefined;
  const seriesHeading = activeCollectedSeries
    ? seriesDisplayLabel(activeCollectedSeries.title, activeCollectedSeries.year)
    : search.series && search.year != null
      ? seriesDisplayLabel(search.series, search.year)
      : search.series;

  return (
    <main className="flex min-w-0 max-w-full flex-col gap-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-display text-3xl tracking-wide uppercase">Comic catalog</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Browse Publisher → Series (by run year) → Issues. Same-title reboots stay split.
            Collected Editions live under each publisher, grouped by series, when that catalog has trades or omnibuses.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="secondary">
            <Link to="/scan">
              <Camera /> Scan cover
            </Link>
          </Button>
          <Button variant="outline" onClick={() => setCustomOpen(true)}>
            <Plus /> {inCollected ? "Custom collected" : "Custom issue"}
          </Button>
        </div>
      </header>

      <nav aria-label="Comics breadcrumb" className="flex flex-wrap items-center gap-1 text-xs tracking-wide uppercase">
        <Link
          to="/comics"
          search={{}}
          className={cn("text-gold hover:underline", level === "publishers" && !search.q ? "text-fg" : "")}
        >
          Comics
        </Link>
        {search.publisher ? (
          <>
            <ChevronRight className="size-3 text-muted" />
            <button
              type="button"
              className={cn(
                "text-gold hover:underline",
                level === "series" ? "text-fg" : "",
              )}
              onClick={() =>
                navigate({
                  search: (prev) => ({
                    ...prev,
                    publisher: search.publisher,
                    series: undefined,
                    year: undefined,
                    section: undefined,
                    q: undefined,
                  }),
                })
              }
            >
              {search.publisher}
            </button>
          </>
        ) : null}
        {level === "collected" || level === "collected-volumes" ? (
          <>
            <ChevronRight className="size-3 text-muted" />
            {level === "collected-volumes" ? (
              <button
                type="button"
                className="text-gold hover:underline"
                onClick={() =>
                  navigate({
                    search: (prev) => ({
                      ...prev,
                      publisher: search.publisher,
                      section: "collected",
                      series: undefined,
                      year: undefined,
                      q: undefined,
                      sort: undefined,
                    }),
                  })
                }
              >
                Collected Editions
              </button>
            ) : (
              <span className="text-fg">Collected Editions</span>
            )}
          </>
        ) : null}
        {level === "collected-volumes" && search.series ? (
          <>
            <ChevronRight className="size-3 text-muted" />
            <span className="min-w-0 break-words text-fg">{seriesHeading}</span>
          </>
        ) : null}
        {search.series && search.year != null && level !== "collected" && level !== "collected-volumes" ? (
          <>
            <ChevronRight className="size-3 text-muted" />
            <span className="text-fg">{seriesHeading}</span>
          </>
        ) : null}
        {search.q ? (
          <>
            <ChevronRight className="size-3 text-muted" />
            <span className="normal-case tracking-normal text-fg">Search “{search.q}”</span>
          </>
        ) : null}
      </nav>

      {level !== "publishers" || search.q ? (
        <div>
          <Button variant="ghost" size="sm" onClick={goUp}>
            <ArrowLeft /> Back
          </Button>
        </div>
      ) : null}

      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" />
        <Input
          value={qDraft}
          placeholder="Amazing Spider-Man 300, Death of Superman Compendium, Saga…"
          className="pl-10"
          onChange={(e) => setQDraft(e.target.value)}
        />
      </div>

      <div className="hide-scrollbar -mx-4 flex flex-wrap gap-2 overflow-x-auto px-4 md:mx-0 md:px-0">
        <FilterChip
          active={Boolean(search.keys)}
          onClick={() => navigate({ search: (prev) => ({ ...prev, keys: prev.keys ? undefined : true }) })}
        >
          Keys only
        </FilterChip>
        {(showIssueSort
          ? (["issue", "release", "name", "acquired"] as const)
          : (["release", "name", "acquired"] as const)
        ).map((s) => (
          <FilterChip
            key={s}
            active={sort === s}
            onClick={() =>
              navigate({
                search: (prev) => ({
                  ...prev,
                  sort: s === sortDefault ? undefined : s,
                }),
              })
            }
          >
            {s === "issue" && viewingCollectedVolumes ? "Volume #" : SORT_LABEL[s]}
          </FilterChip>
        ))}
      </div>

      {level === "publishers" ? (
        <>
          <section className="flex flex-col gap-3">
            <div>
              <h2 className="font-display text-lg tracking-wide uppercase">Publishers</h2>
              <p className="mt-1 text-xs text-muted">Step 1 of the ladder — pick a publisher to open its series.</p>
            </div>
            {loadingPublishers ? (
              <p className="rounded-lg bg-bg-elevated px-4 py-6 text-sm text-muted shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
                Loading publishers…
              </p>
            ) : publishers.length === 0 ? (
              <p className="rounded-lg bg-bg-elevated px-4 py-6 text-sm text-muted shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
                No publishers in this catalog slice yet.
              </p>
            ) : (
              <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3" data-sort={sort}>
                {publishers.map((p) => {
                  const collectedCount = collectedCounts.get(normalizePublisher(p.publisher)) ?? 0;
                  return (
                    <li key={p.publisher}>
                      <button
                        type="button"
                        onClick={() =>
                          navigate({
                            search: (prev) => ({
                              ...prev,
                              publisher: p.publisher,
                              series: undefined,
                              year: undefined,
                              section: undefined,
                              q: undefined,
                            }),
                          })
                        }
                        className="flex w-full items-center justify-between gap-3 rounded-lg bg-bg-elevated px-4 py-3 text-left shadow-[0_0_0_1px_rgba(214,230,255,0.08)] transition-colors hover:bg-surface"
                      >
                        <span className="min-w-0">
                          <span className="block truncate font-medium">{p.publisher}</span>
                          <span className="text-xs text-muted">
                            {p.seriesCount} series · {p.issueCount} issues
                            {collectedCount
                              ? ` · ${collectedCount} collected`
                              : ""}
                          </span>
                        </span>
                        <ChevronRight className="size-4 shrink-0 text-muted" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          <section className="flex flex-col gap-3">
            <div>
              <h2 className="font-display text-lg tracking-wide uppercase">New &amp; noteworthy</h2>
              <p className="mt-1 text-xs text-muted">
                Fresh street-week titles. They still live under their publisher ladder above.
              </p>
            </div>
            {filteredNoteworthy.length ? (
              <ComicGrid
                comics={filteredNoteworthy}
                ownedIds={ownedIds}
                wanted={wanted}
                onAdd={setAdding}
                yearById={yearById}
              />
            ) : (
              <p className="rounded-lg bg-bg-elevated px-4 py-6 text-sm text-muted shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
                No fresh releases in the window yet — check back after Wednesday&apos;s street day.
              </p>
            )}
          </section>
        </>
      ) : null}

      {level === "series" ? (
        <>
          {collectedEditionCount > 0 ? (
            <section className="flex flex-col gap-3">
              <div>
                <h2 className="font-display text-lg tracking-wide uppercase">Collected Editions</h2>
                <p className="mt-1 text-xs text-muted">
                  Trades, hardcovers, and omnibuses from this publisher — grouped by series, off the singles ladder.
                </p>
              </div>
              <button
                type="button"
                onClick={() =>
                  navigate({
                    search: (prev) => ({
                      ...prev,
                      publisher: search.publisher,
                      series: undefined,
                      year: undefined,
                      q: undefined,
                      sort: undefined,
                      section: "collected",
                    }),
                  })
                }
                className="flex w-full min-w-0 items-center gap-3 rounded-lg bg-bg-elevated p-2 text-left shadow-[0_0_0_1px_rgba(214,230,255,0.08)] transition-colors hover:bg-surface"
              >
                {collectedSample ? (
                  <ComicCover
                    comic={collectedSample}
                    resolveRemote
                    className="h-16 w-11 shrink-0 rounded-sm"
                  />
                ) : (
                  <div className="h-16 w-11 shrink-0 rounded-sm bg-surface" />
                )}
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">Collected Editions</span>
                  <span className="text-xs text-muted">
                    {collectedEditionCount} edition{collectedEditionCount === 1 ? "" : "s"}
                    {collectedSeries.length
                      ? ` · ${collectedSeries.length} series`
                      : ""}
                  </span>
                </span>
                <span className="flex flex-wrap justify-end gap-1">
                  {collectedFormatLabels.map((label) => (
                    <Badge key={label} tone="ice">
                      {label}
                    </Badge>
                  ))}
                </span>
                <ChevronRight className="size-4 shrink-0 text-muted" />
              </button>
            </section>
          ) : null}
          <section className="flex flex-col gap-3">
            <div>
              <h2 className="font-display text-lg tracking-wide uppercase">Series · {search.publisher}</h2>
              <p className="mt-1 text-xs text-muted">
                Runs are split by start year so reboots do not merge. {seriesList.length} series.
              </p>
            </div>
            {loadingDetail ? (
              <p className="rounded-lg bg-bg-elevated px-4 py-6 text-sm text-muted shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
                Loading series…
              </p>
            ) : seriesList.length === 0 ? (
              <p className="rounded-lg bg-bg-elevated px-4 py-6 text-sm text-muted shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
                No series under this publisher yet.
              </p>
            ) : (
              <div data-sort={sort} data-testid="series-list" className="min-w-0 max-w-full">
                <VirtualGrid
                  items={seriesList}
                  getKey={(s) => s.key}
                  columns={COLLECTED_SERIES_COLUMNS}
                  estimateRowHeight={92}
                  gapClassName="gap-2"
                  renderItem={(s) => (
                    <button
                      type="button"
                      onClick={() =>
                        navigate({
                          search: (prev) => ({
                            ...prev,
                            publisher: s.publisher,
                            series: s.title,
                            year: s.year,
                            q: undefined,
                            sort: undefined,
                            section: undefined,
                          }),
                        })
                      }
                      className="flex w-full items-center gap-3 rounded-lg bg-bg-elevated p-2 text-left shadow-[0_0_0_1px_rgba(214,230,255,0.08)] transition-colors hover:bg-surface"
                    >
                      {s.sample ? (
                        <ComicCover comic={s.sample} resolveRemote className="h-16 w-11 shrink-0 rounded-sm" />
                      ) : (
                        <div className="h-16 w-11 shrink-0 rounded-sm bg-surface" />
                      )}
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{seriesDisplayLabel(s.title, s.year)}</span>
                        <span className="text-xs text-muted">
                          {s.issueCount} issue{s.issueCount === 1 ? "" : "s"}
                        </span>
                      </span>
                      {s.year ? <Badge tone="gold">{s.year}</Badge> : <Badge>Unknown</Badge>}
                      <ChevronRight className="size-4 shrink-0 text-muted" />
                    </button>
                  )}
                />
              </div>
            )}
          </section>
        </>
      ) : null}

      {level === "issues" ? (
        <section className="flex flex-col gap-3">
          <div>
            <h2 className="font-display text-lg tracking-wide uppercase">{seriesHeading}</h2>
            <p className="mt-1 text-xs text-muted">
              {search.publisher} · sorted by {SORT_LABEL[sort].toLowerCase()} · {issueComics.length} shown
            </p>
          </div>
          {loadingRun ? (
            <p className="rounded-lg bg-bg-elevated px-4 py-6 text-sm text-muted shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
              Loading issues…
            </p>
          ) : (
          <ComicGrid
            comics={issueComics}
            ownedIds={ownedIds}
            wanted={wanted}
            onAdd={setAdding}
            yearById={yearById}
            emptyAction={() => setCustomOpen(true)}
            showSeriesYear={false}
          />
          )}
        </section>
      ) : null}

      {level === "collected" ? (
        <section className="flex min-w-0 max-w-full flex-col gap-3">
          <div>
            <h2 className="font-display text-lg tracking-wide uppercase">Collected Editions</h2>
            <p className="mt-1 text-xs text-muted">
              {search.publisher} · grouped by series · {collectedSeries.length} series ·{" "}
              {collectedEditionCount} edition{collectedEditionCount === 1 ? "" : "s"}
            </p>
          </div>
          {collectedSeries.length === 0 ? (
            <ComicGrid
              comics={[]}
              ownedIds={ownedIds}
              wanted={wanted}
              onAdd={setAdding}
              yearById={yearById}
              emptyAction={() => setCustomOpen(true)}
              collectedEmpty
            />
          ) : (
            <div data-testid="collected-series-list" className="min-w-0 max-w-full">
              <VirtualGrid
                items={collectedSeries}
                getKey={(s) => s.key}
                columns={COLLECTED_SERIES_COLUMNS}
                estimateRowHeight={92}
                gapClassName="gap-2"
                renderItem={(s) => (
                  <button
                    type="button"
                    onClick={() =>
                      navigate({
                        search: (prev) => ({
                          ...prev,
                          publisher: search.publisher,
                          section: "collected",
                          series: s.title,
                          year: undefined,
                          q: undefined,
                          sort: undefined,
                        }),
                      })
                    }
                    className="flex w-full min-w-0 max-w-full items-center gap-3 rounded-lg bg-bg-elevated p-2 text-left shadow-[0_0_0_1px_rgba(214,230,255,0.08)] transition-colors hover:bg-surface"
                  >
                    {s.sample ? (
                      <ComicCover comic={s.sample} resolveRemote className="h-16 w-11 shrink-0 rounded-sm" />
                    ) : (
                      <div className="h-16 w-11 shrink-0 rounded-sm bg-surface" />
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{seriesDisplayLabel(s.title, s.year)}</span>
                      <span className="text-xs text-muted">
                        {s.issueCount} volume{s.issueCount === 1 ? "" : "s"}
                      </span>
                    </span>
                    {s.year ? <Badge tone="gold">{s.year}</Badge> : <Badge>Unknown</Badge>}
                    <ChevronRight className="size-4 shrink-0 text-muted" />
                  </button>
                )}
              />
            </div>
          )}
        </section>
      ) : null}

      {level === "collected-volumes" ? (
        <section className="flex min-w-0 max-w-full flex-col gap-3">
          <div>
            <h2 className="font-display text-lg tracking-wide uppercase">{seriesHeading}</h2>
            <p className="mt-1 text-xs text-muted">
              {search.publisher} · sorted by{" "}
              {(sort === "issue" ? "volume #" : SORT_LABEL[sort]).toLowerCase()} · {collectedComics.length} shown
            </p>
          </div>
          <ComicGrid
            comics={collectedComics}
            ownedIds={ownedIds}
            wanted={wanted}
            onAdd={setAdding}
            yearById={yearById}
            emptyAction={() => setCustomOpen(true)}
            collectedEmpty={!search.keys}
            showCollectedMeta
          />
        </section>
      ) : null}

      {level === "search" ? (
        <ComicGrid
          comics={filteredSearch}
          ownedIds={ownedIds}
          wanted={wanted}
          onAdd={setAdding}
          yearById={yearById}
          emptyAction={() => setCustomOpen(true)}
        />
      ) : null}

      {adding ? (
        <AddComicDialog
          comic={adding.id.startsWith("custom-") ? undefined : adding}
          custom={adding.id.startsWith("custom-") ? customComics[adding.id] : undefined}
          open
          onOpenChange={(v) => !v && setAdding(null)}
        />
      ) : null}
      <CustomComicDialog open={customOpen} onOpenChange={setCustomOpen} collected={inCollected} />
    </main>
  );
}

const COMIC_GRID_COLUMNS = { base: 2, md: 4, lg: 5 } as const;
const COLLECTED_SERIES_COLUMNS = { base: 1, md: 1, lg: 1 } as const;

function ComicGrid({
  comics,
  ownedIds,
  wanted,
  onAdd,
  yearById,
  emptyAction,
  showSeriesYear = true,
  collectedEmpty = false,
  showCollectedMeta = false,
}: {
  comics: CatalogComic[];
  ownedIds: Set<string>;
  wanted: Record<string, unknown>;
  onAdd: (c: CatalogComic) => void;
  yearById: Map<string, number>;
  emptyAction?: () => void;
  showSeriesYear?: boolean;
  collectedEmpty?: boolean;
  showCollectedMeta?: boolean;
}) {
  if (!comics.length) {
    if (!emptyAction) return null;
    return (
      <div className="rounded-xl bg-bg-elevated p-8 text-center shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
        <p className="font-display text-xl tracking-wide uppercase">
          {collectedEmpty ? "No collected editions yet" : "No matches"}
        </p>
        <p className="mt-2 text-sm text-muted">
          {collectedEmpty
            ? "Trades, hardcovers, and omnibuses will appear here as the catalog grows. Add a custom collected book if you already own one."
            : "Add it as a custom issue."}
        </p>
        <Button className="mt-4" onClick={emptyAction}>
          {collectedEmpty ? "Add custom collected" : "Add custom issue"}
        </Button>
      </div>
    );
  }

  return (
    <VirtualGrid
      items={comics}
      getKey={(comic) => comic.id}
      columns={COMIC_GRID_COLUMNS}
      estimateRowHeight={360}
      renderItem={(comic) => {
        const have = ownedIds.has(comic.id);
        const want = Boolean(wanted[comic.id]);
        const year = seriesRunYearFor(comic, yearById);
        const isCustom = comic.id.startsWith("custom-");
        const cover = <ComicCover comic={comic} resolveRemote className="aspect-2/3" />;
        return (
          <div className="overflow-hidden rounded-lg bg-bg-elevated shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
            {isCustom ? (
              <button type="button" className="block w-full" onClick={() => onAdd(comic)}>
                {cover}
              </button>
            ) : (
              <Link to="/comics/$comicId" params={{ comicId: comic.id }} className="block">
                {cover}
              </Link>
            )}
            <div className="grid gap-1.5 p-3">
              <p className="line-clamp-2 text-sm font-medium">{comicLabel(comic)}</p>
              <p className="text-xs text-muted">
                {comic.publisher}
                {showCollectedMeta
                  ? ` · ${formatMonthYear(comic.streetDate ?? comic.coverDate)}`
                  : showSeriesYear && year
                    ? ` · ${year}`
                    : ""}
              </p>
              <div className="flex flex-wrap gap-1">
                {have ? <Badge tone="gain">Owned</Badge> : null}
                {want && !have ? <Badge tone="gold">Wanted</Badge> : null}
                {comic.key ? <Badge tone="red">Key</Badge> : null}
                {isCollectedComic(comic) ? <Badge tone="ice">{comicFormatLabel(comic.format)}</Badge> : null}
                {isCustom ? <Badge>Custom</Badge> : null}
              </div>
              <div className="flex items-center justify-between">
                <span className="tabular text-sm text-gold">{usdOrDash(msrpPrice(comic.msrp))}</span>
                <Button size="sm" variant="ghost" onClick={() => onAdd(comic)}>
                  {have ? "Edit" : "Add"}
                </Button>
              </div>
            </div>
          </div>
        );
      }}
    />
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
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "h-10 rounded-full px-3 text-xs font-medium tracking-wide",
        active ? "bg-primary text-primary-fg" : "bg-surface text-muted",
      )}
    >
      {children}
    </button>
  );
}

function CustomComicDialog({
  open,
  onOpenChange,
  collected = false,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  collected?: boolean;
}) {
  const [series, setSeries] = useState("");
  const [issue, setIssue] = useState("");
  const [publisher, setPublisher] = useState("");
  const [coverDate, setCoverDate] = useState("");
  const [msrp, setMsrp] = useState("");
  const [format, setFormat] = useState<ComicFormat>(collected ? "tpb" : "single");
  const [variant, setVariant] = useState("");
  const [draft, setDraft] = useState<CustomComic | null>(null);

  useEffect(() => {
    if (!open) return;
    setFormat(collected ? "tpb" : "single");
  }, [open, collected]);

  function next() {
    if (!series.trim()) return;
    const custom: CustomComic = {
      id: `custom-${slug(series)}-${slug(issue || "nn")}-${Date.now()}`,
      series: series.trim(),
      issue: issue.trim() || "nn",
      publisher: publisher.trim() || "Unknown",
      coverDate: coverDate || undefined,
      msrp: Number(msrp) > 0 ? Number(msrp) : undefined,
      format,
      variant: variant.trim() || undefined,
    };
    setDraft(custom);
  }

  return (
    <>
      <Dialog open={open && !draft} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{collected ? "Custom collected" : "Custom issue"}</DialogTitle>
            <DialogDescription>
              {collected
                ? "For a trade, hardcover, or omnibus the catalog does not carry yet."
                : "For books the catalog does not carry yet."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <Field label="Series" value={series} onChange={setSeries} placeholder="Action Comics" />
            <Field label="Issue" value={issue} onChange={setIssue} placeholder="1" />
            <Field label="Publisher" value={publisher} onChange={setPublisher} placeholder="DC Comics" />
            <div className="grid gap-1.5">
              <Label>Cover date</Label>
              <Input type="date" value={coverDate} onChange={(e) => setCoverDate(e.target.value)} />
            </div>
            <Field label="Cover price" value={msrp} onChange={setMsrp} />
            <div className="grid gap-1.5">
              <Label>Format</Label>
              <Select value={format} onValueChange={(v) => setFormat(v as ComicFormat)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(["single", "annual", "tpb", "hc", "omnibus", "facsimile"] as const).map((f) => (
                    <SelectItem key={f} value={f}>
                      {COMIC_FORMAT_LABELS[f]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Field label="Variant (optional)" value={variant} onChange={setVariant} placeholder="Cover B" />
            <Button onClick={next} disabled={!series.trim()}>
              Continue
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      {draft ? (
        <AddComicDialog
          custom={draft}
          open
          onOpenChange={(v) => {
            if (!v) {
              setDraft(null);
              onOpenChange(false);
            }
          }}
        />
      ) : null}
    </>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="grid gap-1.5">
      <Label>{label}</Label>
      <Input value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

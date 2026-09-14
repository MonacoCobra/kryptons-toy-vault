import { useEffect, useMemo, useState, type ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, Camera, ChevronRight, Plus, Search } from "lucide-react";
import { comicLabel, mergeComics, searchComics } from "@/data/comics";
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
import { libraryCatalogRows, splitComicsClient } from "@/lib/comic-catalog";
import {
  catalogFromCustom,
  COMIC_FORMAT_LABELS,
  comicFormatLabel,
  filterCollectedComics,
  filterIssueComics,
  isCollectedComic,
} from "@/lib/comic-format";
import {
  assignSeriesRunYears,
  buildPublisherList,
  buildSeriesList,
  collectedCountByPublisher,
  collectedForPublisher,
  comicMatchesSeries,
  comicReleaseDate,
  makeSeriesKey,
  seriesDisplayLabel,
  seriesRunYearFor,
  sortCatalogComics,
  sortPublisherList,
  sortSeriesList,
  type LadderSortMode,
} from "@/lib/comic-series";
import { collapseComicVariants } from "@/lib/comic-variants";
import { formatMonthYear, usd } from "@/lib/format";
import { normalizePublisher } from "@/lib/locg-import";
import { useEnsureComicLibrary, useLiveComics } from "@/lib/live-store";
import { comicEstimate } from "@/lib/market";
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

type LadderLevel = "publishers" | "series" | "issues" | "collected" | "search";

function ComicsPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const owned = useVault((s) => s.ownedComics);
  const wanted = useVault((s) => s.wantedComics);
  const customComics = useVault((s) => s.customComics);
  const extras = useLiveComics();
  const library = useEnsureComicLibrary(extras);
  const libraryRows = useMemo(() => libraryCatalogRows(library), [library]);
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
  const sort =
    inCollected && search.sort === "issue"
      ? "release"
      : (search.sort ??
        (search.publisher && search.series && search.year != null && !inCollected ? "issue" : "release"));
  const ladderSort: LadderSortMode = sort === "name" || sort === "acquired" ? sort : "release";

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

  const split = useMemo(() => {
    if (library) {
      return { noteworthy: library.noteworthy, archive: library.archive };
    }
    return splitComicsClient(extras);
  }, [library, extras]);

  const catalogAll = useMemo(
    () => mergeComics(extras, libraryRows),
    [extras, libraryRows],
  );

  const customCollected = useMemo(
    () => Object.values(customComics).filter(isCollectedComic).map(catalogFromCustom),
    [customComics],
  );

  const issueCatalog = useMemo(() => filterIssueComics(catalogAll), [catalogAll]);

  const collectedCatalog = useMemo(() => {
    const fromCatalog = filterCollectedComics(catalogAll);
    if (customCollected.length === 0) return fromCatalog;
    const seen = new Set(fromCatalog.map((c) => c.id));
    const extra = customCollected.filter((c) => !seen.has(c.id));
    return extra.length ? [...fromCatalog, ...extra] : fromCatalog;
  }, [catalogAll, customCollected]);

  const yearById = useMemo(() => assignSeriesRunYears(catalogAll), [catalogAll]);
  const collectedCounts = useMemo(
    () => collectedCountByPublisher(collectedCatalog),
    [collectedCatalog],
  );

  const level: LadderLevel = search.q
    ? "search"
    : search.publisher && search.section === "collected"
      ? "collected"
      : search.publisher && search.series && search.year != null
        ? "issues"
        : search.publisher
          ? "series"
          : "publishers";

  const acquiredLookups = useMemo(() => {
    const bySeries = new Map<string, string>();
    const byPublisher = new Map<string, string>();
    if (ladderSort !== "acquired") return { bySeries, byPublisher };
    const ownedList = Object.values(owned);
    if (!ownedList.length) return { bySeries, byPublisher };
    const want = new Set<string>();
    for (const entry of ownedList) {
      if (entry.catalogId) want.add(entry.catalogId);
    }
    const byId = new Map<string, CatalogComic>();
    if (want.size) {
      for (const c of catalogAll) {
        if (!want.has(c.id)) continue;
        byId.set(c.id, c);
        if (byId.size >= want.size) break;
      }
    }
    for (const entry of ownedList) {
      const comic =
        (entry.catalogId ? byId.get(entry.catalogId) : undefined) ??
        (entry.custom ? catalogFromCustom(entry.custom) : undefined);
      if (!comic) continue;
      const seriesKey = makeSeriesKey(comic.publisher, comic.series, seriesRunYearFor(comic, yearById));
      const pubKey = normalizePublisher(comic.publisher);
      if (!bySeries.has(seriesKey) || entry.addedAt > bySeries.get(seriesKey)!) {
        bySeries.set(seriesKey, entry.addedAt);
      }
      if (!byPublisher.has(pubKey) || entry.addedAt > byPublisher.get(pubKey)!) {
        byPublisher.set(pubKey, entry.addedAt);
      }
    }
    return { bySeries, byPublisher };
  }, [owned, catalogAll, yearById, ladderSort]);

  const publishers = useMemo(() => {
    const list = buildPublisherList(issueCatalog, yearById);
    const seen = new Set(list.map((p) => normalizePublisher(p.publisher)));
    const extra: typeof list = [];
    const extraIndex = new Map<string, number>();
    for (const c of collectedCatalog) {
      const key = normalizePublisher(c.publisher);
      if (seen.has(key)) continue;
      const date = comicReleaseDate(c);
      const idx = extraIndex.get(key);
      if (idx == null) {
        extraIndex.set(key, extra.length);
        extra.push({ publisher: c.publisher, seriesCount: 0, issueCount: 0, latestDate: date });
      } else if (date && date > extra[idx]!.latestDate) {
        extra[idx]!.latestDate = date;
      }
    }
    const merged = extra.length ? [...list, ...extra] : list;
    return sortPublisherList(merged, ladderSort, acquiredLookups.byPublisher);
  }, [issueCatalog, yearById, collectedCatalog, ladderSort, acquiredLookups]);

  const seriesList = useMemo(() => {
    if (!search.publisher) return [];
    const list = buildSeriesList(issueCatalog, yearById, search.publisher);
    return sortSeriesList(list, ladderSort, acquiredLookups.bySeries);
  }, [issueCatalog, yearById, search.publisher, ladderSort, acquiredLookups]);

  const publisherCollected = useMemo(() => {
    if (!search.publisher) return [];
    return collectedForPublisher(collectedCatalog, search.publisher);
  }, [collectedCatalog, search.publisher]);

  const issueComics = useMemo(() => {
    if (level !== "issues" || !search.publisher || !search.series || search.year == null) return [];
    let list = issueCatalog.filter((c) =>
      comicMatchesSeries(
        c,
        { publisher: search.publisher!, seriesTitle: search.series!, year: search.year! },
        yearById,
      ),
    );
    if (search.keys) list = list.filter((c) => c.key);
    list = collapseComicVariants(list);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [level, issueCatalog, search.publisher, search.series, search.year, search.keys, sort, yearById, ownedByCatalog]);

  const collectedComics = useMemo(() => {
    if (level !== "collected") return [];
    let list = publisherCollected;
    if (search.keys) list = list.filter((c) => c.key);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [level, publisherCollected, search.keys, sort, ownedByCatalog]);

  const filteredSearch = useMemo(() => {
    if (level !== "search") return [];
    let list = searchComics(search.q!, extras, libraryRows);
    const q = search.q!.trim().toLowerCase();
    const customHits = customCollected.filter((c) => {
      const hay = `${c.series} ${c.issue} ${c.publisher} ${c.upc ?? ""} ${c.format} ${c.description}`.toLowerCase();
      return hay.includes(q);
    });
    const seen = new Set(list.map((c) => c.id));
    for (const c of customHits) {
      if (!seen.has(c.id)) list.push(c);
    }
    if (search.publisher) {
      const want = normalizePublisher(search.publisher);
      list = list.filter((c) => normalizePublisher(c.publisher) === want);
    }
    if (search.section === "collected") {
      list = filterCollectedComics(list);
    }
    if (search.series && search.year != null) {
      list = list.filter((c) =>
        comicMatchesSeries(
          c,
          { publisher: search.publisher ?? c.publisher, seriesTitle: search.series!, year: search.year! },
          yearById,
        ),
      );
    } else if (search.series) {
      list = list.filter((c) => c.series === search.series);
    }
    if (search.keys) list = list.filter((c) => c.key);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [level, search, extras, libraryRows, customCollected, sort, yearById, ownedByCatalog]);

  const filteredNoteworthy = useMemo(() => {
    if (level !== "publishers") return [];
    let list = filterIssueComics(split.noteworthy);
    if (search.keys) list = list.filter((c) => c.key);
    list = collapseComicVariants(list);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [level, split.noteworthy, search.keys, sort, ownedByCatalog]);

  function goUp() {
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

  const seriesHeading =
    search.series && search.year != null ? seriesDisplayLabel(search.series, search.year) : search.series;

  return (
    <main className="flex flex-col gap-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-display text-3xl tracking-wide uppercase">Comic catalog</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Browse Publisher → Series (by run year) → Issues. Same-title reboots stay split.
            Collected Editions live under each publisher when that catalog has trades or omnibuses.
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
        {level === "collected" ? (
          <>
            <ChevronRight className="size-3 text-muted" />
            <span className="text-fg">Collected Editions</span>
          </>
        ) : null}
        {search.series && search.year != null && level !== "collected" ? (
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
        {(inCollected
          ? (["release", "name", "acquired"] as const)
          : level === "issues" || level === "search"
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
                  sort: s === (inCollected || level !== "issues" ? "release" : "issue") ? undefined : s,
                }),
              })
            }
          >
            {SORT_LABEL[s]}
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
            {publishers.length === 0 ? (
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
          {publisherCollected.length > 0 ? (
            <section className="flex flex-col gap-3">
              <div>
                <h2 className="font-display text-lg tracking-wide uppercase">Collected Editions</h2>
                <p className="mt-1 text-xs text-muted">
                  Trades, hardcovers, and omnibuses from this publisher — kept off the series ladder.
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
                className="flex w-full items-center gap-3 rounded-lg bg-bg-elevated p-2 text-left shadow-[0_0_0_1px_rgba(214,230,255,0.08)] transition-colors hover:bg-surface"
              >
                {publisherCollected[0] ? (
                  <ComicCover comic={publisherCollected[0]} resolveRemote className="h-16 w-11 shrink-0 rounded-sm" />
                ) : (
                  <div className="h-16 w-11 shrink-0 rounded-sm bg-surface" />
                )}
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">Collected Editions</span>
                  <span className="text-xs text-muted">
                    {publisherCollected.length} edition{publisherCollected.length === 1 ? "" : "s"}
                  </span>
                </span>
                <span className="flex flex-wrap justify-end gap-1">
                  {[...new Set(publisherCollected.map((c) => comicFormatLabel(c.format)))].map((label) => (
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
            {seriesList.length === 0 ? (
              <p className="rounded-lg bg-bg-elevated px-4 py-6 text-sm text-muted shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
                No series under this publisher yet.
              </p>
            ) : (
              <ul className="grid gap-2" data-sort={sort}>
                {seriesList.map((s) => (
                  <li key={s.key}>
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
                  </li>
                ))}
              </ul>
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
          <ComicGrid
            comics={issueComics}
            ownedIds={ownedIds}
            wanted={wanted}
            onAdd={setAdding}
            yearById={yearById}
            emptyAction={() => setCustomOpen(true)}
            showSeriesYear={false}
          />
        </section>
      ) : null}

      {level === "collected" ? (
        <section className="flex flex-col gap-3">
          <div>
            <h2 className="font-display text-lg tracking-wide uppercase">Collected Editions</h2>
            <p className="mt-1 text-xs text-muted">
              {search.publisher} · trades, hardcovers, and omnibuses · {collectedComics.length} shown
            </p>
          </div>
          <ComicGrid
            comics={collectedComics}
            ownedIds={ownedIds}
            wanted={wanted}
            onAdd={setAdding}
            yearById={yearById}
            emptyAction={() => setCustomOpen(true)}
            collectedEmpty
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
        const est = comicEstimate(comic);
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
                <span className="tabular text-sm text-gold">{usd(est)}</span>
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
  const [msrp, setMsrp] = useState("4.99");
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
      msrp: msrp ? Number(msrp) : undefined,
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

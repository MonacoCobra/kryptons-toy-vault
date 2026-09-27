import { useEffect, useMemo, useState } from "react";
import {
  loadComicRun,
  loadComicsByIds,
  loadNoteworthy,
  loadPublisherDetail,
  loadPublisherIndex,
  searchComicShards,
  type ComicSearchHit,
} from "@/lib/catalog-client";
import { mergeComicsInto, searchComicList } from "@/lib/catalog-search";
import type { ComicRunFile, NoteworthyFile, PublisherDetail, PublisherIndex, SeriesShardRef } from "@/lib/catalog-shard";
import { libraryCatalogRows, type ComicLibrary } from "@/lib/comic-catalog";
import {
  catalogFromCustom,
  comicFormatLabel,
  filterCollectedComics,
  filterIssueComics,
  isCollectedComic,
} from "@/lib/comic-format";
import { comicLabel } from "@/lib/comic-label";
import {
  buildCollectedSeriesList,
  buildSeriesList,
  collectedComicMatchesSeries,
  comicMatchesSeries,
  comicReleaseDate,
  comicTitleYear,
  makeCollectedSeriesKey,
  makeSeriesKey,
  seriesBaseNorm,
  seriesBaseTitle,
  seriesRunYearFor,
  sortCatalogComics,
  sortCollectedVolumes,
  sortPublisherList,
  sortSeriesList,
  type ComicSortMode,
  type LadderSortMode,
  type SeriesRef,
} from "@/lib/comic-series";
import { collapseComicVariants } from "@/lib/comic-variants";
import { normalizePublisher } from "@/lib/locg-import";
import type { CatalogComic, CustomComic } from "@/lib/types";

type OwnedEntry = { catalogId?: string; custom?: CustomComic; addedAt: string; id: string };

type LadderSearch = {
  q?: string;
  publisher?: string;
  series?: string;
  year?: number;
  keys?: boolean;
  sort?: ComicSortMode;
  section?: "collected";
};

function isPublisherDetail(value: PublisherDetail | unknown[]): value is PublisherDetail {
  return Boolean(value) && !Array.isArray(value) && Array.isArray((value as PublisherDetail).series);
}

function yearForExtra(comic: CatalogComic, series: SeriesRef[]): number {
  const titled = comicTitleYear(comic.series);
  if (titled) return titled;
  const base = seriesBaseNorm(comic.series);
  const dateYear = Number((comic.streetDate || comic.coverDate || "").slice(0, 4)) || 0;
  const same = series.filter((row) => row.titleNorm === base);
  const eligible = same.filter((row) => row.year && dateYear && row.year <= dateYear);
  if (eligible.length) return Math.max(...eligible.map((row) => row.year));
  if (same.length === 1) return same[0]!.year;
  return dateYear;
}

function foldLiveIssues(series: SeriesShardRef[], extras: CatalogComic[], publisher: string): SeriesShardRef[] {
  const live = extras.filter(
    (comic) =>
      comic.id.startsWith("live-") &&
      !isCollectedComic(comic) &&
      normalizePublisher(comic.publisher) === normalizePublisher(publisher),
  );
  if (!live.length) return series;
  const out = series.map((row) => ({ ...row }));
  for (const comic of live) {
    const year = yearForExtra(comic, out);
    const key = makeSeriesKey(comic.publisher, comic.series, year);
    const hit = out.find((row) => row.key === key);
    if (hit) hit.issueCount += 1;
    else {
      out.push({
        key,
        publisher: comic.publisher,
        title: seriesBaseTitle(comic.series),
        titleNorm: seriesBaseNorm(comic.series),
        year,
        issueCount: 1,
        latestDate: comicReleaseDate(comic),
        sample: comic,
        shard: "",
      });
    }
  }
  return out;
}

export function useComicsLadder(opts: {
  search: LadderSearch;
  extras: CatalogComic[];
  library: ComicLibrary | null;
  customComics: Record<string, CustomComic>;
  owned: Record<string, OwnedEntry>;
  ownedByCatalog: Map<string, OwnedEntry>;
  ladderSort: LadderSortMode;
  sort: ComicSortMode;
  level: string;
}) {
  const { search, extras, library, customComics, owned, ownedByCatalog, ladderSort, sort, level } = opts;
  const libraryRows = useMemo(() => libraryCatalogRows(library), [library]);
  const [pubIndex, setPubIndex] = useState<PublisherIndex | null>(null);
  const [detail, setDetail] = useState<PublisherDetail | null>(null);
  const [runFile, setRunFile] = useState<ComicRunFile | null>(null);
  const [runShard, setRunShard] = useState("");
  const [noteFile, setNoteFile] = useState<NoteworthyFile | null>(null);
  const [searchHits, setSearchHits] = useState<ComicSearchHit[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [ownedHits, setOwnedHits] = useState<ComicSearchHit[]>([]);

  useEffect(() => {
    let cancel = false;
    loadPublisherIndex()
      .then((index) => {
        if (cancel) return;
        if (index && !Array.isArray(index) && Array.isArray(index.publishers)) setPubIndex(index);
        else setPubIndex({ publishers: [] });
      })
      .catch(() => {
        if (!cancel) setPubIndex({ publishers: [] });
      });
    return () => {
      cancel = true;
    };
  }, []);

  useEffect(() => {
    if (level !== "publishers") return;
    let cancel = false;
    loadNoteworthy()
      .then((file) => {
        if (!cancel) setNoteFile(file);
      })
      .catch(() => {
        if (!cancel) setNoteFile({ comics: [], years: {} });
      });
    return () => {
      cancel = true;
    };
  }, [level]);

  const publisherEntry = useMemo(() => {
    if (!search.publisher || !pubIndex) return undefined;
    const want = normalizePublisher(search.publisher);
    return pubIndex.publishers.find((row) => normalizePublisher(row.publisher) === want);
  }, [pubIndex, search.publisher]);

  useEffect(() => {
    if (!publisherEntry) {
      setDetail(null);
      return;
    }
    let cancel = false;
    loadPublisherDetail(publisherEntry.shard)
      .then((next) => {
        if (cancel) return;
        setDetail(isPublisherDetail(next) ? next : null);
      })
      .catch(() => {
        if (!cancel) setDetail(null);
      });
    return () => {
      cancel = true;
    };
  }, [publisherEntry]);

  const customCollected = useMemo(
    () => Object.values(customComics).filter(isCollectedComic).map(catalogFromCustom),
    [customComics],
  );

  const seriesRows = useMemo(() => {
    if (!search.publisher) return [] as SeriesShardRef[];
    if (detail && publisherEntry && normalizePublisher(detail.publisher) === normalizePublisher(search.publisher)) {
      return foldLiveIssues(detail.series, extras, search.publisher);
    }
    if (publisherEntry) return [];
    const live = extras.filter(
      (comic) => !isCollectedComic(comic) && normalizePublisher(comic.publisher) === normalizePublisher(search.publisher!),
    );
    return buildSeriesList(live, new Map(), search.publisher).map((row) => ({ ...row, shard: "" }));
  }, [detail, extras, publisherEntry, search.publisher]);

  const activeSeries = useMemo(() => {
    if (!search.series || search.year == null || search.section === "collected") return undefined;
    const want = seriesBaseNorm(search.series);
    return seriesRows.find((row) => row.titleNorm === want && row.year === search.year);
  }, [search.section, search.series, search.year, seriesRows]);

  const activeCollected = useMemo(() => {
    if (search.section !== "collected" || !search.series || !detail) return undefined;
    const want = seriesBaseNorm(search.series);
    return detail.collectedSeries.find((row) => row.titleNorm === want);
  }, [detail, search.section, search.series]);

  const activeShard = search.section === "collected" ? activeCollected?.shard : activeSeries?.shard;

  useEffect(() => {
    if (!activeShard) {
      setRunFile(null);
      setRunShard("");
      return;
    }
    let cancel = false;
    loadComicRun(activeShard)
      .then((file) => {
        if (cancel) return;
        setRunFile(file);
        setRunShard(activeShard);
      })
      .catch(() => {
        if (!cancel) {
          setRunFile({ comics: [], related: [], years: {} });
          setRunShard(activeShard);
        }
      });
    return () => {
      cancel = true;
    };
  }, [activeShard]);

  useEffect(() => {
    const q = search.q?.trim();
    if (!q) {
      setSearchHits([]);
      setSearchQuery("");
      return;
    }
    let cancel = false;
    searchComicShards(q)
      .then((hits) => {
        if (cancel) return;
        setSearchHits(hits);
        setSearchQuery(q);
      })
      .catch(() => {
        if (!cancel) {
          setSearchHits([]);
          setSearchQuery(q);
        }
      });
    return () => {
      cancel = true;
    };
  }, [search.q]);

  const ownedKey = useMemo(
    () =>
      Object.values(owned)
        .map((entry) => entry.catalogId)
        .filter(Boolean)
        .sort()
        .join("|"),
    [owned],
  );

  useEffect(() => {
    if (ladderSort !== "acquired" || !ownedKey) {
      setOwnedHits([]);
      return;
    }
    let cancel = false;
    loadComicsByIds(ownedKey.split("|")).then((hits) => {
      if (!cancel) setOwnedHits(hits);
    });
    return () => {
      cancel = true;
    };
  }, [ladderSort, ownedKey]);

  const ownedYearById = useMemo(() => {
    const years = new Map<string, number>();
    for (const hit of ownedHits) years.set(hit.comic.id, hit.year);
    return years;
  }, [ownedHits]);

  const acquiredLookups = useMemo(() => {
    const bySeries = new Map<string, string>();
    const byPublisher = new Map<string, string>();
    const byCollectedSeries = new Map<string, string>();
    if (ladderSort !== "acquired") return { bySeries, byPublisher, byCollectedSeries };
    const byId = new Map(ownedHits.map((hit) => [hit.comic.id, hit.comic]));
    for (const entry of Object.values(owned)) {
      const comic =
        (entry.catalogId ? byId.get(entry.catalogId) : undefined) ??
        (entry.custom ? catalogFromCustom(entry.custom) : undefined);
      if (!comic) continue;
      const seriesKey = makeSeriesKey(comic.publisher, comic.series, seriesRunYearFor(comic, ownedYearById));
      const pubKey = normalizePublisher(comic.publisher);
      if (!bySeries.has(seriesKey) || entry.addedAt > bySeries.get(seriesKey)!) bySeries.set(seriesKey, entry.addedAt);
      if (!byPublisher.has(pubKey) || entry.addedAt > byPublisher.get(pubKey)!) byPublisher.set(pubKey, entry.addedAt);
      if (isCollectedComic(comic)) {
        const collectedKey = makeCollectedSeriesKey(comic.publisher, comic.series);
        if (!byCollectedSeries.has(collectedKey) || entry.addedAt > byCollectedSeries.get(collectedKey)!) {
          byCollectedSeries.set(collectedKey, entry.addedAt);
        }
      }
    }
    return { bySeries, byPublisher, byCollectedSeries };
  }, [ladderSort, owned, ownedHits, ownedYearById]);

  const publishers = useMemo(() => {
    const list = (pubIndex?.publishers ?? []).map((row) => ({
      publisher: row.publisher,
      seriesCount: row.seriesCount,
      issueCount: row.issueCount,
      latestDate: row.latestDate,
    }));
    const seen = new Set(list.map((row) => normalizePublisher(row.publisher)));
    for (const comic of [...extras, ...customCollected]) {
      const key = normalizePublisher(comic.publisher);
      if (seen.has(key)) continue;
      if (!comic.id.startsWith("live-") && !comic.id.startsWith("custom-")) continue;
      seen.add(key);
      list.push({
        publisher: comic.publisher,
        seriesCount: 0,
        issueCount: 0,
        latestDate: comicReleaseDate(comic),
      });
    }
    return sortPublisherList(list, ladderSort, acquiredLookups.byPublisher);
  }, [acquiredLookups.byPublisher, customCollected, extras, ladderSort, pubIndex]);

  const collectedCounts = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of pubIndex?.publishers ?? []) map.set(normalizePublisher(row.publisher), row.collectedCount);
    for (const comic of customCollected) {
      if (!comic.id.startsWith("custom-")) continue;
      const key = normalizePublisher(comic.publisher);
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return map;
  }, [customCollected, pubIndex]);

  const seriesList = useMemo(
    () => sortSeriesList(seriesRows, ladderSort, acquiredLookups.bySeries),
    [acquiredLookups.bySeries, ladderSort, seriesRows],
  );

  const collectedSeries = useMemo(() => {
    if (!search.publisher || !detail) {
      if (!search.publisher) return [];
      const customOnly = customCollected.filter(
        (comic) => normalizePublisher(comic.publisher) === normalizePublisher(search.publisher!),
      );
      return sortSeriesList(
        buildCollectedSeriesList(customOnly, search.publisher).map((row) => ({ ...row, shard: "" })),
        ladderSort,
        acquiredLookups.byCollectedSeries,
      );
    }
    const customHere = customCollected.filter(
      (comic) => normalizePublisher(comic.publisher) === normalizePublisher(search.publisher!),
    );
    const extra = buildCollectedSeriesList(customHere, search.publisher);
    const merged = new Map(detail.collectedSeries.map((row) => [row.key, { ...row }]));
    for (const row of extra) {
      const prev = merged.get(row.key);
      if (prev) prev.issueCount += row.issueCount;
      else merged.set(row.key, { ...row, shard: "" });
    }
    return sortSeriesList([...merged.values()], ladderSort, acquiredLookups.byCollectedSeries);
  }, [acquiredLookups.byCollectedSeries, customCollected, detail, ladderSort, search.publisher]);

  const collectedEditionCount = useMemo(() => {
    const catalogCount =
      detail && search.publisher && normalizePublisher(detail.publisher) === normalizePublisher(search.publisher)
        ? detail.collectedCount
        : 0;
    const customCount = customCollected.filter(
      (comic) => search.publisher && normalizePublisher(comic.publisher) === normalizePublisher(search.publisher),
    ).length;
    return catalogCount + customCount;
  }, [customCollected, detail, search.publisher]);

  const collectedFormatLabels = useMemo(() => {
    const labels = new Set(detail?.collectedFormats ?? []);
    for (const comic of customCollected) {
      if (!search.publisher) continue;
      if (normalizePublisher(comic.publisher) !== normalizePublisher(search.publisher)) continue;
      labels.add(comicFormatLabel(comic.format));
    }
    return [...labels];
  }, [customCollected, detail, search.publisher]);

  const yearById = useMemo(() => {
    const years = new Map<string, number>();
    if (noteFile) for (const [id, year] of Object.entries(noteFile.years)) years.set(id, year);
    if (runFile && runShard === (activeShard ?? "")) {
      for (const [id, year] of Object.entries(runFile.years)) years.set(id, year);
    }
    for (const hit of searchHits) years.set(hit.comic.id, hit.year);
    for (const [id, year] of ownedYearById) years.set(id, year);
    return years;
  }, [activeShard, noteFile, ownedYearById, runFile, runShard, searchHits]);

  const issueComics = useMemo(() => {
    if (level !== "issues" || !search.publisher || !search.series || search.year == null) return [];
    const baked = runFile && runShard === (activeShard ?? "") ? runFile.comics : [];
    const years = new Map(yearById);
    const pool = mergeComicsInto(extras, libraryRows);
    for (const comic of pool) {
      if (!years.has(comic.id)) years.set(comic.id, yearForExtra(comic, seriesRows));
    }
    const live = pool.filter(
      (comic) =>
        !isCollectedComic(comic) &&
        comicMatchesSeries(
          comic,
          { publisher: search.publisher!, seriesTitle: search.series!, year: search.year! },
          years,
        ),
    );
    let list = mergeComicsInto(baked, live);
    if (search.keys) list = list.filter((comic) => comic.key);
    list = collapseComicVariants(list);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [
    activeShard,
    extras,
    level,
    libraryRows,
    ownedByCatalog,
    runFile,
    runShard,
    search.keys,
    search.publisher,
    search.series,
    search.year,
    seriesRows,
    sort,
    yearById,
  ]);

  const collectedComics = useMemo(() => {
    if (level !== "collected-volumes" || !search.publisher || !search.series) return [];
    const baked = runFile && runShard === (activeShard ?? "") ? runFile.comics : [];
    const customHere = customCollected.filter((comic) =>
      collectedComicMatchesSeries(comic, { publisher: search.publisher!, seriesTitle: search.series! }),
    );
    let list = mergeComicsInto(baked, customHere);
    if (search.keys) list = list.filter((comic) => comic.key);
    if (sort === "issue") return sortCollectedVolumes(list);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [
    activeShard,
    customCollected,
    level,
    ownedByCatalog,
    runFile,
    runShard,
    search.keys,
    search.publisher,
    search.series,
    sort,
  ]);

  const filteredSearch = useMemo(() => {
    if (level !== "search" || !search.q || searchQuery !== search.q.trim()) return [];
    let list = mergeComicsInto(
      searchHits.map((hit) => hit.comic),
      searchComicList(mergeComicsInto(extras, libraryRows), search.q),
    );
    const q = search.q.trim().toLowerCase();
    const customHits = customCollected.filter((comic) => {
      const hay = `${comic.series} ${comic.issue} ${comic.publisher} ${comic.upc ?? ""} ${comic.format} ${comic.description}`.toLowerCase();
      return hay.includes(q);
    });
    list = mergeComicsInto(list, customHits);
    if (search.publisher) {
      const want = normalizePublisher(search.publisher);
      list = list.filter((comic) => normalizePublisher(comic.publisher) === want);
    }
    if (search.section === "collected") list = filterCollectedComics(list);
    if (search.section === "collected" && search.series) {
      list = list.filter((comic) =>
        collectedComicMatchesSeries(comic, { publisher: search.publisher ?? comic.publisher, seriesTitle: search.series! }),
      );
    } else if (search.series && search.year != null) {
      list = list.filter((comic) =>
        comicMatchesSeries(
          comic,
          { publisher: search.publisher ?? comic.publisher, seriesTitle: search.series!, year: search.year! },
          yearById,
        ),
      );
    } else if (search.series) {
      list = list.filter((comic) => comic.series === search.series);
    }
    if (search.keys) list = list.filter((comic) => comic.key);
    if (sort === "issue" && search.section === "collected") return sortCollectedVolumes(list);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [
    customCollected,
    extras,
    level,
    libraryRows,
    ownedByCatalog,
    search,
    searchHits,
    searchQuery,
    sort,
    yearById,
  ]);

  const filteredNoteworthy = useMemo(() => {
    if (level !== "publishers") return [];
    const baked = noteFile?.comics ?? [];
    let list = filterIssueComics(mergeComicsInto(baked, [...(library?.noteworthy ?? []), ...extras]));
    if (search.keys) list = list.filter((comic) => comic.key);
    list = collapseComicVariants(list);
    return sortCatalogComics(list, sort, { ownedByCatalog, label: comicLabel });
  }, [extras, level, library, noteFile, ownedByCatalog, search.keys, sort]);

  const collectedSample = collectedSeries[0]?.sample;
  const loadingPublishers = pubIndex == null;
  const loadingRun = Boolean(activeShard) && runShard !== activeShard;

  return {
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
    loadingDetail: Boolean(search.publisher && publisherEntry && !detail),
    loadingRun,
    customCollected,
  };
}

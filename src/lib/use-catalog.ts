import { useEffect, useMemo, useState } from "react";
import { loadComicsByIds, loadFiguresByIds, loadManifest } from "@/lib/catalog-client";
import type { CatalogManifest } from "@/lib/catalog-shard";
import { useFigureExtras, useLiveComics } from "@/lib/live-store";
import { useVault } from "@/lib/store";
import type { CatalogComic, CatalogFigure } from "@/lib/types";

export function useCatalogManifest() {
  const [manifest, setManifest] = useState<CatalogManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let cancel = false;
    loadManifest()
      .then((next) => {
        if (!cancel) setManifest(next);
      })
      .catch((err: unknown) => {
        if (!cancel) setError(err instanceof Error ? err.message : "Catalog unavailable");
      });
    return () => {
      cancel = true;
    };
  }, []);
  return { manifest, error };
}

/** Resolve catalog rows for specific ids. Repeated ids share the in-memory shard cache. */
export function useResolvedCatalog(figureIds: string[], comicIds: string[]) {
  const figKey = figureIds.slice().sort().join("|");
  const comicKey = comicIds.slice().sort().join("|");
  const [figures, setFigures] = useState<CatalogFigure[]>([]);
  const [comics, setComics] = useState<CatalogComic[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancel = false;
    const fids = figKey ? figKey.split("|") : [];
    const cids = comicKey ? comicKey.split("|") : [];
    if (!fids.length && !cids.length) {
      setFigures([]);
      setComics([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      fids.length ? loadFiguresByIds(fids) : Promise.resolve([] as CatalogFigure[]),
      cids.length ? loadComicsByIds(cids) : Promise.resolve([]),
    ])
      .then(([figs, hits]) => {
        if (cancel) return;
        setFigures(figs);
        setComics(hits.map((hit) => hit.comic));
        setLoading(false);
      })
      .catch(() => {
        if (!cancel) setLoading(false);
      });
    return () => {
      cancel = true;
    };
  }, [figKey, comicKey]);

  return { figures, comics, loading };
}

/** Owned vault rows plus this week's live extras, without the baked catalogs. */
export function useOwnedCatalog() {
  const ownedFigures = useVault((s) => s.ownedFigures);
  const ownedComics = useVault((s) => s.ownedComics);
  const liveFigures = useFigureExtras();
  const liveComics = useLiveComics();
  const figureIds = useMemo(() => Object.keys(ownedFigures), [ownedFigures]);
  const comicIds = useMemo(
    () =>
      Object.values(ownedComics)
        .map((entry) => entry.catalogId)
        .filter((id): id is string => Boolean(id)),
    [ownedComics],
  );
  const resolved = useResolvedCatalog(figureIds, comicIds);
  const figures = useMemo(() => {
    const map = new Map(resolved.figures.map((figure) => [figure.id, figure]));
    for (const figure of liveFigures) map.set(figure.id, figure);
    return [...map.values()];
  }, [resolved.figures, liveFigures]);
  const comics = useMemo(() => {
    const map = new Map(resolved.comics.map((comic) => [comic.id, comic]));
    for (const comic of liveComics) map.set(comic.id, comic);
    return [...map.values()];
  }, [resolved.comics, liveComics]);
  return { figures, comics, loading: resolved.loading };
}

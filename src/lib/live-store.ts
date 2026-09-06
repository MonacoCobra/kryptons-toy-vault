import { createContext, createElement, useContext, useEffect, useLayoutEffect, useMemo, type ReactNode } from "react";
import { create } from "zustand";
import type { CatalogComic, CatalogFigure, WeeklyDrop } from "@/lib/types";
import { getComicLibrary, type ComicLibrary } from "@/lib/comic-catalog";
import { getFigureLibrary, type FigureLibrary } from "@/lib/figure-catalog";
import { getWeeklyDrop } from "@/lib/weekly-drop";

type LiveState = {
  drop: WeeklyDrop | null;
  loading: boolean;
  ensure: (force?: boolean) => Promise<void>;
};

type ComicLibState = {
  library: ComicLibrary | null;
  loading: boolean;
  ensure: (extras?: CatalogComic[], force?: boolean) => Promise<void>;
};

type FigureLibState = {
  library: FigureLibrary | null;
  loading: boolean;
  ensure: (extras?: CatalogFigure[], force?: boolean) => Promise<void>;
};

const EMPTY_COMICS: CatalogComic[] = [];
const EMPTY_FIGURES: CatalogFigure[] = [];
const LiveDropContext = createContext<WeeklyDrop | null>(null);

export const useLiveDrop = create<LiveState>((set, get) => ({
  drop: null,
  loading: false,
  ensure: async (force = false) => {
    const current = get().drop;
    if (!force && current?.status === "ok" && (current.comics.length || current.figures.length)) {
      return;
    }
    if (get().loading) return;
    set({ loading: true });
    try {
      const drop = await getWeeklyDrop({ data: { force } });
      set({ drop, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));

export const useComicLib = create<ComicLibState>((set, get) => ({
  library: null,
  loading: false,
  ensure: async (extras = [], force = false) => {
    if (!force && get().library) return;
    if (get().loading) return;
    set({ loading: true });
    try {
      const library = await getComicLibrary({ data: { extras } });
      set({ library, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));

export const useFigureLib = create<FigureLibState>((set, get) => ({
  library: null,
  loading: false,
  ensure: async (extras = [], force = false) => {
    if (!force && get().library) return;
    if (get().loading) return;
    set({ loading: true });
    try {
      const library = await getFigureLibrary({ data: { extras } });
      set({ library, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));

export function LiveDropHydrator({
  drop,
  children,
}: {
  drop: WeeklyDrop | null;
  children: ReactNode;
}) {
  useLayoutEffect(() => {
    if (drop?.status === "ok" && (drop.comics.length || drop.figures.length)) {
      useLiveDrop.setState({ drop, loading: false });
    }
  }, [drop]);
  return createElement(LiveDropContext.Provider, { value: drop }, children);
}

function useResolvedDrop(): WeeklyDrop | null {
  const store = useLiveDrop((s) => s.drop);
  const loaded = useContext(LiveDropContext);
  if (store?.status === "ok" && (store.comics.length || store.figures.length)) return store;
  return loaded;
}

export function useEnsureLiveDrop() {
  const ensure = useLiveDrop((s) => s.ensure);
  const drop = useResolvedDrop();
  const ready = Boolean(drop?.comics.length || drop?.figures.length);
  useEffect(() => {
    if (!ready) void ensure(true);
  }, [ensure, ready]);
}

export function useLiveComics(): CatalogComic[] {
  return useResolvedDrop()?.comics ?? EMPTY_COMICS;
}

export function useLiveFigures(): CatalogFigure[] {
  return useResolvedDrop()?.figures ?? EMPTY_FIGURES;
}

/** Promoted-only titles (not in the static COMICS seed) for detail/search merge. */
export function usePromotedComics(): CatalogComic[] {
  const library = useComicLib((s) => s.library);
  if (!library) return EMPTY_COMICS;
  // Archive includes static + promoted; callers that need "extra permanent" use archive ids not in COMIC_BY_ID.
  // For merge we pass archive so comicById can resolve promoted ids after static miss.
  return library.archive;
}

export function useEnsureComicLibrary(extras: CatalogComic[]) {
  const ensure = useComicLib((s) => s.ensure);
  const library = useComicLib((s) => s.library);
  const extrasKey = extras.map((c) => c.id).join(",");
  useEffect(() => {
    void ensure(extras, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- extrasKey captures content
  }, [ensure, extrasKey]);
  return library;
}

/** Live SKU overlay rows from figure_catalog (permanent archive without republish). */
export function useOverlayFigures(): CatalogFigure[] {
  const library = useFigureLib((s) => s.library);
  return library?.overlay ?? EMPTY_FIGURES;
}

/** Weekly drop figures + live SKU overlay for mergeFigures / figureById. */
export function useFigureExtras(): CatalogFigure[] {
  const live = useLiveFigures();
  const overlay = useOverlayFigures();
  return useMemo(() => {
    if (!overlay.length) return live;
    if (!live.length) return overlay;
    return [...overlay, ...live];
  }, [overlay, live]);
}

export function useEnsureFigureLibrary(extras: CatalogFigure[] = []) {
  const ensure = useFigureLib((s) => s.ensure);
  const library = useFigureLib((s) => s.library);
  const extrasKey = extras.map((f) => f.id).join(",");
  useEffect(() => {
    void ensure(extras, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- extrasKey captures content
  }, [ensure, extrasKey]);
  return library;
}

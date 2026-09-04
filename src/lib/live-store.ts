import { createContext, createElement, useContext, useEffect, useLayoutEffect, type ReactNode } from "react";
import { create } from "zustand";
import type { CatalogComic, CatalogFigure, WeeklyDrop } from "@/lib/types";
import { getWeeklyDrop } from "@/lib/weekly-drop";

type LiveState = {
  drop: WeeklyDrop | null;
  loading: boolean;
  ensure: (force?: boolean) => Promise<void>;
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

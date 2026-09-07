import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  ComicGrade,
  Condition,
  CustomComic,
  DisplayPhoto,
  OwnedComic,
  OwnedFigure,
  PulseBaseline,
  VaultState,
  WishlistItem,
} from "@/lib/types";

const STARTER_OWNED_COMICS: OwnedComic[] = [
  {
    id: "own-mv-ff-550-3d",
    catalogId: "mv-ff-550-3d",
    acquiredDate: "2026-09-04",
    acquiredPrice: 8,
    grade: "raw",
    addedAt: "2026-09-04T15:00:00.000Z",
    notes: "Direct Edition 3-D variant.",
    photoDataUrl: "/covers/mv-ff-550-3d.jpg",
  },
];

function initialState(): VaultState {
  return {
    ownedFigures: {},
    wantedFigures: {},
    ownedComics: Object.fromEntries(STARTER_OWNED_COMICS.map((o) => [o.id, o])),
    wantedComics: {},
    customComics: {},
    displays: {},
    pulseBaselines: {},
    lastPulseNoticeWeek: null,
  };
}

type Actions = {
  addFigure: (entry: Omit<OwnedFigure, "addedAt"> & { addedAt?: string }) => void;
  updateFigure: (figureId: string, patch: Partial<OwnedFigure>) => void;
  removeFigure: (figureId: string) => void;
  toggleWantFigure: (figureId: string) => void;
  addComic: (entry: Omit<OwnedComic, "id" | "addedAt"> & { id?: string }) => string;
  updateComic: (id: string, patch: Partial<OwnedComic>) => void;
  removeComic: (id: string) => void;
  toggleWantComic: (comicId: string) => void;
  addCustomComic: (comic: CustomComic) => void;
  addDisplay: (entry: Omit<DisplayPhoto, "id" | "addedAt"> & { id?: string; addedAt?: string }) => string;
  updateDisplay: (id: string, patch: Partial<DisplayPhoto>) => void;
  removeDisplay: (id: string) => void;
  clearVault: () => void;
  ensurePulseBaseline: (baseline: PulseBaseline) => void;
  markPulseNoticeSeen: (week: string) => void;
};

const empty = (): VaultState => ({
  ownedFigures: {},
  wantedFigures: {},
  ownedComics: {},
  wantedComics: {},
  customComics: {},
  displays: {},
  pulseBaselines: {},
  lastPulseNoticeWeek: null,
});

export const useVault = create<VaultState & Actions>()(
  persist(
    (set) => ({
      ...initialState(),
      addFigure: (entry) =>
        set((s) => {
          const { [entry.figureId]: _, ...wanted } = s.wantedFigures;
          return {
            ownedFigures: {
              ...s.ownedFigures,
              [entry.figureId]: { ...s.ownedFigures[entry.figureId], ...entry, addedAt: entry.addedAt ?? new Date().toISOString() },
            },
            wantedFigures: wanted,
          };
        }),
      updateFigure: (figureId, patch) =>
        set((s) => {
          const prev = s.ownedFigures[figureId];
          if (!prev) return s;
          return { ownedFigures: { ...s.ownedFigures, [figureId]: { ...prev, ...patch } } };
        }),
      removeFigure: (figureId) =>
        set((s) => {
          const { [figureId]: _, ...rest } = s.ownedFigures;
          return { ownedFigures: rest };
        }),
      toggleWantFigure: (figureId) =>
        set((s) => {
          if (s.ownedFigures[figureId]) return s;
          if (s.wantedFigures[figureId]) {
            const { [figureId]: _, ...rest } = s.wantedFigures;
            return { wantedFigures: rest };
          }
          return {
            wantedFigures: {
              ...s.wantedFigures,
              [figureId]: { id: figureId, addedAt: new Date().toISOString() },
            },
          };
        }),
      addComic: (entry) => {
        const id = entry.id ?? `own-${entry.catalogId ?? entry.custom?.id ?? crypto.randomUUID()}`;
        set((s) => {
          const catalogId = entry.catalogId;
          const wanted = { ...s.wantedComics };
          if (catalogId && wanted[catalogId]) delete wanted[catalogId];
          return {
            ownedComics: {
              ...s.ownedComics,
              [id]: { ...entry, grade: entry.grade ?? "raw", id, addedAt: new Date().toISOString() },
            },
            wantedComics: wanted,
          };
        });
        return id;
      },
      updateComic: (id, patch) =>
        set((s) => {
          const prev = s.ownedComics[id];
          if (!prev) return s;
          return { ownedComics: { ...s.ownedComics, [id]: { ...prev, ...patch } } };
        }),
      removeComic: (id) =>
        set((s) => {
          const { [id]: _, ...rest } = s.ownedComics;
          return { ownedComics: rest };
        }),
      toggleWantComic: (comicId) =>
        set((s) => {
          const alreadyOwned = Object.values(s.ownedComics).some((o) => o.catalogId === comicId);
          if (alreadyOwned) return s;
          if (s.wantedComics[comicId]) {
            const { [comicId]: _, ...rest } = s.wantedComics;
            return { wantedComics: rest };
          }
          return {
            wantedComics: {
              ...s.wantedComics,
              [comicId]: { id: comicId, addedAt: new Date().toISOString() },
            },
          };
        }),
      addCustomComic: (comic) =>
        set((s) => ({ customComics: { ...s.customComics, [comic.id]: comic } })),
      addDisplay: (entry) => {
        const id = entry.id ?? `display-${crypto.randomUUID()}`;
        set((s) => ({
          displays: {
            ...(s.displays ?? {}),
            [id]: {
              ...entry,
              id,
              addedAt: entry.addedAt ?? new Date().toISOString(),
            },
          },
        }));
        return id;
      },
      updateDisplay: (id, patch) =>
        set((s) => {
          const prev = (s.displays ?? {})[id];
          if (!prev) return s;
          return { displays: { ...(s.displays ?? {}), [id]: { ...prev, ...patch } } };
        }),
      removeDisplay: (id) =>
        set((s) => {
          const { [id]: _, ...rest } = s.displays ?? {};
          return { displays: rest };
        }),
      clearVault: () => set(empty()),
      ensurePulseBaseline: (baseline) =>
        set((s) => {
          if (s.pulseBaselines[baseline.week]) return s;
          return {
            pulseBaselines: { ...s.pulseBaselines, [baseline.week]: baseline },
          };
        }),
      markPulseNoticeSeen: (week) => set({ lastPulseNoticeWeek: week }),
    }),
    {
      name: "krypton-toy-vault-v4",
      storage: createJSONStorage(() => {
        if (typeof window === "undefined") {
          return {
            getItem: () => null,
            setItem: () => {},
            removeItem: () => {},
          };
        }
        return localStorage;
      }),
      partialize: (s) => ({
        ownedFigures: s.ownedFigures,
        wantedFigures: s.wantedFigures,
        ownedComics: s.ownedComics,
        wantedComics: s.wantedComics,
        customComics: s.customComics,
        displays: s.displays ?? {},
        pulseBaselines: s.pulseBaselines ?? {},
        lastPulseNoticeWeek: s.lastPulseNoticeWeek ?? null,
      }),
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<VaultState>;
        return {
          ...current,
          ...p,
          displays: p.displays ?? {},
          pulseBaselines: p.pulseBaselines ?? {},
          lastPulseNoticeWeek: p.lastPulseNoticeWeek ?? null,
        };
      },
    },
  ),
);

export function useHydrated() {
  const persistHasHydrated = useVault.persist.hasHydrated();
  return persistHasHydrated;
}

export const CONDITIONS: { id: Condition; label: string }[] = [
  { id: "mib", label: "MIB / sealed" },
  { id: "opened", label: "Opened complete" },
  { id: "loose", label: "Loose" },
];

export const GRADES: { id: ComicGrade; label: string }[] = [
  { id: "raw", label: "Raw" },
  { id: "10.0", label: "10.0 GM" },
  { id: "9.8", label: "9.8 NM/M" },
  { id: "9.6", label: "9.6 NM+" },
  { id: "9.4", label: "9.4 NM" },
  { id: "9.2", label: "9.2 NM−" },
  { id: "9.0", label: "9.0 VF/NM" },
  { id: "8.5", label: "8.5 VF+" },
  { id: "8.0", label: "8.0 VF" },
  { id: "7.5", label: "7.5 VF−" },
  { id: "7.0", label: "7.0 FN/VF" },
  { id: "6.0", label: "6.0 FN" },
  { id: "5.0", label: "5.0 VG/FN" },
  { id: "4.0", label: "4.0 VG" },
  { id: "3.0", label: "3.0 GD/VG" },
  { id: "2.0", label: "2.0 GD" },
  { id: "1.0", label: "1.0 FR" },
];

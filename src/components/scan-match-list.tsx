import { Plus } from "lucide-react";
import { comicLabel } from "@/data/comics";
import { ComicCover } from "@/components/comic-cover";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CatalogComic } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ScanMatchList({
  comics,
  selectedId,
  ownedIds,
  source,
  onSelect,
  onAdd,
}: {
  comics: CatalogComic[];
  selectedId: string | null;
  ownedIds: Set<string>;
  source: "matches" | "search";
  onSelect: (comic: CatalogComic) => void;
  onAdd: (comic: CatalogComic) => void;
}) {
  if (!comics.length) return null;

  const selected = comics.find((c) => c.id === selectedId) ?? comics[0];

  return (
    <section className="grid gap-3" data-testid="scan-match-list">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-xs tracking-[0.18em] text-gold uppercase">
          {source === "matches" ? "Catalog matches" : "Search results"}
        </h2>
        <span className="text-xs text-muted">{comics.length} found</span>
      </div>
      <ul className="grid gap-3">
        {comics.map((comic, i) => {
          const selectedRow = comic.id === selected.id;
          const owned = ownedIds.has(comic.id);
          return (
            <li key={comic.id}>
              <div
                className={cn(
                  "rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]",
                  selectedRow && "shadow-[0_0_0_2px_var(--color-gold)]",
                )}
              >
                <button
                  type="button"
                  data-testid={`scan-match-${comic.id}`}
                  aria-pressed={selectedRow}
                  onClick={() => {
                    onSelect(comic);
                    onAdd(comic);
                  }}
                  className="flex min-h-11 w-full items-center gap-3 p-3 text-left"
                >
                  <ComicCover comic={comic} className="h-20 w-14 shrink-0 rounded-sm" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">{comicLabel(comic)}</span>
                    <span className="mt-0.5 block truncate text-xs text-muted">
                      {comic.publisher}
                      {i === 0 && source === "matches" ? " · best match" : ""}
                    </span>
                    <span className="mt-1 flex flex-wrap gap-1">
                      {owned ? <Badge tone="gain">Owned</Badge> : null}
                      {i === 0 && source === "matches" ? <Badge tone="gold">Best match</Badge> : null}
                      {selectedRow ? <Badge tone="ice">Selected</Badge> : null}
                    </span>
                  </span>
                </button>
                <div className="px-3 pb-3">
                  <Button
                    type="button"
                    data-testid={`scan-match-add-${comic.id}`}
                    variant={selectedRow ? "default" : "secondary"}
                    className="min-h-11 w-full"
                    onClick={() => {
                      onSelect(comic);
                      onAdd(comic);
                    }}
                  >
                    <Plus className="size-4" />
                    {owned ? "Edit copy" : "Add to collection"}
                  </Button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
      {selected ? (
        <div className="sticky bottom-20 z-30 md:bottom-4">
          <Button
            type="button"
            data-testid="scan-match-confirm"
            className="min-h-12 w-full shadow-[var(--shadow-elevated)]"
            onClick={() => onAdd(selected)}
          >
            <Plus className="size-4" />
            {ownedIds.has(selected.id) ? "Edit copy" : "Add to collection"}
            <span className="truncate"> — {comicLabel(selected)}</span>
          </Button>
        </div>
      ) : null}
    </section>
  );
}

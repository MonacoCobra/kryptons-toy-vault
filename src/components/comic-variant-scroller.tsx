"use client";

import { Link } from "@tanstack/react-router";
import { ComicCover } from "@/components/comic-cover";
import { variantDisplayLabel } from "@/lib/comic-variants";
import type { CatalogComic } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Horizontal, snap-scrolling strip of open-order / variant covers.
 * Hidden when the family has only one catalog row.
 * Thumbs use baked cover URLs / placeholders only — no resolveRemote flood.
 */
export function ComicVariantScroller({
  comic,
  variants,
}: {
  comic: CatalogComic;
  variants: CatalogComic[];
}) {
  if (variants.length <= 1) return null;

  return (
    <section className="mt-4 min-w-0 max-w-full" aria-label="Cover variants">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h2 className="text-[11px] tracking-[0.16em] text-muted uppercase">Variants</h2>
        <span className="tabular text-[11px] text-muted/80">{variants.length} covers</span>
      </div>
      <div
        className="hide-scrollbar -mx-1 flex max-w-full snap-x snap-mandatory gap-2.5 overflow-x-auto overscroll-x-contain px-1 pb-1"
        role="list"
      >
        {variants.map((v) => {
          const selected = v.id === comic.id;
          const label = variantDisplayLabel(v);
          return (
            <Link
              key={v.id}
              role="listitem"
              to="/comics/$comicId"
              params={{ comicId: v.id }}
              replace
              aria-current={selected ? "page" : undefined}
              aria-label={`${label}${selected ? ", selected" : ""}`}
              className={cn(
                "group flex w-[4.75rem] shrink-0 snap-start flex-col gap-1.5 rounded-lg outline-none",
                "focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-bg",
              )}
            >
              <div
                className={cn(
                  "overflow-hidden rounded-md transition-[box-shadow,transform]",
                  selected
                    ? "ring-2 ring-gold ring-offset-2 ring-offset-bg shadow-[0_0_0_1px_rgba(255,210,0,0.35)]"
                    : "ring-1 ring-white/10 group-hover:ring-gold/50",
                )}
              >
                {/* Baked cover / placeholder only — avoid N× resolveRemote in preview */}
                <ComicCover comic={v} className="aspect-2/3 w-full" />
              </div>
              <span
                className={cn(
                  "line-clamp-2 text-center text-[10px] leading-tight tracking-wide",
                  selected ? "font-semibold text-gold" : "text-muted",
                )}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

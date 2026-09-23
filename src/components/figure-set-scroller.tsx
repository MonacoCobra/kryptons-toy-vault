"use client";

import { Link } from "@tanstack/react-router";
import { FigureArt } from "@/components/figure-art";
import type { CatalogFigure } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Horizontal strip of figures that share a set / blind-box family.
 * Hidden when the family has only one catalog row.
 *
 * The rail is the only horizontal scrollport. Ancestors use min-w-0,
 * max-w-full, and overflow clipping so card min-content cannot widen
 * the document and trigger mobile shrink-to-fit.
 */
export function FigureSetScroller({
  figure,
  members,
}: {
  figure: CatalogFigure;
  members: CatalogFigure[];
}) {
  if (members.length <= 1) return null;

  return (
    <section className="mt-4 min-w-0 max-w-full overflow-hidden" aria-label="In this set">
      <div className="mb-2 flex min-w-0 items-baseline justify-between gap-2">
        <h2 className="text-xs tracking-widest text-muted uppercase">In this set</h2>
        <span className="tabular text-xs text-muted">{members.length}</span>
      </div>
      <div
        className="hide-scrollbar flex w-full min-w-0 max-w-full snap-x snap-mandatory gap-2.5 overflow-x-auto overscroll-x-contain px-1 pb-1"
        role="list"
      >
        {members.map((member) => {
          const selected = member.id === figure.id;
          const label = member.name;
          return (
            <Link
              key={member.id}
              role="listitem"
              to="/figures/$figureId"
              params={{ figureId: member.id }}
              replace
              aria-current={selected ? "page" : undefined}
              aria-label={`${label}${selected ? ", selected" : ""}`}
              className={cn(
                "group flex w-20 min-w-0 max-w-full shrink-0 snap-start flex-col gap-1.5 rounded-lg outline-none",
                "focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-bg",
              )}
            >
              <div
                className={cn(
                  "min-w-0 overflow-hidden rounded-md transition-[box-shadow,transform]",
                  selected
                    ? "ring-2 ring-gold ring-offset-2 ring-offset-bg"
                    : "ring-1 ring-white/10 group-hover:ring-gold/50",
                )}
              >
                <FigureArt figure={member} caption={false} className="aspect-4/5 h-auto w-full max-w-full" />
              </div>
              <span
                className={cn(
                  "line-clamp-2 text-center text-xs leading-tight",
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

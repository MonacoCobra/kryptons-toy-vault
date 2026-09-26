import { useWindowVirtualizer } from "@tanstack/react-virtual";
import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

export type GridColumns = {
  /** < md */
  base: number;
  /** >= 768px */
  md: number;
  /** >= 1024px */
  lg: number;
};

function columnsForWidth(width: number, base: number, md: number, lg: number): number {
  if (width >= 1024) return lg;
  if (width >= 768) return md;
  return base;
}

/**
 * Window-scrolled virtualized CSS grid. Only mounts rows near the viewport so
 * catalogs with thousands of cards stay scrollable on mobile.
 */
export function VirtualGrid<T>({
  items,
  getKey,
  renderItem,
  columns,
  estimateRowHeight,
  gapClassName = "gap-3",
  overscan = 4,
}: {
  items: T[];
  getKey: (item: T) => string;
  renderItem: (item: T) => ReactNode;
  columns: GridColumns;
  /** Approximate row height in px (card + gap); refined via measureElement. */
  estimateRowHeight: number;
  gapClassName?: string;
  overscan?: number;
}) {
  const { base, md, lg } = columns;
  const parentRef = useRef<HTMLDivElement>(null);
  // Always start from `base` so the server HTML and the first client render
  // describe the same rows. The real width is applied in layout, before paint.
  const [columnCount, setColumnCount] = useState(base);
  const [scrollMargin, setScrollMargin] = useState(0);

  useLayoutEffect(() => {
    const update = () => setColumnCount(columnsForWidth(window.innerWidth, base, md, lg));
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [base, md, lg]);

  useLayoutEffect(() => {
    const el = parentRef.current;
    if (!el) return;

    const syncMargin = () => {
      const top = el.getBoundingClientRect().top + window.scrollY;
      setScrollMargin(top);
    };

    syncMargin();
    const ro = new ResizeObserver(syncMargin);
    if (el.parentElement) ro.observe(el.parentElement);
    window.addEventListener("resize", syncMargin);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", syncMargin);
    };
  }, [items.length, columnCount]);

  const rowCount = columnCount > 0 ? Math.ceil(items.length / columnCount) : 0;

  const virtualizer = useWindowVirtualizer({
    count: rowCount,
    estimateSize: () => estimateRowHeight,
    overscan,
    scrollMargin,
    // Window measurement is 0 until layout. A non-zero initial height lets
    // SSR and the hydration render emit the first screen instead of an empty
    // spacer the size of the whole list (thousands of collected editions).
    initialRect: { width: 0, height: 960 },
  });

  useEffect(() => {
    virtualizer.measure();
  }, [columnCount, items.length, virtualizer]);

  if (!items.length) return null;

  const virtualRows = virtualizer.getVirtualItems();

  // If the scroll rect is still 0, paint a short in-flow prefix. Same markup
  // on the server and the first client render; the virtualizer takes over
  // once it has a real viewport height.
  if (virtualRows.length === 0) {
    const perRow = Math.max(columnCount, 1);
    const visibleCount = Math.min(items.length, perRow * (overscan + 2));
    const rows: T[][] = [];
    for (let i = 0; i < visibleCount; i += perRow) {
      rows.push(items.slice(i, i + perRow));
    }
    return (
      <div ref={parentRef} className="w-full max-w-full" data-virtual-fallback="">
        {rows.map((rowItems, index) => (
          <ul
            key={index}
            className={`grid ${gapClassName} pb-3`}
            style={{ gridTemplateColumns: `repeat(${perRow}, minmax(0, 1fr))` }}
          >
            {rowItems.map((item) => (
              <li key={getKey(item)} className="min-w-0">
                {renderItem(item)}
              </li>
            ))}
          </ul>
        ))}
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      className="relative w-full"
      style={{ height: virtualizer.getTotalSize() }}
    >
      {virtualRows.map((virtualRow) => {
        const start = virtualRow.index * columnCount;
        const rowItems = items.slice(start, start + columnCount);
        return (
          <div
            key={virtualRow.key}
            data-index={virtualRow.index}
            ref={virtualizer.measureElement}
            className="absolute top-0 left-0 w-full"
            style={{
              transform: `translateY(${virtualRow.start - scrollMargin}px)`,
            }}
          >
            <ul
              className={`grid ${gapClassName} pb-3`}
              style={{ gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))` }}
            >
              {rowItems.map((item) => (
                <li key={getKey(item)} className="min-w-0">
                  {renderItem(item)}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

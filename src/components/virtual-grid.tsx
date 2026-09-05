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
  const [columnCount, setColumnCount] = useState(() =>
    typeof window === "undefined" ? base : columnsForWidth(window.innerWidth, base, md, lg),
  );
  const [scrollMargin, setScrollMargin] = useState(0);

  useEffect(() => {
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
  });

  useEffect(() => {
    virtualizer.measure();
  }, [columnCount, items.length, virtualizer]);

  if (!items.length) return null;

  const virtualRows = virtualizer.getVirtualItems();

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

import type { SoldComp } from "@/lib/types";
import { relativeDays, usd } from "@/lib/format";

export function SoldListings({ comps }: { comps: SoldComp[] }) {
  return (
    <ul className="grid gap-2">
      {comps.map((c, i) => (
        <li
          key={`${c.date}-${c.price}-${i}`}
          className="grid grid-cols-[1fr_auto] gap-3 rounded-md bg-surface p-3 shadow-[0_0_0_1px_rgba(214,230,255,0.08)]"
        >
          <div className="min-w-0">
            {c.url ? (
              <a
                href={c.url}
                target="_blank"
                rel="noreferrer"
                className="line-clamp-2 text-sm leading-snug text-ice hover:text-fg"
              >
                {c.title}
              </a>
            ) : (
              <p className="line-clamp-2 text-sm leading-snug">{c.title}</p>
            )}
            <p className="mt-1 text-xs text-muted">
              <span className="font-semibold tracking-wide text-gain uppercase">Sold</span>
              {" · "}
              {relativeDays(c.date)}
              {" · "}
              {c.condition}
              {c.source === "ebay" ? " · eBay" : null}
            </p>
          </div>
          <p className="self-center font-display text-lg tracking-wide text-gold tabular">{usd(c.price)}</p>
        </li>
      ))}
    </ul>
  );
}

"use client";

import { useEffect, useState } from "react";
import { comicLabel } from "@/data/comics";
import { getComicCover } from "@/lib/comic-covers";
import type { CatalogComic, CustomComic } from "@/lib/types";
import { cn, hashString } from "@/lib/utils";

type CoverSource = Pick<CatalogComic, "series" | "issue" | "publisher" | "variant"> & {
  palette?: [string, string, string];
  key?: boolean;
  id?: string;
  coverDate?: string;
  msrp?: number;
  cover?: string;
};

/** Palette placeholder only — never generative AI art. */
function PlaceholderCover({
  comic,
  className,
}: {
  comic: CoverSource | CustomComic;
  className?: string;
}) {
  const palette =
    "palette" in comic && comic.palette ? comic.palette : (["#1e3a8a", "#e30613", "#f8fafc"] as [string, string, string]);
  const isKey = "key" in comic && comic.key;
  const issue = comic.issue.toLowerCase() === "nn" ? "OS" : comic.issue;
  const seed = hashString(comic.id ?? `${comic.series}-${comic.issue}`);
  const art = seed % 4;
  const year = "coverDate" in comic && comic.coverDate ? comic.coverDate.slice(0, 4) : "";

  const bars = Array.from({ length: 18 }, (_, i) => {
    const n = ((seed >> (i % 12)) + i * 17) % 7;
    return 1 + (n % 4);
  });

  return (
    <div className={cn("relative overflow-hidden", className)} style={{ background: palette[0] }}>
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage: `radial-gradient(${palette[2]}40 1.1px, transparent 1.3px)`,
          backgroundSize: "5px 5px",
        }}
      />

      {art === 0 ? (
        <div
          className="absolute top-10 -right-8 size-40 rotate-12 rounded-full opacity-40"
          style={{ background: palette[1] }}
        />
      ) : art === 1 ? (
        <div
          className="absolute right-0 bottom-8 left-0 h-24 -skew-y-6 opacity-35"
          style={{ background: palette[1] }}
        />
      ) : art === 2 ? (
        <div
          className="absolute top-1/3 left-1/2 size-36 -translate-x-1/2 rotate-45 opacity-30"
          style={{ background: palette[2] }}
        />
      ) : (
        <>
          <div className="absolute top-12 left-0 h-2 w-full opacity-50" style={{ background: palette[1] }} />
          <div className="absolute top-20 left-0 h-10 w-full opacity-25" style={{ background: palette[2] }} />
        </>
      )}

      <div
        className="absolute top-0 right-0 left-0 flex h-6 items-center justify-between px-2"
        style={{ background: palette[1] }}
      >
        <span className="truncate text-[9px] font-semibold tracking-[0.16em] text-white uppercase">
          {comic.publisher}
        </span>
        {isKey ? (
          <span className="text-[9px] font-bold tracking-widest text-gold uppercase">Key</span>
        ) : (
          <span className="text-[9px] text-white/70">{year}</span>
        )}
      </div>

      <div className="absolute inset-x-0 top-8 px-2.5">
        <p
          className="font-display text-[13px] leading-tight tracking-wide text-balance uppercase"
          style={{ color: palette[2] }}
        >
          {comic.series}
        </p>
      </div>

      <div className="absolute right-2 bottom-14 font-display text-5xl leading-none text-white/90 drop-shadow-sm">
        {issue}
      </div>

      <div className="absolute right-2 bottom-8 text-[9px] tracking-widest text-white/55 uppercase">
        {comic.variant ? comic.variant : `#${issue}`}
      </div>

      <div className="absolute bottom-0 left-0 flex h-6 w-full items-end gap-px px-2 pb-1.5">
        {bars.map((w, i) => (
          <span
            key={i}
            className="inline-block bg-white/45"
            style={{ width: w, height: 8 + (i % 3) * 2 }}
          />
        ))}
      </div>

      <span className="sr-only">{comicLabel(comic)}</span>
    </div>
  );
}

export function ComicCover({
  comic,
  className,
  photo,
  resolveRemote = false,
}: {
  comic: CoverSource | CustomComic;
  className?: string;
  photo?: string;
  /** When true, look up a real Comic Vine cover if none is set (requires COMICVINE_API_KEY). */
  resolveRemote?: boolean;
}) {
  const catalogCover = "cover" in comic ? comic.cover : undefined;
  const [remote, setRemote] = useState<string | undefined>();
  const [broken, setBroken] = useState(false);

  useEffect(() => {
    setBroken(false);
    setRemote(undefined);
  }, [comic.id, catalogCover, photo]);

  useEffect(() => {
    if (!resolveRemote || photo || catalogCover || !comic.id) return;
    let cancelled = false;
    void (async () => {
      try {
        const result = await getComicCover({
          data: {
            comicId: comic.id!,
            series: comic.series,
            issue: comic.issue,
            publisher: comic.publisher,
          },
        });
        if (!cancelled && result.status === "ok" && result.coverUrl) {
          setRemote(result.coverUrl);
        }
      } catch {
        // keep placeholder
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [resolveRemote, photo, catalogCover, comic.id, comic.series, comic.issue, comic.publisher]);

  const src = photo || catalogCover || remote;

  if (src && !broken) {
    return (
      <div className={cn("relative overflow-hidden bg-surface", className)}>
        <img
          src={src}
          alt={comicLabel(comic)}
          className="absolute inset-0 size-full object-cover object-top"
          onError={() => setBroken(true)}
          loading="lazy"
          decoding="async"
        />
      </div>
    );
  }

  return <PlaceholderCover comic={comic} className={className} />;
}

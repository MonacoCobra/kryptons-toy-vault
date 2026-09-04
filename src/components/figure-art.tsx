import { COMPANY_BY_ID } from "@/data/companies";
import type { CatalogFigure } from "@/lib/types";
import { cn, hashString } from "@/lib/utils";

type Theme = {
  card: string;
  bar: string;
  suit: string;
  accent: string;
  glow: string;
  ink: string;
};

const THEMES: Record<string, Theme> = {
  marvel: { card: "#16080c", bar: "#e30613", suit: "#dc2626", accent: "#1d4ed8", glow: "#e30613", ink: "#fff5f5" },
  spidey: { card: "#14080c", bar: "#dc2626", suit: "#b91c1c", accent: "#2563eb", glow: "#ef4444", ink: "#fff5f5" },
  xmen: { card: "#0b1224", bar: "#1d4ed8", suit: "#1e40af", accent: "#fbbf24", glow: "#3b82f6", ink: "#eef4ff" },
  dc: { card: "#071018", bar: "#1e3a8a", suit: "#1e3a8a", accent: "#e30613", glow: "#3a74d4", ink: "#e8f0ff" },
  bats: { card: "#0b0d12", bar: "#111827", suit: "#1f2937", accent: "#eab308", glow: "#eab308", ink: "#f8fafc" },
  supes: { card: "#07122a", bar: "#1e3a8a", suit: "#1d4ed8", accent: "#e30613", glow: "#3b82f6", ink: "#fff8e7" },
  sw: { card: "#0a0a0c", bar: "#111111", suit: "#4b5563", accent: "#eab308", glow: "#eab308", ink: "#f8fafc" },
  gundam: { card: "#101418", bar: "#e60012", suit: "#e5e7eb", accent: "#1e3a8a", glow: "#e60012", ink: "#f8fafc" },
  dbz: { card: "#1a1208", bar: "#ea580c", suit: "#fb923c", accent: "#1d4ed8", glow: "#f97316", ink: "#fff7ed" },
  anime: { card: "#12101c", bar: "#6d28d9", suit: "#a78bfa", accent: "#f472b6", glow: "#a78bfa", ink: "#f5f3ff" },
  motu: { card: "#1a1408", bar: "#c2410c", suit: "#f59e0b", accent: "#7c2d12", glow: "#f59e0b", ink: "#fffbeb" },
  spawn: { card: "#140808", bar: "#7f1d1d", suit: "#1a1a1a", accent: "#eab308", glow: "#dc2626", ink: "#fff7ed" },
  tmnt: { card: "#08140c", bar: "#166534", suit: "#16a34a", accent: "#eab308", glow: "#22c55e", ink: "#ecfdf5" },
  horror: { card: "#0c140c", bar: "#14532d", suit: "#166534", accent: "#111827", glow: "#4ade80", ink: "#ecfdf5" },
  joe: { card: "#0c140c", bar: "#14532d", suit: "#15803d", accent: "#111827", glow: "#22c55e", ink: "#ecfdf5" },
  tf: { card: "#140a08", bar: "#dc2626", suit: "#1e3a8a", accent: "#eab308", glow: "#dc2626", ink: "#fff7ed" },
  pr: { card: "#14080c", bar: "#dc2626", suit: "#ef4444", accent: "#f8fafc", glow: "#ef4444", ink: "#fff5f5" },
  wwe: { card: "#140808", bar: "#dc2626", suit: "#111827", accent: "#f8fafc", glow: "#dc2626", ink: "#fff5f5" },
  sixth: { card: "#12100c", bar: "#9a7b2f", suit: "#1f2937", accent: "#eab308", glow: "#eab308", ink: "#fffbeb" },
  nintendo: { card: "#081418", bar: "#e60012", suit: "#16a34a", accent: "#fbbf24", glow: "#22c55e", ink: "#ecfdf5" },
  mk: { card: "#140a08", bar: "#b91c1c", suit: "#f97316", accent: "#111827", glow: "#f97316", ink: "#fff7ed" },
  sf: { card: "#140808", bar: "#dc2626", suit: "#ef4444", accent: "#1e3a8a", glow: "#ef4444", ink: "#fff5f5" },
  default: { card: "#0a1220", bar: "#1e4fa3", suit: "#d6e6ff", accent: "#3a74d4", glow: "#3a74d4", ink: "#e8f0ff" },
};

function themeFor(figure: CatalogFigure): Theme {
  const tags = new Set(figure.tags);
  const n = `${figure.name} ${figure.subtitle}`.toLowerCase();
  if (tags.has("spider-man") || n.includes("spider") || n.includes("venom") || n.includes("carnage")) return THEMES.spidey!;
  if (tags.has("x-men") || n.includes("wolverine") || n.includes("magneto") || n.includes("gambit")) return THEMES.xmen!;
  if (n.includes("batman") || n.includes("joker") || n.includes("who laughs")) return THEMES.bats!;
  if (n.includes("superman") || n.includes("kal-el")) return THEMES.supes!;
  if (tags.has("star-wars") || n.includes("vader") || n.includes("mando") || n.includes("ahsoka")) return THEMES.sw!;
  if (tags.has("gundam") || figure.kind === "kit") return THEMES.gundam!;
  if (tags.has("dbz") || n.includes("goku") || n.includes("vegeta")) return THEMES.dbz!;
  if (tags.has("spawn")) return THEMES.spawn!;
  if (tags.has("tmnt") || n.includes("turtle") || n.includes("leonardo")) return THEMES.tmnt!;
  if (tags.has("horror") || tags.has("kaiju")) return THEMES.horror!;
  if (tags.has("gi-joe")) return THEMES.joe!;
  if (tags.has("transformers")) return THEMES.tf!;
  if (tags.has("power-rangers")) return THEMES.pr!;
  if (tags.has("wwe")) return THEMES.wwe!;
  if (tags.has("sixth-scale")) return THEMES.sixth!;
  if (tags.has("nintendo") || tags.has("zelda") || tags.has("metroid")) return THEMES.nintendo!;
  if (tags.has("mk") || n.includes("scorpion") || n.includes("sub-zero")) return THEMES.mk!;
  if (tags.has("sf") || n.includes("ryu") || n.includes("akuma")) return THEMES.sf!;
  if (tags.has("motu") || tags.has("thundercats")) return THEMES.motu!;
  if (tags.has("anime") || tags.has("one-piece") || tags.has("nier")) return THEMES.anime!;
  if (tags.has("marvel")) return THEMES.marvel!;
  if (tags.has("dc")) return THEMES.dc!;
  const company = COMPANY_BY_ID[figure.company];
  return { ...THEMES.default!, bar: company.accent, accent: company.accent, glow: company.accent };
}

function pose(seed: number) {
  const s = seed % 6;
  if (s === 0) return "M32 22c6 0 10 6 10 12v8l8 18H54l-6-16-4 28h-8l-3-20-3 20h-8l-4-28-6 16H8l8-18v-8c0-6 4-12 10-12z";
  if (s === 1) return "M32 20c5 0 9 5 9 11v10l14 8-2 8-12-6v21H23V51l-12 6-2-8 14-8V31c0-6 4-11 9-11z";
  if (s === 2) return "M32 21c6 0 10 5 10 12 8 4 12 14 10 22l-8 2c1-6-1-12-6-16v21H24V41c-5 4-7 10-6 16l-8-2c-2-8 2-18 10-22 0-7 4-12 10-12z";
  if (s === 3) return "M32 23c5.5 0 9 5 9 11v7l16 4v8l-16-2-3 21h-12l-3-21-16 2v-8l16-4v-7c0-6 3.5-11 9-11z";
  if (s === 4) return "M32 20c6 0 10 6 10 12v6c10 8 12 18 10 26l-9-2c1-6-1-12-6-16v20H25V46c-5 4-7 10-6 16l-9 2c-2-8 0-18 10-26v-6c0-6 4-12 10-12z";
  return "M24 22c0-6 4-12 8-12s8 6 8 12c10 2 16 12 16 22h-8c0-6-2-12-8-14v24H32V32c-6 2-8 8-8 14h-8c0-10 6-20 16-22z";
}

export function FigureArt({
  figure,
  className,
  photo,
  caption = true,
}: {
  figure: CatalogFigure;
  className?: string;
  photo?: string;
  caption?: boolean;
}) {
  const company = COMPANY_BY_ID[figure.company];
  const seed = hashString(figure.id);
  const theme = themeFor(figure);
  const kit = figure.kind === "kit";
  const initials = figure.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  if (photo) {
    return (
      <div className={cn("relative overflow-hidden bg-surface", className)}>
        <img src={photo} alt="" className="size-full object-cover" />
        {caption ? (
          <div className="absolute inset-x-0 bottom-0 bg-linear-to-t from-bg/85 to-transparent p-2">
            <p className="truncate font-display text-sm tracking-wide">{figure.name}</p>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className={cn("relative overflow-hidden", className)} style={{ background: theme.card }}>
      <div
        className="absolute inset-0 opacity-50"
        style={{ background: `radial-gradient(circle at 50% 38%, ${theme.glow}55, transparent 58%)` }}
      />
      <div className="absolute top-0 right-0 left-0 flex h-7 items-center justify-between px-2.5" style={{ background: theme.bar }}>
        <span className="font-display text-[10px] tracking-[0.18em] text-white uppercase">{company.short}</span>
        <span className="text-[10px] text-white/80">{figure.scale}</span>
      </div>

      <svg viewBox="0 0 64 80" className="absolute inset-0 size-full" aria-hidden>
        <text
          x="32"
          y="48"
          textAnchor="middle"
          fontSize="22"
          fontFamily="Oswald, sans-serif"
          fill={theme.ink}
          opacity="0.08"
        >
          {initials}
        </text>
        {kit ? (
          <>
            <rect x="11" y="20" width="42" height="46" rx="2" fill={theme.suit} opacity="0.2" />
            <rect x="14" y="23" width="36" height="24" fill={theme.accent} opacity="0.28" />
            <polygon points="32,28 44,46 20,46" fill={theme.suit} opacity="0.85" />
            <polygon points="32,31 40,44 24,44" fill={theme.accent} opacity="0.7" />
            <rect x="16" y="52" width="32" height="3" fill={theme.ink} opacity="0.35" />
            <rect x="16" y="58" width="20" height="2" fill={theme.ink} opacity="0.25" />
          </>
        ) : (
          <>
            <circle cx="32" cy="18" r="5.2" fill={theme.suit} opacity="0.95" />
            <path d={pose(seed)} fill={theme.suit} opacity="0.92" />
            <path d={pose(seed)} fill={theme.accent} opacity="0.28" transform="translate(1 1)" />
          </>
        )}
      </svg>

      {caption ? (
        <div className="absolute inset-x-0 bottom-0 px-2.5 py-2" style={{ background: `${theme.card}ee` }}>
          <p className="truncate font-display text-sm tracking-wide text-fg">{figure.name}</p>
          <p className="truncate text-[11px] text-muted">{figure.subtitle}</p>
        </div>
      ) : null}

      {figure.exclusive ? (
        <span className="absolute top-9 right-2 rounded-full bg-gold px-1.5 py-0.5 text-[9px] font-semibold tracking-wide text-gold-fg uppercase">
          Exclusive
        </span>
      ) : null}
    </div>
  );
}

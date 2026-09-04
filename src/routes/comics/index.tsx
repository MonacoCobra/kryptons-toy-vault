import { useMemo, useState, type ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Camera, Plus, Search } from "lucide-react";
import { comicLabel, mergeComics, recentComics, searchComics } from "@/data/comics";
import { AddComicDialog } from "@/components/add-comic-dialog";
import { ComicCover } from "@/components/comic-cover";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { usd } from "@/lib/format";
import { useLiveComics } from "@/lib/live-store";
import { comicEstimate } from "@/lib/market";
import { useVault } from "@/lib/store";
import type { CatalogComic, ComicFormat, CustomComic } from "@/lib/types";
import { cn, slug } from "@/lib/utils";

type Search = {
  q?: string;
  publisher?: string;
  keys?: boolean;
};

export const Route = createFileRoute("/comics/")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    q: typeof s.q === "string" ? s.q : undefined,
    publisher: typeof s.publisher === "string" ? s.publisher : undefined,
    keys: s.keys === true || s.keys === "true",
  }),
  component: ComicsPage,
});

function ComicsPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const owned = useVault((s) => s.ownedComics);
  const wanted = useVault((s) => s.wantedComics);
  const extras = useLiveComics();
  const [adding, setAdding] = useState<CatalogComic | null>(null);
  const [customOpen, setCustomOpen] = useState(false);

  const ownedIds = useMemo(
    () => new Set(Object.values(owned).map((o) => o.catalogId).filter(Boolean)),
    [owned],
  );

  const catalog = useMemo(() => mergeComics(extras), [extras]);
  const publishers = useMemo(
    () => [...new Set(catalog.map((c) => c.publisher))].sort(),
    [catalog],
  );

  const filtered = useMemo(() => {
    let list = search.q ? searchComics(search.q, extras) : catalog;
    if (search.publisher) list = list.filter((c) => c.publisher === search.publisher);
    if (search.keys) list = list.filter((c) => c.key);
    return list;
  }, [search, extras, catalog]);

  return (
    <main className="flex flex-col gap-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs tracking-[0.28em] text-gold uppercase">Issue records</p>
          <h1 className="mt-1 font-display text-3xl tracking-wide uppercase">Comic catalog</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Search by series and issue, scan a cover, or log a book the catalog missed. This week's
            street list is pulled automatically.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="secondary">
            <Link to="/scan">
              <Camera /> Scan cover
            </Link>
          </Button>
          <Button variant="outline" onClick={() => setCustomOpen(true)}>
            <Plus /> Custom issue
          </Button>
        </div>
      </header>

      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" />
        <Input
          value={search.q ?? ""}
          placeholder="Amazing Spider-Man 300, Absolute Batman, Saga…"
          className="pl-10"
          onChange={(e) => navigate({ search: (prev) => ({ ...prev, q: e.target.value || undefined }) })}
        />
      </div>

      <div className="hide-scrollbar -mx-4 flex flex-wrap gap-2 overflow-x-auto px-4 md:mx-0 md:px-0">
        <FilterChip
          active={!search.publisher}
          onClick={() => navigate({ search: (prev) => ({ ...prev, publisher: undefined }) })}
        >
          All publishers
        </FilterChip>
        {publishers.map((p) => (
          <FilterChip
            key={p}
            active={search.publisher === p}
            onClick={() =>
              navigate({ search: (prev) => ({ ...prev, publisher: prev.publisher === p ? undefined : p }) })
            }
          >
            {p}
          </FilterChip>
        ))}
        <FilterChip
          active={Boolean(search.keys)}
          onClick={() => navigate({ search: (prev) => ({ ...prev, keys: prev.keys ? undefined : true }) })}
        >
          Keys only
        </FilterChip>
      </div>

      {!search.q && !search.publisher && !search.keys ? (
        <section>
          <h2 className="mb-3 font-display text-lg tracking-wide uppercase">New on the pull</h2>
          <ul className="hide-scrollbar -mx-4 flex gap-3 overflow-x-auto px-4 md:mx-0 md:grid md:grid-cols-5 md:overflow-visible md:px-0">
            {recentComics(5, extras).map((comic) => (
              <li key={comic.id} className="w-36 shrink-0 md:w-auto">
                <Link
                  to="/comics/$comicId"
                  params={{ comicId: comic.id }}
                  className="block overflow-hidden rounded-lg bg-bg-elevated shadow-[var(--shadow-border)]"
                >
                  <ComicCover comic={comic} className="aspect-2/3" />
                  <p className="line-clamp-2 p-2 text-xs font-medium">{comicLabel(comic)}</p>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <ul className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-5">
        {filtered.map((comic) => {
          const have = ownedIds.has(comic.id);
          const want = Boolean(wanted[comic.id]);
          const est = comicEstimate(comic);
          return (
            <li
              key={comic.id}
              className="overflow-hidden rounded-lg bg-bg-elevated shadow-[0_0_0_1px_rgba(214,230,255,0.08)]"
            >
              <Link to="/comics/$comicId" params={{ comicId: comic.id }} className="block">
                <ComicCover comic={comic} className="aspect-2/3" />
              </Link>
              <div className="grid gap-1.5 p-3">
                <p className="line-clamp-2 text-sm font-medium">{comicLabel(comic)}</p>
                <p className="text-xs text-muted">{comic.publisher}</p>
                <div className="flex flex-wrap gap-1">
                  {have ? <Badge tone="gain">Owned</Badge> : null}
                  {want && !have ? <Badge tone="gold">Wanted</Badge> : null}
                  {comic.key ? <Badge tone="red">Key</Badge> : null}
                </div>
                <div className="flex items-center justify-between">
                  <span className="tabular text-sm text-gold">{usd(est)}</span>
                  <Button size="sm" variant="ghost" onClick={() => setAdding(comic)}>
                    {have ? "Edit" : "Add"}
                  </Button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {filtered.length === 0 ? (
        <div className="rounded-xl bg-bg-elevated p-8 text-center shadow-[0_0_0_1px_rgba(214,230,255,0.08)]">
          <p className="font-display text-xl tracking-wide uppercase">No matches</p>
          <p className="mt-2 text-sm text-muted">Add it as a custom issue.</p>
          <Button className="mt-4" onClick={() => setCustomOpen(true)}>
            Add custom issue
          </Button>
        </div>
      ) : null}

      {adding ? <AddComicDialog comic={adding} open onOpenChange={(v) => !v && setAdding(null)} /> : null}
      <CustomComicDialog open={customOpen} onOpenChange={setCustomOpen} />
    </main>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "h-10 rounded-full px-3 text-xs font-medium tracking-wide",
        active ? "bg-primary text-primary-fg" : "bg-surface text-muted",
      )}
    >
      {children}
    </button>
  );
}

function CustomComicDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const [series, setSeries] = useState("");
  const [issue, setIssue] = useState("");
  const [publisher, setPublisher] = useState("");
  const [coverDate, setCoverDate] = useState("");
  const [msrp, setMsrp] = useState("4.99");
  const [format, setFormat] = useState<ComicFormat>("single");
  const [variant, setVariant] = useState("");
  const [draft, setDraft] = useState<CustomComic | null>(null);

  function next() {
    if (!series.trim()) return;
    const custom: CustomComic = {
      id: `custom-${slug(series)}-${slug(issue || "nn")}-${Date.now()}`,
      series: series.trim(),
      issue: issue.trim() || "nn",
      publisher: publisher.trim() || "Unknown",
      coverDate: coverDate || undefined,
      msrp: msrp ? Number(msrp) : undefined,
      format,
      variant: variant.trim() || undefined,
    };
    setDraft(custom);
  }

  return (
    <>
      <Dialog open={open && !draft} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Custom issue</DialogTitle>
            <DialogDescription>For books the catalog does not carry yet.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <Field label="Series" value={series} onChange={setSeries} placeholder="Action Comics" />
            <Field label="Issue" value={issue} onChange={setIssue} placeholder="1" />
            <Field label="Publisher" value={publisher} onChange={setPublisher} placeholder="DC Comics" />
            <div className="grid gap-1.5">
              <Label>Cover date</Label>
              <Input type="date" value={coverDate} onChange={(e) => setCoverDate(e.target.value)} />
            </div>
            <Field label="Cover price" value={msrp} onChange={setMsrp} />
            <div className="grid gap-1.5">
              <Label>Format</Label>
              <Select value={format} onValueChange={(v) => setFormat(v as ComicFormat)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(["single", "annual", "tpb", "hc", "omnibus", "facsimile"] as const).map((f) => (
                    <SelectItem key={f} value={f}>
                      {f}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Field label="Variant (optional)" value={variant} onChange={setVariant} placeholder="Cover B" />
            <Button onClick={next} disabled={!series.trim()}>
              Continue
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      {draft ? (
        <AddComicDialog
          custom={draft}
          open
          onOpenChange={(v) => {
            if (!v) {
              setDraft(null);
              onOpenChange(false);
            }
          }}
        />
      ) : null}
    </>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="grid gap-1.5">
      <Label>{label}</Label>
      <Input value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

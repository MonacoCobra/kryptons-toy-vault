import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, ExternalLink } from "lucide-react";

export const Route = createFileRoute("/credits")({
  component: CreditsPage,
  head: () => ({
    meta: [{ title: "Credits — Krypton's Toy Vault" }],
  }),
});

type CreditSource = {
  name: string;
  href: string;
  usedFor: string;
  extraLinks?: { label: string; href: string }[];
};

const COMIC_SOURCES: CreditSource[] = [
  {
    name: "Grand Comics Database",
    href: "https://www.comics.org/",
    usedFor:
      "Series and issue metadata, GCD issue ids, and UPC/ISBN backfill from their public JSON API. GCD also publishes downloadable dumps for researchers; this vault uses the live API, not a redistributed dump.",
    extraLinks: [{ label: "JSON API", href: "https://www.comics.org/api/" }],
  },
  {
    name: "Metron",
    href: "https://metron.cloud/",
    usedFor:
      "Issue barcodes and series metadata via the Metron API, used to fill UPC/ISBN when a stronger community match is not already on file.",
  },
  {
    name: "League of Comic Geeks",
    href: "https://leagueofcomicgeeks.com/",
    usedFor:
      "Primary UPC/ISBN identity, weekly new-comics lists, collection CSV import, and cover matching against LOCG issue pages and CDN art.",
  },
  {
    name: "Comic Vine",
    href: "https://comicvine.gamespot.com/",
    usedFor:
      "Published cover scans (fallback after LOCG) and occasional barcode lookup when no UPC is on the LOCG record.",
  },
];

const FIGURE_SOURCES: CreditSource[] = [
  {
    name: "Mephitsu",
    href: "https://www.mephitsu.co.uk/",
    usedFor:
      "Collector figure line listings, GTINs, and photos for Marvel Legends and other Hasbro lines used in the figure identity bake.",
  },
  {
    name: "IDW Publishing storefront",
    href: "https://www.idwpublishing.com/",
    usedFor:
      "Comic SKUs and UPC/ISBN from IDW's public Shopify product feed, when a non-exclusive barcode is present.",
  },
];

function CreditsPage() {
  return (
    <main className="flex flex-col gap-8">
      <header className="max-w-2xl">
        <p className="text-xs tracking-[0.18em] text-gold uppercase">Attribution</p>
        <h1 className="mt-2 font-display text-3xl tracking-wide uppercase">Credits</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          Catalog metadata — titles, issue numbers, barcodes, covers, and related
          collector ids — comes from these community databases and public APIs.
          Krypton&apos;s Toy Vault is a personal fan project. Character names, logos,
          and other trademarks belong to their owners. We are not affiliated with,
          endorsed by, or sponsored by any publisher, retailer, or database listed
          here.
        </p>
      </header>

      <section aria-labelledby="comic-sources-heading" className="flex flex-col gap-3">
        <h2 id="comic-sources-heading" className="font-display text-xl tracking-wide uppercase">
          Comic catalog
        </h2>
        <ul className="grid gap-3">
          {COMIC_SOURCES.map((source) => (
            <SourceCard key={source.name} source={source} />
          ))}
        </ul>
      </section>

      <section aria-labelledby="figure-sources-heading" className="flex flex-col gap-3">
        <h2 id="figure-sources-heading" className="font-display text-xl tracking-wide uppercase">
          Figures &amp; shop feeds
        </h2>
        <p className="max-w-2xl text-sm leading-relaxed text-muted">
          We also read public Shopify product JSON from official manufacturer and
          specialty shops (Super7, NECA, DC Shop, and others) for figure SKUs,
          barcodes, and product photos. Those shops own their catalogs; we do not
          claim their images or product copy.
        </p>
        <ul className="grid gap-3">
          {FIGURE_SOURCES.map((source) => (
            <SourceCard key={source.name} source={source} />
          ))}
        </ul>
      </section>

      <p className="max-w-2xl text-sm leading-relaxed text-subtle">
        Cover and product art is hosted by the communities and shops above. Nothing
        here is generated artwork, and we do not republish their licenses or terms.
      </p>

      <p>
        <Link
          to="/"
          className="inline-flex h-11 items-center gap-2 text-sm text-muted transition-colors duration-150 hover:text-fg"
        >
          <ArrowLeft className="size-4" />
          Back to vault
        </Link>
      </p>
    </main>
  );
}

function SourceCard({ source }: { source: CreditSource }) {
  return (
    <li className="rounded-xl bg-bg-elevated p-5 shadow-[var(--shadow-border)]">
      <h3 className="font-display text-lg tracking-wide uppercase">{source.name}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted">{source.usedFor}</p>
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1">
        <a
          href={source.href}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-11 items-center gap-1.5 text-sm text-gold transition-colors duration-150 hover:text-fg"
        >
          Visit {source.name}
          <ExternalLink className="size-3.5" aria-hidden />
        </a>
        {source.extraLinks?.map((link) => (
          <a
            key={link.href}
            href={link.href}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-11 items-center gap-1.5 text-sm text-muted transition-colors duration-150 hover:text-fg"
          >
            {link.label}
            <ExternalLink className="size-3.5" aria-hidden />
          </a>
        ))}
      </div>
    </li>
  );
}

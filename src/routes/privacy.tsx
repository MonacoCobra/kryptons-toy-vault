import type { ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

export const Route = createFileRoute("/privacy")({
  component: PrivacyPage,
  head: () => ({
    meta: [{ title: "Privacy Policy — Krypton's Toy Vault" }],
  }),
});

/** Play Console contact — Shelby: swap this if a dedicated inbox is set. */
const PRIVACY_EMAIL = "privacy@kryptonstoyvault.com";
const YOUTUBE_URL = "https://youtube.com/@kryptonstoyvault";

function PrivacyPage() {
  return (
    <main className="flex flex-col gap-8">
      <header className="max-w-2xl">
        <p className="text-xs tracking-[0.18em] text-gold uppercase">Your data</p>
        <h1 className="mt-2 font-display text-3xl tracking-wide uppercase">Privacy Policy</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          Krypton&apos;s Toy Vault is a personal collector app. We do not track you, we do not
          run accounts, and your collection stays on your device. This page is the plain-English
          policy for the web app and the Google Play listing.
        </p>
        <p className="mt-2 text-xs tracking-[0.14em] text-subtle uppercase">
          Last updated September 18, 2026
        </p>
      </header>

      <section aria-labelledby="not-collected-heading" className="max-w-2xl">
        <PolicyCard headingId="not-collected-heading" title="What we don't collect">
          <p>
            We do not collect personal information. There is no sign-in, no profile, and no
            account system. We do not use advertising IDs, analytics pixels, or other tracking
            tools to follow you around.
          </p>
        </PolicyCard>
      </section>

      <section aria-labelledby="collection-heading" className="max-w-2xl">
        <PolicyCard headingId="collection-heading" title="Your collection stays on your device">
          <p>
            Figures, comics, wishlists, notes, and display photos you add are stored in this
            browser&apos;s local storage — on your phone or computer. They are not uploaded to
            our servers for an account, and there is no cloud sync.
          </p>
          <p>
            If you clear the app&apos;s site data, uninstall, or switch devices, that local
            collection is gone unless you kept your own backup.
          </p>
        </PolicyCard>
      </section>

      <section aria-labelledby="camera-heading" className="max-w-2xl">
        <PolicyCard headingId="camera-heading" title="Camera and gallery (optional)">
          <p>
            Camera and photo-library access are optional. They are used only if you choose Scan
            (photograph or pick a cover to match it in the catalog) or add a display photo.
          </p>
          <p>
            Scan photos are sent only to identify the comic so we can match it. They are not
            used to track you, build a profile, or attach to an account. Display photos you save
            stay in local storage on your device.
          </p>
        </PolicyCard>
      </section>

      <section aria-labelledby="catalog-heading" className="max-w-2xl">
        <PolicyCard headingId="catalog-heading" title="Catalog covers and public listings">
          <p>
            Cover art and product photos in the catalog come from public community databases and
            shop feeds — Comic Vine, League of Comic Geeks, Grand Comics Database, Metron,
            Mephitsu, and similar sources. Those are published catalog assets, not your personal
            data.
          </p>
          <p>
            Sold-comp estimates use public marketplace listings for catalog items. That lookup
            does not send your private collection or identity.
          </p>
        </PolicyCard>
      </section>

      <section aria-labelledby="contact-heading" className="max-w-2xl">
        <PolicyCard headingId="contact-heading" title="Contact">
          <p>Questions about this policy? Email the address below, or reach the vault on YouTube.</p>
          <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1">
            <a
              href={`mailto:${PRIVACY_EMAIL}`}
              className="inline-flex h-11 items-center text-sm text-gold transition-colors duration-150 hover:text-fg"
            >
              {PRIVACY_EMAIL}
            </a>
            <a
              href={YOUTUBE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-11 items-center text-sm text-gold transition-colors duration-150 hover:text-fg"
            >
              @kryptonstoyvault
            </a>
          </div>
        </PolicyCard>
      </section>

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

function PolicyCard({
  headingId,
  title,
  children,
}: {
  headingId: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-xl bg-bg-elevated p-5 shadow-[var(--shadow-border)]">
      <h2 id={headingId} className="font-display text-xl tracking-wide uppercase">
        {title}
      </h2>
      <div className="mt-3 flex flex-col gap-3 text-sm leading-relaxed text-muted">{children}</div>
    </div>
  );
}

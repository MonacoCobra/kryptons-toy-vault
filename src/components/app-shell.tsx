import type { ReactNode } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { Activity, BookOpen, Camera, Package, Vault, Youtube } from "lucide-react";
import { PulseNotice } from "@/components/pulse-notice";
import { useEnsureLiveDrop } from "@/lib/live-store";
import { cn } from "@/lib/utils";

const YOUTUBE_URL = "https://youtube.com/@kryptonstoyvault";

const NAV: {
  to: "/" | "/figures" | "/scan" | "/comics" | "/pulse";
  label: string;
  icon: typeof Vault;
  exact?: boolean;
  accent?: boolean;
}[] = [
  { to: "/", label: "Vault", icon: Vault, exact: true },
  { to: "/figures", label: "Figures", icon: Package },
  { to: "/scan", label: "Scan", icon: Camera, accent: true },
  { to: "/comics", label: "Comics", icon: BookOpen },
  { to: "/pulse", label: "Pulse", icon: Activity },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  useEnsureLiveDrop();

  return (
    <div className="min-h-dvh bg-bg text-fg">
      <div className="pointer-events-none fixed inset-0 vault-grid opacity-50" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,rgba(30,79,163,0.16),transparent_55%)]" />

      <header className="sticky top-0 z-40 hidden border-b border-border bg-bg/90 backdrop-blur-md md:block">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-end gap-3 px-4">
          <nav className="flex items-center gap-1">
            {NAV.filter((n) => n.to !== "/scan").map((item) => {
              const active = item.exact ? pathname === "/" : pathname.startsWith(item.to);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={cn(
                    "inline-flex h-11 items-center px-3 text-sm font-medium transition-colors duration-150",
                    active ? "text-fg" : "text-muted hover:text-fg",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
            <Link
              to="/scan"
              className="ml-2 inline-flex h-11 items-center gap-2 rounded-sm bg-primary px-4 text-sm font-medium text-primary-fg"
            >
              <Camera className="size-4" />
              Scan cover
            </Link>
          </nav>
        </div>
      </header>

      <PulseNotice />
      <div className="relative mx-auto w-full max-w-6xl px-4 pt-6 pb-32 md:pb-10">
        {children}
        <footer className="mt-16 flex items-center justify-between gap-3 border-t border-border pt-5">
          <p className="text-xs tracking-[0.18em] text-subtle uppercase">Krypton's Toy Vault</p>
          <a
            href={YOUTUBE_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Krypton's Toy Vault on YouTube"
            className="inline-flex h-11 items-center gap-2 text-sm text-muted transition-colors duration-150 hover:text-fg"
          >
            <Youtube className="size-4" />
            @kryptonstoyvault
          </a>
        </footer>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-bg/95 backdrop-blur-md md:hidden">
        <ul className="grid grid-cols-5 px-1 pb-[env(safe-area-inset-bottom)]">
          {NAV.map((item) => {
            const active = item.exact ? pathname === "/" : pathname.startsWith(item.to);
            const Icon = item.icon;
            return (
              <li key={item.to} className="flex justify-center">
                <Link
                  to={item.to}
                  className={cn(
                    "flex h-16 w-full flex-col items-center justify-center gap-1 text-[10px] tracking-wide uppercase",
                    item.accent && "-mt-3",
                    active && !item.accent ? "text-fg" : "text-muted",
                  )}
                >
                  <span
                    className={cn(
                      "inline-flex items-center justify-center",
                      item.accent &&
                        "size-12 rounded-full bg-primary text-primary-fg shadow-[0_8px_24px_-8px_rgba(227,6,19,0.8)]",
                    )}
                  >
                    <Icon className="size-5" />
                  </span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}

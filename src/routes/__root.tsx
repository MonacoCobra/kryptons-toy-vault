import { createRootRoute, HeadContent, Outlet, Scripts } from "@tanstack/react-router";
import { AuthProvider } from "@/lib/auth/provider";
import { PreviewHostBridge } from "@/components/preview-host-bridge";
import { AppShell } from "@/components/app-shell";
import { LiveDropHydrator } from "@/lib/live-store";
import { getWeeklyDrop } from "@/lib/weekly-drop";
import type { WeeklyDrop } from "@/lib/types";
import { Toaster } from "sonner";
import appCss from "../styles.css?url";

const APP_NAME = "Krypton's Toy Vault";

export const Route = createRootRoute({
  loader: async (): Promise<{ drop: WeeklyDrop | null }> => {
    try {
      const drop = await getWeeklyDrop({ data: { force: false } });
      return { drop };
    } catch {
      return { drop: null };
    }
  },
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: APP_NAME },
      {
        name: "description",
        content:
          "Krypton's Toy Vault — figures, kits, and comics with live weekly street lists, cover scans, and sold-comp estimates.",
      },
      { name: "theme-color", content: "#070b14" },
    ],
    links: [
      { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
      { rel: "stylesheet", href: appCss },
      { rel: "manifest", href: "/__grok/manifest.webmanifest" },
      { rel: "apple-touch-icon", href: "/__grok/icon-180.png" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Oswald:wght@400;500;600;700&display=swap",
      },
    ],
  }),
  component: Root,
});

function Root() {
  const data = Route.useLoaderData() as { drop: WeeklyDrop | null } | undefined;
  const drop = data?.drop ?? null;
  return (
    <html lang="en" className="antialiased" suppressHydrationWarning>
      <head>
        <HeadContent />
      </head>
      <body>
        <PreviewHostBridge />
        <LiveDropHydrator drop={drop}>
          <AuthProvider>
            <AppShell>
              <Outlet />
            </AppShell>
            <Toaster
              theme="dark"
              position="top-center"
              toastOptions={{
                style: {
                  background: "#0e1628",
                  border: "1px solid #243454",
                  color: "#f2f5fa",
                },
              }}
            />
          </AuthProvider>
        </LiveDropHydrator>
        <Scripts />
      </body>
    </html>
  );
}

import { createRouter, Link } from "@tanstack/react-router";
import { AppErrorComponent } from "@/lib/error-component";
import { routeTree } from "./routeTree.gen";

function NotFound() {
  return (
    <main className="py-20 text-center">
      <h1 className="font-display text-3xl tracking-wide uppercase">Not in the vault</h1>
      <p className="mt-2 text-sm text-muted">That record is not in the catalog.</p>
      <Link to="/" className="mt-4 inline-block text-sm text-gold">
        Return to vault
      </Link>
    </main>
  );
}

export function getRouter() {
  return createRouter({
    routeTree,
    defaultErrorComponent: AppErrorComponent,
    defaultNotFoundComponent: NotFound,
  });
}

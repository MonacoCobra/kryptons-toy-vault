import { createFileRoute, Link } from "@tanstack/react-router";
import { DisplaysGallery } from "@/components/displays-gallery";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/displays")({ component: DisplaysPage });

function DisplaysPage() {
  return (
    <main className="flex flex-col gap-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-display text-3xl tracking-wide uppercase">Displays</h1>
          <p className="mt-2 text-sm text-muted">
            Photos of your shelves and setups — stored locally in your personal vault.
          </p>
        </div>
        <Button variant="secondary" asChild>
          <Link to="/collection">Back to collection</Link>
        </Button>
      </header>
      <DisplaysGallery />
    </main>
  );
}

import type { ErrorComponentProps } from "@tanstack/react-router";
import { TriangleAlert } from "lucide-react";

function errorMessage(error: unknown): string {
  if (error == null) return "An unexpected error occurred. Try reloading the page.";
  if (typeof error === "string") {
    return error.trim() || "An unexpected error occurred. Try reloading the page.";
  }
  if (error instanceof Error) {
    const msg = (error.message || error.name || "").trim();
    return msg || "An unexpected error occurred. Try reloading the page.";
  }
  if (typeof error === "object") {
    const rec = error as { message?: unknown; error?: unknown; statusMessage?: unknown };
    for (const key of ["message", "statusMessage", "error"] as const) {
      const v = rec[key];
      if (typeof v === "string" && v.trim()) return v.trim();
    }
    try {
      const json = JSON.stringify(error);
      if (json && json !== "{}") return json;
    } catch {
      /* ignore */
    }
  }
  return String(error);
}

export function AppErrorComponent({ error }: ErrorComponentProps) {
  const message = errorMessage(error);
  return (
    <main
      className={
        "flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center " +
        "bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-50"
      }
    >
      <span className="text-red-500" aria-hidden="true">
        <TriangleAlert className="size-10" strokeWidth={2} />
      </span>
      <h1 className="text-lg font-semibold">Something went wrong</h1>
      <pre
        className={
          "max-w-md whitespace-pre-wrap break-words rounded-md border border-red-500/60 " +
          "bg-red-500/10 px-3 py-2 text-left text-sm text-red-700 dark:text-red-300"
        }
      >
        {message}
      </pre>
    </main>
  );
}

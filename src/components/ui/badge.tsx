import { cn } from "@/lib/utils";

export function Badge({
  className,
  tone = "default",
  ...props
}: React.ComponentProps<"span"> & { tone?: "default" | "red" | "gold" | "ice" | "gain" | "loss" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        tone === "default" && "bg-surface-2 text-muted",
        tone === "red" && "bg-primary/15 text-primary",
        tone === "gold" && "bg-gold/15 text-gold",
        tone === "ice" && "bg-shield/25 text-ice",
        tone === "gain" && "bg-gain/15 text-gain",
        tone === "loss" && "bg-loss/15 text-loss",
        className,
      )}
      {...props}
    />
  );
}

export function usd(n: number, digits = 2): string {
  const value = typeof n === "number" && Number.isFinite(n) ? n : Number(n);
  const safe = Number.isFinite(value) ? value : 0;
  return safe.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function usdCompact(n: number): string {
  if (Math.abs(n) >= 1000) {
    return n.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    });
  }
  return usd(n);
}

export function signedUsd(n: number): string {
  const sign = n > 0 ? "+" : n < 0 ? "−" : "";
  return `${sign}${usd(Math.abs(n))}`;
}

export function pct(n: number): string {
  const sign = n > 0 ? "+" : n < 0 ? "−" : "";
  return `${sign}${Math.abs(n).toFixed(1)}%`;
}

export function formatDate(iso?: string | number | null): string {
  if (iso == null || iso === "") return "—";
  const s = String(iso).replace(/\u0000/g, "").trim();
  if (!s) return "—";
  const d = new Date(s + (s.length <= 10 ? "T00:00:00" : ""));
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatMonthYear(iso?: string | number | null): string {
  if (iso == null || iso === "") return "—";
  const s = String(iso).replace(/\u0000/g, "").trim();
  if (!s) return "—";
  const d = new Date(s + (s.length <= 10 ? "T00:00:00" : ""));
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

export function relativeDays(iso: string): string {
  const d = new Date(iso + (iso.length <= 10 ? "T00:00:00" : ""));
  const days = Math.round((Date.now() - d.getTime()) / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 14) return `${days}d ago`;
  if (days < 60) return `${Math.round(days / 7)}w ago`;
  return formatDate(iso);
}

export function plural(n: number, one: string, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`;
}

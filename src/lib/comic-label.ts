/** Display label for a catalog or custom comic. Kept out of the catalog module so UI does not pull the dump. */
export function comicLabel(c: { series: string; issue: string | number; variant?: string }) {
  const issueStr = String(c.issue ?? "").trim();
  const issue = issueStr.toLowerCase() === "nn" || !issueStr ? "" : ` #${issueStr}`;
  const variant = c.variant ? ` (${c.variant})` : "";
  return `${c.series}${issue}${variant}`;
}

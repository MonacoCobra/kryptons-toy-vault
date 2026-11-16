/**
 * Serves the short-bookmarklet export script at `/x.js` with a JavaScript
 * content type and no long cache, so the old site can load the latest copy.
 */
import { VAULT_EXPORT_SCRIPT, VAULT_EXPORT_SCRIPT_PATH } from "../../src/lib/vault-backup";

interface VaultExportEvent {
  url: URL;
  req: { method: string };
}

const SCRIPT_HEADERS = {
  "content-type": "text/javascript; charset=utf-8",
  "cache-control": "no-cache, no-store, must-revalidate",
  "x-content-type-options": "nosniff",
  "access-control-allow-origin": "*",
};

export default async function vaultExportMiddleware(
  event: VaultExportEvent,
  next: () => unknown | Promise<unknown>,
): Promise<unknown> {
  const method = (event.req.method ?? "GET").toUpperCase();
  if (event.url.pathname !== VAULT_EXPORT_SCRIPT_PATH) return next();
  if (method !== "GET" && method !== "HEAD") return next();
  return new Response(method === "HEAD" ? null : VAULT_EXPORT_SCRIPT, {
    headers: SCRIPT_HEADERS,
  });
}

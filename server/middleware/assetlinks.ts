/**
 * Digital Asset Links for Play TWA verification.
 *
 * Serves `/.well-known/assetlinks.json` with `application/json` even when the
 * SPA HTML fallback would otherwise win. The canonical fingerprints live in
 * `public/.well-known/assetlinks.json` (also copied to static output).
 */
import {
  ASSETLINKS_JSON_HEADERS,
  publishedAssetLinks,
} from "../../src/lib/android/assetlinks";

interface AssetLinksEvent {
  url: URL;
  req: { method: string };
}

export default async function assetlinksMiddleware(
  event: AssetLinksEvent,
  next: () => unknown | Promise<unknown>,
): Promise<unknown> {
  const method = (event.req.method ?? "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") return next();
  if (event.url.pathname !== "/.well-known/assetlinks.json") return next();

  const body = JSON.stringify(publishedAssetLinks(), null, 2) + "\n";
  return new Response(method === "HEAD" ? null : body, {
    headers: ASSETLINKS_JSON_HEADERS,
  });
}

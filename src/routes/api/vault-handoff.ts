import { createFileRoute } from "@tanstack/react-router";
import {
  parseVaultBackup,
  readBackupFromRequest,
  renderHandoffError,
  renderHandoffPage,
} from "@/lib/vault-backup";

function html(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
      "referrer-policy": "no-referrer",
    },
  });
}

export const Route = createFileRoute("/api/vault-handoff")({
  server: {
    handlers: {
      GET: ({ request }) => Response.redirect(new URL("/import", request.url), 302),
      POST: async ({ request }) => {
        let raw = "";
        try {
          raw = (await readBackupFromRequest(request)).trim();
        } catch {
          return html(
            renderHandoffError("The backup could not be read from that request."),
            400,
          );
        }
        if (!raw) {
          return html(renderHandoffError("The backup was empty."), 400);
        }
        const parsed = parseVaultBackup(raw);
        if (!parsed.ok) {
          return html(renderHandoffError(parsed.error), 400);
        }
        return html(renderHandoffPage(JSON.stringify(parsed.backup)));
      },
    },
  },
});

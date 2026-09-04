import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

const Input = z.object({
  imageBase64: z.string().min(80).max(1_800_000),
  mimeType: z.string().default("image/jpeg"),
});

export type IdentifyResult =
  | {
      ok: true;
      series: string;
      issue: string;
      publisher: string;
      year?: string;
      variant?: string;
      writers: string[];
      artists: string[];
      notes?: string;
    }
  | { ok: false; error: string };

export const identifyCover = createServerFn({ method: "POST" })
  .validator((data: unknown) => Input.parse(data))
  .handler(async ({ data }): Promise<IdentifyResult> => {
    const apiKey = process.env.XAI_API_KEY;
    if (!apiKey) {
      return { ok: false, error: "Cover scan is unavailable in this environment." };
    }

    const prompt = `Identify this comic book cover. Return ONLY compact JSON with keys:
series (string, series title without issue number),
issue (string, issue number or "nn" for one-shots),
publisher (string),
year (string, cover year if visible),
variant (string, empty if A cover / none),
writers (string array),
artists (string array),
notes (short string).
If it is not a comic cover, still guess the closest comic or set series to empty.`;

    try {
      const res = await fetch("https://api.x.ai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: "grok-4.5",
          max_tokens: 400,
          temperature: 0.1,
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: prompt },
                {
                  type: "image_url",
                  image_url: {
                    url: `data:${data.mimeType};base64,${data.imageBase64}`,
                  },
                },
              ],
            },
          ],
        }),
      });

      if (!res.ok) {
        return { ok: false, error: `Scan failed (${res.status}). Try a clearer photo or search instead.` };
      }

      const body = (await res.json()) as {
        choices?: { message?: { content?: string } }[];
      };
      const text = body.choices?.[0]?.message?.content ?? "";
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return { ok: false, error: "Could not read that cover. Search the catalog instead." };
      }
      const parsed = JSON.parse(jsonMatch[0]) as {
        series?: string;
        issue?: string;
        publisher?: string;
        year?: string;
        variant?: string;
        writers?: string[];
        artists?: string[];
        notes?: string;
      };
      if (!parsed.series) {
        return { ok: false, error: "No comic recognized. Search or add a custom issue." };
      }
      return {
        ok: true,
        series: String(parsed.series),
        issue: String(parsed.issue ?? "1"),
        publisher: String(parsed.publisher ?? ""),
        year: parsed.year ? String(parsed.year) : undefined,
        variant: parsed.variant ? String(parsed.variant) : undefined,
        writers: Array.isArray(parsed.writers) ? parsed.writers.map(String) : [],
        artists: Array.isArray(parsed.artists) ? parsed.artists.map(String) : [],
        notes: parsed.notes ? String(parsed.notes) : undefined,
      };
    } catch {
      return { ok: false, error: "Scan could not complete. Search the catalog instead." };
    }
  });

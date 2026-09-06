/**
 * League of Comic Geeks UPC/ISBN lookup (non-AI).
 * Prefer LOCG identity for barcodes; never invent codes.
 * Be polite: respect robots.txt Crawl-delay (30s) in batch scripts.
 */

export type LocgIssueIdentity = {
  locgId: string;
  title?: string;
  upc?: string;
  isbn?: string;
  coverUrl?: string;
  variant?: string;
  series?: string;
  issue?: string;
  publisher?: string;
  url: string;
  source: "locg";
};

const UA =
  "KryptonsToyVault/1.0 (personal collection; upc lookup; +https://github.com/MonacoCobra/kryptons-toy-vault)";

function normalizeDigits(raw: string | undefined): string | undefined {
  if (!raw) return undefined;
  const digits = raw.replace(/\D/g, "");
  if (digits.length >= 11 && digits.length <= 18) return digits;
  return undefined;
}

/** Normalize UPC/ISBN-ish codes from LOCG or CSV (digits only, no invention). */
export function normalizeUpc(raw: string | undefined | null): string | undefined {
  if (!raw?.trim()) return undefined;
  return normalizeDigits(raw.trim()) ?? (raw.trim().replace(/\s+/g, "") || undefined);
}

export function locgCoverUrl(locgId: string, size: "medium" | "large" = "large"): string {
  if (size === "medium") {
    return `https://s3.amazonaws.com/comicgeeks/comics/covers/medium-${locgId}.jpg`;
  }
  return `https://s3.amazonaws.com/comicgeeks/comics/covers/large-${locgId}.jpg`;
}

export function parseLocgComicHtml(html: string, url: string): LocgIssueIdentity | null {
  const idMatch =
    url.match(/\/comic\/(\d+)\//) ||
    html.match(/canonical" href="https:\/\/leagueofcomicgeeks\.com\/comic\/(\d+)\//);
  const locgId = idMatch?.[1];
  if (!locgId) return null;

  const h1 = html.match(/<h1[^>]*>\s*([\s\S]*?)\s*<\/h1>/i)?.[1]?.replace(/<[^>]+>/g, "").trim();
  const upcBlock =
    html.match(/UPC\s*<\/div>\s*<div[^>]*>\s*([0-9A-Za-z\-]+)/i)?.[1] ||
    html.match(/UPC[\s\S]{0,120}?([0-9]{11,18})/i)?.[1];
  const isbnBlock =
    html.match(/ISBN\s*<\/div>\s*<div[^>]*>\s*([0-9Xx\-]+)/i)?.[1] ||
    html.match(/ISBN[\s\S]{0,120}?([0-9Xx\-]{10,17})/i)?.[1];
  const og =
    html.match(/property="og:image"\s+content="([^"]+)"/i)?.[1] ||
    html.match(/content="(https:\/\/s3\.amazonaws\.com\/comicgeeks\/comics\/covers\/[^"]+)"/i)?.[1];
  const publisher =
    html.match(/href="\/comics\/[^"]+"[^>]*>\s*([^<]+)\s*<\/a>\s*&nbsp;&nbsp;·/i)?.[1]?.trim() ||
    html.match(/comics\/[a-z0-9-]+">\s*([^<]+)\s*<\/a>/i)?.[1]?.trim();

  const upc = normalizeUpc(upcBlock);
  const isbn = normalizeUpc(isbnBlock);
  const identityCode = upc || isbn;

  const issueFromTitle = h1?.match(/#\s*([0-9]+[A-Za-z]?|nn)\b/i)?.[1];
  const seriesFromTitle = h1?.replace(/\s*#\s*[0-9A-Za-z]+.*$/i, "").trim();

  return {
    locgId,
    title: h1,
    upc: identityCode,
    isbn: isbn && isbn !== upc ? isbn : undefined,
    coverUrl: og || locgCoverUrl(locgId),
    series: seriesFromTitle,
    issue: issueFromTitle,
    publisher,
    url: url.includes(`/comic/${locgId}/`)
      ? url.split("?")[0]!
      : `https://leagueofcomicgeeks.com/comic/${locgId}/`,
    source: "locg",
  };
}

/** Fetch a single LOCG comic page by numeric id (+ optional slug). */
export async function fetchLocgIssueById(
  locgId: string,
  slug = "issue",
): Promise<LocgIssueIdentity | null> {
  const url = `https://leagueofcomicgeeks.com/comic/${locgId}/${slug}`;
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": UA, Accept: "text/html" },
      redirect: "follow",
      signal: AbortSignal.timeout(45_000),
    });
    if (!res.ok) return null;
    const html = await res.text();
    if (html.length < 8_000) return null;
    return parseLocgComicHtml(html, res.url || url);
  } catch {
    return null;
  }
}

export type LocgSeriesHit = {
  seriesId: string;
  name: string;
  publisher: string;
  years?: string;
  coverComicId?: string;
};

/** Search LOCG series list (public get_comics search). */
export async function searchLocgSeries(keyword: string): Promise<LocgSeriesHit[]> {
  const url = new URL("https://leagueofcomicgeeks.com/comic/get_comics");
  url.searchParams.set("list", "search");
  url.searchParams.set("keyword", keyword);
  url.searchParams.set("format", "json");
  url.searchParams.set("view", "list");
  try {
    const res = await fetch(url.toString(), {
      headers: {
        "User-Agent": UA,
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      signal: AbortSignal.timeout(45_000),
    });
    if (!res.ok) return [];
    const data = (await res.json()) as { list?: string };
    const html = data.list ?? "";
    const hits: LocgSeriesHit[] = [];
    for (const li of html.split(/<li>/i).slice(1)) {
      const seriesId = li.match(/data-id="(\d+)"/)?.[1];
      const publisher = li.match(/copy-really-small[^>]*>\s*<span[^>]*>\s*([^<]+)/i)?.[1]?.trim();
      const name = li.match(/class="title[^"]*"[\s\S]*?data-id="\d+"\s*>\s*([^<]+)/i)?.[1]?.trim();
      const coverComicId = li.match(/medium-(\d+)\.jpg/i)?.[1];
      const years = li.match(/(\d{4}\s*-\s*(?:Present|\d{4}))/i)?.[1];
      if (!seriesId || !name || !publisher) continue;
      hits.push({ seriesId, name, publisher, years, coverComicId });
    }
    return hits;
  } catch {
    return [];
  }
}

function normPub(p: string): string {
  return p.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

export function pickLocgSeries(
  hits: LocgSeriesHit[],
  series: string,
  publisher: string,
): LocgSeriesHit | null {
  const wantSeries = series.toLowerCase().split("(")[0]!.trim();
  const wantPub = normPub(publisher);
  const scored = hits
    .map((h) => {
      const name = h.name.toLowerCase();
      const pub = normPub(h.publisher);
      let score = 0;
      if (name === wantSeries) score += 8;
      else if (name.includes(wantSeries) || wantSeries.includes(name)) score += 4;
      if (pub === wantPub) score += 6;
      else if (pub.includes(wantPub) || wantPub.includes(pub)) score += 3;
      if (/panini|jbc|fomo|marmara|urban comics|other/i.test(h.publisher)) score -= 4;
      return { h, score };
    })
    .sort((a, b) => b.score - a.score);
  const best = scored[0];
  return best && best.score >= 8 ? best.h : null;
}

/**
 * Resolve UPC (+ cover) from LOCG for series/issue.
 * Uses series search cover-id as entry for issue #1 when possible;
 * for other issues prefer an explicit locgId seed.
 */
export async function lookupLocgUpc(input: {
  series: string;
  issue: string;
  publisher?: string;
  locgId?: string;
  slug?: string;
}): Promise<LocgIssueIdentity | null> {
  if (input.locgId) {
    return fetchLocgIssueById(input.locgId, input.slug || "issue");
  }

  const hits = await searchLocgSeries(input.series);
  const seriesHit = pickLocgSeries(hits, input.series, input.publisher ?? "");
  if (!seriesHit?.coverComicId) return null;

  const entry = await fetchLocgIssueById(seriesHit.coverComicId, input.slug || "issue");
  if (!entry) return null;

  const want = input.issue.replace(/^#/, "").toLowerCase();
  if ((entry.issue || "").toLowerCase() === want) return entry;
  if (want === "1" && (entry.issue || "1").toLowerCase() === "1") return entry;
  return null;
}

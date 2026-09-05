#!/usr/bin/env python3
"""Bake real Shopify CDN product images onto curated/placeholder figures.

No generative AI. Builds a searchable product→image index from AF Shopify
storefronts (same shops as figure-storefronts / oneshot), fuzzy-matches
catalog rows that lack imageUrl, and persists high-confidence hits only.

Outputs:
  - src/data/figure-image-urls.json  (id → CDN URL, comic-cover-urls style)
  - patches imageUrl on matching rows in src/data/figure-archive/oneshot.json
  - src/data/figure-archive/image-bake-stats.json
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_oneshot.shopify_dump import STOREFRONTS, fetch_all_products, is_figure_like, tag_list  # noqa: E402

ARCHIVE_JSON = ROOT / "src/data/figure-archive/oneshot.json"
URLS_JSON = ROOT / "src/data/figure-image-urls.json"
STATS_JSON = ROOT / "src/data/figure-archive/image-bake-stats.json"
INDEX_JSON = ROOT / "src/data/figure-archive/product-image-index.json"
FIGURES_TS = ROOT / "src/data/figures.ts"

STOP = set(
    "the a an of and or for to with from series wave deluxe exclusive edition "
    "figure figures action ver version vol volume pack set new toys toy scale "
    "ultimate ultimates reaction collectibles collection comic comics movie "
    "multipack boxed bundle pack".split()
)
WEAK = set("man men boy girl king queen lord lady black white red blue green glow robot pack".split())

LINE_AS_NAME = re.compile(
    r"ultimates?!?|reaction|masters of the universe|dc multiverse|mcfarlane|"
    r"teenage mutant|g\.?i\.?\s*joe|thundercats|silverhawks|universal monsters|"
    r"toho|spongebob|wwe elite|ben cooper",
    re.I,
)

FAMILY_REQUIRE = {
    "masterverse": re.compile(r"masterverse", re.I),
    "origins": re.compile(r"origins", re.I),
    "ultimates": re.compile(r"ultimates?", re.I),
    "reaction": re.compile(r"reaction", re.I),
    "bst": re.compile(r"bst|axn|loyal", re.I),
    "wwe": re.compile(r"\bwwe\b", re.I),
    "jurassic": re.compile(r"jurassic|hammond", re.I),
    "multiverse": re.compile(r"multiverse", re.I),
    "spawn": re.compile(r"\bspawn\b", re.I),
    "tmnt": re.compile(r"tmnt|turtle|ronin", re.I),
    "universal": re.compile(r"universal monster", re.I),
    "jlu": re.compile(r"justice league unlimited|\bjlu\b", re.I),
    "dcuc": re.compile(r"dc universe classics|universe classics", re.I),
    "dcd": re.compile(r"dc direct|dc collectibles", re.I),
    "motu-generic": re.compile(r"masters of the universe|masterverse|origins", re.I),
    "hacks": re.compile(r"h\.?a\.?c\.?k|hacks|boss fight", re.I),
}

# Curated lines with no honest Shopify counterpart on our feeds — never match.
BLOCKED_FAMILIES = {"jlu", "dcuc", "dcd"}


def norm(s: str) -> str:
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s: str) -> list[str]:
    return [t for t in norm(s).split() if t and t not in STOP and len(t) > 1]


def significant_name_tokens(name: str) -> list[str]:
    toks = tokens(name)
    return [t for t in toks if t not in WEAK or len(toks) == 1]


def line_family(line: str, company: str) -> str:
    l = norm(line)
    if "masterverse" in l:
        return "masterverse"
    if "origins" in l:
        return "origins"
    if "ultimates" in l:
        return "ultimates"
    if "reaction" in l:
        return "reaction"
    if "bst" in l or "axn" in l:
        return "bst"
    if "wwe" in l or (company == "mattel" and "elite" in l):
        return "wwe"
    if "jurassic" in l or "hammond" in l:
        return "jurassic"
    if "multiverse" in l:
        return "multiverse"
    if "spawn" in l:
        return "spawn"
    if "tmnt" in l or "turtle" in l or "ronin" in l:
        return "tmnt"
    if "universal monster" in l:
        return "universal"
    if "universe classics" in l:
        return "dcuc"
    if "justice league unlimited" in l or re.search(r"\bjlu\b", l):
        return "jlu"
    if "dc direct" in l or "dc collectibles" in l:
        return "dcd"
    if "h.a.c.k" in l or "hacks" in l:
        return "hacks"
    if company == "mattel" and "masters of the universe" in l:
        return "motu-generic"
    if company == "neca":
        return "neca"
    if company == "super7":
        return "super7"
    return company


def product_character_text(name: str, subtitle: str) -> str:
    """Where the character usually lives for noisy Shopify titles."""
    n, s = name or "", subtitle or ""
    if LINE_AS_NAME.search(n) and s.strip():
        # Prefer subtitle character; keep name too for MotU "... Keldor Action Figure"
        return f"{s} {n}"
    if re.match(r"^masters of the universe\b", n, re.I):
        return f"{n} {s}"
    return f"{n} {s}"


def image_from_product(p: dict) -> str | None:
    for im in p.get("images") or []:
        src = (im or {}).get("src")
        if src and str(src).startswith("http"):
            return str(src)
    return None


def build_index_from_live() -> list[dict]:
    """Paginate Shopify products into a searchable image index."""
    index: list[dict] = []
    seen: set[str] = set()
    for source in STOREFRONTS:
        products = fetch_all_products(source)
        kept = 0
        for p in products:
            if not is_figure_like(p, source):
                continue
            img = image_from_product(p)
            if not img:
                continue
            title = str(p.get("title") or "").strip()
            if not title:
                continue
            handle = str(p.get("handle") or title)
            pid = f"{source['id']}:{handle}"[:120]
            if pid in seen:
                continue
            seen.add(pid)
            # Lightweight name/subtitle split mirroring shopify_dump
            parts = re.split(r"\s+[—–-]\s+", title)
            if len(parts) >= 2:
                name, subtitle = parts[0].strip(), " - ".join(parts[1:]).strip()
            else:
                colon = title.split(":")
                if len(colon) >= 2 and len(colon[0]) < 48:
                    name, subtitle = colon[0].strip(), ":".join(colon[1:]).strip()
                else:
                    name, subtitle = title, str(p.get("product_type") or source["id"])
            index.append(
                {
                    "id": pid,
                    "shop": source["id"],
                    "company": source["company"],
                    "name": name[:160],
                    "subtitle": subtitle[:160],
                    "line": str(p.get("product_type") or p.get("vendor") or source["id"])[:80],
                    "tags": tag_list(p.get("tags"))[:12],
                    "title": title[:240],
                    "imageUrl": img,
                }
            )
            kept += 1
        print(f"index {source['id']}: raw={len(products)} with_image={kept}")
        time.sleep(0.05)
    return index


def build_index_from_oneshot(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if r.get("source") != "shopify" or not r.get("imageUrl"):
            continue
        out.append(
            {
                "id": r["id"],
                "shop": next((t for t in (r.get("tags") or []) if t not in {"archive", "shopify", "figure", r["company"]}), r["company"]),
                "company": r["company"],
                "name": r["name"],
                "subtitle": r["subtitle"],
                "line": r["line"],
                "tags": r.get("tags") or [],
                "title": f"{r['name']} {r['subtitle']}",
                "imageUrl": r["imageUrl"],
            }
        )
    return out


def enrich_index(entries: list[dict]) -> None:
    for p in entries:
        char = product_character_text(p["name"], p["subtitle"])
        p["_char"] = norm(char)
        p["_title"] = norm(p.get("title") or f"{p['name']} {p['subtitle']}")
        p["_blob"] = norm(
            f"{p['name']} {p['subtitle']} {p['line']} {' '.join(p.get('tags') or [])} {p.get('title') or ''}"
        )
        p["_char_toks"] = set(tokens(char))


def score_pair(fig: dict, prod: dict) -> float:
    if fig["company"] != prod["company"]:
        return -1.0
    fam = line_family(fig["line"], fig["company"])
    if fam in BLOCKED_FAMILIES:
        return -1.0
    req = FAMILY_REQUIRE.get(fam)
    if req and not req.search(prod["_blob"]):
        return -1.0

    fn = significant_name_tokens(fig["name"])
    if not fn:
        return -1.0

    char = prod["_char"]
    char_toks = prod["_char_toks"]
    title = prod["_title"]

    # Figure name must live in the character-focused text (not franchise-only title).
    fname = norm(fig["name"])
    contiguous = fname in char or fname in title
    covered = [t for t in fn if t in char_toks or t in char]
    if not covered:
        return -1.0
    if len(covered) < max(1, (len(fn) + 1) // 2):
        return -1.0
    # First significant token must appear in character text
    if fn[0] not in char_toks and fn[0] not in char:
        return -1.0
    if len(fn) == 1 and fn[0] in WEAK and not contiguous:
        return -1.0

    # Anti false-positive: if product looks like line-header + other character,
    # require figure name in subtitle/character prominently.
    if LINE_AS_NAME.search(prod["name"]) and prod.get("subtitle"):
        sub_n = norm(prod["subtitle"])
        if fname not in sub_n and not all(t in set(tokens(prod["subtitle"])) for t in fn):
            # allow if name is in full MotU-style product name (Keldor at end)
            if fname not in norm(prod["name"]) and not all(t in set(tokens(prod["name"])) for t in fn):
                return -1.0

    name_score = 0.0
    if contiguous:
        name_score += 12
    name_score += 8 * len(covered) / len(fn)
    if fname == norm(prod["name"]) or fname == norm(prod.get("subtitle") or ""):
        name_score += 6

    fs = [t for t in tokens(fig["subtitle"]) if t not in WEAK]
    if fs:
        hits = sum(1 for t in fs if t in char or t in prod["_blob"])
        sub_score = 5.0 * hits / len(fs)
        # Strong wave/subtitle identity: if ≥2 tokens and zero hits, reject
        if len(fs) >= 2 and hits == 0:
            return -1.0
    else:
        sub_score = 1.0

    line_score = 4.0 if req and req.search(prod["_blob"]) else 1.0
    if re.search(r"\b(accessories|empty box|backdrop|stand only)\b", prod["_blob"]):
        return -1.0
    # Kids costume multipacks / novelty bundles are weak product photos for catalog AF
    if re.search(r"ben cooper|costume kids|costumed action figure bundle", prod["_blob"]):
        return -1.0
    # "X as Character" crossovers only if figure line/subtitle mentions crossover partner
    if re.search(r"\bas\b.+(dracula|frankenstein|mummy|wolf|creature|bride)", prod["_title"]) or re.search(
        r"(tmnt|turtle).*(x|as).*(universal|dracula|frankenstein)", prod["_blob"]
    ):
        fig_l = norm(f"{fig.get('line','')} {fig.get('subtitle','')} {' '.join(fig.get('tags') or [])}")
        if "tmnt" not in fig_l and "turtle" not in fig_l and "crossover" not in fig_l:
            return -1.0
    # Castlevania / game lines must appear on product
    if "castlevania" in norm(f"{fig['subtitle']} {fig['line']}"):
        if "castlevania" not in prod["_blob"]:
            return -1.0
    # WWE Elite curated should not take LJN / Superstars-only product shots
    if fig["company"] == "mattel" and "elite" in norm(fig["line"]):
        if re.search(r"\bljn\b", prod["_blob"]) and "elite" not in prod["_blob"]:
            return -1.0

    # Short single-token names: require whole-token match in character text (not Gizmo⊂Gizmoduck)
    if len(fn) == 1 and len(fn[0]) <= 6:
        if fn[0] not in char_toks:
            return -1.0
        # reject if only matches inside a longer compound token already handled by char_toks
        # also reject when product title clearly different character compound
        for ct in char_toks:
            if ct != fn[0] and fn[0] in ct and len(ct) > len(fn[0]) + 1:
                # e.g. gizmo in gizmoduck — char_toks has gizmoduck not gizmo, so OK;
                # if tokenizer splits wrong, still guard contiguous word boundary:
                pass
        if not re.search(rf"\b{re.escape(fn[0])}\b", char):
            return -1.0

    # Franchise / line cues for NECA curated rows
    fig_blob = norm(f"{fig['name']} {fig['subtitle']} {fig['line']} {' '.join(fig.get('tags') or [])}")
    if fig["company"] == "neca":
        # Universal Monsters: require universal monsters (reject TMNT crossover / Ben Cooper kids unless stated)
        if "universal" in fig_blob or fam == "neca" and "monster" in norm(fig.get("line") or ""):
            if "universal monster" in fig_blob or "universal monsters" in norm(fig.get("line") or ""):
                if "universal monster" not in prod["_blob"]:
                    return -1.0
                if re.search(r"\btmnt\b|ninja turtle|ben cooper", prod["_blob"]) and "universal monster" in prod["_blob"] and "x" in prod["_title"]:
                    # allow official UM x TMNT only if figure subtitle hints crossover — else reject
                    if "tmnt" not in fig_blob and "turtle" not in fig_blob:
                        return -1.0
        # Aliens / Predator / Halloween / IT cues
        for cue, rx in (
            ("alien", re.compile(r"\baliens?\b|xenomorph|bishop|ripley|hicks", re.I)),
            ("predator", re.compile(r"\bpredator\b", re.I)),
            ("halloween", re.compile(r"halloween|laurie|myers|loomis", re.I)),
            ("pennywise", re.compile(r"pennywise|\bit\b|derry", re.I)),
            ("evil dead", re.compile(r"evil dead|\bash\b", re.I)),
        ):
            if cue in fig_blob or (cue == "pennywise" and "pennywise" in fig_blob):
                if cue == "alien" and re.search(r"\baliens?\b", fig_blob):
                    if not re.search(r"\baliens?\b|xenomorph", prod["_blob"]):
                        return -1.0
                    # reject "Ben Bishop" false positive
                    if "bishop" in fname and "ben bishop" in prod["_blob"] and not re.search(r"\baliens?\b", prod["_blob"]):
                        return -1.0
                if cue == "halloween" and "halloween" in fig_blob:
                    if "halloween" not in prod["_blob"]:
                        return -1.0
                if cue == "pennywise" and "pennywise" in fig_blob:
                    if "pennywise" not in prod["_blob"] and not re.search(r"\bit\b", prod["_blob"]):
                        return -1.0

    # Skip obvious Mattel DC Premier mismatches for non-Premier curated lines
    fig_line = norm(fig["line"])
    if fig["company"] == "mattel" and "premier" in prod["_blob"]:
        if "premier" not in fig_line and "total heroes" not in fig_line:
            if fam not in {"wwe", "masterverse", "origins", "jurassic", "motu-generic"}:
                return -1.0

    total = name_score + sub_score + line_score
    if not contiguous and sub_score < 2.5:
        return -1.0
    return total


def parse_seed_ids_needing_images() -> list[dict]:
    """Pull seed tuples from figures.ts that have no baked URL yet (best-effort)."""
    # Archive is primary; seed gaps get overlay via id if we can match by reading archive+need only.
    # Seed figures without images are already partially duplicated in curated densify; skip TS parse.
    return []


def main() -> None:
    fetch_live = "--fetch" in sys.argv or "--live" in sys.argv
    use_cache = "--cache-only" in sys.argv
    min_score = 16.0

    rows = json.loads(ARCHIVE_JSON.read_text())
    before_with = sum(1 for r in rows if r.get("imageUrl"))
    before_total = len(rows)
    need = [r for r in rows if not r.get("imageUrl")]

    if use_cache and INDEX_JSON.exists():
        print(f"=== Using cached index {INDEX_JSON} ===")
        index = json.loads(INDEX_JSON.read_text())
    elif fetch_live:
        print("=== Live Shopify pagination → product image index ===")
        index = build_index_from_live()
        INDEX_JSON.write_text(json.dumps(index, indent=2) + "\n")
        print(f"wrote {INDEX_JSON} ({len(index)} products)")
    else:
        print("=== Index from oneshot Shopify rows (pass --fetch for live) ===")
        index = build_index_from_oneshot(rows)
        # Merge any prior live cache extras
        if INDEX_JSON.exists():
            cached = json.loads(INDEX_JSON.read_text())
            seen = {e["id"] for e in index}
            extra = 0
            for e in cached:
                if e["id"] not in seen and e.get("imageUrl"):
                    index.append(e)
                    seen.add(e["id"])
                    extra += 1
            if extra:
                print(f"merged {extra} cached index entries")

    enrich_index(index)
    by_co: dict[str, list[dict]] = defaultdict(list)
    for p in index:
        by_co[p["company"]].append(p)

    print(f"index size={len(index)} need_images={len(need)} before_pct={100*before_with/before_total:.1f}%")

    cands: list[tuple[float, str, str, dict, dict]] = []
    for fig in need:
        best = None
        best_s = 0.0
        for p in by_co.get(fig["company"], []):
            s = score_pair(fig, p)
            if s > best_s:
                best_s, best = s, p
        if best and best_s >= min_score:
            cands.append((best_s, fig["id"], best["id"], fig, best))

    cands.sort(reverse=True, key=lambda x: x[0])
    used_prod: set[str] = set()
    used_fig: set[str] = set()
    finals: list[tuple[float, dict, dict]] = []
    for s, fid, pid, f, p in cands:
        if fid in used_fig or pid in used_prod:
            continue
        used_fig.add(fid)
        used_prod.add(pid)
        finals.append((s, f, p))

    # Persist URL map (merge with prior)
    prior_urls: dict[str, str] = {}
    if URLS_JSON.exists():
        prior_urls = json.loads(URLS_JSON.read_text())
    urls = dict(prior_urls)
    patched = 0
    by_id = {r["id"]: r for r in rows}
    for s, f, p in finals:
        urls[f["id"]] = p["imageUrl"]
        row = by_id.get(f["id"])
        if row is not None and not row.get("imageUrl"):
            row["imageUrl"] = p["imageUrl"]
            tags = list(row.get("tags") or [])
            if "image-bake" not in tags:
                tags.append("image-bake")
            row["tags"] = tags
            patched += 1

    URLS_JSON.write_text(json.dumps(urls, indent=2, sort_keys=True) + "\n")
    ARCHIVE_JSON.write_text(json.dumps(rows, indent=2) + "\n")

    after_with = sum(1 for r in rows if r.get("imageUrl"))
    stats = {
        "bakedAt": datetime.now(timezone.utc).isoformat(),
        "day": date.today().isoformat(),
        "minScore": min_score,
        "indexSize": len(index),
        "fetchLive": fetch_live,
        "before": {"total": before_total, "withImage": before_with, "pct": round(100 * before_with / before_total, 2)},
        "after": {"total": len(rows), "withImage": after_with, "pct": round(100 * after_with / len(rows), 2)},
        "matched": len(finals),
        "candidatesAboveThreshold": len(cands),
        "patchedOneshot": patched,
        "urlMapSize": len(urls),
        "byCompany": dict(Counter(f["company"] for _, f, _ in finals).most_common()),
        "safeguards": [
            "same-company hard gate",
            "blocked families: JLU/DCUC/DC Direct (no honest Shopify line)",
            "line-family regex required when known",
            "character-focused name match (subtitle for ULTIMATES/ReAction headers)",
            "first significant name token required",
            "multi-token subtitle requires ≥1 hit",
            "one product image → one figure (best score)",
            "Mattel DC Premier not used for unrelated curated lines",
        ],
        "samples": [
            {
                "score": round(s, 2),
                "figureId": f["id"],
                "figure": f"{f['name']} / {f['subtitle']} / {f['line']}",
                "product": f"{p['name']} / {p['subtitle']}",
                "imageUrl": p["imageUrl"][:100],
            }
            for s, f, p in finals[:12]
        ],
        "lowSamples": [
            {
                "score": round(s, 2),
                "figureId": f["id"],
                "figure": f"{f['name']} / {f['subtitle']} / {f['line']}",
                "product": f"{p['name']} / {p['subtitle']}",
            }
            for s, f, p in finals[-8:]
        ],
    }
    STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps({k: stats[k] for k in ("before", "after", "matched", "byCompany")}, indent=2))
    print(f"wrote {URLS_JSON} ({len(urls)} urls)")
    print(f"patched oneshot imageUrl on {patched} rows")
    leftovers_by_co = Counter(r["company"] for r in rows if not r.get("imageUrl"))
    print("leftovers by company:", dict(leftovers_by_co.most_common(15)))


if __name__ == "__main__":
    main()

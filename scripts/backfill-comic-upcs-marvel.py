#!/usr/bin/env python3
"""DEPRECATED: Marvel public API is shut down. Do not run.

Use LOCG parallel workers or Shopify retailer backfill instead.
"""
import sys
print("Marvel API is shut down — refusing to run.", file=sys.stderr)
raise SystemExit(2)

#!/usr/bin/env python3
"""Backfill comic UPC/ISBN from Marvel Comics API (gateway.marvel.com).

Much faster than LOCG (polite ~0.2–0.5s pacing; Marvel allows higher throughput).
Never invents codes. Never overwrites an existing non-empty UPC in comic-upc-map.json
unless --force (still refuses to invent).

Keys (first match wins):
  1. Env MARVEL_PUBLIC_KEY + MARVEL_PRIVATE_KEY
  2. /home/box/.config/krypton/marvel-api.json
     { "publicKey": "...", "privateKey": "..." }
  3. /home/box/.config/krypton/marvel-public-key + marvel-private-key files

Comic objects expose upc / isbn / ean / diamondCode. We store upc or isbn digits.

Examples:
  python3 scripts/backfill-comic-upcs-marvel.py --limit 500 --delay 0.35
  python3 scripts/backfill-comic-upcs-marvel.py --ones-only --min-year 2015 --limit 800
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
COMICS_TS = ROOT / "src/data/comics.ts"
STATS = ROOT / "scripts/comic-upc-marvel-stats.json"
SKIP = ROOT / "scripts/comic-upc-marvel-skip.json"
KEY_JSON = Path("/home/box/.config/krypton/marvel-api.json")
KEY_PUB_FILE = Path("/home/box/.config/krypton/marvel-public-key")
KEY_PRIV_FILE = Path("/home/box/.config/krypton/marvel-private-key")

UA = (
    "KryptonsToyVault/1.0 (personal collection; marvel upc backfill; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)
BASE = "https://gateway.marvel.com/v1/public"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_upc(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if 11 <= len(digits) <= 18:
        return digits
    cleaned = raw.strip()
    return cleaned or None


def load_keys() -> tuple[str, str] | None:
    pub = os.environ.get("MARVEL_PUBLIC_KEY", "").strip()
    priv = os.environ.get("MARVEL_PRIVATE_KEY", "").strip()
    if pub and priv:
        return pub, priv
    if KEY_JSON.exists():
        try:
            data = json.loads(KEY_JSON.read_text())
            pub = (data.get("publicKey") or data.get("public") or data.get("apikey") or "").strip()
            priv = (data.get("privateKey") or data.get("private") or data.get("secret") or "").strip()
            if pub and priv:
                return pub, priv
        except Exception as e:
            print(f"marvel-api.json read error: {e}", file=sys.stderr)
    try:
        pub = KEY_PUB_FILE.read_text().strip()
        priv = KEY_PRIV_FILE.read_text().strip()
        if pub and priv:
            return pub, priv
    except OSError:
        pass
    return None


def keys_help() -> str:
    return (
        "Marvel API keys missing.\n"
        "Register at https://developer.marvel.com/account then store:\n"
        f"  {KEY_JSON}  → {{\"publicKey\":\"...\",\"privateKey\":\"...\"}}\n"
        "or env MARVEL_PUBLIC_KEY + MARVEL_PRIVATE_KEY\n"
        f"(same vault pattern as {Path('/home/box/.config/krypton/comicvine-api-key')})"
    )


def auth_params(pub: str, priv: str) -> dict[str, str]:
    ts = str(int(time.time() * 1000))
    h = hashlib.md5(f"{ts}{priv}{pub}".encode("utf-8")).hexdigest()
    return {"ts": ts, "apikey": pub, "hash": h}


def marvel_get(path: str, pub: str, priv: str, params: dict) -> dict:
    q = dict(params)
    q.update(auth_params(pub, priv))
    url = f"{BASE}{path}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as res:
        return json.loads(res.read().decode("utf-8", "ignore"))


def parse_comics_meta() -> dict[str, dict]:
    # Reuse same regex as LOCG backfill
    text = COMICS_TS.read_text()
    pat = re.compile(
        r'\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*'
        r'"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*([0-9.]+),\s*"([^"]+)",\s*'
        r'([0-9.]+),\s*([0-9]+),\s*"([^"]*)"',
        re.M,
    )
    out: dict[str, dict] = {}
    for m in pat.finditer(text):
        cid, series, issue, publisher, cover_date = (
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(4),
            m.group(5),
        )
        fmt = m.group(10)
        rest = text[m.end() : m.end() + 400]
        variant = None
        upc = None
        em = re.search(r"\{([^}]*)\}\s*\]", rest)
        if em and "upc" in em.group(1):
            um = re.search(r'upc:\s*"([^"]+)"', em.group(1))
            if um:
                upc = um.group(1)
        if em and "variant" in em.group(1):
            vm = re.search(r'variant:\s*"([^"]+)"', em.group(1))
            if vm:
                variant = vm.group(1)
        out[cid] = {
            "series": series,
            "issue": issue,
            "publisher": publisher,
            "coverDate": cover_date,
            "variant": variant,
            "upc": upc,
            "format": fmt,
        }
    return out


def series_core(name: str) -> str:
    s = re.sub(r"\s*\([^)]*\)\s*", " ", name)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def title_matches(marvel_title: str, want_series: str, want_issue: str) -> bool:
    t = (marvel_title or "").lower()
    # Marvel titles often: "Amazing Spider-Man (2018) #1"
    im = re.search(r"#\s*([0-9]+(?:\.[0-9]+)?)", t)
    if not im:
        return False
    got_iss = im.group(1)
    want = str(want_issue).lstrip("#").lower()
    if got_iss.split(".")[0] != want.split(".")[0] and got_iss != want:
        return False
    core = series_core(want_series)
    # strip issue from marvel title for series compare
    st = re.sub(r"#\s*[0-9].*$", "", t)
    st = series_core(st)
    if core == st or core in st or st in core:
        return True
    # token overlap
    wt = {x for x in core.split() if len(x) > 2 and x not in {"the", "and"}}
    gt = set(st.split())
    return bool(wt) and len(wt & gt) >= max(1, len(wt) - 1)


def pick_code(comic: dict) -> tuple[str | None, str | None]:
    upc = normalize_upc(comic.get("upc"))
    isbn = normalize_upc(comic.get("isbn"))
    ean = normalize_upc(comic.get("ean"))
    if upc:
        return upc, "upc"
    if isbn:
        return isbn, "isbn"
    if ean:
        return ean, "ean"
    return None, None


def cover_from(comic: dict) -> str | None:
    img = comic.get("thumbnail") or {}
    path = img.get("path") or ""
    ext = img.get("extension") or "jpg"
    if not path or "image_not_available" in path:
        return None
    # Prefer portrait/uncanny detail when available via path; thumbnail is fine
    return f"{path}.{ext}"


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--delay", type=float, default=0.35, help="Seconds between Marvel API calls")
    ap.add_argument("--min-year", type=int, default=2005)
    ap.add_argument("--ones-only", action="store_true")
    ap.add_argument("--max-minutes", type=float, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Replace existing UPC (still must be real Marvel code)")
    ap.add_argument("--only", type=str, default="")
    args = ap.parse_args()

    keys = load_keys()
    if not keys:
        print(keys_help(), file=sys.stderr)
        save_json(
            STATS,
            {
                "startedAt": now_iso(),
                "finishedAt": now_iso(),
                "error": "missing_marvel_api_keys",
                "help": keys_help(),
                "vaultPath": str(KEY_JSON),
            },
        )
        return 2

    pub, priv = keys
    upc_map = load_json(UPC_MAP, {})
    cover_urls = load_json(COVER_URLS, {})
    skip = load_json(SKIP, {})
    meta = parse_comics_meta()
    before_upc = len([1 for v in upc_map.values() if v.get("upc")])

    # Probe API health once
    try:
        probe = marvel_get("/comics", pub, priv, {"limit": 1, "format": "comic", "noVariants": "true"})
        if probe.get("code") not in (200, "200", 200):
            print(f"Marvel API unexpected: {probe.get('code')} {probe.get('status')}", file=sys.stderr)
    except Exception as e:
        print(f"Marvel API probe failed: {e}", file=sys.stderr)
        print(keys_help(), file=sys.stderr)
        save_json(
            STATS,
            {
                "startedAt": now_iso(),
                "finishedAt": now_iso(),
                "error": f"probe_failed:{e}",
                "help": keys_help(),
            },
        )
        return 3

    # Candidates: Marvel publisher, missing UPC
    cands: list[str] = []
    if args.only:
        cands = [x.strip() for x in args.only.split(",") if x.strip()]
    else:
        scored: list[tuple[float, str]] = []
        for cid, m in meta.items():
            if "Marvel" not in (m.get("publisher") or ""):
                continue
            if (m.get("format") or "single") not in ("single", "one-shot", "annual", "giant"):
                continue
            if m.get("variant"):
                continue
            if cid.endswith("-fac") or m.get("format") == "facsimile":
                continue
            existing = (upc_map.get(cid) or {}).get("upc") or m.get("upc")
            if existing and not args.force:
                continue
            if cid in skip:
                continue
            d = m.get("coverDate") or ""
            y = int(d[:4]) if d[:4].isdigit() else 0
            if y and y < args.min_year:
                continue
            iss = str(m.get("issue") or "").lstrip("#")
            if args.ones_only and iss not in ("1", "0", "nn"):
                continue
            score = 0.0
            if iss in ("1", "0"):
                score += 20
            if y >= 2015:
                score += 10
            if y >= 2020:
                score += 5
            scored.append((score, cid))
        scored.sort(key=lambda x: -x[0])
        cands = [c for _, c in scored[: args.limit]]

    print(f"marvel-upc: {len(cands)} candidates, delay={args.delay}s, before_upc={before_upc}")
    stats = {
        "startedAt": now_iso(),
        "attempted": 0,
        "upcFilled": 0,
        "coverUpdated": 0,
        "noCode": 0,
        "mismatch": 0,
        "errors": 0,
        "skippedExisting": 0,
        "beforeUpc": before_upc,
        "details": [],
    }
    started = time.time()
    deadline = started + args.max_minutes * 60 if args.max_minutes and args.max_minutes > 0 else None

    for cid in cands:
        if deadline and time.time() >= deadline:
            stats["timedOut"] = True
            break
        m = meta.get(cid) or {}
        existing = upc_map.get(cid) or {}
        if existing.get("upc") and not args.force:
            stats["skippedExisting"] += 1
            continue

        stats["attempted"] += 1
        series = m.get("series") or ""
        issue = str(m.get("issue") or "").lstrip("#")
        year = (m.get("coverDate") or "")[:4]
        # Marvel search: title + issueNumber
        params: dict = {
            "format": "comic",
            "formatType": "comic",
            "noVariants": "true",
            "limit": 20,
            "orderBy": "-onsaleDate",
        }
        # Prefer titleStartsWith of series core without year suffix
        title_q = re.sub(r"\s*\([^)]*\)\s*", " ", series).strip()
        params["titleStartsWith"] = title_q[:80]
        if issue.isdigit():
            params["issueNumber"] = issue
        if year.isdigit():
            # narrow window around cover year
            y = int(year)
            params["dateRange"] = f"{y-1}-01-01,{y+1}-12-31"

        time.sleep(args.delay)
        try:
            data = marvel_get("/comics", pub, priv, params)
        except urllib.error.HTTPError as e:
            stats["errors"] += 1
            body = ""
            try:
                body = e.read().decode("utf-8", "ignore")[:200]
            except Exception:
                pass
            print(f"! {cid}: HTTP {e.code} {body}", file=sys.stderr)
            if e.code in (401, 403, 429):
                print("Stopping on auth/rate limit", file=sys.stderr)
                break
            continue
        except Exception as e:
            stats["errors"] += 1
            print(f"! {cid}: {e}", file=sys.stderr)
            continue

        results = ((data.get("data") or {}).get("results")) or []
        hit = None
        for r in results:
            if title_matches(r.get("title") or "", series, issue):
                # Prefer records that actually have a code
                code, _ = pick_code(r)
                if code:
                    hit = r
                    break
                if hit is None:
                    hit = r
        if not hit:
            # retry with exact title param
            params2 = dict(params)
            params2["title"] = title_q
            time.sleep(args.delay)
            try:
                data = marvel_get("/comics", pub, priv, params2)
                results = ((data.get("data") or {}).get("results")) or []
                for r in results:
                    if title_matches(r.get("title") or "", series, issue):
                        code, _ = pick_code(r)
                        if code:
                            hit = r
                            break
                        if hit is None:
                            hit = r
            except Exception as e:
                print(f"  retry err {cid}: {e}", file=sys.stderr)

        if not hit:
            stats["mismatch"] += 1
            print(f"· {cid}: no Marvel match for {series} #{issue}")
            continue

        code, kind = pick_code(hit)
        cover = cover_from(hit)
        detail = {
            "id": cid,
            "marvelId": hit.get("id"),
            "title": hit.get("title"),
            "codeKind": kind,
            "upc": code,
        }
        if not code:
            stats["noCode"] += 1
            detail["status"] = "marvel_no_upc"
            # Still keep marvel id for later; do not invent
            if not args.dry_run:
                entry = dict(existing)
                entry.update(
                    {
                        "source": "marvel-api",
                        "marvelId": str(hit.get("id")),
                        "title": hit.get("title"),
                        "fetchedAt": now_iso(),
                    }
                )
                if cover and not entry.get("coverUrl"):
                    entry["coverUrl"] = cover
                # only write if no conflicting upc
                if not entry.get("upc"):
                    upc_map[cid] = {k: v for k, v in entry.items() if v}
            print(f"· {cid}: Marvel hit but no upc/isbn — {hit.get('title')}")
            stats["details"].append(detail)
            continue

        # Do not overwrite a good LOCG UPC with Marvel unless force
        if existing.get("upc") and not args.force:
            src = str(existing.get("source") or "")
            if "locg" in src or existing.get("upc"):
                stats["skippedExisting"] += 1
                continue

        stats["upcFilled"] += 1
        detail["status"] = "marvel_upc"
        if not args.dry_run:
            entry = dict(existing)
            # Preserve locgId if present
            entry.update(
                {
                    "upc": code,
                    "source": ("locg+marvel-api" if existing.get("locgId") else "marvel-api"),
                    "marvelId": str(hit.get("id")),
                    "title": hit.get("title"),
                    "url": f"https://gateway.marvel.com/docs#!/public/getComicCollection_get_0",
                    "fetchedAt": now_iso(),
                }
            )
            if cover:
                entry["coverUrl"] = entry.get("coverUrl") or cover
                # Only bake Marvel cover if we don't already have LOCG cover
                if cid not in cover_urls or "comicgeeks" not in str(cover_urls.get(cid)):
                    if "comicgeeks" not in str(entry.get("coverUrl") or ""):
                        # Prefer not replacing LOCG covers; if no cover yet, skip Marvel image
                        # (Marvel thumbnails are OK as last resort only when empty)
                        if cid not in cover_urls:
                            pass  # don't bake Marvel digital thumbs as primary art by default
            upc_map[cid] = {k: v for k, v in entry.items() if v}
            # merge-safe write
            disk = load_json(UPC_MAP, {})
            for k, ent in upc_map.items():
                cur = dict(disk.get(k) or {})
                if cur.get("upc") and "locg" in str(cur.get("source") or "") and ent.get("upc") and cur.get("upc") != ent.get("upc"):
                    ent = {**ent, "upc": cur["upc"], "source": cur.get("source"), "locgId": cur.get("locgId") or ent.get("locgId")}
                disk[k] = {**cur, **{a: b for a, b in ent.items() if b is not None}}
            upc_map = disk
            save_json(UPC_MAP, upc_map)
            if stats["upcFilled"] % 25 == 0:
                save_json(STATS, {**stats, "details": stats["details"][-50:]})
        print(f"✓ {cid}: {kind}={code} marvel={hit.get('id')} {hit.get('title')}")
        stats["details"].append(detail)

    stats["finishedAt"] = now_iso()
    stats["elapsedMinutes"] = round((time.time() - started) / 60, 2)
    stats["afterUpc"] = len([1 for v in upc_map.values() if v.get("upc")])
    stats["coverUrlSize"] = len(cover_urls)
    if not args.dry_run:
        save_json(UPC_MAP, upc_map)
        save_json(STATS, stats)
    print(json.dumps({k: stats[k] for k in stats if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

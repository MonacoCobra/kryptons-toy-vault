#!/usr/bin/env python3
"""Backfill comic UPC/ISBN from Metron (metron.cloud) API with basic auth.

Credentials (never commit):
  /home/box/.config/krypton/metron-username
  /home/box/.config/krypton/metron-password

Rate limits (Shelby): half of Metron's published caps → 10 req/min, 2500/day.
Hard floor is 6s between HTTP calls via a shared rate file; daily counter stops
the run when the cap is hit.

Never invents codes. Never overwrites an existing UPC. Uses flock on map writes
so it can run beside the GCD backfill.

Examples:
  python3 scripts/backfill-comic-upcs-metron.py --limit 50 --dry-run
  python3 scripts/backfill-comic-upcs-metron.py --limit 200 --delay 6 --min-year 2005
"""
from __future__ import annotations

import argparse
import base64
import fcntl
import json
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
COMICS_TS = ROOT / "src/data/comics.ts"
STATS = ROOT / "scripts/comic-upc-metron-stats.json"
DAILY_COUNTER = ROOT / "scripts/comic-upc-metron-daily.json"
RATE_STATE = ROOT / "scripts/comic-upc-metron-rate.json"
USER_FILE = Path("/home/box/.config/krypton/metron-username")
PASS_FILE = Path("/home/box/.config/krypton/metron-password")
API = "https://metron.cloud/api"

# Half of Metron published caps (20/min, 5000/day).
METRON_RPM = 10
METRON_DAILY_CAP = 2500
METRON_MIN_INTERVAL = 60.0 / METRON_RPM  # 6.0s

UA = (
    "KryptonsToyVault/1.0 (personal collection; metron upc backfill; "
    "+https://github.com/MonacoCobra/kryptons-toy-vault)"
)


class DailyCapReached(Exception):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_upc(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("111111"):
        return None
    if 11 <= len(digits) <= 18:
        return digits
    return None


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def parse_comics_meta() -> dict[str, dict]:
    text = COMICS_TS.read_text()
    pat = re.compile(
        r'\["([^"]+)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*'
        r'"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*([0-9.]+),\s*"([^"]+)",\s*'
        r'([0-9.]+),\s*([0-9]+),\s*"([^"]*)"',
        re.M,
    )
    out: dict[str, dict] = {}
    for m in pat.finditer(text):
        out[m.group(1)] = {
            "series": m.group(2),
            "issue": m.group(3),
            "publisher": m.group(4),
            "coverDate": m.group(10),
        }
    return out


def series_base_and_year(series: str) -> tuple[str, int | None]:
    s = (series or "").strip()
    ym = re.search(r"\((19|20)\d{2}\)\s*$", s)
    year = int(ym.group(0)[1:5]) if ym else None
    base = re.sub(r"\s*\((19|20)\d{2}\)\s*$", "", s).strip()
    return base, year


def cover_year(meta: dict) -> int | None:
    _, sy = series_base_and_year(meta.get("series") or "")
    if sy:
        return sy
    cd = str(meta.get("coverDate") or "")
    m = re.search(r"(19|20)\d{2}", cd)
    return int(m.group(0)) if m else None


def issue_key(issue: str) -> str | None:
    iss = str(issue or "").lstrip("#").strip()
    if not iss:
        return None
    if re.match(r"^\d", iss):
        try:
            return str(int(float(re.split(r"[^\d.]", iss, maxsplit=1)[0])))
        except Exception:
            return iss
    return iss


def load_auth_header() -> str:
    if not USER_FILE.exists() or not PASS_FILE.exists():
        raise SystemExit("Missing Metron credentials under /home/box/.config/krypton/")
    user = USER_FILE.read_text().strip()
    pw = PASS_FILE.read_text().strip()
    if not user or not pw:
        raise SystemExit("Empty Metron credentials")
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return f"Basic {token}"


def _utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_daily() -> dict:
    d = load_json(DAILY_COUNTER, {})
    if d.get("day") != _utc_day():
        return {"day": _utc_day(), "requests": 0}
    return {"day": d["day"], "requests": int(d.get("requests") or 0)}


def save_daily(d: dict) -> None:
    save_json(DAILY_COUNTER, d)


def daily_remaining() -> int:
    return max(0, METRON_DAILY_CAP - int(load_daily().get("requests") or 0))


def wait_for_rate_slot(extra_delay: float = 0.0) -> None:
    """Enforce <= METRON_RPM across processes via flocked rate file."""
    RATE_STATE.parent.mkdir(parents=True, exist_ok=True)
    if not RATE_STATE.exists():
        RATE_STATE.write_text("{}\n")
    with open(RATE_STATE, "a+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        raw = f.read().strip()
        st = json.loads(raw) if raw else {}
        last = float(st.get("lastRequestAt") or 0)
        now = time.time()
        wait = max(METRON_MIN_INTERVAL - (now - last), float(extra_delay or 0.0), 0.0)
        if wait > 0:
            # release lock while sleeping so we don't block writers forever
            st["lastRequestAt"] = now + wait
            f.seek(0)
            f.truncate()
            f.write(json.dumps(st) + "\n")
            f.flush()
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            time.sleep(wait)
            with open(RATE_STATE, "a+", encoding="utf-8") as f2:
                fcntl.flock(f2.fileno(), fcntl.LOCK_EX)
                f2.seek(0)
                raw2 = f2.read().strip()
                st2 = json.loads(raw2) if raw2 else {}
                st2["lastRequestAt"] = time.time()
                f2.seek(0)
                f2.truncate()
                f2.write(json.dumps(st2) + "\n")
                f2.flush()
                fcntl.flock(f2.fileno(), fcntl.LOCK_UN)
            return
        st["lastRequestAt"] = now
        f.seek(0)
        f.truncate()
        f.write(json.dumps(st) + "\n")
        f.flush()
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def bump_daily() -> int:
    d = load_daily()
    d["requests"] = int(d.get("requests") or 0) + 1
    save_daily(d)
    return int(d["requests"])


def http_get_json(url: str, auth: str, delay: float = 0.0) -> dict | None:
    if daily_remaining() <= 0:
        raise DailyCapReached(f"Metron daily cap {METRON_DAILY_CAP} reached for {_utc_day()}")
    # Hard floor 10 rpm; --delay only adds wait above that when larger.
    extra = max(0.0, float(delay or 0.0) - METRON_MIN_INTERVAL)
    wait_for_rate_slot(extra_delay=extra)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": auth,
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                used = bump_daily()
                if used % 50 == 0:
                    print(f"  metron daily usage {used}/{METRON_DAILY_CAP}", file=sys.stderr)
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 4:
                wait = min(120, 10 * (2 ** attempt))
                print(f"  HTTP {e.code} — backing off {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"  HTTP {e.code} {url}", file=sys.stderr)
            bump_daily()
            return None
        except DailyCapReached:
            raise
        except Exception as e:
            print(f"  GET error {url}: {e}", file=sys.stderr)
            return None
    return None


def norm_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def pick_issue(results: list[dict], series_name: str, year: int, auth: str, delay: float) -> dict | None:
    """Fetch details and pick best exact-ish series match with a barcode."""
    want = norm_name(series_name)
    scored: list[tuple[int, dict]] = []
    for r in results:
        detail = http_get_json(f"{API}/issue/{r['id']}/", auth, delay)
        if not isinstance(detail, dict):
            continue
        code = normalize_upc(detail.get("upc")) or normalize_upc(detail.get("isbn"))
        if not code:
            continue
        ser = detail.get("series") or {}
        sname = norm_name(str(ser.get("name") or ""))
        yb = ser.get("year_began")
        score = 0
        if sname == want:
            score += 50
        elif want in sname or sname in want:
            score += 15
        else:
            wt = set(want.split())
            st = set(sname.split())
            if not wt or len(wt & st) / max(1, len(wt)) < 0.6:
                continue
            score += 5
        if yb == year:
            score += 20
        elif isinstance(yb, int) and abs(yb - year) <= 1:
            score += 8
        stype = ((ser.get("series_type") or {}).get("name") or "").lower()
        if "single" in stype or stype == "":
            score += 3
        if "one-shot" in stype or "fcbd" in sname or "free comic book day" in sname:
            score -= 10
        scored.append((score, detail))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    best_score, best = scored[0]
    if best_score < 50:
        return None
    return best


def flock_merge_upc(local: dict) -> dict:
    UPC_MAP.parent.mkdir(parents=True, exist_ok=True)
    with open(UPC_MAP, "a+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        raw = f.read()
        disk = json.loads(raw) if raw.strip() else {}
        for cid, new in local.items():
            cur = dict(disk.get(cid) or {})
            if cur.get("upc"):
                continue
            if not new.get("upc"):
                continue
            cur.update({k: v for k, v in new.items() if v is not None})
            disk[cid] = cur
        f.seek(0)
        f.truncate()
        f.write(json.dumps(disk, indent=2, sort_keys=True) + "\n")
        f.flush()
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return disk


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument(
        "--delay",
        type=float,
        default=6.0,
        help="Per-call spacing; hard floor is 6s (10 req/min) regardless",
    )
    ap.add_argument("--min-year", type=int, default=2005)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", type=str, default="")
    ap.add_argument("--reverse", action="store_true", help="Process candidates in reverse (for pairing with GCD)")
    ap.add_argument("--max-minutes", type=float, default=0)
    args = ap.parse_args()

    auth = load_auth_header()
    meta = parse_comics_meta()
    upc_map = load_json(UPC_MAP, {})

    if args.only:
        ids = [x.strip() for x in args.only.split(",") if x.strip()]
    else:
        ids = [
            cid
            for cid, m in meta.items()
            if not (upc_map.get(cid) or {}).get("upc")
            and cover_year(m) is not None
            and cover_year(m) >= args.min_year
        ]
        ids.sort(reverse=bool(args.reverse))
    ids = ids[: args.limit]
    before = len([1 for v in upc_map.values() if isinstance(v, dict) and v.get("upc")])
    deadline = time.time() + args.max_minutes * 60 if args.max_minutes > 0 else None

    local: dict = {}
    details = []
    filled = skipped = no_match = no_barcode = errors = 0
    daily = load_daily()

    print(
        f"metron backfill: {len(ids)} candidates, delay={args.delay}, min_year={args.min_year}, "
        f"rpm_cap={METRON_RPM}, daily_cap={METRON_DAILY_CAP}, daily_used={daily.get('requests')}"
    )
    print(f"before upc={before}")

    try:
        for cid in ids:
            if deadline and time.time() >= deadline:
                print("max-minutes reached")
                break
            if daily_remaining() <= 0:
                raise DailyCapReached(f"Metron daily cap {METRON_DAILY_CAP} reached for {_utc_day()}")
            disk_ent = (load_json(UPC_MAP, {}) if not args.dry_run else upc_map).get(cid) or {}
            if disk_ent.get("upc") or (local.get(cid) or {}).get("upc"):
                skipped += 1
                continue
            m = meta.get(cid) or {}
            base, sy = series_base_and_year(m.get("series") or "")
            year = sy or cover_year(m)
            iss = issue_key(m.get("issue") or "")
            if not base or not iss or year is None:
                no_match += 1
                continue

            q = urllib.parse.urlencode(
                {
                    "series_name": base,
                    "number": iss,
                    "series_year_began": year,
                }
            )
            data = http_get_json(f"{API}/issue/?{q}", auth, args.delay)
            if not isinstance(data, dict):
                errors += 1
                continue
            results = list(data.get("results") or [])
            if not results:
                q2 = urllib.parse.urlencode({"series_name": base, "number": iss})
                data = http_get_json(f"{API}/issue/?{q2}", auth, args.delay)
                results = list((data or {}).get("results") or []) if isinstance(data, dict) else []
            if not results:
                no_match += 1
                details.append({"id": cid, "status": "no_results"})
                print(f"· {cid}: no Metron results for {base!r} #{iss} ({year})")
                continue

            # Keep detail fetches tiny to respect daily budget.
            hit = pick_issue(results[:3], base, year, auth, args.delay)
            if not hit:
                no_match += 1
                details.append({"id": cid, "status": "no_confident_match"})
                print(f"· {cid}: no confident Metron match for {base!r} #{iss}")
                continue

            code = normalize_upc(hit.get("upc")) or normalize_upc(hit.get("isbn"))
            if not code:
                no_barcode += 1
                continue

            entry = {
                "upc": code,
                "source": "metron",
                "sourceId": str(hit.get("id")),
                "title": ((hit.get("series") or {}).get("name") or base),
                "fetchedAt": now_iso(),
            }
            local[cid] = entry
            filled += 1
            details.append({"id": cid, "status": "metron_upc", "upc": code})
            print(f"✓ {cid}: upc={code} metron={entry['sourceId']} {entry['title']} #{iss}")

            if not args.dry_run and filled % 10 == 0:
                upc_map = flock_merge_upc(local)
                local = {}
    except DailyCapReached as e:
        print(f"stopping: {e}")

    if not args.dry_run and local:
        upc_map = flock_merge_upc(local)

    upc_map = load_json(UPC_MAP, upc_map)
    after = len([1 for v in upc_map.values() if isinstance(v, dict) and v.get("upc")])
    daily = load_daily()
    stats = {
        "startedAt": now_iso(),
        "finishedAt": now_iso(),
        "beforeUpc": before,
        "afterUpc": after,
        "upcFilled": filled,
        "skippedExisting": skipped,
        "noMatch": no_match,
        "noBarcode": no_barcode,
        "errors": errors,
        "limit": args.limit,
        "minYear": args.min_year,
        "dryRun": bool(args.dry_run),
        "rpmCap": METRON_RPM,
        "dailyCap": METRON_DAILY_CAP,
        "dailyUsed": daily.get("requests"),
        "details": details[:200],
    }
    if not args.dry_run:
        save_json(STATS, stats)
    print(json.dumps({k: stats[k] for k in stats if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

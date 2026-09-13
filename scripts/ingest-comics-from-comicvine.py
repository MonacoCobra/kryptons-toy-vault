#!/usr/bin/env python3
"""Ingest NEW verified comic catalog rows from Comic Vine (cv_id + covers).

Rate ~200/hr; backoff on HTTP 420. No Metron calls.

  python3 scripts/ingest-comics-from-comicvine.py --dry-run
  python3 scripts/ingest-comics-from-comicvine.py --limit-add 400 --inject
"""
from __future__ import annotations
import argparse, html, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
sys.path.insert(0, str(ROOT / "scripts"))
from comic_backlog_common import FLOOR, BACKLOG, inject_batch, load_live_blocklists  # noqa: E402

UPC_MAP = ROOT / "src/data/comic-upc-map.json"
COVER_URLS = ROOT / "src/data/comic-cover-urls.json"
STATE = ROOT / "scripts/comic-cv-ingest-state.json"
STATS = ROOT / "scripts/comic-cv-ingest-stats.json"
CV_KEY_FILE = Path("/home/box/.config/krypton/comicvine-api-key")
CV_API = "https://comicvine.gamespot.com/api"
UA = "KryptonsToyVault/1.0 (personal collection; cv catalog ingest; +https://github.com/MonacoCobra/kryptons-toy-vault)"
CV_HOURLY_CAP = 200
CV_MIN_INTERVAL = 3600.0 / CV_HOURLY_CAP

PRIORITY_VOLUMES = [
    (46568, "Saga", "Image Comics", "im-saga", "7c2d12,1e3a8a,fbbf24", "Brian K. Vaughan", "Fiona Staples"),
    (17993, "Invincible", "Image Comics", "im-inv", "1e3a8a,dc2626,f8fafc", "Robert Kirkman", "Ryan Ottley / Cory Walker"),
    (4937, "Spawn", "Image Comics", "im-spawn", "111827,166534,dc2626", "Todd McFarlane / Various", "Todd McFarlane / Various"),
    (133722, "Radiant Black", "Image Comics", "im-rb", "111827,0ea5e9,f8fafc", "Kyle Higgins", "Various"),
    (59366, "East of West", "Image Comics", "im-eow", "1e3a8a,dc2626,f8fafc", "Jonathan Hickman", "Nick Dragotta"),
    (85128, "Paper Girls", "Image Comics", "im-pg", "1e3a8a,dc2626,f8fafc", "Brian K. Vaughan", "Cliff Chiang"),
    (85776, "Monstress", "Image Comics", "im-mon", "1e3a8a,dc2626,f8fafc", "Marjorie Liu", "Sana Takeda"),
    (107948, "Ice Cream Man", "Image Comics", "im-icm", "1e3a8a,dc2626,f8fafc", "W. Maxwell Prince", "Martín Morazzo"),
    (71032, "Deadly Class", "Image Comics", "im-dc", "1e3a8a,dc2626,f8fafc", "Rick Remender", "Wes Craig"),
    (69537, "Black Science", "Image Comics", "im-bs", "1e3a8a,dc2626,f8fafc", "Rick Remender", "Matteo Scalera"),
    (73649, "Nailbiter", "Image Comics", "im-nail", "1e3a8a,dc2626,f8fafc", "Joshua Williamson", "Mike Henderson"),
    (130740, "The Department of Truth", "Image Comics", "im-dot", "1e3a8a,dc2626,f8fafc", "James Tynion IV", "Martin Simmonds"),
    (122630, "Undiscovered Country", "Image Comics", "im-uc", "1e3a8a,dc2626,f8fafc", "Scott Snyder / Charles Soule", "Giuseppe Camuncoli"),
    (131724, "Crossover", "Image Comics", "im-xo", "1e3a8a,dc2626,f8fafc", "Donny Cates", "Geoff Shaw"),
    (130377, "Stillwater", "Image Comics", "im-sw", "1e3a8a,dc2626,f8fafc", "Chip Zdarsky", "Ramón Pérez"),
    (115236, "Bitter Root", "Image Comics", "im-br", "1e3a8a,dc2626,f8fafc", "David F. Walker / Chuck Brown", "Sanford Greene"),
    (148591, "Local Man", "Image Comics", "im-lm", "1e3a8a,dc2626,f8fafc", "Tim Seeley / Tony Fleecs", "Tony Fleecs"),
    (141212, "Geiger", "Image Comics", "im-geiger", "1e3a8a,dc2626,f8fafc", "Geoff Johns", "Gary Frank"),
    (157520, "Geiger", "Image Comics", "im-geiger2024", "1e3a8a,dc2626,f8fafc", "Geoff Johns", "Gary Frank"),
    (130977, "The Walking Dead Deluxe", "Image Comics", "im-twdd", "1f2937,9ca3af,7f1d1d", "Robert Kirkman", "Charlie Adlard"),
    (121102, "Something is Killing the Children", "Boom! Studios", "boom-siktc", "7f1d1d,1e293b,f8fafc", "James Tynion IV", "Werther Dell'Edera"),
]

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def normalize_upc(raw):
    if not raw: return None
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("111111"): return None
    return digits if 11 <= len(digits) <= 18 else None

def strip_html(s, max_len=280):
    if not s: return ""
    t = re.sub(r"(?is)<script.*?>.*?</script>", " ", s)
    t = re.sub(r"(?is)<style.*?>.*?</style>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return (t[: max_len - 1].rstrip() + "…") if len(t) > max_len else t

def issue_num_key(n):
    s = str(n or "").lstrip("#").strip()
    if re.match(r"^\d", s):
        try: return str(int(float(re.split(r"[^\d.]", s, maxsplit=1)[0])))
        except Exception: return s
    return s

def series_norm(s):
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s or "")
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[4:] if s.startswith("the ") else s

def pub_norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def pub_family(a, b):
    if a == b or a in b or b in a: return True
    for t in ("image", "boom", "skybound", "idw", "dark horse", "dynamite", "oni"):
        if t in a and t in b: return True
    return False

def load_cv_key():
    import os
    env = os.environ.get("COMICVINE_API_KEY", "").strip()
    if env: return env
    key = CV_KEY_FILE.read_text().strip()
    if not key: raise SystemExit("Missing Comic Vine API key")
    return key

class CvRate:
    def __init__(self):
        self.state = load_json(STATE, {})
        day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
        hour = self.state.get("hour") or {}
        if hour.get("key") != day_key:
            hour = {"key": day_key, "requests": 0}
        self.hour = hour
        self.last = float(self.state.get("lastRequestAt") or 0)
    def remaining(self):
        return max(0, CV_HOURLY_CAP - int(self.hour.get("requests") or 0))
    def wait(self):
        wait = max(0.0, CV_MIN_INTERVAL - (time.time() - self.last))
        if wait > 0: time.sleep(wait)
    def bump(self):
        day_key = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
        if self.hour.get("key") != day_key:
            self.hour = {"key": day_key, "requests": 0}
        self.hour["requests"] = int(self.hour.get("requests") or 0) + 1
        self.last = time.time()
        self.state["hour"] = self.hour
        self.state["lastRequestAt"] = self.last
        # preserve completedVolumes
        save_json(STATE, {**self.state, "hour": self.hour, "lastRequestAt": self.last})

RATE = CvRate()

def cv_get(path, params):
    if RATE.remaining() <= 0:
        raise RuntimeError(f"Comic Vine hourly soft-cap {CV_HOURLY_CAP} reached")
    params = dict(params); params["api_key"] = load_cv_key(); params["format"] = "json"
    url = f"{CV_API}/{path.lstrip('/')}?{urllib.parse.urlencode(params)}"
    for attempt in range(6):
        RATE.wait()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                RATE.bump()
                data = json.loads(resp.read().decode("utf-8", "replace"))
                if int(data.get("status_code") or 0) != 1:
                    print(f"  CV status {data.get('status_code')} {data.get('error')}", file=sys.stderr)
                    return None
                return data
        except urllib.error.HTTPError as e:
            RATE.bump()
            if e.code in (420, 429, 503) and attempt < 5:
                wait = min(300, 15 * (2 ** attempt))
                print(f"  CV HTTP {e.code} — backoff {wait}s", file=sys.stderr)
                time.sleep(wait); continue
            print(f"  CV HTTP {e.code} {path}", file=sys.stderr); return None
        except Exception as e:
            print(f"  CV error {path}: {e}", file=sys.stderr); return None
    return None

def fetch_volume_issues(volume_id):
    out = []; offset = 0; limit = 100
    while True:
        data = cv_get("issues/", {
            "filter": f"volume:{volume_id}",
            "field_list": "id,name,issue_number,cover_date,store_date,description,image,volume,barcode",
            "limit": str(limit), "offset": str(offset), "sort": "cover_date:asc",
        })
        if not data: break
        batch = list(data.get("results") or [])
        out.extend(batch)
        total = int(data.get("number_of_total_results") or 0)
        offset += limit
        if not batch or offset >= total: break
    return out

def stable_id(prefix, issue, used):
    base = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]+", "-", f"{prefix}-{issue}".lower())).strip("-")
    if base not in used: return base
    n = 2
    while f"{base}-{n}" in used: n += 1
    return f"{base}-{n}"

def build_key_index(existing_keys):
    idx = {}
    for k in existing_keys:
        parts = k.split("|")
        if len(parts) != 3: continue
        sn, iss, pub = parts
        idx.setdefault((series_norm(sn), issue_num_key(iss)), set()).add(pub_norm(pub))
    return idx

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--volumes", type=str, default="")
    ap.add_argument("--limit-add", type=int, default=500)
    ap.add_argument("--batch-id", type=str, default="batch-018-cv-real")
    ap.add_argument("--inject", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-year", type=int, default=1980)
    ap.add_argument("--reset-completed", action="store_true")
    args = ap.parse_args()

    existing_ids, existing_keys = load_live_blocklists()
    key_index = build_key_index(existing_keys)
    used_ids = set(existing_ids); used_keys = set(existing_keys)

    vol_map = {v[0]: v for v in PRIORITY_VOLUMES}
    st = load_json(STATE, {})
    if args.reset_completed:
        st["completedVolumes"] = []; save_json(STATE, st)
    done = set(st.get("completedVolumes") or [])

    if args.volumes:
        volumes = []
        for raw in args.volumes.split(","):
            raw = raw.strip()
            if not raw: continue
            vid = int(raw)
            if vid in vol_map: volumes.append(vol_map[vid])
            else:
                data = cv_get(f"volume/4050-{vid}/", {"field_list": "id,name,start_year,publisher,count_of_issues"})
                if not data or not data.get("results"): continue
                r = data["results"]; pub = ((r.get("publisher") or {}).get("name") or "Unknown").strip()
                name = (r.get("name") or f"Volume {vid}").strip()
                slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:24]
                volumes.append((vid, name, pub, f"cv-{slug}", "1e3a8a,dc2626,f8fafc", "Various", "Various"))
    else:
        volumes = [v for v in PRIORITY_VOLUMES if v[0] not in done] or list(PRIORITY_VOLUMES)

    rows = []; upc_local = {}; cover_local = {}
    skipped = Counter(); series_added = Counter(); pub_added = Counter()
    volumes_scanned = 0; issues_seen = 0; completed = []

    print(f"cv ingest: volumes={len(volumes)} limit_add={args.limit_add} hourly_remaining≈{RATE.remaining()} dry_run={args.dry_run}")
    try:
        for vid, series, publisher, prefix, palette, writers, artists in volumes:
            if len(rows) >= args.limit_add: break
            volumes_scanned += 1
            print(f"→ volume {vid} {series} ({publisher})", flush=True)
            issues = fetch_volume_issues(vid)
            print(f"  fetched {len(issues)} issues", flush=True)
            for iss in issues:
                if len(rows) >= args.limit_add: break
                issues_seen += 1
                cv_id = iss.get("id")
                if not cv_id: skipped["no_cv_id"] += 1; continue
                num = issue_num_key(str(iss.get("issue_number") or ""))
                if not num: skipped["no_number"] += 1; continue
                cover_date = (iss.get("cover_date") or iss.get("store_date") or "")[:10]
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", cover_date): skipped["no_date"] += 1; continue
                if cover_date < FLOOR or int(cover_date[:4]) < args.min_year: skipped["pre_floor"] += 1; continue
                sn = series_norm(series); pn = pub_norm(publisher)
                pubs = key_index.get((sn, num), set())
                if any(pub_family(pn, p) for p in pubs): skipped["in_catalog"] += 1; continue
                skey = f"{series}|{num}|{publisher}".lower()
                if skey in used_keys: skipped["batch_key"] += 1; continue
                rid = stable_id(prefix, num, used_ids)
                desc = strip_html(iss.get("description")) or f"{series} #{num}."
                upc = normalize_upc(iss.get("barcode"))
                image = iss.get("image") or {}
                img = image.get("super_url") or image.get("medium_url") or image.get("original_url") if isinstance(image, dict) else None
                street = (iss.get("store_date") or "")[:10] or None
                extra = {k: v for k, v in {"upc": upc, "streetDate": street}.items() if v} or None
                y = int(cover_date[:4]); msrp = 2.99 if y < 2012 else 3.99
                row = [rid, series, num, publisher, cover_date, writers, artists, desc, float(msrp), "single", 0.55, 0, palette]
                if extra: row.append(extra)
                rows.append(row); used_ids.add(rid); used_keys.add(skey)
                key_index.setdefault((sn, num), set()).add(pn)
                series_added[series] += 1; pub_added[publisher] += 1
                upc_local[rid] = {"source": "comicvine", "cvId": str(cv_id), "sourceId": str(cv_id), "title": series, "fetchedAt": now_iso()}
                if upc: upc_local[rid]["upc"] = upc
                if img:
                    upc_local[rid]["coverUrl"] = img; cover_local[rid] = img
            completed.append(vid)
    except RuntimeError as e:
        print(f"stopping: {e}")

    st = load_json(STATE, {})
    done = set(st.get("completedVolumes") or []); done.update(completed)
    st["completedVolumes"] = sorted(done); st["lastRunAt"] = now_iso()
    st["hour"] = RATE.hour; st["lastRequestAt"] = RATE.last
    save_json(STATE, st)

    print(f"ADDABLE {len(rows)} volumes_scanned={volumes_scanned} issues_seen={issues_seen}")
    print("SKIP", dict(skipped)); print("BY_PUB", dict(pub_added))
    print("BY_SERIES", series_added.most_common(30)); print("sample ids", [r[0] for r in rows[:12]])

    if args.dry_run or not rows:
        save_json(STATS, {"finishedAt": now_iso(), "dryRun": args.dry_run, "wouldAdd": len(rows),
            "volumesScanned": volumes_scanned, "issuesSeen": issues_seen, "skipped": dict(skipped),
            "byPublisher": dict(pub_added), "hourlyUsed": RATE.hour.get("requests"), "sampleIds": [r[0] for r in rows[:20]]})
        return 0

    batch = {"id": args.batch_id, "title": "Comic Vine verified densify (cv_id + covers)",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "status": "queued",
        "focus": "Image/Boom flagships from Comic Vine; every row has cv_id", "rows": rows,
        "conventions": {"floor": FLOOR, "dates": "Comic Vine cover_date", "identity": "cv_id verified",
            "covers": "Comic Vine super_url → comic-cover-urls.json"}, "source": "comicvine",
        "stats": {"volumesScanned": volumes_scanned, "issuesSeen": issues_seen, "skipped": dict(skipped), "byPublisher": dict(pub_added)}}
    out = BACKLOG / f"{args.batch_id}.json"
    out.write_text(json.dumps(batch, indent=2) + "\n")
    print(f"wrote {out} rows={len(rows)}")

    disk_upc = load_json(UPC_MAP, {})
    for cid, ent in upc_local.items():
        cur = dict(disk_upc.get(cid) or {}); cur.update({k: v for k, v in ent.items() if v is not None}); disk_upc[cid] = cur
    save_json(UPC_MAP, disk_upc)
    disk_covers = load_json(COVER_URLS, {})
    for cid, url in cover_local.items():
        if url and cid not in disk_covers: disk_covers[cid] = url
    save_json(COVER_URLS, disk_covers)

    injected = 0
    if args.inject:
        injected = inject_batch(args.batch_id, comment=f"Injected CV-verified comics ({args.batch_id}; floor {FLOOR})")
        print(f"injected {injected}")
    save_json(STATS, {"finishedAt": now_iso(), "added": len(rows), "injected": injected, "batchId": args.batch_id,
        "volumesScanned": volumes_scanned, "issuesSeen": issues_seen, "skipped": dict(skipped),
        "byPublisher": dict(pub_added), "bySeries": series_added.most_common(), "hourlyUsed": RATE.hour.get("requests"),
        "sampleIds": [r[0] for r in rows[:20]]})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

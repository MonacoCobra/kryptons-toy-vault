#!/usr/bin/env python3
"""Conservative near-duplicate removal for figure oneshot archive.

Exact name|subtitle|line|company keys are already unique. Densify / BBTS wave
passes often created near-dupes: same company + name + line with only filler
subtitle differences (Wave6, Classic, empty vs generic).

Keeps real wave variants with distinct meaningful subtitles (Batman Hush vs
Batman Knightfall). Prefer rows with real imageUrl, more specific subtitle,
earlier releaseDate, non-densify source.

Writes:
  - updates src/data/figure-archive/oneshot.json
  - rebuilds src/data/figure-image-urls.json from remaining rows with imageUrl
  - src/data/figure-archive/dedupe-stats.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/collection-app")
ARCHIVE_JSON = ROOT / "src/data/figure-archive/oneshot.json"
URLS_JSON = ROOT / "src/data/figure-image-urls.json"
STATS_JSON = ROOT / "src/data/figure-archive/dedupe-stats.json"
ONESHOT_STATS = ROOT / "src/data/figure-archive/oneshot-stats.json"

STOP = set(
    "the a an of and or for to with from series wave deluxe exclusive edition "
    "figure figures action ver version vol volume pack set new".split()
)
# Noise stripped only for near-dupe grouping (keep battle/movie/animated — real variants)
GROUP_NOISE = set(
    "wave waves exclusive deluxe special edition classic remaster remastered "
    "numbered boxed set pack multipack variant ver version vol volume series "
    "collective one12 one mmpr sdcc comic comics".split()
)
SUBTITLE_NOISE = GROUP_NOISE | {"battle", "movie", "animated"}
GENERIC_SUB = re.compile(
    r"^(?:wave\s*\d+[a-z]?|w\d+[a-z]?|exclusive|deluxe|special(?:\s+edition)?|"
    r"classic|remaster(?:ed)?|collector(?:\s+edition)?|platinum(?:\s+edition)?|"
    r"variant|ver\.?\s*\d*|version|series\s*\d+|numbered|ultimate|ultimates?!?|"
    r"reaction|one:?12|comic version|retro card|build-?a-?figure)?$",
    re.I,
)


def norm(s: str) -> str:
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s: str) -> list[str]:
    return [t for t in norm(s).split() if t and t not in STOP and len(t) > 1]


def norm_name(s: str) -> str:
    return norm(s)


def norm_line(s: str) -> str:
    return norm(s)


def subtitle_core(s: str) -> str:
    """Strip wave numbers and generic densify filler for near-dupe grouping.

    Keep years and distinctive tokens (Hush, 1954, Knightfall) so real variants stay.
    """
    t = norm(s)
    t = re.sub(r"\b(?:w|wave)\s*\d+[a-z]?\b", " ", t)
    for w in GROUP_NOISE:
        t = re.sub(rf"\b{re.escape(w)}\b", " ", t)
    # Do NOT strip years — 1954 vs 1984 Godzilla are distinct SKUs
    return re.sub(r"\s+", " ", t).strip()


def is_generic_subtitle(s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return True
    if GENERIC_SUB.match(s):
        return True
    core = subtitle_core(s)
    return not core


def is_densify_row(r: dict) -> bool:
    src = str(r.get("source") or "")
    if "densify" in src:
        return True
    return any("densif" in str(t).lower() for t in (r.get("tags") or []))


def is_wave_filler_subtitle(s: str) -> bool:
    s = (s or "").strip()
    if re.match(r"^(?:wave\s*\d+[a-z]?|w\d+[a-z]?)$", s, re.I):
        return True
    # "Page Punchers Wave 5", "Amazing Yamaguchi Wave6" — core equals line-ish filler
    if re.search(r"\bwave\s*\d+[a-z]?\b", s, re.I):
        core = subtitle_core(s)
        # after stripping wave+noise, little left beyond franchise noise
        return len(core.split()) <= 3
    return False


def keep_score(r: dict) -> float:
    sc = 0.0
    if r.get("imageUrl"):
        sc += 100
    sub = (r.get("subtitle") or "").strip()
    if sub and not is_generic_subtitle(sub):
        core = subtitle_core(sub)
        sc += 50 + min(40, len(core) * 2)
        # Distinctive variant tokens
        if re.search(
            r"\b(hush|knightfall|year one|long halloween|flashpoint|hellbat|"
            r"dark knight|arkham|zero year|earth.?2|new.?52|animated)\b",
            sub,
            re.I,
        ):
            sc += 20
    elif sub:
        sc += 5
    src = str(r.get("source") or "")
    if src == "shopify":
        sc += 45
    elif src == "curated":
        sc += 30
    elif "densify" in src:
        sc -= 25
    elif re.search(r"bbts-wave", src):
        sc -= 5
    rd = str(r.get("releaseDate") or "9999")[:4]
    try:
        sc += max(0, 2100 - int(rd)) / 5
    except ValueError:
        pass
    # Prefer shorter ids from earlier curated passes as mild tie-break
    sc -= min(5, len(str(r.get("id") or "")) / 20)
    return sc


def should_drop(keep: dict, drop: dict) -> bool:
    """Conservative: only drop clear densify/wave-filler near-dupes."""
    ksub = (keep.get("subtitle") or "").strip()
    dsub = (drop.get("subtitle") or "").strip()
    kcore, dcore = subtitle_core(ksub), subtitle_core(dsub)
    # Must be same core (already grouped) — double-check
    if kcore != dcore:
        return False

    dens = is_densify_row(drop)
    waveish = is_wave_filler_subtitle(dsub) or is_generic_subtitle(dsub)
    keep_better_sub = (not is_generic_subtitle(ksub)) and (
        is_generic_subtitle(dsub) or is_wave_filler_subtitle(dsub) or dens
    )

    # Drop densify junk when keep is better or equal specificity
    if dens and (keep_better_sub or is_generic_subtitle(dsub) or dcore == kcore):
        # Never drop if drop has a MORE specific raw subtitle with distinct tokens
        d_toks = set(tokens(dsub)) - SUBTITLE_NOISE
        k_toks = set(tokens(ksub)) - SUBTITLE_NOISE
        # meaningful non-noise tokens unique to drop
        extra = {t for t in d_toks if not re.match(r"^(?:w|wave)?\d+[a-z]?$", t)} - k_toks
        if extra and not is_generic_subtitle(dsub) and not is_wave_filler_subtitle(dsub):
            return False
        return True

    # BBTS wave filler: "X Wave6" vs "X" / "X Wave5"
    if waveish and dcore == kcore:
        src = str(drop.get("source") or "")
        if dens or "bbts-wave" in src or is_generic_subtitle(dsub):
            # Keep must not be worse densify-only with emptier sub
            if keep_score(keep) >= keep_score(drop):
                return True

    # Empty / Classic densify vs specific keep
    if is_generic_subtitle(dsub) and not is_generic_subtitle(ksub):
        if dens or "bbts-wave" in str(drop.get("source") or ""):
            return True

    return False


def main() -> None:
    dry = "--dry-run" in sys.argv
    rows = json.loads(ARCHIVE_JSON.read_text())
    before = len(rows)

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        key = (
            r["company"],
            norm_name(r["name"]),
            norm_line(r.get("line") or ""),
            subtitle_core(r.get("subtitle") or ""),
        )
        groups[key].append(r)

    remove_ids: set[str] = set()
    samples: list[dict] = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        ranked = sorted(group, key=keep_score, reverse=True)
        # Iteratively keep best, drop clear junk against kept set
        kept: list[dict] = []
        for cand in ranked:
            if cand["id"] in remove_ids:
                continue
            drop_me = False
            for k in kept:
                if should_drop(k, cand):
                    drop_me = True
                    break
            if drop_me:
                remove_ids.add(cand["id"])
                if len(samples) < 40:
                    samples.append(
                        {
                            "keepId": kept[0]["id"],
                            "keepSub": kept[0].get("subtitle"),
                            "keepSrc": kept[0].get("source"),
                            "dropId": cand["id"],
                            "dropSub": cand.get("subtitle"),
                            "dropSrc": cand.get("source"),
                            "company": key[0],
                            "name": cand.get("name"),
                            "line": cand.get("line"),
                        }
                    )
            else:
                kept.append(cand)

    removed = [r for r in rows if r["id"] in remove_ids]
    kept_rows = [r for r in rows if r["id"] not in remove_ids]

    # Safety: never remove if it would collapse distinct real variants
    # (already gated by subtitle_core equality + should_drop)

    print(f"before={before} remove={len(removed)} after={len(kept_rows)}")
    print("removed by source:", dict(Counter(r.get("source") for r in removed).most_common()))
    for s in samples[:12]:
        print(
            f"  KEEP {s['keepId'][:36]} [{s['keepSub']}] <- DROP {s['dropId'][:36]} [{s['dropSub']}] ({s['dropSrc']})"
        )

    if dry:
        print("dry-run — not writing")
        return

    ARCHIVE_JSON.write_text(json.dumps(kept_rows, indent=2) + "\n")
    urls = {r["id"]: r["imageUrl"] for r in kept_rows if r.get("imageUrl")}
    URLS_JSON.write_text(json.dumps(urls, indent=2, sort_keys=True) + "\n")

    with_img = sum(1 for r in kept_rows if r.get("imageUrl"))
    stats = {
        "dedupedAt": datetime.now(timezone.utc).isoformat(),
        "day": date.today().isoformat(),
        "before": before,
        "removed": len(removed),
        "after": len(kept_rows),
        "withImageUrl": with_img,
        "coveragePct": round(100 * with_img / len(kept_rows), 2) if kept_rows else 0,
        "removedBySource": dict(Counter(r.get("source") for r in removed).most_common()),
        "samples": samples[:25],
        "policy": [
            "same company + normalized name + line + subtitle_core",
            "prefer imageUrl, specific subtitle, earlier releaseDate, non-densify",
            "drop densify/wave-filler near-dupes only",
            "keep distinct real variants (Hush vs Knightfall)",
        ],
    }
    STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n")

    if ONESHOT_STATS.exists():
        os_stats = json.loads(ONESHOT_STATS.read_text())
        os_stats["archiveTotal"] = len(kept_rows)
        os_stats["withImageUrl"] = with_img
        os_stats["dedupeRemoved"] = len(removed)
        os_stats["dedupedAt"] = stats["dedupedAt"]
        by_co = Counter(r["company"] for r in kept_rows)
        os_stats["byCompany"] = dict(by_co.most_common())
        ONESHOT_STATS.write_text(json.dumps(os_stats, indent=2) + "\n")

    print(f"wrote {ARCHIVE_JSON} and {STATS_JSON}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Attach hand-audited Marvel Legends photos to the figures the app displays.

The UI reads ``oneshot.json`` ``imageUrl``, then ``figure-image-urls.json``.
Mephitsu product ids are not display ids. This script:

* updates the  ``replaces_existing`` photos on ``mephitsu/marvel-legends.json``
  (those ids are the product records themselves)
* sets a display figure's image only when the manifest row and that figure
  are the same release: character, line, wave/series, and year
* leaves uncertain rows untouched and writes a CSV of them

Does not change names, subtitles, series labels, SKUs, or tags.

  python3 scripts/ml_verified_photos.py --manifest matched_photos.json --dry-run
  python3 scripts/ml_verified_photos.py --manifest matched_photos.json --apply
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import audit_blocklist  # noqa: E402

ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
MEPH = ROOT / "src/data/figure-archive/mephitsu/marvel-legends.json"
OVERLAY = ROOT / "src/data/figure-image-urls.json"
REPORT = ROOT / "src/data/figure-archive/ml-verified-photo-report.json"
APPLIED_CSV = ROOT / "src/data/figure-archive/ml-verified-photo-applied.csv"
UNMAPPED_CSV = ROOT / "src/data/figure-archive/ml-verified-photo-unmapped.csv"

ML_LINES = {
    "marvel legends",
    "marvel legends (toy biz)",
    "marvel legends icons (toy biz)",
    "face-off (toy biz)",
    "marvel legends baf (toy biz)",
    "legendary riders (toy biz)",
}

# Shared, but too weak to identify a wave when the other side also names something else.
_WEAK = {
    "deluxe", "classic", "retro", "vintage", "standard", "basic", "baf", "buildafigure",
}

# Franchise words. Overlap on these alone does not distinguish a wave.
_FRANCHISE = {
    "x", "men", "spider", "man", "avenger", "avengers", "guardian", "guardians",
    "gotg", "fantastic", "four", "defender", "defenders", "mutant", "mutants",
}

# Tokens that never identify a wave on their own.
_STOP = {
    "a", "an", "the", "of", "and", "or", "for", "with", "in", "on", "to", "from",
    "by", "vs", "versus", "marvel", "legend", "legends", "wave", "waves", "series",
    "build", "figure", "figures", "hasbro", "toy", "biz", "toybiz", "comic",
    "comics", "single", "carded", "card", "cards", "boxed", "pack", "packs", "exclusive", "exclusives",
    "us", "usa", "uk", "eu", "channel", "fan", "new", "line", "assortment", "ml",
    "tb", "action", "edition", "collection", "walmart", "target", "amazon",
    "gamestop", "pulse", "walgreens", "toysrus", "sdcc", "nycc", "ee", "entertainment",
    "earth", "store", "stores", "shop", "version", "repaint", "rerelease", "reissue",
    "was", "now",
}

_ROMAN = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8,
    "ix": 9, "x": 10, "xi": 11, "xii": 12, "xiii": 13, "xiv": 14, "xv": 15, "xvi": 16,
}

_WIX_ID = re.compile(r"/media/([a-z0-9]+_[a-f0-9]{16,})~", re.I)
_YEAR_PAREN = re.compile(r"\((\d{4})\)\s*$")


def tokens(value: str | None) -> list[str]:
    """Lowercase word tokens. Hyphens split; mr/dr and grey/gray fold; x23 -> x 23."""
    s = (value or "").lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", " ").replace("”", " ")
    s = s.replace("build-a-figure", " baf ").replace("build a figure", " baf ")
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    out: list[str] = []
    for raw in s.split():
        t = {"mr": "mister", "dr": "doctor"}.get(raw, raw)
        if t == "grey":
            t = "gray"
        m = re.match(r"^([a-z]{1,2})(\d{2,4})$", t)
        if m:
            out.extend([m.group(1), m.group(2)])
        else:
            out.append(t)
    return out


def specific(toks: set[str]) -> set[str]:
    out = set()
    for t in toks:
        if t in _STOP:
            continue
        if t.isdigit() and len(t) == 4 and t.startswith(("19", "20")):
            continue
        out.add(t)
    return out


def strong_overlap(inter: set[str]) -> bool:
    if not inter:
        return False
    if any(len(t) >= 3 or (t.isdigit() and len(t) >= 2) for t in inter):
        return True
    return len(inter) >= 2


def _labeled_numbers(toks: list[str], label: str, *, limit: int) -> set[int]:
    found: set[int] = set()
    for i, t in enumerate(toks):
        if t == label and i + 1 < len(toks):
            nxt = toks[i + 1]
            if nxt.isdigit() and int(nxt) <= limit:
                found.add(int(nxt))
            elif label == "series" and nxt in _ROMAN:
                found.add(_ROMAN[nxt])
        if t.startswith(label) and t[len(label):].isdigit():
            n = int(t[len(label):])
            if n <= limit:
                found.add(n)
    return found


def series_numbers(toks: list[str]) -> set[int]:
    return _labeled_numbers(toks, "series", limit=30)


def wave_indexes(toks: list[str]) -> set[int]:
    return _labeled_numbers(toks, "wave", limit=30)


def pack_sizes(toks: list[str]) -> set[int]:
    found: set[int] = set()
    for i, t in enumerate(toks):
        if t.isdigit() and i + 1 < len(toks) and toks[i + 1] in {"pack", "packs"}:
            n = int(t)
            if 2 <= n <= 8:
                found.add(n)
    return found


def canon_url(url: str | None) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    m = _WIX_ID.search(u)
    if m:
        return "wix:" + m.group(1).lower()
    return u.split("#", 1)[0].split("?", 1)[0]


def catalog_years(fig: dict) -> tuple[set[str], str, str]:
    release = (fig.get("releaseDate") or "")[:4]
    paren = ""
    m = _YEAR_PAREN.search(fig.get("name") or "")
    if m:
        paren = m.group(1)
    years = {y for y in (release, paren) if len(y) == 4 and y.isdigit()}
    return years, release, paren


def catalog_name_tokens(fig: dict) -> list[str]:
    name = _YEAR_PAREN.sub("", fig.get("name") or "").strip()
    toks = tokens(name)
    if toks and toks[0] == "the" and len(toks) > 1:
        toks = toks[1:]
    return toks


def meph_name_tokens(name: str) -> list[str]:
    toks = tokens(name)
    if toks and toks[0] == "the" and len(toks) > 1:
        toks = toks[1:]
    return toks


def character_compatible(
    meph_name: list[str],
    cat_name: list[str],
    meph_wave: list[str],
    cat_sub: list[str],
) -> str | None:
    """Return equal / prefix / suffix when the names are the same character, else None.

    Extra words on the catalog name must be in the photo's wave (so a Deluxe
    Beast photo cannot claim an X-Men '97 Beast). Extra words on the photo
    name must also appear in the catalog subtitle.
    """
    if not meph_name or not cat_name:
        return None
    if meph_name == cat_name or (
        len(meph_name) == len(cat_name) and sorted(meph_name) == sorted(cat_name)
    ):
        return "equal"
    n = len(meph_name)
    if len(cat_name) > n and cat_name[:n] == meph_name:
        extra = cat_name[n:]
        wave = set(meph_wave)
        if all(t in wave for t in extra):
            return "prefix"
        return None
    m = len(cat_name)
    if len(meph_name) > m and meph_name[-m:] == cat_name and sum(len(t) for t in cat_name) >= 4:
        lead = meph_name[:-m]
        wave = set(meph_wave)
        sub = set(cat_sub)
        if lead and all(t in wave for t in lead) and all(t in sub for t in lead):
            return "suffix"
    return None


def wave_relation(
    meph_wave: list[str],
    cat_sub: list[str],
    meph_name: list[str],
    cat_name: list[str],
) -> str:
    """agree, generic, or conflict. Series / wave-index / pack-size clashes conflict."""
    ms_series, cs_series = series_numbers(meph_wave), series_numbers(cat_sub)
    if ms_series and cs_series and ms_series.isdisjoint(cs_series):
        return "conflict"
    shared_series = ms_series & cs_series
    ms_wave, cs_wave = wave_indexes(meph_wave), wave_indexes(cat_sub)
    if ms_wave and cs_wave and ms_wave.isdisjoint(cs_wave):
        return "conflict"
    shared_waves = ms_wave & cs_wave
    if pack_sizes(meph_wave) and pack_sizes(cat_sub) and pack_sizes(meph_wave).isdisjoint(pack_sizes(cat_sub)):
        return "conflict"
    # Also compare pack size when it lives in the name ("2-pack" titles).
    if pack_sizes(meph_name + meph_wave) and pack_sizes(cat_name + cat_sub):
        if pack_sizes(meph_name + meph_wave).isdisjoint(pack_sizes(cat_name + cat_sub)):
            return "conflict"

    # The BAF is often named after the character ("Kingpin BAF"). Drop only
    # the shared character words, not the catalog's wave words ("X-Men '97").
    shared_character = set(meph_name) & set(cat_name)
    meph_bag = (set(meph_wave) - shared_character) | (set(meph_name) - set(cat_name))
    cat_bag = (set(cat_sub) - shared_character) | (set(cat_name) - set(meph_name))
    for n in shared_series:
        meph_bag.add(f"series{n}")
        cat_bag.add(f"series{n}")
    for n in shared_waves:
        meph_bag.add(f"wavenum{n}")
        cat_bag.add(f"wavenum{n}")
    ms, cs = specific(meph_bag), specific(cat_bag)
    if ms and cs:
        inter = ms & cs
        extras = (ms - inter) | (cs - inter)
        distinctive = inter - _WEAK - _FRANCHISE
        if strong_overlap(distinctive):
            return "agree"
        # "Retro" vs "Retro Card", with no competing wave name on either side.
        if inter & _WEAK and not (extras - _WEAK - _FRANCHISE):
            return "agree"
        # Franchise overlap ("X-Men") is enough when only one side adds a
        # detail. Both sides naming a further, different detail is not a match
        # (animated VHS versus X-Men '97).
        if strong_overlap(inter - _WEAK) and not (extras - _WEAK):
            return "agree"
        if inter:
            return "unconfirmed"
        return "conflict"
    # classic / retro / baf still count when only one side says them.
    # Generic is both sides silent (a retailer, or "Marvel Legends" alone).
    if ms or cs:
        return "unconfirmed"
    return "generic"


def line_ok(manifest_line: str, fig: dict) -> bool:
    company = (fig.get("company") or "").lower()
    line = (fig.get("line") or "").lower()
    if line not in ML_LINES:
        return False
    if manifest_line == "Toy Biz":
        return company == "toybiz"
    if manifest_line == "Hasbro":
        return company == "hasbro" and line == "marvel legends"
    return False


def hosted_url(row: dict) -> str | None:
    """Public URL, or the one owner photo hosted under public/figures/."""
    url = (row.get("source_image_url") or "").strip()
    if url:
        return url
    member = (row.get("tar_member") or "").strip()
    if row.get("needs_file") and member:
        return "/figures/" + member
    return None


def pair_ok(row: dict, fig: dict) -> dict | None:
    """Confident pair, or None. Does not apply uniqueness yet."""
    if not line_ok(row.get("line") or "", fig):
        return None
    myear = str(row.get("year") or "").strip()
    if len(myear) != 4 or not myear.isdigit():
        return None
    years, release, paren = catalog_years(fig)
    if myear not in years:
        return None
    year_basis = "both" if myear == release and (not paren or myear == paren) else (
        "release" if myear == release else "paren"
    )
    years_disagree = bool(paren) and bool(release) and paren != release
    m_name = meph_name_tokens(row.get("name") or "")
    c_name = catalog_name_tokens(fig)
    m_wave = tokens(row.get("wave") or "")
    c_sub = tokens(fig.get("subtitle") or "")
    how = character_compatible(m_name, c_name, m_wave, c_sub)
    if not how:
        return None
    relation = wave_relation(m_wave, c_sub, m_name, c_name)
    if relation in ("conflict", "unconfirmed"):
        return None
    # A catalog row whose two year fields disagree is only safe when the wave
    # itself agrees. A generic wave plus a dirty year is a guess.
    if years_disagree and year_basis != "both" and relation != "agree":
        return None
    if relation != "agree" and years_disagree:
        return None
    return {
        "how": how,
        "relation": relation,
        "yearBasis": year_basis,
    }


def build_pairs(rows: list[dict], figs: list[dict]) -> list[dict]:
    """Mephitsu rows only. same_id rows are handled separately."""
    by_year: dict[str, list[dict]] = defaultdict(list)
    for fig in figs:
        years, _, _ = catalog_years(fig)
        for y in years:
            by_year[y].append(fig)
    pairs = []
    for idx, row in enumerate(rows):
        if str(row.get("app_id") or "").startswith("mephitsu:") is False:
            continue
        if row.get("catalog_match_method") == "same_id":
            continue
        year = str(row.get("year") or "").strip()
        for fig in by_year.get(year, []):
            info = pair_ok(row, fig)
            if not info:
                continue
            pairs.append({
                "rowIndex": idx,
                "figureId": fig["id"],
                "sha": row.get("sha256") or canon_url(hosted_url(row) or ""),
                **info,
            })
    return pairs


def resolve_unique(pairs: list[dict]) -> tuple[list[dict], dict[int, str], dict[str, str]]:
    """Drop rows or figures that still have more than one credible claim.

    Prefer a wave-agreeing claim over a generic one before deciding ambiguity.
    One photo may land on duplicate catalog rows that share name, subtitle, and
    year. Different figures, or different photos for one figure, are skipped.
    """
    by_fig: dict[str, list[dict]] = defaultdict(list)
    by_row: dict[int, list[dict]] = defaultdict(list)
    for p in pairs:
        by_fig[p["figureId"]].append(p)
        by_row[p["rowIndex"]].append(p)

    def prefer(group: list[dict], key: str) -> list[dict]:
        agreed = [p for p in group if p["relation"] == "agree"]
        if agreed and any(p["relation"] != "agree" for p in group):
            keep_keys = {p[key] for p in agreed}
            return [p for p in group if p[key] in keep_keys]
        return group

    # Per figure, ignore generic claimants when an agreeing photo exists.
    fig_keep: dict[str, set[int]] = {}
    ambiguous_figs: set[str] = set()
    for fid, group in by_fig.items():
        kept = prefer(group, "rowIndex")
        shas = {p["sha"] for p in kept}
        if len(shas) > 1:
            ambiguous_figs.add(fid)
        fig_keep[fid] = {p["rowIndex"] for p in kept}

    row_keep: dict[int, set[str]] = {}
    ambiguous_rows: set[int] = set()
    for idx, group in by_row.items():
        kept = [p for p in group if p["rowIndex"] in fig_keep.get(p["figureId"], set())]
        kept = prefer(kept, "figureId")
        row_keep[idx] = {p["figureId"] for p in kept}
        if len(row_keep[idx]) > 1:
            ambiguous_rows.add(idx)

    final = [
        p for p in pairs
        if p["figureId"] not in ambiguous_figs
        and p["rowIndex"] not in ambiguous_rows
        and p["rowIndex"] in fig_keep.get(p["figureId"], set())
        and p["figureId"] in row_keep.get(p["rowIndex"], set())
    ]
    # A row kept against several duplicate listings is fine; a row kept against
    # differing listings is not. resolve_unique's caller checks duplicates.
    row_reason = {idx: "ambiguous_multiple_figures" for idx in ambiguous_rows}
    fig_reason = {fid: "ambiguous_multiple_photos" for fid in ambiguous_figs}
    return final, row_reason, fig_reason


def listings_are_duplicates(figs: list[dict]) -> bool:
    def key(f: dict) -> tuple:
        years, _, _ = catalog_years(f)
        return (
            tuple(catalog_name_tokens(f)),
            tuple(tokens(f.get("subtitle") or "")),
            tuple(sorted(years)),
            (f.get("company") or "").lower(),
        )
    return len({key(f) for f in figs}) == 1


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def effective_url(fig: dict, overlay: dict[str, str]) -> str:
    own = fig.get("imageUrl") or ""
    if isinstance(own, str) and own.strip():
        return own.strip()
    over = overlay.get(fig["id"]) or ""
    return over.strip() if isinstance(over, str) else ""


def classify_action(current: str, verified: str) -> str:
    if not current:
        return "new"
    if canon_url(current) == canon_url(verified):
        return "already_correct"
    return "replaced"


def same_id_name_ok(row: dict, fig: dict) -> bool:
    """Sanity check for rows whose app_id is already the display id."""
    mt = set(meph_name_tokens(row.get("name") or ""))
    ct = set(catalog_name_tokens(fig))
    if not mt or not ct:
        return False
    return not mt.isdisjoint(ct)


def run(manifest_path: Path, *, apply: bool) -> dict:
    manifest = load_json(manifest_path)
    rows: list[dict] = list(manifest["rows"])
    oneshot: list[dict] = load_json(ONESHOT)
    overlay: dict[str, str] = load_json(OVERLAY)
    meph_doc = load_json(MEPH)
    products: list[dict] = list(meph_doc["products"])
    by_meph = {p["id"]: p for p in products}
    by_fig = {f["id"]: f for f in oneshot}
    blocks = audit_blocklist.load()

    ml_figs = [f for f in oneshot if (f.get("line") or "").lower() in ML_LINES]

    meph_rows = [r for r in rows if str(r.get("app_id") or "").startswith("mephitsu:")]
    same_rows = [r for r in rows if not str(r.get("app_id") or "").startswith("mephitsu:")]

    raw_pairs = build_pairs(rows, ml_figs)
    # build_pairs indexes into the full rows list
    final_pairs, row_ambig, fig_ambig = resolve_unique(raw_pairs)

    # Collapse final pairs. A row applied to non-duplicate figures is ambiguous.
    pairs_by_row: dict[int, list[dict]] = defaultdict(list)
    for p in final_pairs:
        pairs_by_row[p["rowIndex"]].append(p)

    accepted: dict[int, list[dict]] = {}
    for idx, group in pairs_by_row.items():
        figs = [by_fig[p["figureId"]] for p in group]
        if len(figs) > 1 and not listings_are_duplicates(figs):
            row_ambig[idx] = "ambiguous_multiple_figures"
            continue
        accepted[idx] = group

    applied_records: list[dict] = []
    unmapped: list[dict] = []
    display_counts = {"new": 0, "replaced": 0, "already_correct": 0}
    skipped_reasons: dict[str, int] = defaultdict(int)
    meph_archive = {"confirmed_same_url": 0, "replaced": 0, "missing_product": 0, "status_disagrees": 0}
    applied_figs: dict[str, str] = {}

    # --- Mephitsu archive replacements (identity is the product id) ---
    archive_changed = 0
    for row in meph_rows:
        product = by_meph.get(row["app_id"])
        if product is None:
            meph_archive["missing_product"] += 1
            continue
        verified = (row.get("source_image_url") or "").strip()
        current = (product.get("imageUrl") or "").strip()
        if row.get("status") == "already_in_app_same_url":
            if canon_url(current) == canon_url(verified):
                meph_archive["confirmed_same_url"] += 1
            else:
                meph_archive["status_disagrees"] = meph_archive.get("status_disagrees", 0) + 1
            continue
        if row.get("status") != "replaces_existing" or not verified:
            continue
        if canon_url(current) == canon_url(verified):
            meph_archive["confirmed_same_url"] += 1
            continue
        gallery = [u for u in (product.get("imageUrls") or []) if isinstance(u, str)]
        gallery = [verified] + [u for u in gallery if u != verified and u != current]
        product["imageUrl"] = verified
        product["imageUrls"] = gallery
        archive_changed += 1
        meph_archive["replaced"] += 1

    def note_unmapped(row: dict, reason: str, candidates: list[str] | None = None) -> None:
        skipped_reasons[reason] += 1
        ids = candidates or []
        names = []
        for fid in ids:
            fig = by_fig.get(fid)
            if fig:
                names.append(f"{fig.get('name')} [{fig.get('subtitle')}] {str(fig.get('releaseDate') or '')[:4]}")
        unmapped.append({
            "app_id": row.get("app_id") or "",
            "name": row.get("name") or "",
            "line": row.get("line") or "",
            "wave": row.get("wave") or "",
            "year": row.get("year") or "",
            "sku": row.get("sku") or "",
            "status": row.get("status") or "",
            "reason": reason,
            "candidate_figure_ids": ";".join(ids),
            "candidate_figures": " | ".join(names),
        })

    def apply_display(row: dict, fig: dict, *, match: str) -> str:
        """Apply one photo to one listing. Returns applied / duplicate / blocked / no_url / conflict."""
        verified = hosted_url(row)
        if not verified:
            note_unmapped(row, "no_image_url")
            return "no_url"
        sha = row.get("sha256") or canon_url(verified)
        prev = applied_figs.get(fig["id"])
        if prev is not None:
            if prev != sha:
                note_unmapped(row, "second_photo_not_used", [fig["id"]])
                return "conflict"
            return "duplicate"
        if blocks.id_removed(fig["id"]) or blocks.image_blocked(fig["id"], verified):
            note_unmapped(row, "audit_image_blocked", [fig["id"]])
            return "blocked"
        current = effective_url(fig, overlay)
        action = classify_action(current, verified)
        if action != "already_correct":
            fig["imageUrl"] = verified
            if fig["id"] in overlay and canon_url(overlay[fig["id"]]) != canon_url(verified):
                overlay[fig["id"]] = verified
        applied_figs[fig["id"]] = sha
        display_counts[action] += 1
        applied_records.append({
            "app_id": row.get("app_id") or "",
            "figure_id": fig["id"],
            "action": action,
            "match": match,
            "manifest_name": row.get("name") or "",
            "manifest_wave": row.get("wave") or "",
            "manifest_year": row.get("year") or "",
            "figure_name": fig.get("name") or "",
            "figure_subtitle": fig.get("subtitle") or "",
            "figure_year": (fig.get("releaseDate") or "")[:4],
            "image_url": verified,
        })
        return "applied"

    mapped_rows: set[int] = set()
    handled: set[int] = set()

    # same_id: the manifest already carries the display id.
    for idx, row in enumerate(rows):
        if str(row.get("app_id") or "").startswith("mephitsu:"):
            continue
        fig = by_fig.get(row.get("app_id") or "")
        if fig is None:
            note_unmapped(row, "same_id_missing")
            continue
        if (fig.get("line") or "").lower() not in ML_LINES:
            note_unmapped(row, "same_id_not_marvel_legends", [fig["id"]])
            continue
        if not same_id_name_ok(row, fig):
            note_unmapped(row, "same_id_name_mismatch", [fig["id"]])
            continue
        apply_display(row, fig, match="same_id")
        mapped_rows.add(idx)

    # Confident mephitsu -> display pairs.
    claimed_figs: dict[str, int] = {}
    for idx, group in accepted.items():
        # If two different photos already landed on this figure via another row, skip.
        conflict = False
        verified = hosted_url(rows[idx]) or ""
        sha = rows[idx].get("sha256") or canon_url(verified)
        for p in group:
            prev = claimed_figs.get(p["figureId"])
            if prev is not None:
                prev_sha = rows[prev].get("sha256") or canon_url(hosted_url(rows[prev]) or "")
                if prev_sha != sha:
                    conflict = True
        if conflict:
            note_unmapped(rows[idx], "ambiguous_multiple_photos", [p["figureId"] for p in group])
            handled.add(idx)
            continue
        any_applied = False
        for p in group:
            claimed_figs[p["figureId"]] = idx
            outcome = apply_display(
                rows[idx],
                by_fig[p["figureId"]],
                match=f"{p['how']}:{p['relation']}:{p['yearBasis']}",
            )
            if outcome in ("applied", "duplicate"):
                any_applied = True
        if any_applied:
            mapped_rows.add(idx)
        else:
            handled.add(idx)

    # Unmapped mephitsu rows, with the best reason we have.
    pair_figs: dict[int, list[str]] = defaultdict(list)
    for p in raw_pairs:
        pair_figs[p["rowIndex"]].append(p["figureId"])

    for idx, row in enumerate(rows):
        if idx in mapped_rows or idx in handled:
            continue
        if not str(row.get("app_id") or "").startswith("mephitsu:"):
            continue
        if idx in row_ambig:
            note_unmapped(row, row_ambig[idx], pair_figs.get(idx))
            continue
        cands = pair_figs.get(idx) or []
        if any(fid in fig_ambig for fid in cands):
            note_unmapped(row, "ambiguous_multiple_photos", cands)
            continue
        if cands:
            note_unmapped(row, "ambiguous_multiple_figures", cands)
            continue
        # Distinguish "no character+year at all" from "wave rejected".
        year = str(row.get("year") or "")
        m_name = meph_name_tokens(row.get("name") or "")
        char_hits = []
        for fig in ml_figs:
            years, _, _ = catalog_years(fig)
            if year not in years or not line_ok(row.get("line") or "", fig):
                continue
            how = character_compatible(
                m_name,
                catalog_name_tokens(fig),
                tokens(row.get("wave") or ""),
                tokens(fig.get("subtitle") or ""),
            )
            if how:
                char_hits.append(fig["id"])
        if char_hits:
            note_unmapped(row, "wave_or_year_conflict", char_hits[:8])
        else:
            note_unmapped(row, "no_catalog_figure")

    # Figures that were photo-ambiguous should be mentioned once per losing row;
    # already recorded via row loop.

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "manifest": manifest_path.name,
        "manifestSha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "manifestRows": len(rows),
        "dryRun": not apply,
        "display": {
            "applied": display_counts,
            "appliedTotal": sum(display_counts.values()),
            "skipped": dict(sorted(skipped_reasons.items())),
            "skippedTotal": sum(skipped_reasons.values()),
        },
        "mephitsuArchive": meph_archive,
        "notes": [
            "Display counts are Marvel Legends listings the app renders (oneshot imageUrl, else figure-image-urls).",
            "already_correct: mapped, and that listing already showed this photo.",
            "new: listing had no photo.",
            "replaced: listing showed a different photo; it now shows the audited one.",
            "Mephitsu archive replacements update marvel-legends.json only. They do not by themselves change the UI.",
            "second_photo_not_used: the listing was already given the photo from its own catalog id; a second audited photo of that same figure was left unused.",
            "no_catalog_figure: no Marvel Legends listing shares that character, line, and year.",
            "wave_or_year_conflict: a listing shares the character and year, but the wave/series does not agree.",
            "Unmapped rows were not guessed. See ml-verified-photo-unmapped.csv.",
        ],
    }

    if apply:
        write_json(ONESHOT, oneshot)
        write_json(OVERLAY, overlay)
        if archive_changed:
            write_json(MEPH, meph_doc)
        write_json(REPORT, report)
        _write_csv(APPLIED_CSV, applied_records, [
            "app_id", "figure_id", "action", "match", "manifest_name", "manifest_wave",
            "manifest_year", "figure_name", "figure_subtitle", "figure_year", "image_url",
        ])
        _write_csv(UNMAPPED_CSV, unmapped, [
            "app_id", "name", "line", "wave", "year", "sku", "status", "reason",
            "candidate_figure_ids", "candidate_figures",
        ])
    return {
        "report": report,
        "applied": applied_records,
        "unmapped": unmapped,
    }


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.apply and args.dry_run:
        raise SystemExit("pass only one of --apply / --dry-run")
    result = run(args.manifest, apply=args.apply)
    print(json.dumps(result["report"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

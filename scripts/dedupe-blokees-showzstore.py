#!/usr/bin/env python3
"""Collapse Showzstore Blokees doubles onto the stronger vault row.

Showzstore 3P/official densify added Blokees case listings and numbered
kits that already exist as Blokees store / Shopify parents (often with a
GTIN-style house sku and the official photo). This keeps that row, moves
Show.Z aliases onto it, and drops the duplicate card.

Shining Version and Galaxy Version already use the Defender set model
(parent setId + member rows). Galaxy pieces that were reused from the
flat BBTS list stayed on "Blokees Transformers"; they are moved onto
"Blokees Galaxy Version" so the line browses like Defender Version.

The 2025 X Yearly case (Show.Z "set of 6") is not the 2024 Golden Lagoon
(5) or 2026 Dinobot Desertion (8). It becomes a parent with the six
TFWiki members underneath. No other new SKUs are invented.

  python3 scripts/dedupe-blokees-showzstore.py --dry-run
  python3 scripts/dedupe-blokees-showzstore.py --apply
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
STATS = ROOT / "src/data/figure-archive/blokees-showz-dedupe-stats.json"

SOURCE = "inject-showzstore-3p-official"
STOP = {
    "blokees",
    "transformers",
    "classic",
    "class",
    "edition",
    "action",
    "champion",
    "version",
    "model",
    "kit",
    "rise",
    "of",
    "the",
    "beasts",
    "one",
    "dark",
    "moon",
    "movie",
    "dx",
    "set",
    "and",
    "ver",
    "g1",
    "tf",
    "prime",
    "a",
}
STORE_PATH = ROOT / "scripts/figure_oneshot/blokees-tf-store.json"


def norm(value: str) -> str:
    text = (value or "").lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_store_titles() -> dict[str, str]:
    if not STORE_PATH.exists():
        return {}
    products = json.loads(STORE_PATH.read_text()).get("products") or []
    return {str(product.get("sku")): product.get("title") or "" for product in products if product.get("sku")}


STORE_TITLES: dict[str, str] = {}


def identity_text(row: dict) -> str:
    title = STORE_TITLES.get(str(row.get("sku") or ""), "")
    return f"{row.get('name', '')} {row.get('subtitle', '')} {title}"


def blob(row: dict) -> str:
    return norm(identity_text(row))


def has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def char_tokens(text: str) -> list[str]:
    cleaned = re.sub(r"\b\d{2}\b", " ", norm(text))
    return [tok for tok in cleaned.split() if tok not in STOP and len(tok) > 2]


def class_numbers(text: str) -> list[str]:
    found = []
    for match in re.finditer(
        r"(?:classic class|action edition|champion class|dx classic class)\D{0,4}(\d{2})\b",
        text,
        re.I,
    ):
        found.append(match.group(1))
    for match in re.finditer(r"\b(\d{2})\b", text):
        if match.group(1) not in found:
            found.append(match.group(1))
    return found


def variant_flags(text: str) -> set[str]:
    folded = norm(text)
    flags: set[str] = set()
    if "energy explosion" in folded:
        flags.add("energy")
    if "ver evo" in folded or re.search(r"\bevo\b", folded):
        flags.add("evo")
    if "orion" in folded:
        flags.add("orion")
    if "jet wing" in folded:
        flags.add("jetwing")
    if "transformers prime" in folded or "tfp" in folded:
        flags.add("tfp")
    if "comic" in folded:
        flags.add("comic")
    return flags


def showz_code(row: dict) -> str | None:
    for tag in row.get("tags") or []:
        if isinstance(tag, str) and tag.lower().startswith("showz:"):
            return tag.split(":", 1)[1]
    return None


def ensure_tag(row: dict, tag: str) -> None:
    tags = row.setdefault("tags", [])
    if tag not in tags:
        tags.append(tag)


def parents_on(rows: list[dict], line: str) -> list[dict]:
    return [
        row
        for row in rows
        if row.get("company") == "blokees"
        and row.get("line") == line
        and row.get("setRole") == "parent"
        and row.get("source") != SOURCE
    ]


def wave_number_in_parent(row: dict) -> str | None:
    match = re.search(r"version\s+(\d{1,2})\b", row.get("name") or "", re.I)
    if not match:
        return None
    return f"{int(match.group(1)):02d}"


def tokens_fit(dupe_text: str, keeper: dict) -> bool:
    keeper_text = blob(keeper)
    tokens = char_tokens(dupe_text)
    if not tokens:
        return False
    # Whole words only, so "megatron" does not satisfy "megatronus".
    return all(has_word(keeper_text, token) for token in tokens)


def match_case_set(dupe: dict, rows: list[dict]) -> tuple[dict, str] | None:
    name = dupe.get("name") or ""
    if not re.search(r"set of \d+", name, re.I):
        return None
    # Character multipacks (Bee & Scourge, Prime & Megatron) are their own SKU.
    if "&" in name:
        return None
    folded = norm(name)
    if "combining" in folded:
        return None
    line = dupe.get("line")
    if line not in {
        "Blokees Galaxy Version",
        "Blokees Shining Version",
        "Blokees Defender Version",
    }:
        return None

    chapter = re.search(r"chapter\s+(\d+)\b", name, re.I)
    numbered = re.search(
        r"(?:galaxy version|shining version|defender version)\s+(\d{1,2})\b",
        name,
        re.I,
    )
    if chapter and line == "Blokees Shining Version" and not numbered:
        wave = f"{int(chapter.group(1)):02d}"
        hits = [
            row
            for row in parents_on(rows, line)
            if wave_number_in_parent(row) == wave and "shining version" in norm(row.get("name") or "")
        ]
        if len(hits) == 1:
            return hits[0], f"shining chapter {int(chapter.group(1))} is Shining Version {wave}"
        return None
    if not numbered:
        return None
    wave = f"{int(numbered.group(1)):02d}"
    hits = [row for row in parents_on(rows, line) if wave_number_in_parent(row) == wave]
    if len(hits) == 1:
        return hits[0], f"{line} case listing is wave {wave} parent"
    return None


def match_combining(dupe: dict, rows: list[dict]) -> tuple[dict, str] | None:
    folded = norm(dupe.get("name") or "")
    if "combining" not in folded:
        return None
    needle = "bruticus" if "bruticus" in folded else "devastator" if "devastator" in folded else ""
    if not needle:
        return None
    hits = [
        row
        for row in rows
        if row.get("company") == "blokees"
        and row.get("source") != SOURCE
        and row.get("setRole") == "parent"
        and needle in blob(row)
        and "combining" in blob(row)
    ]
    if len(hits) == 1:
        return hits[0], f"combining accessory is the {needle} store parent"
    return None


def match_golden_lagoon(dupe: dict, rows: list[dict]) -> tuple[dict, str] | None:
    folded = norm(dupe.get("name") or "")
    if "golden lagoon" not in folded or "set of 5" not in folded:
        return None
    hits = [
        row
        for row in rows
        if row.get("company") == "blokees"
        and row.get("source") != SOURCE
        and "golden lagoon" in blob(row)
        and "dinobot" not in blob(row)
        and "defence" not in blob(row)
        and "defense" not in blob(row)
        and row.get("setRole") == "parent"
    ]
    if len(hits) == 1:
        return hits[0], "2024 Golden Lagoon set of 5"
    return None


def match_numbered_single(dupe: dict, rows: list[dict]) -> tuple[dict, str] | None:
    name = dupe.get("name") or ""
    if re.search(r"set of \d+", name, re.I) and ("&" in name or " and " in f" {norm(name)} "):
        return None
    line = dupe.get("line")
    if line not in {"Blokees Classic Class", "Blokees Action Edition", "Blokees Champion Class"}:
        return None
    numbers = []
    for match in re.finditer(
        r"(?:classic class|action edition|champion class|dx classic class)\D{0,6}(\d{2})\b",
        name,
        re.I,
    ):
        numbers.append(match.group(1))
    if not numbers:
        # "Mirage 06" / "Arcee 07" style
        tail = re.search(r"\b(\d{2})\b", name)
        if tail and line == "Blokees Classic Class":
            numbers.append(tail.group(1))
    if len(numbers) != 1:
        return None
    number = numbers[0]
    flags = variant_flags(name)
    pool = [
        row
        for row in rows
        if row.get("company") == "blokees"
        and row.get("line") == line
        and row.get("source") != SOURCE
        and row.get("setRole") != "member"
    ]
    hits = []
    for row in pool:
        keeper_numbers = class_numbers(identity_text(row))
        if number not in keeper_numbers:
            continue
        if variant_flags(identity_text(row)) != flags:
            continue
        if not tokens_fit(name, row):
            continue
        hits.append(row)
    if len(hits) == 1:
        return hits[0], f"{line} #{number} character match"
    return None


def match_g1_optimus(dupe: dict, rows: list[dict]) -> tuple[dict, str] | None:
    folded = norm(dupe.get("name") or "")
    if dupe.get("line") != "Blokees Action Edition":
        return None
    if "g1" not in folded or "optimus" not in folded:
        return None
    if class_numbers(dupe.get("name") or ""):
        # numbered action editions are handled above; bare "Action Edition G1" has no class index
        if re.search(r"action edition\s+\d", dupe.get("name") or "", re.I):
            return None
    hits = [
        row
        for row in rows
        if row.get("line") == "Blokees Action Edition"
        and row.get("source") != SOURCE
        and "g1" in blob(row)
        and "optimus" in blob(row)
        and "megatron" not in blob(row)
        and not re.search(r"action edition\s+\d", row.get("name") or "", re.I)
    ]
    if len(hits) == 1:
        return hits[0], "Action Edition G1 Optimus Prime (unnumbered)"
    return None


def yearly_2025(dupe: dict) -> bool:
    folded = norm(dupe.get("name") or "")
    return folded == "yearly version set of 6 model kit" or (
        "yearly version" in folded and "set of 6" in folded and "golden" not in folded
    )


XY2025_MEMBERS = [
    "Optimus Prime (G1 Toy)",
    "Sideswipe",
    "Bumblebee",
    "Beachcomber",
    "Megatron",
    "Soundwave",
]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]


def attach_yearly_2025(row: dict, by_id: dict[str, dict]) -> list[str]:
    row["name"] = "The Golden Lagoon · Defence"
    row["subtitle"] = "2025 X Yearly Version"
    row["line"] = "Blokees Transformers"
    row["setId"] = row["id"]
    row["setRole"] = "parent"
    ensure_tag(row, "transformers")
    ensure_tag(row, "set-parent")
    added = []
    for member in XY2025_MEMBERS:
        child_id = f"blk-m-xy2025-{slug(member)}"[:80]
        if child_id in by_id:
            existing = by_id[child_id]
            existing["setId"] = row["id"]
            existing["setRole"] = "member"
            continue
        child = {
            "id": child_id,
            "name": member,
            "subtitle": "2025 - The Golden Lagoon · Defence",
            "line": "Blokees Transformers",
            "company": "blokees",
            "kind": "kit",
            "releaseDate": row.get("releaseDate") or "2025-12-01",
            "msrp": row.get("msrp") or 0,
            "scale": '4"',
            "demand": 1,
            "tags": ["blokees", "transformers", "set-member", "tfwiki", "xy2025", "kit"],
            "source": "tfwiki-blokees",
            "setId": row["id"],
            "setRole": "member",
        }
        by_id[child_id] = child
        added.append(child_id)
    return added


def choose_keeper(dupe: dict, rows: list[dict]) -> tuple[dict, str] | None:
    for matcher in (
        match_combining,
        match_golden_lagoon,
        match_case_set,
        match_numbered_single,
        match_g1_optimus,
    ):
        hit = matcher(dupe, rows)
        if hit:
            return hit
    return None


def move_aliases(doc: dict, drop_id: str, keep_id: str, extra: list[str]) -> list[str]:
    by = doc.setdefault("aliasesByFigureId", {})
    to = doc.setdefault("aliasToFigureId", {})
    moved = list(by.get(drop_id) or [])
    for code, owner in list(to.items()):
        if owner == drop_id and code not in moved:
            moved.append(code)
    codes = []
    for code in [*moved, *extra, f"id:{drop_id}"]:
        if code and code not in codes:
            codes.append(code)
    keep_list = list(by.get(keep_id) or [])
    for code in codes:
        if code not in keep_list:
            keep_list.append(code)
        to[code] = keep_id
    if keep_list:
        by[keep_id] = keep_list
    by.pop(drop_id, None)
    return codes


def align_galaxy_lines(rows: list[dict]) -> list[dict]:
    parents = {
        row["id"]: row
        for row in rows
        if row.get("line") == "Blokees Galaxy Version" and row.get("setRole") == "parent"
    }
    changed = []
    for row in rows:
        set_id = row.get("setId")
        if row.get("setRole") != "member" or set_id not in parents:
            continue
        if row.get("line") == "Blokees Galaxy Version":
            ensure_tag(row, "transformers")
            continue
        before = row.get("line")
        row["line"] = "Blokees Galaxy Version"
        ensure_tag(row, "transformers")
        ensure_tag(row, "set-member")
        changed.append({"id": row["id"], "from": before, "to": row["line"], "setId": set_id})
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.apply and args.dry_run:
        raise SystemExit("pick one of --apply or --dry-run")
    dry = not args.apply

    global STORE_TITLES
    STORE_TITLES = load_store_titles()
    rows: list[dict] = json.loads(ONESHOT.read_text())
    aliases = json.loads(ALIASES.read_text())
    by_id = {row["id"]: row for row in rows}
    dupes = [
        row
        for row in rows
        if row.get("company") == "blokees" and row.get("source") == SOURCE
    ]

    merged = []
    kept = []
    drop_ids = set()
    yearly_added: list[str] = []

    for dupe in dupes:
        if yearly_2025(dupe):
            if not dry:
                yearly_added = attach_yearly_2025(dupe, by_id)
            else:
                yearly_added = [f"blk-m-xy2025-{slug(name)}"[:80] for name in XY2025_MEMBERS]
            kept.append(
                {
                    "id": dupe["id"],
                    "name": dupe["name"],
                    "reason": "2025 Golden Lagoon · Defence case (6). Not 2024 (5) or 2026 (8). Structured as a set.",
                }
            )
            continue
        chosen = choose_keeper(dupe, rows)
        if not chosen:
            kept.append({"id": dupe["id"], "name": dupe["name"], "line": dupe.get("line"), "reason": "no high-confidence keeper"})
            continue
        keeper, reason = chosen
        if keeper["id"] == dupe["id"]:
            continue
        code = showz_code(dupe)
        sample = {
            "dropId": dupe["id"],
            "keepId": keeper["id"],
            "dropName": dupe["name"],
            "keepName": keeper["name"],
            "keepSku": keeper.get("sku"),
            "reason": reason,
            "showz": code,
            "imageFilled": bool(dupe.get("imageUrl") and not keeper.get("imageUrl")),
        }
        merged.append(sample)
        drop_ids.add(dupe["id"])
        if dry:
            continue
        if dupe.get("imageUrl") and not keeper.get("imageUrl"):
            keeper["imageUrl"] = dupe["imageUrl"]
        ensure_tag(keeper, "transformers")
        ensure_tag(keeper, "src:showzstore")
        if code:
            ensure_tag(keeper, f"showz:{code}")
        move_aliases(
            aliases,
            dupe["id"],
            keeper["id"],
            [f"SHOWZ{code}"] if code else [],
        )
        aliases.setdefault("collapsed", []).append(
            {
                "keepId": keeper["id"],
                "dropId": dupe["id"],
                "canonicalSku": keeper.get("sku"),
                "aliasesAdded": [f"SHOWZ{code}"] if code else [],
                "reason": f"Showzstore Blokees duplicate: {reason}",
            }
        )

    if not dry:
        for child_id, child in list(by_id.items()):
            if child_id not in {row["id"] for row in rows}:
                rows.append(child)
        rows = [row for row in rows if row["id"] not in drop_ids]
        align = align_galaxy_lines(rows)
        aliases["updatedAt"] = datetime.now(timezone.utc).isoformat()
        stats_blob = aliases.setdefault("stats", {})
        stats_blob["blokeesShowzDedupe"] = {
            "at": aliases["updatedAt"],
            "removed": len(drop_ids),
            "yearlyMembersAdded": len(yearly_added),
            "galaxyLineAligned": len(align),
        }
        ONESHOT.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
        ALIASES.write_text(json.dumps(aliases, indent=2, ensure_ascii=False) + "\n")
    else:
        align = align_galaxy_lines(copy.deepcopy(rows))

    # family counts after the planned edits
    preview = copy.deepcopy([row for row in rows if row["id"] not in drop_ids])
    if dry:
        align_galaxy_lines(preview)
    families = {}
    for row in preview:
        if row.get("company") != "blokees":
            continue
        if row.get("line") not in {"Blokees Shining Version", "Blokees Galaxy Version", "Blokees Defender Version"}:
            continue
        slot = families.setdefault(row["line"], {"parent": 0, "member": 0, "flat": 0})
        role = row.get("setRole")
        if role == "parent":
            slot["parent"] += 1
        elif role == "member":
            slot["member"] += 1
        else:
            slot["flat"] += 1

    shining_sets = []
    galaxy_sets = []
    for row in preview:
        if row.get("setRole") != "parent":
            continue
        if row.get("line") == "Blokees Shining Version" and "transformers" in norm(row.get("name") or ""):
            kids = [r for r in preview if r.get("setId") == row["id"] and r.get("setRole") == "member"]
            shining_sets.append({"id": row["id"], "name": row["name"], "members": len(kids), "sku": row.get("sku")})
        if row.get("line") == "Blokees Galaxy Version" and "transformers" in norm(f"{row.get('name','')} {row.get('subtitle','')}"):
            kids = [r for r in preview if r.get("setId") == row["id"] and r.get("setRole") == "member"]
            if kids:
                galaxy_sets.append({"id": row["id"], "name": row["name"], "members": len(kids), "sku": row.get("sku")})

    report = {
        "dryRun": dry,
        "showzBlokeesSeen": len(dupes),
        "merged": len(merged),
        "kept": kept,
        "yearlyMembersAdded": yearly_added,
        "galaxyLineAligned": len(align),
        "lineCounts": families,
        "shiningSets": shining_sets,
        "galaxySets": galaxy_sets,
        "samples": merged[:12],
        "mergedAll": merged,
    }
    if not dry:
        STATS.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ("dryRun", "showzBlokeesSeen", "merged", "kept", "yearlyMembersAdded", "galaxyLineAligned", "lineCounts", "shiningSets", "galaxySets")}, indent=2))
    print("--- merges ---")
    for row in merged:
        print(f"{row['dropName'][:64]:64} -> {row['keepId'][:56]} | {row['reason']}")


if __name__ == "__main__":
    main()

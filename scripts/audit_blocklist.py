"""Audit block list: codes/photos the date & identity audits stripped, and ids they removed.

Source of truth: src/data/figure-sku-aliases.json
  strippedCodes[] = {figureId, codes[], imageDropped, imageUrls[], reason}
      -> those codes and listing photos must never be re-attached to that figure.
  removed[]       = {dropId, ...}
      -> those figure ids must never be recreated.

Every script that writes barcodes, aliases or photos into the catalog (sku bake,
Mephitsu bake, image bake, Mephitsu listing densify, ToyArk apply) calls
`enforce(...)` right before writing, and may call `code_blocked` /
`image_blocked` / `id_removed` to skip candidates early.
Same idea as the image-mismatch `clearedUrlLedger` that the Mephitsu bake honours.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALIASES = ROOT / "src/data/figure-sku-aliases.json"

_GTIN_RE = re.compile(r"^\d{11,14}$")
_PREFIXED6_RE = re.compile(r"^[A-Z]{2,4}(\d{6})$")
_SIZE_RE = re.compile(r"_(?:\d+x\d*|\d*x\d+)(?=\.[a-z0-9]+$)")


def code_keys(code: Any) -> set[str]:
    u = str(code or "").strip().upper()
    if not u:
        return set()
    u = re.sub(r"DMG$", "", u)
    keys = {u}
    digits = re.sub(r"\D", "", u)
    if len(digits) >= 8:
        keys.add("D:" + digits.lstrip("0"))
    if _GTIN_RE.match(digits) and digits == u:
        keys.add("L6:" + digits[-6:])  # 5010996361400 ~ HAS361400
    m = _PREFIXED6_RE.match(u)
    if m:
        keys.add("L6:" + m.group(1))
    return keys


def url_keys(url: Any) -> set[str]:
    u = str(url or "").strip().lower()
    if not u:
        return set()
    base = re.split(r"[?#]", u, 1)[0]
    name = base.rsplit("/", 1)[-1]
    return {base, "B:" + _SIZE_RE.sub("", name)}


class AuditBlocks:
    def __init__(self, doc: dict | None = None):
        doc = doc or {}
        self.codes: dict[str, set[str]] = {}
        self.images: dict[str, set[str]] = {}
        for e in doc.get("strippedCodes") or []:
            if not isinstance(e, dict) or not e.get("figureId"):
                continue
            fid = str(e["figureId"])
            for c in e.get("codes") or []:
                self.codes.setdefault(fid, set()).update(code_keys(c))
            for u in e.get("imageUrls") or []:
                self.images.setdefault(fid, set()).update(url_keys(u))
        self.removed: set[str] = {
            str(e["dropId"]) for e in doc.get("removed") or [] if isinstance(e, dict) and e.get("dropId")
        }

    def code_blocked(self, figure_id: str, code: Any) -> bool:
        keys = self.codes.get(str(figure_id))
        return bool(keys and code_keys(code) & keys)

    def image_blocked(self, figure_id: str, url: Any) -> bool:
        keys = self.images.get(str(figure_id))
        return bool(keys and url_keys(url) & keys)

    def id_removed(self, figure_id: str) -> bool:
        return str(figure_id) in self.removed


def load(path: Path | str | None = None, doc: dict | None = None) -> AuditBlocks:
    if doc is None:
        p = Path(path) if path else ALIASES
        try:
            doc = json.loads(p.read_text()) if p.exists() else {}
        except Exception:
            doc = {}
    return AuditBlocks(doc)


def _url_of(v: Any) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return str(v.get("imageUrl") or v.get("url") or "")
    return ""


def enforce(
    rows: list[dict],
    alias_doc: dict | None = None,
    image_urls: dict | None = None,
    sku_map: dict | None = None,
    blocks: AuditBlocks | None = None,
) -> dict[str, int]:
    """Undo any re-attachment of audit-stripped codes/photos and drop removed ids (in place)."""
    if blocks is None:
        blocks = load(doc=alias_doc) if alias_doc and ("strippedCodes" in alias_doc or "removed" in alias_doc) else load()
    n = {"rowsDropped": 0, "skuCleared": 0, "aliasesDropped": 0, "imagesCleared": 0, "overlayCleared": 0}
    if blocks.removed:
        keep = [r for r in rows if not blocks.id_removed(r.get("id"))]
        n["rowsDropped"] = len(rows) - len(keep)
        rows[:] = keep
    for r in rows:
        fid = r.get("id")
        if r.get("sku") and blocks.code_blocked(fid, r["sku"]):
            r.pop("sku", None)
            n["skuCleared"] += 1
            if sku_map is not None:
                sku_map.pop(fid, None)
        if r.get("imageUrl") and blocks.image_blocked(fid, r["imageUrl"]):
            r["imageUrl"] = None
            n["imagesCleared"] += 1
    if alias_doc:
        by = alias_doc.get("aliasesByFigureId")
        if isinstance(by, dict):
            for fid in list(by):
                if blocks.id_removed(fid):
                    n["aliasesDropped"] += len(by.pop(fid) or [])
                    continue
                vals = by[fid]
                if isinstance(vals, list) and fid in blocks.codes:
                    kept = [c for c in vals if not blocks.code_blocked(fid, c)]
                    n["aliasesDropped"] += len(vals) - len(kept)
                    if kept:
                        by[fid] = kept
                    else:
                        by.pop(fid)
        rev = alias_doc.get("aliasToFigureId")
        if isinstance(rev, dict):
            for c, fid in list(rev.items()):
                if blocks.id_removed(fid) or blocks.code_blocked(fid, c):
                    del rev[c]
    if image_urls is not None:
        for fid in list(image_urls):
            if blocks.id_removed(fid) or blocks.image_blocked(fid, _url_of(image_urls[fid])):
                del image_urls[fid]
                n["overlayCleared"] += 1
    if sku_map is not None:
        for fid in list(sku_map):
            if blocks.id_removed(fid) or blocks.code_blocked(fid, sku_map[fid]):
                del sku_map[fid]
    return n


def total(counts: dict[str, int]) -> int:
    return sum(counts.values())

#!/usr/bin/env python3
"""Figma densify sweep: Guilty Crown Inori #143 + classics/recent gaps.

Sources (honest):
  - Good Smile Company product pages (EN) — CDN images.goodsmile.info
  - Good Smile US / ToyArena / HobbyFigures / Cmdstore Shopify feeds (JAN + CDN)
  - User-verified CDJapan JAN for Inori: 4545784062326

Policy: company=figma; kind=figure; real CDN only; empty sku over wrong;
dedupe by id / JAN / figma#. Does NOT Build Publish Live.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/workspace/collection-app")
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from figure_identity import clean_code, is_gtin  # noqa: E402

ARCHIVE = ROOT / "src/data/figure-archive/oneshot.json"
ALIASES = ROOT / "src/data/figure-sku-aliases.json"
SKU_MAP = ROOT / "src/data/figure-sku-map.json"
URLS = ROOT / "src/data/figure-image-urls.json"
STATS = ROOT / "src/data/figure-archive/figma-densify-inject-stats.json"

GSC = "https://images.goodsmile.info/cgm/images/product"
COMPANY = "figma"
SCALE = '5.5"'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def ensure_alias_doc(doc: dict) -> dict:
    doc.setdefault("version", 1)
    doc.setdefault("policy", "gtin-canonical")
    doc.setdefault("aliasesByFigureId", {})
    doc.setdefault("aliasToFigureId", {})
    doc.setdefault("collapsed", [])
    doc.setdefault("flagged", [])
    return doc


def add_aliases(doc: dict, figure_id: str, codes: list[str]) -> int:
    doc = ensure_alias_doc(doc)
    by = doc["aliasesByFigureId"]
    to = doc["aliasToFigureId"]
    cur = list(by.get(figure_id) or [])
    added = 0
    for c in codes:
        c2 = clean_code(c) or str(c).strip()
        if not c2:
            continue
        if c2 not in cur:
            cur.append(c2)
            added += 1
        to[c2] = figure_id
    if cur:
        by[figure_id] = cur
    return added


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:60]


def row(
    rid: str,
    name: str,
    subtitle: str,
    *,
    line: str = "figma",
    release: str | None = None,
    msrp: float = 79.99,
    demand: float = 1.35,
    sku: str | None = None,
    image: str | None = None,
    tags: list[str] | None = None,
    source: str = "inject-figma-densify",
    figma_no: int | str | None = None,
) -> dict:
    sub = subtitle
    if figma_no is not None and f"#{figma_no}" not in (subtitle or ""):
        sub = f"{subtitle} · figma #{figma_no}".strip(" ·")
    out: dict[str, Any] = {
        "id": rid,
        "name": name,
        "subtitle": sub,
        "line": line,
        "company": COMPANY,
        "kind": "figure",
        "releaseDate": release,
        "msrp": float(msrp),
        "scale": SCALE,
        "demand": float(demand),
        "tags": tags
        or [
            "figma",
            "max-factory",
            "curated",
            "inject-figma-densify",
        ],
        "source": source,
        "sku": sku,
        "imageUrl": image,
    }
    return out


# ---------------------------------------------------------------------------
# MUST-ADD: Inori #143 (Guilty Crown) — GSC CDN + CDJapan JAN
# ---------------------------------------------------------------------------
INORI = row(
    "figma-143-inori-yuzuriha",
    "Inori Yuzuriha",
    "Guilty Crown",
    line="figma Guilty Crown",
    release="2012-09-01",
    msrp=59.99,
    demand=1.55,
    sku="4545784062326",
    image=f"{GSC}/20120404/3521/17985/large/a8ea600ea68bbbaa2a22f2a7ac32e682.jpg",
    tags=[
        "figma",
        "max-factory",
        "good-smile",
        "guilty-crown",
        "curated",
        "inject-figma-densify",
        "must-add",
    ],
    figma_no=143,
)

# ---------------------------------------------------------------------------
# GSC category / recent gaps — Good Smile CDN images (JAN when verified)
# ---------------------------------------------------------------------------
GSC_BATCH: list[tuple] = [
    # id, name, subtitle, line, release, gsc_path, jan, figma_no, demand
    (
        "figma-shiroko-sunaookami",
        "Shiroko Sunaookami",
        "Blue Archive",
        "figma Blue Archive",
        "2024-07-01",
        f"{GSC}/20220407/12549/97554/large/b73606e8eec374064c8bf570f78417fd.jpg",
        None,
        None,
        1.4,
    ),
    (
        "figma-yuta-okkotsu",
        "Yuta Okkotsu",
        "Jujutsu Kaisen",
        "figma Jujutsu Kaisen",
        "2024-02-01",
        f"{GSC}/20230519/14386/115414/large/a44c777446964d72811da3ae671f8668.jpg",
        None,
        None,
        1.45,
    ),
    (
        "figma-rei-takanashi-sokyu",
        "Rei Takanashi",
        "Sokyu",
        "figma",
        "2024-02-01",
        f"{GSC}/20230525/14420/115773/large/edf27aff740c7c85df51c4c8ecd9c137.jpg",
        None,
        None,
        1.25,
    ),
    (
        "figma-thorfinn",
        "Thorfinn",
        "Vinland Saga",
        "figma Vinland Saga",
        "2024-02-01",
        f"{GSC}/20230525/14421/115784/large/eb50ff9ce2f5d562b420a52397b2aa63.jpg",
        None,
        None,
        1.5,
    ),
    (
        "figma-nh-02",
        "NH-02-",
        "NieR Automata",
        "figma NieR",
        "2024-03-01",
        f"{GSC}/20230531/14440/115950/large/ae361cd09af3a7bd6a9dfb1e998884eb.jpg",
        None,
        None,
        1.35,
    ),
    (
        "figma-611-toge-inumaki",
        "Toge Inumaki",
        "Jujutsu Kaisen",
        "figma Jujutsu Kaisen",
        "2024-03-01",
        f"{GSC}/20230623/14562/117188/large/abe5dd79064e4dc8a853b9b159cf5580.jpg",
        "4580590175587",
        611,
        1.35,
    ),
    (
        "figma-emmi",
        "E.M.M.I.",
        "Metroid Dread",
        "figma Metroid",
        "2024-05-01",
        f"{GSC}/20230704/14612/117745/large/57b47d5afe6e872e97d7f5e4e06732f1.jpg",
        None,
        None,
        1.3,
    ),
    (
        "figma-arcueid-brunestud",
        "Arcueid Brunestud",
        "Tsukihime",
        "figma Tsukihime",
        "2024-05-01",
        f"{GSC}/20230721/14693/118522/large/1faafe76c4bb3eac509a02aaf16a1d15.jpg",
        None,
        None,
        1.45,
    ),
    (
        "figma-arcueid-brunestud-dx",
        "Arcueid Brunestud",
        "Tsukihime DX Edition",
        "figma Tsukihime",
        "2024-05-01",
        f"{GSC}/20230721/14692/118512/large/d3db8b6ab096dbaf8c7c87ea5a27dfaf.jpg",
        None,
        None,
        1.5,
    ),
    (
        "figma-eivor",
        "Eivor",
        "Assassin's Creed Valhalla",
        "figma Assassin's Creed",
        "2024-05-01",
        f"{GSC}/20230825/14858/120004/large/5f95465dd7d6aba5315265140520146a.jpg",
        None,
        None,
        1.35,
    ),
    (
        "figma-chisato-nishikigi",
        "Chisato Nishikigi",
        "Lycoris Recoil",
        "figma Lycoris Recoil",
        "2024-06-01",
        f"{GSC}/20230921/14996/121367/large/a68eebd5c59eb14b77272c01340ebd29.jpg",
        None,
        None,
        1.5,
    ),
    (
        "figma-takina-inoue",
        "Takina Inoue",
        "Lycoris Recoil",
        "figma Lycoris Recoil",
        "2024-06-01",
        f"{GSC}/20230921/14997/121378/large/b466c8a9df17a6d86447d6cd55e80ef6.jpg",
        None,
        None,
        1.5,
    ),
    (
        "figma-gawr-gura",
        "Gawr Gura",
        "hololive English",
        "figma hololive",
        "2024-08-01",
        f"{GSC}/20231019/15103/122375/large/36bbc319cc3c081bf28810963a33f922.jpg",
        None,
        None,
        1.55,
    ),
    (
        "figma-la-darknesss",
        "La+ Darknesss",
        "hololive",
        "figma hololive",
        "2024-09-01",
        f"{GSC}/20231117/15229/123450/large/b93650f0d839b1570415b21c369505ff.jpg",
        None,
        None,
        1.35,
    ),
    (
        "figma-racing-miku-2023",
        "Racing Miku",
        "2023 ver.",
        "figma Vocaloid",
        "2024-08-01",
        f"{GSC}/20231117/15238/123533/large/55f80bbb4c2267ef8894377fe5f1e95c.jpg",
        None,
        None,
        1.35,
    ),
    (
        "figma-kazusa-kyoyama",
        "Kazusa Kyoyama",
        "Oshi no Ko",
        "figma Oshi no Ko",
        "2024-10-01",
        f"{GSC}/20231128/15293/124123/large/043ac668b083d523445bdc81d617d26a.jpg",
        None,
        None,
        1.3,
    ),
    (
        "figma-samurai-cyberpunk",
        "SAMURAI",
        "Cyberpunk: Edgerunners",
        "figma Cyberpunk",
        "2024-10-01",
        f"{GSC}/20231221/15365/124886/large/61f45758a95f8634ddfe624e3903aa5a.jpg",
        None,
        None,
        1.4,
    ),
    (
        "figma-sp080-femto-birth",
        "Femto",
        "Birth of the Hawk of Darkness ver.",
        "figma Berserk",
        "2024-06-01",
        f"{GSC}/20160720/5811/40147/large/8a0808706a7e88f6b0c57e371db80994.jpg",
        "4570001512285",
        None,
        1.55,
    ),
    (
        "figma-femto",
        "Femto",
        "Berserk",
        "figma Berserk",
        "2024-06-01",
        f"{GSC}/20160720/5812/40159/large/1ba8b39b3bd177f621442842638d1d97.jpg",
        None,
        None,
        1.5,
    ),
    (
        "figma-void-ubik",
        "Void",
        "figFIX Ubik · Berserk",
        "figma Berserk",
        "2024-07-01",
        f"{GSC}/20161021/6026/41943/large/1e9e415068ccd2a39c8a74df812675fa.jpg",
        None,
        None,
        1.35,
    ),
    (
        "figma-megumin",
        "Megumin",
        "KonoSuba",
        "figma KonoSuba",
        "2024-05-01",
        f"{GSC}/20180817/7533/53883/large/d488f566084282291b959a7b23cdd9e7.jpg",
        None,
        None,
        1.5,
    ),
    (
        "figma-lanze-reiter",
        "LANZE REITER",
        "Armored Core",
        "figma",
        "2024-07-01",
        f"{GSC}/20200722/9824/72382/large/553dcb8880ece6c965df0aead91f32ce.jpg",
        None,
        None,
        1.3,
    ),
]

# ---------------------------------------------------------------------------
# Classics + recent densify — retailer JAN + Shopify CDN (verified feeds)
# ---------------------------------------------------------------------------
RETAIL_BATCH: list[tuple] = [
    # id, name, subtitle, line, release, jan, image, figma_no, demand
    (
        "figma-bruce-lee",
        "Bruce Lee",
        "Bruce Lee",
        "figma",
        "2016-01-01",
        "4545784062883",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/bruce-lee-5-inch-figma-series-bruce-lee_image.gif?v=1784746524",
        None,
        1.3,
    ),
    (
        "figma-saitama",
        "Saitama",
        "One-Punch Man",
        "figma One-Punch Man",
        "2017-01-01",
        "4545784064450",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/one-punch-man-figma-series-5-inch-saitama_image.gif?v=1723137395",
        None,
        1.55,
    ),
    (
        "figma-260-minami-kotori",
        "Minami Kotori",
        "Love Live!",
        "figma Love Live!",
        "2015-01-01",
        "4545784063811",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/love-live-5-inch-action-figure-figma-series-minami-kotori-260_image.gif?v=1723132581",
        260,
        1.3,
    ),
    (
        "figma-ayase-aragaki",
        "Ayase Aragaki",
        "Oreimo",
        "figma Oreimo",
        "2012-01-01",
        "4545784061961",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-My-Little-Sister-Can39T-Be-This-Cute--Ayase-Aragaki-4545784061961-0.jpg?v=1726716436",
        None,
        1.35,
    ),
    (
        "figma-megurine-luka",
        "Megurine Luka",
        "Vocaloid",
        "figma Vocaloid",
        "2011-01-01",
        "4545784061411",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/max-factory-figma-megurine-luka-action-figure-poseable-collectible_1_1765543730.webp?v=1765543815",
        None,
        1.4,
    ),
    (
        "figma-tainaka-ritsu",
        "Tainaka Ritsu",
        "K-On! Uniform ver.",
        "figma K-On!",
        "2011-01-01",
        "4545784061183",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-KOn-Tainaka-Ritsu-Uniform-Ver.-4545784061183-0.jpg?v=1726716443",
        None,
        1.35,
    ),
    (
        "figma-takamine-manaka",
        "Takamine Manaka",
        "Love Plus",
        "figma Love Plus",
        "2011-01-01",
        "4545784061909",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Love-Plus-Takamine-Manaka-4545784061909-0.jpg?v=1726656744",
        None,
        1.25,
    ),
    (
        "figma-brs2035",
        "BRS2035",
        "Black Rock Shooter The Game",
        "figma Black Rock Shooter",
        "2012-01-01",
        "4545784062029",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Black-Rock-Shooter-The-Game-Brs2035-4545784062029-0.jpg?v=1726715257",
        None,
        1.35,
    ),
    (
        "figma-solid-snake-mgs2",
        "Solid Snake",
        "MGS2 ver. Updated Edition",
        "figma Metal Gear",
        "2023-01-01",
        "4545784069745",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Metal-Gear-Solid-2-Sons-Of-Liberty-Solid-Snake-Mgs2-Ver.-Updated-Edition-4545784069745-0.jpg?v=1736489703",
        None,
        1.5,
    ),
    (
        "figma-skull-knight-dx",
        "Skull Knight",
        "Berserk DX Edition",
        "figma Berserk",
        "2022-01-01",
        "4545784069561",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Berserk-Skull-Knight-Dx-Edition-NonScale-Plastic-PrePainted-Movable-Figure-4545784069561-0.jpg?v=1726713789",
        None,
        1.55,
    ),
    (
        "figma-darkness-konosuba",
        "Darkness",
        "KonoSuba",
        "figma KonoSuba",
        "2022-01-01",
        "4545784069547",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Konosuba-God39S-Blessing-On-This-Wonderful-World-3-Darkness-NonScale-Abs-Amp-Pvc-Painted-Action-Figure-Resale-4545784069547-0.jpg?v=1726715274",
        None,
        1.4,
    ),
    (
        "figma-aqua-konosuba",
        "Aqua",
        "KonoSuba",
        "figma KonoSuba",
        "2022-01-01",
        "4545784069417",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Konosuba-God39S-Blessing-On-This-Wonderful-World-3-Aqua-NonScale-Plastic-PrePainted-Action-Figure-Second-Resale-4545784069417-0.jpg?v=1726717031",
        None,
        1.45,
    ),
    (
        "figma-chilchuck",
        "Chilchuck",
        "Delicious in Dungeon",
        "figma Dungeon Meshi",
        "2024-01-01",
        "4545784069936",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Max-Factory-Figma-Dungeon-Meshi-Chilchuck-NonScale-Plastic-PrePainted-Action-Figure-4545784069936-0.jpg?v=1746024076",
        None,
        1.4,
    ),
    (
        "figma-marcille",
        "Marcille",
        "Delicious in Dungeon",
        "figma Dungeon Meshi",
        "2024-01-01",
        "4545784069592",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Dungeon-Meal-Marsil-NonScale-Plastic-PrePainted-Action-Figure-4545784069592-0.jpg?v=1726714581",
        None,
        1.45,
    ),
    (
        "figma-okarun",
        "Okarun",
        "Dandadan Transformation",
        "figma Dandadan",
        "2024-01-01",
        "4545784069752",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Dandadan-Okarun-Transformation-NonScale-Plastic-Painted-Movable-Figure-4545784069752-0.jpg?v=1734940369",
        None,
        1.5,
    ),
    (
        "figma-momo-dandadan",
        "Momo Ayase",
        "Dandadan",
        "figma Dandadan",
        "2024-01-01",
        "4571697181304",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Good-Smile-Company-Figma-Dandadan-Momo-NonScale-Plastic-PrePainted-Movable-Figure-Good-Smile-Company-4571697181304-0.jpg?v=1745847463",
        None,
        1.5,
    ),
    (
        "figma-holo",
        "Holo",
        "Spice and Wolf",
        "figma Spice and Wolf",
        "2024-01-01",
        "4580590205987",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Spice-And-Wolf-Merchant-Meets-The-Wise-Wolf-Holo-4580590205987-0.jpg?v=1736346821",
        None,
        1.5,
    ),
    (
        "figma-lilith-diablo",
        "Lilith",
        "Diablo IV",
        "figma Diablo",
        "2024-01-01",
        "4580590206588",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Diablo-Iv-Lilith-NonScale-Plastic-PrePainted-Action-Figure-4580590206588-0.jpg?v=1740650762",
        None,
        1.4,
    ),
    (
        "figma-zagreus",
        "Zagreus",
        "Hades",
        "figma Hades",
        "2024-01-01",
        "4580828662162",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Good-Smile-Company-Figma-Hades-Zagreus-NonScale-Plastic-Painted-Action-Figure-4580828662162-0.jpg?v=1759286082",
        None,
        1.45,
    ),
    (
        "figma-nanami-kento",
        "Kento Nanami",
        "Jujutsu Kaisen",
        "figma Jujutsu Kaisen",
        "2022-01-01",
        "4580590129986",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/jujutsu-kaisen-figma-nanami-4580590129986-pkg.jpg?v=1752709688",
        None,
        1.4,
    ),
    (
        "figma-nobara-kugisaki",
        "Nobara Kugisaki",
        "Jujutsu Kaisen",
        "figma Jujutsu Kaisen",
        "2022-01-01",
        "4580590129979",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/jujutsu-kaisen-figma-nobara-kugisaki-4580590129979-pkg.jpg?v=1769559003",
        None,
        1.4,
    ),
    (
        "figma-635-eunie",
        "Eunie",
        "Xenoblade Chronicles 3",
        "figma Xenoblade",
        "2023-01-01",
        "4580416928939",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Xenoblade-3--Eunie--Figma-635-Good-Smile-Company-Shop-Exclusive-4580416928939-0.jpg?v=1730356351",
        635,
        1.45,
    ),
    (
        "figma-byleth",
        "Byleth",
        "Fire Emblem Three Houses",
        "figma Fire Emblem",
        "2022-01-01",
        "4571697185890",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Good-Smile-Company-Good-Smile-Company-Figma-Fire-Emblem-Three-Houses-Byleth-NonScale-Plastic-PrePainted-Action-Figure-4571697185890-0.jpg?v=1749547669",
        None,
        1.4,
    ),
    (
        "figma-edelgard",
        "Edelgard von Hresvelg",
        "Fire Emblem Three Houses",
        "figma Fire Emblem",
        "2023-01-01",
        "4580828661677",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Good-Smile-Company-Figma-Fire-Emblem-Three-Houses-Edelgard-Von-Hresvelg-NonScale-Abs-Amp-Pvc-PrePainted-Movable-Figure-ReRelease-4580828661677-0.jpg?v=1759286021",
        None,
        1.4,
    ),
    (
        "figma-ump45",
        "UMP45",
        "Girls' Frontline",
        "figma Girls' Frontline",
        "2021-01-01",
        "4545784015209",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Max-Factory-Figma-Dolls39-Frontline-Ump45-NonScale-Plastic-Painted-Movable-Figure-Resale-4545784015209-0.jpg?v=1759459122",
        None,
        1.35,
    ),
    (
        "figma-ump9",
        "UMP9",
        "Girls' Frontline",
        "figma Girls' Frontline",
        "2021-01-01",
        "4545784015193",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Max-Factory-Figma-Dolls39-Frontline-Ump9-NonScale-Plastic-Painted-Movable-Figure-Resale-4545784015193-0.jpg?v=1759459126",
        None,
        1.35,
    ),
    (
        "figma-hoshimachi-suisei",
        "Hoshimachi Suisei",
        "hololive",
        "figma hololive",
        "2023-01-01",
        "4545784069691",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Hololive-Production-Hoshimachi-Suisei-Action-Figure-Japan-Official-4545784069691-0.jpg?v=1738591537",
        None,
        1.5,
    ),
    (
        "figma-sakamata-kuroe",
        "Sakamata Kuroe",
        "hololive",
        "figma hololive",
        "2023-01-01",
        "4545784069486",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Hololive-Production-Sakamata-Kuroe-NonScale-Plastic-Painted-Movable-Figure-4545784069486-0.jpg?v=1726717721",
        None,
        1.35,
    ),
    (
        "figma-takanashi-kiara",
        "Takanashi Kiara",
        "hololive English",
        "figma hololive",
        "2023-01-01",
        "4545784069400",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Hololive-Production-Takanashi-Chiara-NonScale-Plastic-Painted-Movable-Figure-4545784069400-0.jpg?v=1726657266",
        None,
        1.4,
    ),
    (
        "figma-goro-akechi",
        "Goro Akechi",
        "Persona 5 Royal",
        "figma Persona",
        "2020-01-01",
        "4545784066959",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Max-Factory-Persona-5-Royal-Goro-Akechi-Figma-Action-Figure-Multicolor-4545784066959-0.jpg?v=1726717717",
        None,
        1.45,
    ),
    (
        "figma-gabimaru",
        "Gabimaru",
        "Hell's Paradise",
        "figma Hell's Paradise",
        "2023-01-01",
        "4580590179257",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Jigoku-Raku--Gabimaru--Figma-Max-Factory-Shop-Exclusive-4580590179257-0.jpg?v=1730041800",
        None,
        1.4,
    ),
    (
        "figma-asako-reizei",
        "Asako Reizei",
        "Girls und Panzer",
        "figma Girls und Panzer",
        "2015-01-01",
        "4545784063590",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Figma-Girls-Amp-Panzer-Asako-Reizei-NonScale-Abs-Amp-AtbcPvc-Painted-Movable-Figure-4545784063590-0.jpg?v=1726714534",
        None,
        1.25,
    ),
    (
        "figma-tracer",
        "Tracer",
        "Overwatch",
        "figma Overwatch",
        "2017-01-01",
        "4580416903554",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/overwatch-figma-series-6-inch-action-figure-tracer_image.gif?v=1784746570",
        None,
        1.35,
    ),
    (
        "figma-reaper",
        "Reaper",
        "Overwatch",
        "figma Overwatch",
        "2017-01-01",
        "4580416905350",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/overwatch-figma-series-6-inch-action-figure-reaper_loose.jpg?v=1723124862",
        None,
        1.3,
    ),
    (
        "figma-widowmaker",
        "Widowmaker",
        "Overwatch",
        "figma Overwatch",
        "2017-01-01",
        "4580416905060",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/overwatch-figma-6-inch-action-figure-widowmaker.jpg?v=1723137810",
        None,
        1.3,
    ),
    (
        "figma-anti-mage",
        "Anti-Mage",
        "Dota 2",
        "figma Dota 2",
        "2017-01-01",
        "4580416901864",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/dota-2-figma-series-6-inch-anti-mage_image.gif?v=1723125007",
        None,
        1.2,
    ),
    (
        "figma-windranger",
        "Windranger",
        "Dota 2",
        "figma Dota 2",
        "2017-01-01",
        "4580416901871",
        "https://cdn.shopify.com/s/files/1/0216/0984/0740/files/dota-2-figma-series-6-inch-wind-ranger_image.gif?v=1723123798",
        None,
        1.2,
    ),
    (
        "figma-slan-conrad",
        "Slan",
        "figFIX Conrad · Berserk",
        "figma Berserk",
        "2024-01-01",
        "4570001512308",
        "https://cdn.shopify.com/s/files/1/0568/2298/8958/files/Berserk--Slan--FigFIX-Conrad--Figma--2024-ReRelease-Freeing-Shop-Exclusive-4570001512308-0.jpg?v=1730528841",
        None,
        1.35,
    ),
]


def main() -> None:
    rows: list[dict] = load_json(ARCHIVE)
    by_id = {r["id"]: r for r in rows}
    sku_owners: dict[str, str] = {}
    for r in rows:
        s = clean_code(r.get("sku"))
        if s and is_gtin(s):
            sku_owners.setdefault(s, r["id"])

    # name+company soft dedupe for figma
    figma_name_keys = set()
    for r in rows:
        if r.get("company") == "figma":
            key = re.sub(r"[^a-z0-9]+", "", f"{r.get('name')}{r.get('subtitle')}".lower())
            figma_name_keys.add(key)

    aliases = ensure_alias_doc(load_json(ALIASES))
    sku_map: dict[str, str] = load_json(SKU_MAP)
    urls: dict[str, str] = load_json(URLS)

    added: list[str] = []
    skipped: list[dict] = []
    gtin_set: list[str] = []
    alias_added = 0
    img_baked = 0
    inori_ok = False

    def soft_dup(r: dict) -> bool:
        key = re.sub(r"[^a-z0-9]+", "", f"{r.get('name')}{r.get('subtitle')}".lower())
        return key in figma_name_keys

    def inject(r: dict, alias_codes: list[str] | None = None) -> bool:
        nonlocal alias_added, img_baked, inori_ok
        rid = r["id"]
        if rid in by_id:
            skipped.append({"id": rid, "reason": "id-exists"})
            return False
        if soft_dup(r):
            skipped.append({"id": rid, "reason": "name-subtitle-soft-dup"})
            return False
        sku = clean_code(r.get("sku"))
        if sku and is_gtin(sku):
            owner = sku_owners.get(sku)
            if owner and owner != rid:
                skipped.append({"id": rid, "reason": f"gtin-owned-by:{owner}", "sku": sku})
                return False
            sku_owners[sku] = rid
            gtin_set.append(sku)
        elif sku and not is_gtin(sku):
            # listing codes → alias only
            alias_codes = list(alias_codes or []) + [sku]
            r["sku"] = None
            sku = None

        tags = list(r.get("tags") or [])
        if r.get("sku") and is_gtin(str(r["sku"])):
            if "sku-bake" not in tags:
                tags += ["sku-bake", "sku-gtin"]
            sku_map[rid] = str(r["sku"])
        if r.get("imageUrl"):
            urls[rid] = r["imageUrl"]
            img_baked += 1
            img_tag = "img:goodsmile" if "goodsmile.info" in (r["imageUrl"] or "") else "img:shopify-cdn"
            if "image-bake" not in tags:
                tags += ["image-bake", img_tag]
        r["tags"] = tags

        rows.append(r)
        by_id[rid] = r
        added.append(rid)
        key = re.sub(r"[^a-z0-9]+", "", f"{r.get('name')}{r.get('subtitle')}".lower())
        figma_name_keys.add(key)
        if alias_codes:
            alias_added += add_aliases(aliases, rid, alias_codes)
        if rid == "figma-143-inori-yuzuriha":
            inori_ok = True
        return True

    # 1) Inori first
    inject(INORI, ["GSC3521", "figma#143", "id:figma-143-inori-yuzuriha"])

    gsc_n = retail_n = 0
    for rid, name, sub, line, release, img, jan, fno, demand in GSC_BATCH:
        r = row(
            rid,
            name,
            sub,
            line=line,
            release=release,
            demand=demand,
            sku=jan,
            image=img,
            figma_no=fno,
            tags=["figma", "max-factory", "good-smile", "curated", "inject-figma-densify", "gsc-catalog"],
        )
        if inject(r, [f"id:{rid}"] + ([f"figma#{fno}"] if fno else [])):
            gsc_n += 1

    for rid, name, sub, line, release, jan, img, fno, demand in RETAIL_BATCH:
        r = row(
            rid,
            name,
            sub,
            line=line,
            release=release,
            demand=demand,
            sku=jan,
            image=img,
            figma_no=fno,
            tags=["figma", "max-factory", "curated", "inject-figma-densify", "retailer-jan"],
        )
        if inject(r, [f"id:{rid}"] + ([f"figma#{fno}"] if fno else [])):
            retail_n += 1

    aliases["updatedAt"] = now_iso()
    aliases.setdefault("stats", {})
    aliases["stats"]["figmaDensifyInject"] = {
        "at": now_iso(),
        "added": len(added),
        "aliasAdded": alias_added,
        "inori": inori_ok,
    }

    write_json(ARCHIVE, rows)
    write_json(ALIASES, aliases)
    write_json(SKU_MAP, sku_map)
    write_json(URLS, urls)

    figma_total = sum(1 for r in rows if r.get("company") == "figma")
    stats = {
        "at": now_iso(),
        "inoriPresent": inori_ok,
        "inoriJan": "4545784062326",
        "added": len(added),
        "gscCatalogAdded": gsc_n,
        "retailerJanAdded": retail_n,
        "addedIds": added,
        "gtins": gtin_set,
        "skipped": skipped,
        "aliasAdded": alias_added,
        "imagesBaked": img_baked,
        "figmaTotalAfter": figma_total,
        "oneshotCount": len(rows),
        "sampleNames": [
            by_id[i].get("name") for i in added[:12] if i in by_id
        ],
        "notes": [
            "Inori #143: GSC CDN large image + CDJapan JAN 4545784062326",
            "GSC category scrape 2024 wave: images from images.goodsmile.info; JAN only when retailer-verified",
            "Classics densify: Max Factory older titles + 2024 releases from Shopify retailer feeds",
            "No Live publish",
        ],
    }
    write_json(STATS, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

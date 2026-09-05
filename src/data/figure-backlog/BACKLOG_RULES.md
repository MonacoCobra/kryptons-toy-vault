# Figure archive rules (Shelby 2026-09-05)

- **Release floor:** 1980-01-01. Catalog modern → 1980; nothing older than 1980.
- **Brand universe:** `company-universe.txt` — full BigBadToyStore A–Z brand list (awareness / filtering; not a fabricate-every-brand mandate).
- **Segment filter:** articulated **action figures** only. Exclude board games, RPG pubs, comics publishers, music labels, apparel, lamps, cards-only, dolls, plush, pins, statue-only lines.
- **Images:** no generative AI art; CSS/palette placeholders OK; real Shopify CDN `imageUrl` when available.
- **Growth strategy:** **one-shot permanent dump** (`scripts/gen-figure-oneshot.py` → `figure-archive/oneshot.json`). Legacy ~3-week backlog batches are **optional only**.
- **Quality:** depth on real AF makers (Hasbro lines, McFarlane, NECA, Mezco, Bandai/SHF, Super7, etc.). Skip obscure brands without a feed rather than inventing garbage rows.

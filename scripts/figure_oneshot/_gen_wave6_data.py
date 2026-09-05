#!/usr/bin/env python3
"""Wave 6 data was generated into bbts_wave6_data.json (canonical).

Re-run curation via: python3 scripts/gen-figure-oneshot.py --curated-only
Do not invent filler SKUs; edit bbts_wave6_data.json + curated_bbts_wave6.py.
"""
from pathlib import Path
print("canonical data:", Path(__file__).with_name("bbts_wave6_data.json"))

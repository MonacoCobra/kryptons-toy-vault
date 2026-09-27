#!/bin/sh
set -eu
cd /workspace
# Catalog rows are static shards, not part of the dev bundle.
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}"
node scripts/preview.mjs stop || true
if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8080/; then
  exit 0
fi
npm run dev >>/tmp/app-startup.log 2>&1 &

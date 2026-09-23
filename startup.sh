#!/bin/sh
set -eu
cd /workspace
# Comics plus the figure archive blow past the default 4GB heap, and 8GB
# still aborts dev SSR of those modules. 12GB keeps the preview process up.
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=12288}"
node scripts/preview.mjs stop || true
if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8080/; then
  exit 0
fi
npm run dev >>/tmp/app-startup.log 2>&1 &

#!/bin/sh
set -eu
cd /workspace
# Comics catalog is large enough that the default 4GB Node heap OOMs on /comics.
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=8192}"
node scripts/preview.mjs stop || true
if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8080/; then
  exit 0
fi
npm run dev >>/tmp/app-startup.log 2>&1 &

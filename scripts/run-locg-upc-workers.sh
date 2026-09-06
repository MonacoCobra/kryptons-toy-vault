#!/usr/bin/env bash
# Three partitioned LOCG UPC workers (Marvel / DC / other). No sidebar bots.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p scripts/logs
DELAY="${DELAY:-30}"
LIMIT="${LIMIT:-2500}"
MAX_MIN="${MAX_MINUTES:-360}"
MIN_YEAR="${MIN_YEAR:-2005}"
MAX_PER="${MAX_PER_SERIES:-100}"

start_worker () {
  local group="$1"
  local log="scripts/logs/upc-backfill-${group}.log"
  local pidf="scripts/logs/upc-backfill-${group}.pid"
  local stats="scripts/comic-upc-backfill-stats-${group}.json"
  if [[ -f "$pidf" ]] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "worker $group already running pid=$(cat "$pidf")"
    return 0
  fi
  nohup python3 -u scripts/backfill-comic-upcs.py \
    --from-catalog --series-batch \
    --publisher-group "$group" \
    --limit "$LIMIT" --max-per-series "$MAX_PER" \
    --min-year "$MIN_YEAR" --max-minutes "$MAX_MIN" \
    --delay "$DELAY" --no-cv \
    --worker-id "$group" \
    --stats-file "$stats" \
    >"$log" 2>&1 &
  echo $! >"$pidf"
  echo "started $group pid=$(cat "$pidf") log=$log"
}

start_worker marvel
sleep 10
start_worker dc
sleep 10
start_worker other
echo "all workers launched"

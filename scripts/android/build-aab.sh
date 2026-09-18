#!/usr/bin/env bash
# Build a Play-upload Android App Bundle from android/ (signed if keystore.properties exists).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/android"

PROPS="keystore.properties"
if [[ ! -f "$PROPS" ]]; then
  echo "Missing $ROOT/android/keystore.properties" >&2
  echo "Copy keystore.properties.example and fill in the gitignored passwords," >&2
  echo "or run: bash scripts/android/create-upload-keystore.sh" >&2
  exit 1
fi

if [[ ! -x "./gradlew" ]]; then
  chmod +x ./gradlew
fi

echo "Building signed release AAB (me.kryptontoyvault.app)…"
./gradlew bundleRelease --no-daemon

AAB="app/build/outputs/bundle/release/app-release.aab"
if [[ ! -f "$AAB" ]]; then
  echo "ERROR: expected $AAB" >&2
  exit 1
fi

echo
echo "AAB: $ROOT/android/$AAB"
echo "Upload that file in Play Console → Test and release → Production (or Internal testing)."
echo
echo "After the first upload, copy the Play App Signing SHA-256 into"
echo "public/.well-known/assetlinks.json and republish the Live web app."

#!/usr/bin/env bash
set -euo pipefail

# Expects working tree prepared by ci-prepare.sh (twa/ + keystore).
# Required env: ALIAS, BUBBLEWRAP_KEYSTORE_PASSWORD, BUBBLEWRAP_KEY_PASSWORD
# Also: JAVA_HOME, ANDROID_HOME (from setup-java / setup-android)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/twa"

ALIAS="${ALIAS:?ALIAS is required}"
: "${BUBBLEWRAP_KEYSTORE_PASSWORD:?BUBBLEWRAP_KEYSTORE_PASSWORD is required}"
: "${BUBBLEWRAP_KEY_PASSWORD:?BUBBLEWRAP_KEY_PASSWORD is required}"
: "${JAVA_HOME:?JAVA_HOME is required}"
: "${ANDROID_HOME:?ANDROID_HOME is required}"

mkdir -p "$HOME/.bubblewrap"
python3 - <<PY
import json, os
from pathlib import Path
cfg = {
    "jdkPath": os.environ["JAVA_HOME"],
    "androidSdkPath": os.environ["ANDROID_HOME"],
}
path = Path.home() / ".bubblewrap" / "config.json"
path.write_text(json.dumps(cfg, indent=2) + "\n")
print(f"Wrote {path}: jdkPath={cfg['jdkPath']} androidSdkPath={cfg['androidSdkPath']}")
PY
if ! command -v bubblewrap >/dev/null 2>&1; then
  echo "Installing @bubblewrap/cli globally"
  npm install -g @bubblewrap/cli
fi

echo "Running bubblewrap update --skipVersionUpgrade"
bubblewrap update --skipVersionUpgrade

echo "Running bubblewrap build (alias=$ALIAS)"
bubblewrap build \
  --skipPwaValidation \
  --signingKeyPath ./android-release.keystore \
  --signingKeyAlias "$ALIAS"

echo "Build artifacts:"
ls -la app-release-signed.apk 2>/dev/null || ls -la *.apk 2>/dev/null || true
ls -la app-release-bundle.aab 2>/dev/null || ls -la *.aab 2>/dev/null || true
echo "ci-build.sh complete"

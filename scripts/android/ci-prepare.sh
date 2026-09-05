#!/usr/bin/env bash
set -euo pipefail

# Env (required unless noted):
#   HOST, VERSION_NAME, VERSION_CODE
#   ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_PASSWORD, ANDROID_KEY_ALIAS
# Optional:
#   ANDROID_KEYSTORE_BASE64  — if unset, generates an ephemeral keystore

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

HOST="${HOST:?HOST is required}"
VERSION_NAME="${VERSION_NAME:?VERSION_NAME is required}"
VERSION_CODE="${VERSION_CODE:?VERSION_CODE is required}"
ANDROID_KEY_ALIAS="${ANDROID_KEY_ALIAS:-krypton}"
ANDROID_KEYSTORE_PASSWORD="${ANDROID_KEYSTORE_PASSWORD:-}"
ANDROID_KEY_PASSWORD="${ANDROID_KEY_PASSWORD:-}"

mkdir -p twa
cp android/twa-manifest.json twa/

# Patch host, URLs, version, and signing alias into the working manifest.
HOST="$HOST" VERSION_NAME="$VERSION_NAME" VERSION_CODE="$VERSION_CODE" \
ANDROID_KEY_ALIAS="$ANDROID_KEY_ALIAS" python3 - <<'PY'
import json, os
from pathlib import Path

host = os.environ["HOST"].strip().removeprefix("https://").removeprefix("http://").rstrip("/")
version_name = os.environ["VERSION_NAME"]
version_code = int(os.environ["VERSION_CODE"])
alias = os.environ["ANDROID_KEY_ALIAS"]
base = f"https://{host}"

path = Path("twa/twa-manifest.json")
data = json.loads(path.read_text())
data["host"] = host
data["iconUrl"] = f"{base}/krypton-logo.png"
data["maskableIconUrl"] = f"{base}/krypton-logo.png"
data["webManifestUrl"] = f"{base}/__grok/manifest.webmanifest"
data["fullScopeUrl"] = f"{base}/"
data["appVersionName"] = version_name
data["appVersionCode"] = version_code
data.setdefault("signingKey", {})
data["signingKey"]["path"] = "./android-release.keystore"
data["signingKey"]["alias"] = alias
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"Patched twa-manifest.json for host={host} version={version_name} ({version_code})")
PY
EPHEMERAL=false
STORE_PASS="${ANDROID_KEYSTORE_PASSWORD}"
KEY_PASS="${ANDROID_KEY_PASSWORD}"
ALIAS="$ANDROID_KEY_ALIAS"
KEYSTORE_PATH="twa/android-release.keystore"

if [[ -n "${ANDROID_KEYSTORE_BASE64:-}" ]]; then
  echo "Decoding provided ANDROID_KEYSTORE_BASE64 -> $KEYSTORE_PATH"
  echo "$ANDROID_KEYSTORE_BASE64" | base64 -d > "$KEYSTORE_PATH"
  if [[ -z "$STORE_PASS" || -z "$KEY_PASS" ]]; then
    echo "ERROR: ANDROID_KEYSTORE_PASSWORD and ANDROID_KEY_PASSWORD are required when using ANDROID_KEYSTORE_BASE64" >&2
    exit 1
  fi
else
  if [[ "${REQUIRE_STABLE_KEYSTORE:-}" == "1" || "${REQUIRE_STABLE_KEYSTORE:-}" == "true" ]]; then
    echo "ERROR: ANDROID_KEYSTORE_BASE64 is required for stable/updatable releases (REQUIRE_STABLE_KEYSTORE=1)." >&2
    exit 1
  fi
  EPHEMERAL=true
  STORE_PASS="${STORE_PASS:-android}"
  KEY_PASS="${KEY_PASS:-android}"
  ALIAS="${ALIAS:-krypton}"
  echo "Generating ephemeral keystore at $KEYSTORE_PATH (alias=$ALIAS)"
  keytool -genkeypair \
    -v \
    -keystore "$KEYSTORE_PATH" \
    -alias "$ALIAS" \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -storepass "$STORE_PASS" \
    -keypass "$KEY_PASS" \
    -dname "CN=Krypton Toy Vault Ephemeral, OU=CI, O=Krypton, L=Unknown, ST=Unknown, C=US"
fi

# SHA-256 fingerprint (colon-separated uppercase, Digital Asset Links style)
FINGERPRINT="$(
  keytool -list -v \
    -keystore "$KEYSTORE_PATH" \
    -alias "$ALIAS" \
    -storepass "$STORE_PASS" \
  | awk -F': ' '/SHA256:/{print $2; exit}'
)"
if [[ -z "$FINGERPRINT" ]]; then
  echo "ERROR: could not read SHA256 fingerprint from keystore" >&2
  exit 1
fi
echo "SHA256 fingerprint: $FINGERPRINT"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "ephemeral=$EPHEMERAL"
    echo "store_pass=$STORE_PASS"
    echo "key_pass=$KEY_PASS"
    echo "alias=$ALIAS"
    echo "fingerprint=$FINGERPRINT"
  } >> "$GITHUB_OUTPUT"
fi

# Stable (non-ephemeral) builds: keep Digital Asset Links in sync for the next deploy.
if [[ "$EPHEMERAL" != "true" ]]; then
  FINGERPRINT="$FINGERPRINT" python3 - <<'PY'
import json, os
from pathlib import Path

fp = os.environ["FINGERPRINT"]
path = Path("public/.well-known/assetlinks.json")
data = json.loads(path.read_text())
if not isinstance(data, list) or not data:
    data = [{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "me.kryptontoyvault.app",
            "sha256_cert_fingerprints": [fp],
        },
    }]
else:
    target = data[0].setdefault("target", {})
    target["namespace"] = "android_app"
    target.setdefault("package_name", "me.kryptontoyvault.app")
    fps = target.get("sha256_cert_fingerprints") or []
    if fp not in fps:
        fps = [x for x in fps if "REPLACE_WITH" not in x]
        if fp not in fps:
            fps.append(fp)
        target["sha256_cert_fingerprints"] = fps
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"Updated {path} with fingerprint")
PY
else
  echo "Ephemeral keystore: skipping assetlinks.json update (fingerprint changes every run)."
fi

echo "ci-prepare.sh complete"

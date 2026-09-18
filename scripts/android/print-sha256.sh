#!/usr/bin/env bash
# Print the Digital Asset Links SHA-256 for a local keystore.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
KEYSTORE="${1:-${ANDROID_UPLOAD_KEYSTORE:-$ROOT/android/upload-keystore.jks}}"
ALIAS="${2:-${ANDROID_KEY_ALIAS:-upload}}"

if [[ ! -f "$KEYSTORE" ]]; then
  echo "Keystore not found: $KEYSTORE" >&2
  echo "Usage: $0 [keystore.jks] [alias]" >&2
  echo "Or run: bash scripts/android/create-upload-keystore.sh" >&2
  exit 1
fi

FINGERPRINT="$(
  keytool -list -v -keystore "$KEYSTORE" -alias "$ALIAS" \
    | awk -F': ' '/SHA256:/{print $2; exit}'
)"

if [[ -z "$FINGERPRINT" ]]; then
  echo "ERROR: could not read SHA256 fingerprint" >&2
  exit 1
fi

echo "$FINGERPRINT"
echo
echo "Paste that value into public/.well-known/assetlinks.json"
echo "under target.sha256_cert_fingerprints, then republish the web app."
echo
echo "Play-installed TWAs also need the Play App Signing certificate SHA-256"
echo "from Play Console → Test and release → App integrity → App signing."

#!/usr/bin/env bash
set -euo pipefail

# Creates/updates GitHub Release for TAG; uploads signed APK (+ AAB if present).
# Required env: TAG, HOST, VERSION_NAME, FINGERPRINT, EPHEMERAL

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

TAG="${TAG:?TAG is required}"
HOST="${HOST:?HOST is required}"
VERSION_NAME="${VERSION_NAME:?VERSION_NAME is required}"
FINGERPRINT="${FINGERPRINT:?FINGERPRINT is required}"
EPHEMERAL="${EPHEMERAL:-false}"

APK="twa/app-release-signed.apk"
AAB="twa/app-release-bundle.aab"

if [[ ! -f "$APK" ]]; then
  APK="$(find twa -maxdepth 1 -name '*signed*.apk' -print -quit || true)"
fi
if [[ -z "${APK:-}" || ! -f "$APK" ]]; then
  echo "ERROR: signed APK not found under twa/" >&2
  exit 1
fi

NOTES_FILE="$(mktemp)"
{
  echo "## Android TWA ${VERSION_NAME}"
  echo
  echo "- **Host:** \`https://${HOST}\`"
  echo "- **Package:** \`me.kryptontoyvault.app\`"
  echo "- **Version:** ${VERSION_NAME}"
  echo "- **Tag:** ${TAG}"
  echo "- **SHA-256 fingerprint:** \`${FINGERPRINT}\`"
  echo
  if [[ "$EPHEMERAL" == "true" ]]; then
    echo "> **Warning:** This build used an **ephemeral** signing key."
    echo "> Digital Asset Links / verified TWA will not stick across rebuilds,"
    echo "> and updates will not install over a differently-signed APK."
    echo "> Set \`ANDROID_KEYSTORE_BASE64\` (+ passwords) for stable releases."
    echo
  else
    echo "Signing key is the repo secret keystore. Ensure \`public/.well-known/assetlinks.json\`"
    echo "on the host includes the fingerprint above."
    echo
  fi
  echo "### Install"
  echo "1. Download \`$(basename "$APK")\`"
  echo "2. Allow Install unknown apps"
  echo "3. Open the APK on device"
} > "$NOTES_FILE"

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "Updating existing release $TAG"
  gh release edit "$TAG" --notes-file "$NOTES_FILE"
else
  echo "Creating release $TAG"
  gh release create "$TAG" --title "Android TWA ${VERSION_NAME}" --notes-file "$NOTES_FILE"
fi

gh release upload "$TAG" "$APK" --clobber
if [[ -f "$AAB" ]]; then
  gh release upload "$TAG" "$AAB" --clobber
fi

rm -f "$NOTES_FILE"
echo "ci-release.sh complete (tag=$TAG)"

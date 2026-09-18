#!/usr/bin/env bash
# Generate a Play upload keystore locally. Never commit the .jks or passwords.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT="${ANDROID_UPLOAD_KEYSTORE:-$ROOT/android/upload-keystore.jks}"
ALIAS="${ANDROID_KEY_ALIAS:-upload}"
PROPS="$ROOT/android/keystore.properties"

if [[ -f "$OUT" ]]; then
  echo "Keystore already exists: $OUT" >&2
  echo "Refusing to overwrite. Remove it first if you really want a new key." >&2
  exit 1
fi

echo "Creating upload keystore at: $OUT"
echo "Alias: $ALIAS"
echo "Store this file + both passwords in a password manager. Never commit them."
echo

keytool -genkeypair \
  -v \
  -keystore "$OUT" \
  -alias "$ALIAS" \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -dname "CN=Krypton's Toy Vault, OU=Play Upload, O=Krypton, L=Unknown, ST=Unknown, C=US"

echo
echo "=== SHA-256 fingerprint (paste into public/.well-known/assetlinks.json) ==="
keytool -list -v -keystore "$OUT" -alias "$ALIAS" | awk -F': ' '/SHA256:/{print $2; exit}'
echo

if [[ ! -f "$PROPS" ]]; then
  REL_STORE="${OUT#"$ROOT/android/"}"
  cat > "$PROPS" <<EOF
storeFile=$REL_STORE
storePassword=
keyAlias=$ALIAS
keyPassword=
EOF
  echo "Wrote $PROPS — fill in storePassword and keyPassword (gitignored)."
else
  echo "Left existing $PROPS untouched."
fi

echo
echo "Next:"
echo "  1. Put passwords in android/keystore.properties"
echo "  2. Append the SHA-256 above to public/.well-known/assetlinks.json"
echo "  3. bash scripts/android/build-aab.sh"
echo "  4. After the first Play upload, also paste the Play App Signing SHA-256"
echo "     (Play Console → App integrity → App signing) into assetlinks.json"
echo "     and republish the web app."

# Krypton's Toy Vault — Android TWA (Play AAB)

Trusted Web Activity around **https://kryptons-toy-vault.grok.me**  
Application id: **`me.kryptontoyvault.app`**

This folder is a Gradle project you open in Android Studio or build with `./gradlew`. It does **not** contain a keystore. Generate keys on your machine; never commit `*.jks`, `*.keystore`, or `keystore.properties`.

`twa-manifest.json` in this directory is the Bubblewrap config used by GitHub Actions for sideload APKs. Keep host / package / colors in sync with the Gradle app below.

## One-time: upload keystore + SHA-256

From the repo root:

```bash
bash scripts/android/create-upload-keystore.sh
```

That writes gitignored `android/upload-keystore.jks` and a `android/keystore.properties` stub. Put **storePassword** and **keyPassword** in that properties file (also gitignored).

Print the fingerprint to paste into Digital Asset Links:

```bash
bash scripts/android/print-sha256.sh
```

### What to paste where

File: `public/.well-known/assetlinks.json`  
Array: `target.sha256_cert_fingerprints`  
Package (already set): `me.kryptontoyvault.app`

| Fingerprint | Required for | How to get it |
| --- | --- | --- |
| Existing value in the file | GitHub Releases sideload APK | Leave it unless you retire those APKs |
| Upload key SHA-256 | Local / sideload builds signed with the new keystore | `print-sha256.sh` (`keytool` `SHA256:` line, colon-separated uppercase) |
| **Play App Signing SHA-256** | **Play-installed TWA URL-bar verification** | Play Console → Test and release → App integrity → App signing → **App signing key certificate** |

Play re-signs the app users install. Chrome checks the **Play App Signing** cert, not only the upload key. After the first AAB upload, append that SHA-256 to **both** `public/.well-known/assetlinks.json` and `src/lib/android/assetlinks.json` (keep them identical), merge, and **republish Live** so `https://kryptons-toy-vault.grok.me/.well-known/assetlinks.json` updates (`Content-Type: application/json`).

## Build the signed AAB

```bash
bash scripts/android/build-aab.sh
```

Output: `android/app/build/outputs/bundle/release/app-release.aab`

Or in this directory:

```bash
./gradlew bundleRelease
```

Upload the AAB in Play Console (Internal testing first is safest). Bump `versionCode` / `versionName` in `app/build.gradle.kts` for each new Play upload.

## Verify Digital Asset Links

```text
https://kryptons-toy-vault.grok.me/.well-known/assetlinks.json
https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://kryptons-toy-vault.grok.me
```

On device (after install): `adb logcat | grep -e OriginVerifier -e digital_asset_links`

## What not to commit

- `upload-keystore.jks` / any `*.jks` / `*.keystore`
- `keystore.properties` (copy from `keystore.properties.example`)
- `local.properties` (Android SDK path; Android Studio writes this)
- Passwords, Play Console service-account JSON

Store the keystore in a password manager. Losing it means you cannot update the Play listing unless Play App Signing is already enabled (you can still upload with a new upload key after Play support reset — keep a backup anyway).

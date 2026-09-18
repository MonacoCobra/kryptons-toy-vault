# Google Play — Trusted Web Activity (AAB)

Package: `me.kryptontoyvault.app`  
Start URL: `https://kryptons-toy-vault.grok.me/`  
Hosted on **Grok Build** (this GitHub repo is the source of truth).

This is the Play Console path. Sideload APKs still ship from GitHub Releases — see [android-apk.md](android-apk.md).

## What lands on Live vs what stays on your machine

| On Live (web deploy) | Local only (never commit) |
| --- | --- |
| `public/.well-known/assetlinks.json` at `https://kryptons-toy-vault.grok.me/.well-known/assetlinks.json` (`Content-Type: application/json`) | `android/upload-keystore.jks` |
| PWA / TWA start URL and manifest | `android/keystore.properties` (passwords) |
| Package name + SHA-256 fingerprint(s) Google Play / Chrome check | The signed `.aab` you upload in Play Console |

## Fingerprints to paste into `assetlinks.json`

Edit `public/.well-known/assetlinks.json` → `target.sha256_cert_fingerprints`. Values must be **colon-separated uppercase SHA-256** (the `keytool` `SHA256:` line). Invalid placeholders break Play verification — paste real fingerprints only.

1. **Keep** the existing fingerprint if GitHub-release sideload APKs should stay verified.
2. **Upload key** — after `bash scripts/android/create-upload-keystore.sh`, copy the printed SHA-256. Skip this if Play uses the same keystore already represented in the file.
3. **Play App Signing (required for Play-installed TWA)** — after the first AAB upload: Play Console → **Test and release** → **App integrity** → **App signing** → copy **App signing key certificate** SHA-256. Chrome checks *this* cert for Play installs, not the upload key.

Then merge to `main` and republish the Grok Build Live site so the crawler sees the new JSON.

Check: [Digital Asset Links statement list](https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://kryptons-toy-vault.grok.me)

## Local AAB (upload to Play)

```bash
# one-time: upload keystore (gitignored)
bash scripts/android/create-upload-keystore.sh
# fill storePassword / keyPassword in android/keystore.properties

bash scripts/android/print-sha256.sh          # paste into assetlinks.json
bash scripts/android/build-aab.sh             # android/app/build/outputs/bundle/release/app-release.aab
```

Needs JDK 17+ and a network fetch of the Gradle distribution on first run. Android Studio can also open `android/` and run **Build → Generate Signed Bundle / APK**.

Play Console: create the app with application id `me.kryptontoyvault.app` if it does not exist → Internal testing (or Production) → upload the AAB. Enable Play App Signing (default) → copy the app-signing SHA-256 as above.

## Bubblewrap CI (sideload APK)

GitHub Actions still builds a Bubblewrap TWA APK from `android/twa-manifest.json` for GitHub Releases. That path can emit an `.aab` artifact too; **Play upload is meant to use the Gradle project in `android/`** so the signing key stays on your machine.

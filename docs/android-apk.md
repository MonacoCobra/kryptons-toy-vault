# Android APK from GitHub (no Grok Build host)

Sideload APKs for testing. **Google Play AAB** (upload keystore, Digital Asset Links fingerprints, Play Console) is documented in [android-play.md](android-play.md) and [android/README.md](../android/README.md).

Install path:

1. **GitHub Releases** -> download `app-release-signed.apk`
2. Android -> allow Install unknown apps -> open the APK

The APK is a **Trusted Web Activity** around your **production web host** (`kryptonstoyvault.com`).

Package id: `me.kryptontoyvault.app`

## Architecture

| Piece | Where |
| --- | --- |
| Source of truth | GitHub `MonacoCobra/kryptons-toy-vault` |
| Live web app | https://kryptonstoyvault.com |
| Phone install | APK attached to GitHub Releases |
| Collection data | Still device `localStorage` inside the TWA |

## One-time setup

1. Keep the live app published at **https://kryptonstoyvault.com**; GitHub remains source of truth.
2. Set production env as needed (`DATABASE_URL`, `COMICVINE_API_KEY`; leave `VITE_AUTH_ENABLED=false` unless you want accounts).
3. Note your production host (e.g. `kryptonstoyvault.com` or a custom domain).
4. **Required** repo secrets for updatable APKs: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_PASSWORD`, `ANDROID_KEY_ALIAS` (default `krypton`), plus optional `TWA_HOST`.
5. Keep `public/.well-known/assetlinks.json` on the live host in sync with the release keystore SHA-256 fingerprint (CI updates the file in-repo on stable builds; republish the web app so `/.well-known/assetlinks.json` is live).
6. **One-time:** uninstall any APK signed with the old ephemeral key before installing the first stable build — Android will not update across different signing keys. Later `android-v*` builds update in place.

## Build / publish APK

Tag:

```bash
git tag android-v1.0.0
git push origin android-v1.0.0
```

Or Actions -> **Android TWA APK** -> Run workflow (host defaults to `kryptonstoyvault.com`).

## Without an APK

Chrome -> open `https://kryptonstoyvault.com` -> Add to Home screen (PWA).

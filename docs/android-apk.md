# Android APK from GitHub (no Grok Build host)

Install path:

1. **GitHub Releases** -> download `app-release-signed.apk`
2. Android -> allow Install unknown apps -> open the APK

The APK is a **Trusted Web Activity** around your **production web host** (Vercel recommended), not `*.grok.me`.

Package id: `me.kryptontoyvault.app`

## Architecture

| Piece | Where |
| --- | --- |
| Source of truth | GitHub `MonacoCobra/kryptons-toy-vault` |
| Live web app | Vercel (or similar) from that repo |
| Phone install | APK attached to GitHub Releases |
| Collection data | Still device `localStorage` inside the TWA |

## One-time setup

1. Connect the GitHub repo to **Vercel** (Import project -> this repo -> deploy).
2. Set production env as needed (`DATABASE_URL`, `COMICVINE_API_KEY`; leave `VITE_AUTH_ENABLED=false` unless you want accounts).
3. Note your production host (e.g. `kryptons-toy-vault.vercel.app` or a custom domain).
4. Optional repo secrets for stable APK updates: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_PASSWORD`, `ANDROID_KEY_ALIAS` (default `krypton`), `TWA_HOST`.
5. Deploy `public/.well-known/assetlinks.json` on that host with the Release SHA-256 fingerprint.

## Build / publish APK

Tag:

```bash
git tag android-v1.0.0
git push origin android-v1.0.0
```

Or Actions -> **Android TWA APK** -> Run workflow -> set `twa_host` to your Vercel host.

## Without an APK

Chrome -> open the Vercel URL -> Add to Home screen (PWA).

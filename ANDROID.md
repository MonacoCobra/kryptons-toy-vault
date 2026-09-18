# Android install

Two paths wrap the same Live web app (`https://kryptons-toy-vault.grok.me`) as package `me.kryptontoyvault.app`:

| Path | What | Where |
| --- | --- | --- |
| **Google Play (this PR)** | Signed **AAB** (Trusted Web Activity) | Build locally from [`android/`](android/README.md), upload in Play Console |
| GitHub Releases | Sideload **APK** | [docs/android-apk.md](docs/android-apk.md) |

Digital Asset Links for Play TWA verification: `https://kryptons-toy-vault.grok.me/.well-known/assetlinks.json` (ships with the web app). After you create the Play upload keystore / first Play upload, paste SHA-256 fingerprints into that file and **republish Live**. Details: [docs/android-play.md](docs/android-play.md).

Never commit keystores or passwords.

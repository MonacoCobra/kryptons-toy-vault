# Digital Asset Links

Live URL (this folder deploys with the web app):

`https://kryptons-toy-vault.grok.me/.well-known/assetlinks.json`

Package: `me.kryptontoyvault.app`

## Fingerprint slot

Edit `assetlinks.json` → `target.sha256_cert_fingerprints` (colon-separated **uppercase** SHA-256).

| Slot | What to paste | Where it comes from |
| --- | --- | --- |
| Existing entry | GitHub Releases / sideload signing cert | Already in the file. Keep it so sideload APKs stay verified. |
| **Play App Signing** | App signing key certificate SHA-256 | Play Console → Test and release → App integrity → **App signing**. This is the fingerprint Chrome uses for Play-installed TWAs. |
| Play upload key (optional) | Upload-key SHA-256 | `keytool -list -v -keystore android/upload-keystore.jks -alias upload` after you generate the keystore locally. Needed if that cert differs from the existing sideload key. |

Invalid placeholders (non-hex) must never ship in the live JSON — Google's crawler will reject them. Paste only real `AA:BB:…` fingerprints, then republish the web app so Live updates.

Full walkthrough: [android/README.md](../../android/README.md) and [docs/android-play.md](../../docs/android-play.md).

# Altron APK build — setup guide

Developer: **Abbas** · App name: **Altron** (renamed from Jarvis)

GitHub builds the Android APK for you, free, on their servers. You never install
Android tools on your phone or PC.

## Files in this pack

| File | Where it goes in the repo |
|---|---|
| `.github/workflows/build-apk.yml` | `.github/workflows/build-apk.yml` |
| `buildozer.spec` | repo root |
| `main.py` | repo root |
| `rebrand.sh` | repo root (run once, then you can delete it) |

## Steps

1. Open https://github.com/MarkFrencerLozada/jarvis (or your own fork).
2. Add the four files above using **Add file → Create new file** and paste the contents.
   For the workflow, type the path `.github/workflows/build-apk.yml` and GitHub creates the folders.
3. Rename Jarvis to Altron: run `bash rebrand.sh` locally and push, or just edit the
   name in the UI files by hand. The APK is titled **Altron** either way, because that
   comes from `buildozer.spec`.
4. Go to the **Actions** tab → **Build Altron APK** → **Run workflow**.
5. First build takes 30–60 minutes (it downloads the Android SDK/NDK). Later builds are
   much faster thanks to caching.
6. When it finishes, the APK is in two places:
   - **Releases** — `Altron-v1.0.x.apk`, a public download link you can share.
   - **Actions → the run → Artifacts** — `Altron-APK`.
7. On the phone: open the APK, allow "install from unknown sources", install.

## Extras already included

- Manual **Run workflow** button with an optional version tag.
- Automatic version numbers (`v1.0.<build number>`) and automatic GitHub Release.
- Build caching so repeat builds are fast.
- Builds for both 64-bit and 32-bit phones (`arm64-v8a`, `armeabi-v7a`).
- Microphone, internet and storage permissions requested, so the voice button works.
- Full-screen in-app view of the existing chat interface, so it feels like a real app.
- Safe fallback: if the original Python files fail to import on the phone, Altron still
  opens with a working built-in chat screen instead of crashing.

## Notes and limits

- The APK is a **debug/unsigned** build. That is normal and installs fine manually, but
  it cannot go on Google Play as-is. Play needs a signed release build with a keystore —
  tell me if you want that added.
- Heavy Python libraries (torch, whisper, large OCR/PDF tools) cannot be packed into an
  APK. Altron on Android runs the chat UI plus whatever pure-Python parts import cleanly.
  Anything needing those heavy libraries should stay on Termux or a server.
- If the first build fails, open the failed step's log and send me the last lines — the
  usual cause is one package in `requirements` that has no Android build.

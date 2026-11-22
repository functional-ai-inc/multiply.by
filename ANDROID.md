# multiply.by as an Android app (Google Play)

Notes for packaging the multiply.by games as an Android app.

## Build the app yourself

Anyone can build the app from the public repo, on Linux, Mac or Windows. You need:

- **Java 17** (a JDK) and the **Android SDK** with Android 16 (API 36). Android Studio installs
  both; without it, install a JDK 17 and Google's command-line tools, then
  `sdkmanager "platforms;android-36" "build-tools;36.0.0" "platform-tools"`.
- **Python 3** and **git**.

Then:

1. Get the code:
   `git clone https://github.com/john-l-roseman/multiply.by.git` and `cd multiply.by/android`.
2. Get the games: `python3 gather-assets.py`. It downloads the current pages from
   https://multiply.by (about 4 MB) into `app/src/main/assets/site/`. The built pages are not in
   the repo, so this step is needed; run it again to pick up new games.
3. Build, either way:
   - **Android Studio:** open the `android` folder, then Run (to a phone over USB, or an emulator).
   - **Command line:** tell Gradle where the SDK is (the `ANDROID_HOME` environment variable, or
     a file `local.properties` with the line `sdk.dir=/path/to/Android/sdk`), then
     `./gradlew assembleDebug` (Windows: `gradlew.bat assembleDebug`). The first build downloads
     Gradle and the libraries, a few minutes. The app is
     `app/build/outputs/apk/debug/app-debug.apk`.
4. Install it: `adb install app/build/outputs/apk/debug/app-debug.apk`, or copy the file to the
   phone and open it there (Android asks once to allow installs from that app).

A debug build is signed with your own computer's key, so it can't be installed over the Play
Store version: uninstall that first. To publish **your own version**, give it its own package
name (`applicationId` in `app/build.gradle.kts`; `by.multiply.app` is taken) and app name
(`app/src/main/res/values/strings.xml`), sign it with your own key, and keep the MIT license's
copyright notice.

## Free, and no monetization needed

The app is free, open source and build-it-yourself, like the site: no ads in the app, no in-app
purchases, no subscriptions, no paid versions (for schools or anyone). Publishing costs almost
nothing, so the app needs no income:

- **Google Play:** the developer account is $25 once (already paid: organization account). Play
  charges nothing to publish or update an app, and nothing per download.
- **Hosting:** none; the games ship inside the app, which works without the website.
- **Building:** the `android-build` VM, about $5 a month for its disk while stopped, plus about
  $0.13 an hour during a build. Zero if the VM is deleted between releases (a new one sets itself
  up in about 3 minutes) or if builds move to GitHub Actions (free for a public repo).

## The project (`android/`)

- `settings.gradle.kts`, `build.gradle.kts`, `gradle.properties`, `app/build.gradle.kts`: AGP
  8.13, Kotlin 2.2, compileSdk and targetSdk 36, minSdk 24, AndroidX `activity` and `webkit` only.
  The Gradle wrapper (`gradlew`, `gradlew.bat`, `gradle/wrapper/`) pins Gradle 8.14.3 and
  downloads it on first use. `preBuild` stops with a clear message if the games haven't been
  gathered. Release signing reads `upload-key.properties` when it is there (see "Release build"
  below; without it a release build is unsigned). Launcher icon: an adaptive icon for Android 8+
  (`res/mipmap-anydpi-v26/ic_launcher.xml`: the page color behind
  `res/drawable/ic_launcher_foreground.xml`, the "2x2" of `icon.svg` as a vector, scaled to fit
  the 66 dp circle every launcher shape keeps; also the monochrome layer for Android 13's themed
  icons), and `res/mipmap-*/ic_launcher.png` (48 to 192 px, rendered from `icon.svg`) for older
  phones.
- `app/src/main/java/by/multiply/app/`: `MainActivity.kt` (the WebView, address rules, share
  bridge, back button, edge-to-edge insets), `SiteFiles.kt` (serves the bundled files and the
  in-app 404 page), `ParentalGate.kt`.
- `gather-assets.py [--web] [OUT]`: copies the live pages into the app (default OUT
  `app/src/main/assets/site/`, git-ignored). On the multiply.by server it reads the web folder;
  anywhere else, or with `--web`, it downloads from https://multiply.by (both give the same files).
  It starts at / and /games/ and follows every link to a file that exists on the site, so a new game linked from the front
  page or /games/ is bundled with no list to edit. Never bundled: /about, /build-it/ (its page and
  prompt.txt; its screenshots are, for /games/), /gamify, /sw.js. It writes `files.txt`, the list
  the app serves from, and prints links to addresses that are not on the site.
- `build-app [debug]` (the site owner's route): stages the project in a temp folder (the
  gathered pages are never written into the web folder), starts `android-build` if stopped,
  builds over IAP SSH with `./gradlew`, copies the APK to `~/multiply-android/` (outside the web folder), and stops
  the VM again if it started it. `build-app release` builds what Play takes (next section).

## How the app works

- One Activity with a full-screen WebView; no Capacitor or framework. Kotlin, Gradle, AndroidX
  `activity` and `webkit`.
- **Same addresses inside the app.** `shouldInterceptRequest` answers every `https://multiply.by/...`
  request from the app's assets (`assets/site/`). We own the domain, so using it here is fine.
  Pages load unchanged: absolute links work (the front page strip links to
  `https://multiply.by/train/` etc.), localStorage per origin works as on the website (saved
  progress, `multiply_last_game`), and SOURCE's relative `prompt/` link (or `prompt.txt`, on pages built earlier) opens the bundled copy.
  No generated page is edited (the site's rule: never edit a generated page by hand).
- **Folder addresses:** `SiteFiles` (not `WebViewAssetLoader`, whose `AssetsPathHandler` serves
  exact file paths only) adds `index.html` to a path ending in `/` and sets the MIME type from the
  extension. A link to `/train` (no slash) is reloaded as `/train/`, so relative links resolve.
- Each address, decided in `shouldOverrideUrlLoading` / `shouldInterceptRequest`:
  - a bundled page or file: served from the app;
  - a page that isn't bundled (About, Build It, /gamify/, another site, mailto:, ...): the parental
    gate, then the phone's browser (`Intent.ACTION_VIEW`);
  - a file that isn't bundled, or any request to another host: the in-app 404 response (the pages
    are self-contained, so nothing is fetched from the network).
- **Service worker:** `/sw.js` is not bundled, so it gets the 404. `pwa.js` catches a failed
  registration (`startOffline()` ends with `.catch(function () {})`), and it registers only when the
  page looks installed (`isInstalled()`) or a service worker already exists, which a fresh WebView
  probably never does. Still check the console on a phone (Chrome's `chrome://inspect`; debug builds
  allow it): Chromium can log a failed request even when the script catches it, and the play tests
  treat console errors as failures. The install prompt in `pwa.js` does nothing in a WebView.
- **Share:** WebView has no `navigator.share`, so the app adds one before each page's scripts run
  (`addDocumentStartJavaScript`, only on https://multiply.by) that posts the text to the app
  (`addWebMessageListener`, object `MultiplyApp`). The app asks the parental gate, then opens
  Android's share sheet with the text. The games then take their phone path (layout.txt: SHARE THE
  SITE), and their desktop share menu and copy-link never appear. On an old WebView without these
  features, the games fall back to copying the link.
  - Found on 2026-11-20 (a site bug, not the app's): four games share links that 404 on the
    website and in the app: Monster `https://multiply.by/munchy/`, Planes `/flight/`, Great Wall
    `/greatwall/`, Block Craft `/blockcraft/` (each game's `shareText()`).
- WebView settings: JavaScript on, DOM storage on, file and content access off, no extra windows
  (`target="_blank"` opens in the same view). `mediaPlaybackRequiresUserGesture` is left on (the
  games start audio after a tap); check the Web Audio sounds on a real phone.
- Portrait (as the web manifest), edge to edge (required from Android 15) with the page padded
  clear of the system bars on a #fafaf9 background. Back: WebView history back, then the system's
  back (leaves the app). Rotation and dark-mode changes don't restart the Activity, so a game in
  progress survives them.

## What goes in the app

The pages and sizes on 2026-11-20 (each game is one self-contained HTML file):

| Page | Bytes |
|---|---|
| / (front page: base game + strip) | 69,825 |
| /base/ | 63,991 |
| /games/ | 17,915 |
| /monster/ | 83,358 |
| /train/ | 177,703 |
| /dino/ | 78,525 |
| /robot/ | 108,750 |
| /plane/ | 156,447 |
| /space/ | 385,380 |
| /chinese/ | 105,870 |
| /blocks/ | 120,701 |
| /evolution/ | 341,414 |
| /divide/ | 59,688 |

Plus each page's prompt (SOURCE: its `prompt/` page, or `prompt.txt` on pages built earlier), the strip
thumbnails (`/thumbnails/*.png`), the /games/ screenshots (`/build-it/*.png`; together about
1.8 MB with the thumbnails), the icons and the manifest. About 4 MB in all: small for an app.

`gather-assets.py` (above) gathers the current live files at every build, so a release is: build,
upload. A new or rebuilt game reaches the app only with a new release
(the website updates instantly; the app does not).

## Build machine (Google Cloud VM `android-build`)

Created 2026-11-20 09:18 UTC by Claude Code (gcloud from the web server), for building the app.
**Keep it stopped when not building.**

### The VM

| Setting | Value |
|---|---|
| Name | `android-build` (instance id 7764053744562318987) |
| Project | `functional-ai` (gcloud account: the site owner's Google account) |
| Zone / region | `us-east1-b` / `us-east1` (the project's default) |
| Machine type | e2-standard-4: 4 vCPU, 16 GB RAM, standard (not preemptible / spot) |
| Boot disk | `android-build`, 50 GB pd-balanced, deleted with the VM (auto-delete on) |
| Image | Ubuntu 24.04 LTS, `ubuntu-2404-noble-amd64-v20261105` (family `ubuntu-2404-lts-amd64`, project `ubuntu-os-cloud`) |
| Network | `default` network and subnetwork; internal IP 10.142.15.228; an **ephemeral** external IP (a new one at every start; not needed: SSH goes through IAP) |
| Service account | the project's default Compute Engine account, default scopes (Storage read-only, Logging, Monitoring, ...) |
| Shielded VM | vTPM and integrity monitoring on, Secure Boot off (the defaults) |
| Maintenance | live migrate, automatic restart |
| Labels / network tags | none |
| Startup script | in the instance metadata, key `startup-script` (below) |

It was created with:

```
gcloud compute instances create android-build --zone=us-east1-b --machine-type=e2-standard-4 \
  --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB --boot-disk-type=pd-balanced \
  --metadata-from-file=startup-script=startup.sh
```

### Cost

About $0.13 an hour while running (e2-standard-4 in us-east1). Stopped (TERMINATED), only the
50 GB disk is billed, about $5 a month. Deleting the VM deletes its disk too.

### What is installed (checked 2026-11-20)

- OpenJDK 17.0.21 (`openjdk-17-jdk-headless`), plus `unzip`, `zip`, `git`, `curl`.
- Android SDK in `/opt/android-sdk`: cmdline-tools (`cmdline-tools/latest`, from
  `commandlinetools-linux-11076708_latest.zip`), platform-tools 37.0.3, platforms android-35 and
  android-36, build-tools 35.0.0 and 36.0.0. SDK licenses accepted.
- Gradle 8.14.3 in `/opt/gradle-8.14.3` (link `/opt/gradle`).
- Environment for every login shell, `/etc/profile.d/android.sh`: `ANDROID_HOME` and
  `ANDROID_SDK_ROOT` = `/opt/android-sdk`; PATH adds the cmdline-tools, platform-tools and Gradle
  bin folders.
- Disk: 4.2 GB used of 48 GB.
- Setup log: `/var/log/android-setup.log` (ends with a SUMMARY block); marker file
  `/opt/android-setup.done`.

### History

1. Created; the startup script ran once (about 3 minutes), wrote its log and the marker, and
   powered the VM off.
2. Started again only to read the log (SSH without IAP hung; with `--tunnel-through-iap` it
   worked), then stopped. Status now: TERMINATED.

### Using it

```
gcloud compute instances start android-build --zone=us-east1-b
gcloud compute ssh android-build --zone=us-east1-b --tunnel-through-iap
gcloud compute instances stop android-build --zone=us-east1-b
gcloud compute instances describe android-build --zone=us-east1-b --format='value(status)'
```

- **SSH needs `--tunnel-through-iap`**; without it the connection hangs.
- Copy files with `gcloud compute scp --tunnel-through-iap ...` (e.g. the built `.aab` back).
- On a start, the startup script runs again but exits at once (the marker file exists), so the
  VM stays up.
- To delete it (VM and disk): `gcloud compute instances delete android-build --zone=us-east1-b`.

### The startup script (as installed in the metadata)

```bash
#!/bin/bash
# One-time setup of an Android build machine; powers the VM off when done.
# Later boots skip it (the marker file exists), so a started VM stays up for work.
MARK=/opt/android-setup.done
LOG=/var/log/android-setup.log
[ -f "$MARK" ] && exit 0
exec >>"$LOG" 2>&1
set -x
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y openjdk-17-jdk-headless unzip zip git curl

SDK=/opt/android-sdk
mkdir -p $SDK/cmdline-tools
cd /tmp
curl -fsSLo tools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -q tools.zip -d $SDK/cmdline-tools && mv $SDK/cmdline-tools/cmdline-tools $SDK/cmdline-tools/latest
SM=$SDK/cmdline-tools/latest/bin/sdkmanager
yes | $SM --sdk_root=$SDK --licenses >/dev/null
for p in "platform-tools" "platforms;android-35" "build-tools;35.0.0" "platforms;android-36" "build-tools;36.0.0"; do
  $SM --sdk_root=$SDK --install "$p" || echo "SKIPPED: $p"
done
yes | $SM --sdk_root=$SDK --update || true

GV=8.14.3
curl -fsSLo gradle.zip https://services.gradle.org/distributions/gradle-$GV-bin.zip && unzip -q gradle.zip -d /opt && ln -sfn /opt/gradle-$GV /opt/gradle

cat > /etc/profile.d/android.sh <<'P'
export ANDROID_HOME=/opt/android-sdk
export ANDROID_SDK_ROOT=/opt/android-sdk
export PATH=$PATH:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:/opt/gradle/bin
P
chmod -R a+rX $SDK

set +x
echo "===== SUMMARY ====="
java -version 2>&1 | head -1
/opt/gradle/bin/gradle --version 2>/dev/null | grep '^Gradle'
$SM --sdk_root=$SDK --list_installed 2>/dev/null | grep -E 'platform|build-tools|cmdline'
df -h / | tail -1
echo "===== DONE ====="
touch "$MARK"
sync
poweroff
```

## Release build (what is uploaded to Play)

`android/build-app release` builds, on the VM, the **App Bundle** (`.aab`, the file Play takes)
and an **APK of the same build** (to install on a phone and check before uploading), both signed
with the **upload key**, into `~/multiply-android/` as `multiply-by-release-DATE.aab` and `.apk`.

- **The upload key** is in `~/.multiply-play/` on the server (`upload-key.jks` and
  `upload-key.properties` with its password), outside the web folder and the repo; the folder and
  files are readable by their owner only. The first release build made it, on the VM (RSA 4096,
  valid 10,000 days, alias `upload`), with a random password that was never printed. For a
  build, `build-app` copies the two files into the temporary build folder and deletes them from
  the VM afterwards. **Back up `~/.multiply-play/`** somewhere safe and private (e.g. a password
  manager): with Play App Signing, a lost upload key can be replaced through Play Console
  support, but that takes days.
- **Play App Signing:** accept it when creating the release. Google then signs what phones
  download with its own app signing key; ours only proves an upload comes from us.
- **Version:** `versionCode` (1, then +1 for every upload; Play refuses a number it has seen) and
  `versionName` ("1.0", what users see) in `app/build.gradle.kts`.
- **Building your own release** (from the public repo): make your own key with `keytool
  -genkeypair -keystore upload-key.jks -storetype PKCS12 -alias upload -keyalg RSA -keysize 4096
  -validity 10000`, put it and an `upload-key.properties` (`storeFile=upload-key.jks`,
  `storePassword=...`, `keyAlias=upload`, `keyPassword=...`, the same password twice) in the
  `android` folder (both git-ignored), then `./gradlew bundleRelease assembleRelease`; the files
  are in `app/build/outputs/bundle/release/` and `app/build/outputs/apk/release/`.
- **Check before uploading:** install the release APK on a phone (`adb install`; uninstall a
  debug build first, it has another key) and play a game through.

## Google Play requirements

- **Upload an Android App Bundle (`.aab`)**, not an APK; build an APK too, to install on a phone
  for testing.
- **Target SDK:** Play requires a recent target API level for new apps (35 at least; check the
  current rule when submitting). SDK 36 is installed.
- **Signing:** the upload key and Play App Signing (previous section).
- **Developer account:** $25 once. A new **personal** account must run a **closed test with at
  least 12 testers for 14 days** before publishing to everyone. An **organization** account
  (Functional AI Inc.) skips that but needs a D-U-N-S number.
- **Families policy** (an app for children): target-age declaration, content-rating
  questionnaire, data-safety form (the games collect nothing; progress stays on the phone), and a
  **privacy policy URL**: https://multiply.by/privacy/ (`PRIVACY.md`, which `make` renders with
  `md-html.py`, like this page). The answers to every Play Console form are in
  `android/assets/play-console.txt`.
- **App name:** "Multiply.by – Times Tables" in the store (the listing title, set in the Play
  Console). On the phone's home screen, under the icon, "Multiply.by" (`app_name` in
  `app/src/main/res/values/strings.xml`): a home screen shows only about 12 characters.
- **Store listing:** 512 x 512 icon, 1024 x 500 feature graphic, 2 to 8 phone screenshots, short
  and full descriptions, optionally a YouTube video: all in `android/assets/` (next section).

## Store listing files (`android/assets/`)

Everything the Play Console's store listing asks for, served at
https://multiply.by/android/assets/ so it can be looked at or downloaded from anywhere:

| File | What it is | Play's rule |
|---|---|---|
| `listing.txt` | App name, short and full description, category | 30, 80 and 4000 characters |
| `play-console.txt` | The answers to the Play Console's forms, page by page: app details, store settings, privacy policy, app access, ads, content rating, target audience (6-8 and 9-12: the Families policy), data safety ("no data collected"), release notes | |
| `icon-512.png` | The store icon, the site's `icon-512.png` (the "2x2" of `icon.svg`) | 512 x 512 PNG, square: Play rounds the corners |
| `feature-graphic.png` | Logo, name, one line and six game pictures (the front page's thumbnails) | 1024 x 500, no transparency |
| `phone/NN-PAGE.png` | Phone screenshots in store order: Monster, Robot, Train, Dinosaurs, Block Craft (each a few questions in), the /games/ chooser, Build It, About | 2 to 8, 9:16, 1080 x 1920 |
| `tablet-7/`, `tablet-10/` | Tablet screenshots, upright like the app: Monster, Train, Robot, /games/ | optional; 1200 x 1920 and 1600 x 2560 |
| `robot.mp4` | The Robot game played from the start to "You Won!" on a phone: the first 10 moves (7 right, 3 wrong) at 1.4x speed with the game's sounds and a mouse pointer, the rest at 12x, silent, then 3 s on "You Won!". About 28 s, 1080 x 1920, about 2 MB | Play takes a YouTube link only |

**How to make them.** `listing.txt` and `play-console.txt` are written by hand and kept in git;
the rest is generated
(git-ignored) by `android/store-assets.py` from the live site, so anyone can remake it:

1. Install Python 3 with Playwright and Pillow (`pip install playwright pillow`, then
   `playwright install chromium`) and ffmpeg (for the video).
2. From the `android` folder: `python3 store-assets.py`. About three minutes, most of it the
   video. `--only icon,feature,phone,tablet,video` makes some of them; `--site URL` reads another copy
   of the site.

The script plays the games the way `play-test.py` does: it reads the question, taps the right
answer (or, in the video, sometimes a wrong one) and waits for the next question. Screenshots
are taken at 360 x 640 with 3x pixels (a phone), in a fresh browser (no saved progress), and
saved without transparency. To change what is shown, edit the `PHONE` list (file name, page,
questions answered first), `TABLETS` and `TABLET_PAGES`, `VIDEO_PAGE`, `VIDEO_SLOW` (the first moves, True for a wrong
one), `VIDEO_FIRST` (their speed), `VIDEO_FAST`, `VIDEO_END` or `FEATURE_GAMES` at the top of the script.
The video is recorded with Chrome's own screencast (full phone resolution) and put together by
ffmpeg. Headless Chrome draws no mouse pointer and plays no sound, so the script adds both inside
the page: an arrow that follows the mouse (glided to each answer, with a ripple on the click), and
a recorder on the game's Web Audio, whose sound is sped up with the picture (at the same pitch)
and goes under the first part.

**Before launch:**
- Remake the files after a game shown in them is rebuilt.
- Build It and About are on the website only: in the app their links open the browser after the
  parental gate. Play wants screenshots of what the app shows, so drop those two (or keep them
  last) if the review objects.
- Upload `robot.mp4` to YouTube (public or unlisted; ads off) and paste the link into the
  listing.

## Links to the app on the website (written 2026-11-20, live since 2026-11-21)

The specs already link to the Play listing, https://play.google.com/store/apps/details?id=by.multiply.app,
which is a 404 until the app is published:

- `about/about.txt`, GET THE APP: a line, Google's official "Get it on Google Play" badge
  (`/google-play.png`, 188 x 56; Google's `en_badge_web_generic.png` with only its transparent
  margin trimmed, tracked in git) and the trademark line Google asks for.
- `footer.txt`, LEFT column: a "Get the Android app" link. The footer is on About, Build It and
  /games/; /games/ is bundled in the app, where the link goes through the parental gate like the
  footer's other links.

**Live before launch, on purpose**: About, Build It and /games/ were rebuilt on 2026-11-21 and
show the link, a 404 until the app is published. That is fine while the site has no visitors
from outside. On launch day: check the link opens the listing, then build the app (its bundled
/games/ already has the link).

## Fixes to the site before packaging

- The web manifest's "maskable" icon is the same image as the normal one; Android crops maskable
  icons to a circle or squircle, so its edges may be cut off (the website's installed app only;
  the Android app has its own adaptive icon, above).

## Not chosen, and why

- **TWA (Bubblewrap or PWABuilder):** the easiest route (a signed `.aab` in minutes from
  pwabuilder.com, plus `/.well-known/assetlinks.json` on the site), but it shows the whole
  website, including the pages that will carry ads, and needs the network on first open.
- **Building on this web server:** not enough memory, no Java.

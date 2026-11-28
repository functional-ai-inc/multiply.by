# multiply.by as an Android app (Google Play)

Notes for packaging the multiply.by games as an Android app.

**What the build needs:** Java 17 and the Android SDK, installed in the user's own folders if
missing.

**No root or administrator access:** the install neither needs nor uses it. Everything goes in
the user's own folders (below).

**Optional, a separate user:** to keep all of it (about 2 GB) out of your own home folder, run
the build as a new user made just for it, e.g. `multiply-build`, and log in or open a terminal as
that user. Everything then goes in that user's home folder, and deleting the user removes it all.

**Linux, Mac or Windows.** The machine needs about 8 GB of RAM and about 2 GB
of free disk.

| | Linux | Mac | Windows |
|---|---|---|---|
| JDK folder (`JAVA_HOME`) | `~/.local/jdk-17` | `~/.local/jdk-17/Contents/Home` | `%USERPROFILE%\.jdks\jdk-17` |
| Android SDK (`ANDROID_HOME`) | `~/Android/Sdk` | `~/Library/Android/sdk` | `%LOCALAPPDATA%\Android\Sdk` |
| Gradle and libraries (first build) | `~/.gradle` | `~/.gradle` | `%USERPROFILE%\.gradle` |
| Build command | `./gradlew assembleDebug` | `./gradlew assembleDebug` | `gradlew.bat assembleDebug` |
| Python | `python3` | `python3` | `py` or `python` |

If a step fails, say which step and show the error.

## Build the app yourself

Anyone can build the app from the public repo, on Linux, Mac or Windows. You need:

- **Java 17** (a JDK) and the **Android SDK** with Android 16 (API 36). Android Studio installs
  both; without it, install a JDK 17 and Google's command-line tools, then
  `sdkmanager "platforms;android-36" "build-tools;36.0.0" "platform-tools"`.
  **Accept the SDK licenses** before the first build: `yes | sdkmanager --licenses` (Windows:
  run `sdkmanager.bat --licenses` and answer `y` to each). An SDK with older tools refuses to
  build until they are accepted ("Failed to install the following SDK components ... licences
  have not been accepted"); Android Studio asks the same question in its setup. The newest
  command-line tools no longer ask (sdkmanager says "The --licenses option is no longer needed").
- **Python 3**. If it is missing, install it in the user's folders with uv
  (https://docs.astral.sh/uv/: its installer puts `uv` in the user's folders, then
  `uv python install 3.12`).
- **git** (optional): without it, download the code as an archive (step 1).

An AI agent installs whatever is missing.

Then:

1. Get the code:
   `git clone https://github.com/functional-ai-inc/multiply.by.git` and `cd multiply.by/android`;
   without git, `curl -L https://github.com/functional-ai-inc/multiply.by/archive/refs/heads/main.tar.gz | tar xz`
   and `cd multiply.by-main/android`.
2. Get the games: `python3 gather-assets.py`. It downloads the current pages from
   https://multiply.by (about 4 MB) into `app/src/main/assets/site/`. The built pages are not in
   the repo, so this step is needed; run it again to pick up new games.
3. Build, either way:
   - **Android Studio:** open the `android` folder, then Build > Build App Bundle(s) / APK(s) >
     Build APK(s).
   - **Command line:** tell Gradle where the SDK is (the `ANDROID_HOME` environment variable, or
     a file `local.properties` with the line `sdk.dir=/path/to/Android/sdk`), then
     `./gradlew assembleDebug` (Windows: `gradlew.bat assembleDebug`). The first build downloads
     Gradle and the libraries, a few minutes. The app is
     `app/build/outputs/apk/debug/app-debug.apk`.
4. When the build is done, print the APK's full path (e.g.
   `/home/you/multiply.by/android/app/build/outputs/apk/debug/app-debug.apk`), so the person who
   asked for it can find it. An AI agent building it ends its answer with that path.

A debug build is signed with your own computer's key, so it can't be installed over the Play
Store version: uninstall that first. To publish **your own version**, give it its own package
name (`applicationId` in `app/build.gradle.kts`; `multiply.by.app` is taken) and app name
(`app/src/main/res/values/strings.xml`), sign it with your own key, and keep the MIT license's
copyright notice.

## Free, and no monetization needed

The app is free, open source and build-it-yourself, like the site: no ads in the app, no in-app
purchases, no subscriptions, no paid versions (for schools or anyone). Publishing costs almost
nothing, so the app needs no income:

- **Google Play:** the developer account is $25 once (already paid: organization account). Play
  charges nothing to publish or update an app, and nothing per download.
- **Hosting:** none; the games ship inside the app, which works without the website.
- **Building:** free, on your own computer.

## The project (`android/`)

- `settings.gradle.kts`, `build.gradle.kts`, `gradle.properties`, `app/build.gradle.kts`: AGP
  8.13, Kotlin 2.2, compileSdk and targetSdk 36, minSdk 24, AndroidX `activity` and `webkit` only.
  The Gradle wrapper (`gradlew`, `gradlew.bat`, `gradle/wrapper/`) pins Gradle 8.14.3 and
  downloads it on first use. `preBuild` stops with a clear message if the games haven't been
  gathered. Release signing reads `upload-key.properties` from the `android` folder or from
  `~/.multiply-play/` (see "Release build" below); without it a release build stops with a clear
  message, so it never makes an unsigned bundle. Launcher icon (since 2026-11-27; the site's tab
  icon keeps its "2x2", the website's installable app uses it with a "PWA" badge): an
  orange-to-crimson x with a soft shadow on a peach gradient, all made by `make-icons.py` from the design at its top, which also writes `android/icon.svg` (the whole
  icon, the store icon's source). An adaptive icon for Android 8+
  (`res/mipmap-anydpi-v26/ic_launcher.xml`: `res/drawable/ic_launcher_background.xml`, the
  gradient; `res/mipmap-*/ic_launcher_foreground.png`, the x with its shadow, sized so it fills
  the same share of the 72 dp the launcher shows as in `icon.svg`; and
  `res/drawable/ic_launcher_monochrome.xml`, the x alone for Android 13's themed icons), and
  `res/mipmap-*/ic_launcher.png` (48 to 192 px, the whole icon) for older phones.
- `app/src/main/java/by/multiply/app/`: `MainActivity.kt` (the WebView, address rules, share
  bridge, back button, edge-to-edge insets), `SiteFiles.kt` (serves the bundled files and the
  in-app 404 page), `ParentalGate.kt`.
- `gather-assets.py [--web] [OUT]`: copies the live pages into the app (default OUT
  `app/src/main/assets/site/`, git-ignored). It downloads the pages from https://multiply.by
  (run inside a copy of the site's folder with its built pages, it reads them there instead;
  `--web` always downloads; both give the same files).
  It starts at / and /games/ and follows every link to a file that exists on the site, so a new
  game linked from the front page or /games/ is bundled with no list to edit. That includes About
  and Build It (with every game's prompt.txt and build.txt, which Build It reads), each page's
  SOURCE prompt page, the selector, grid and orders files, both privacy policies, /gamify/ (the
  build guide every prompt links to) and /android/ (these notes, linked from Build It). Never
  bundled (`EXCLUDE`): /sw.js, /faq. Pages no bundled page links to are left
  out too: /match/, the model-comparison copies (/trains/carbon/, ...), robots.txt and the sitemap.
  It writes `files.txt`, the list the app serves from, and prints links to addresses that are not
  on the site.

## How the app works

- One Activity with a full-screen WebView; no Capacitor or framework. Kotlin, Gradle, AndroidX
  `activity` and `webkit`.
- **Same addresses inside the app.** `shouldInterceptRequest` answers every `https://multiply.by/...`
  request from the app's assets (`assets/site/`). We own the domain, so using it here is fine.
  Pages load unchanged: absolute links work (the front page strip links to
  `https://multiply.by/trains/` etc.), localStorage per origin works as on the website (saved
  progress, `multiply_last_game`), and SOURCE's relative `prompt/` link (or `prompt.txt`, on pages built earlier) opens the bundled copy.
  No generated page is edited (the site's rule: never edit a generated page by hand).
- **Folder addresses:** `SiteFiles` (not `WebViewAssetLoader`, whose `AssetsPathHandler` serves
  exact file paths only) adds `index.html` to a path ending in `/` and sets the MIME type from the
  extension. A link to `/trains` (no slash) is reloaded as `/trains/`, so relative links resolve.
- Each address, decided in `shouldOverrideUrlLoading` / `shouldInterceptRequest`:
  - a bundled page or file: served from the app;
  - a page that isn't bundled (another site such as the AI chat sites linked from
    Build It and the prompts, GitHub, mailto:, ...): the parental gate, then the
    phone's browser (`Intent.ACTION_VIEW`);
  - a file that isn't bundled, or any request to another host: the in-app 404 response (the pages
    are self-contained, so nothing is fetched from the network).
- **Service worker:** none. The website's installable web app (Build It's "install the web
  app") has `/sw.js`, which is not bundled and would get the 404; Build It's `pwa.js` sees
  `MultiplyByApp` in the user agent, removes that line and never registers it.
- **Share:** WebView has no `navigator.share`, so the app adds one before each page's scripts run
  (`addDocumentStartJavaScript`, only on https://multiply.by) that posts the text to the app
  (`addWebMessageListener`, object `MultiplyApp`). The app asks the parental gate, then opens
  Android's share sheet with the text. The games then take their phone path (layout.txt: SHARE THE
  SITE), and their desktop share menu and copy-link never appear. On an old WebView without these
  features, the games fall back to copying the link.
- **No ads anywhere in the app**, on every page, the bundled About and Build It included. The
  website may show ads on its non-game pages (`PRIVACY-WEBSITE.md`); the app shows the same
  pages without them, in two layers:
  1. **The app identifies itself.** `MainActivity.kt` adds `MultiplyByApp/VERSION` (e.g.
     `MultiplyByApp/1.0`) to the WebView's user agent. Every page that carries ads on the
     website says in its spec (`layout.txt`, `build-it/page.txt`, `about/about.txt`, wherever the
     ads are added): "If `navigator.userAgent` contains `MultiplyByApp`, create no ad slots and
     load no ad script." So in the app the page looks exactly as it would with no ads at all: no
     empty boxes, no ad requests. When ads are added to the website, put that sentence in the
     spec, rebuild the page, and check it in the app (or in a desktop browser with its user agent
     set to include `MultiplyByApp`) before the next release.
  2. **Safety net:** every request to another host gets the in-app 404 (above), so even a page
     that forgot the check can't load ad code; its ad slot would at worst stay empty.
  The Play Console's "Contains ads" answer is therefore No (`android/assets/play-console.txt`).
  The user agent change needs an app release: a phone keeps its installed version's behavior
  until it updates.
- **No division in the app:** division was removed from the site on 2026-11-23, but games built
  before then still end with "Next: learn division at divide.by" (`#division-line`, a link to
  https://multiply.by/divide/), and so did About. The app adds a style before each page is drawn
  (`HIDE_DIVISION_SCRIPT`, a document-start script like the share one) that hides
  `#division-line` and any link to /divide (with its list item), and `shouldOverrideUrlLoading`
  sends any /divide address to /games/ inside the app (as nginx does on the website), never to the
  parental gate. Rebuilt games lose the line anyway (game.txt no longer has it); the four built
  in the ChatGPT web app (Evolution, Space, Train, Trains) keep it until the user rebuilds them.
  Needs an app release.
- **SOURCE in the app:** a game's SOURCE is the relative link `prompt/`, so it opens the bundled
  prompt page (the game's prompt.txt in a box with a copy button), inside the app with no gate. The
  copy button uses `navigator.clipboard.writeText` with a `select()` fallback.
  Links inside a prompt to the AI chat sites leave the app after the gate; links to bundled pages
  (https://multiply.by/gamify, /dots/prompt/, /selector/prompt/) stay inside.
- WebView settings: JavaScript on, DOM storage on, file and content access off, no extra windows
  (`target="_blank"` opens in the same view). `mediaPlaybackRequiresUserGesture` is left on (the
  games start audio after a tap).
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
| /trains/ | 177,703 |
| /dino/ | 78,525 |
| /robot/ | 108,750 |
| /planes/ | 156,447 |
| /space/ | 385,380 |
| /chinese/ | 105,870 |
| /blocks/ | 120,701 |
| /evolution/ | 341,414 |

Plus each page's prompt (SOURCE: its `prompt/` page, or `prompt.txt` on pages built earlier), the strip
thumbnails (`/thumbnails/*.png`), the /games/ screenshots (`/build-it/*.png`; together about
1.8 MB with the thumbnails), the icons and the manifest. About 4 MB in all: small for an app.

`gather-assets.py` (above) gathers the current live files at every build, so a release is: build,
upload. A new or rebuilt game reaches the app only with a new release
(the website updates instantly; the app does not).

## Release build (what is uploaded to Play)

From the `android` folder, after `python3 gather-assets.py`: `./gradlew bundleRelease
assembleRelease` builds the **App Bundle** (`.aab`, the file Play takes, in
`app/build/outputs/bundle/release/`) and an **APK of the same build** (in
`app/build/outputs/apk/release/`), both signed with the **upload key**.

- **The upload key:** `upload-key.jks` and `upload-key.properties` (`storeFile=upload-key.jks`,
  `storePassword=...`, `keyAlias=upload`, `keyPassword=...`). The build reads them IN PLACE from
  `~/.multiply-play/` (a path in `storeFile` is relative to that folder), or from the `android`
  folder if they are there (both git-ignored); nothing is copied before a build, so an AI agent
  never handles the key. Without them a release build stops. The site's own key (RSA 4096, valid
  10,000 days, alias `upload`) is in `~/.multiply-play/` on the web server and on the owner's
  desktop, readable by its owner only (`chmod 700` the folder, `600` the files). The owner puts
  it on a new desktop once, by hand, from their own terminal:
  `gcloud compute scp --zone=us-east1-b --tunnel-through-iap --recurse 'jlr@openlang-staging:~/.multiply-play' ~/`
  **Back it up** somewhere safe and private (e.g. a password manager): with Play App
  Signing, a lost upload key can be replaced through Play Console support, but that takes days.
- **Play App Signing:** accept it when creating the release. Google then signs what phones
  download with its own app signing key; ours only proves an upload comes from us.
- **Version:** `versionCode` (+1 for every release build; Play refuses a number it has seen, and
  skipped numbers are fine) and `versionName` ("1.0", what users see) in `app/build.gradle.kts`.
- **Building your own release** (from the public repo): make your own key with `keytool
  -genkeypair -keystore upload-key.jks -storetype PKCS12 -alias upload -keyalg RSA -keysize 4096
  -validity 10000` and its `upload-key.properties` (the same password twice), then build as above.

## Play release, step by step (the site owner's desktop)

What an AI agent does when the site owner asks it for "the Play Store release and the store
assets using https://multiply.by/android". It runs on the owner's desktop (the build needs about
8 GB of RAM; the web server is too small), UNATTENDED: ask nothing, decide by these steps, and
report at the end. Install whatever is missing in the user's folders, no root (the table at the
top).

1. **Code and games:** clone https://github.com/functional-ai-inc/multiply.by (or `git pull` an
   existing clone), then in the `android` folder `python3 gather-assets.py`: the current live
   games, About, Build It and their pictures.
2. **The upload key:** check that `~/.multiply-play/upload-key.properties` and
   `upload-key.jks` exist (`ls`; never open, print or copy them). If they don't, stop and tell
   the owner the one command under "Release build" that puts them there.
3. **Version:** raise `versionCode` in `app/build.gradle.kts` by 1 (leave `versionName` as it
   is unless the owner's request names a new one). Then `./gradlew bundleRelease assembleRelease`.
   It signs with the key in place; with no key it stops instead of making an unsigned bundle.
4. **Check the signature:** `jarsigner -verify` on the `.aab` says "jar verified"
   (`keytool -printcert -jarfile` on it shows the certificate); otherwise stop and report.
5. **Store assets:** `python3 store-assets.py` (all of them: icon, feature graphic, phone and
   tablet screenshots, video; about three minutes). Look at a few of the pictures: a game caught
   mid-animation or a blank picture is remade (`--only phone`, for example).
6. **Commit the version:** commit and push `app/build.gradle.kts` alone (message "Android:
   versionCode N"), so the repo always holds the last number built.

End with the full paths of the `.aab` (what the owner uploads to Play), the release `.apk` and the
`android/assets/` folder, and say which step, if any, was skipped or failed.

## Google Play requirements

- **Upload an Android App Bundle (`.aab`)**, not an APK.
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
| `icon-512.png` | The store icon: the app's `android/icon.svg` (`make-icons.py`), rendered at 512 x 512 | 512 x 512 PNG, square: Play rounds the corners |
| `feature-graphic.png` | The app icon, name, one line and six game pictures (the front page's thumbnails) | 1024 x 500, no transparency |
| `phone/NN-PAGE.png` | Phone screenshots in store order, About first (parents choose the app, and its lists persuade them most): 1. the card from "About Multiply.by" with its three lists (the card ends there; its link drawn as plain text); 2. "Make your own game" and "Learned everywhere" (the card ends there); 3. Build It (from "Build it yourself", no title band or menu, drawn at a 540 px wide page so the first game's whole prompt fits); 4. the rest of the card: "How the site and the app were built", Portability and Scalability (the site info and footer left out); 5. the /games/ chooser | 2 to 8, 9:16, 1080 x 1920 |
| `tablet-7/`, `tablet-10/` | Tablet screenshots, upright like the app: the same five as the phone's (`TABLET_PAGES = PHONE`), at tablet size; About's pages are too short to scroll on a tablet, so its pictures start at the card and are shorter than 9:16 | optional; 1200 x 1920 and 1600 x 2560 |
| `multiply.mp4` | The Robot game played from the start to "You Won!" on a phone: the first 10 moves (7 right, 3 wrong) at 1.4x speed with the game's sounds and a mouse pointer, the rest at 12x, silent, then 3 s on "You Won!". About 28 s, 1080 x 1920, about 2 MB | Play takes a YouTube link only |

**How to make them.** `listing.txt` and `play-console.txt` are written by hand and kept in git;
the rest is generated
(git-ignored) by `android/store-assets.py` from the live site, so anyone can remake it:

1. Install Python 3 with Playwright and Pillow (`pip install playwright pillow`, then
   `playwright install chromium`) and ffmpeg (for the video).
2. From the `android` folder: `python3 store-assets.py`. About three minutes, most of it the
   video. `--only icon,feature,phone,tablet,video` makes some of them; `--site URL` reads another copy
   of the site.

The script plays the games the way `play-test.py` does: it reads the question, taps the right
answer (or, in the video, sometimes a wrong one) and waits for the next question. Phone screenshots
are taken at 405 x 720 with 8/3x pixels (a phone), in a fresh browser (no saved progress), and
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
- Build It and About are in the app (bundled since 2026-11-23), so their store screenshots show
  what the app shows.
- Upload `multiply.mp4` to YouTube (public or unlisted; ads off) and paste the link into the
  listing.

## Links to the app on the website (written 2026-11-20, live since 2026-11-21)

The specs already link to the Play listing, https://play.google.com/store/apps/details?id=multiply.by.app,
which is a 404 until the app is published:

- `about/about.txt`, GET THE APP: a line, Google's official "Get it on Google Play" badge
  (`/google-play.png`, 188 x 56; Google's `en_badge_web_generic.png` with only its transparent
  margin trimmed, tracked in git) and the trademark line Google asks for.
- `footer.txt`, LEFT column: the same official badge, smaller (161 x 48), and the trademark
  line. The footer is on About, Build It and /games/; /games/ is bundled in the app, where the link goes through the parental gate like the
  footer's other links.

**Live before launch, on purpose**: About, Build It and /games/ were rebuilt on 2026-11-21 and
show the link, a 404 until the app is published. That is fine while the site has no visitors
from outside. On launch day: check the link opens the listing, then build the app (its bundled
/games/ already has the link).

## Not chosen, and why

- **TWA (Bubblewrap or PWABuilder):** the easiest route (a signed `.aab` in minutes from
  pwabuilder.com, plus `/.well-known/assetlinks.json` on the site), but it shows the whole
  website, including the pages that will carry ads, and needs the network on first open.

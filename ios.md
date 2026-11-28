# multiply.by as an iPhone and iPad app (App Store)

Notes for building the multiply.by games as an iOS app on GitHub's macOS runners, with no Mac of
our own. **Status (2026-11-25): planned, not built yet.** Nothing below exists in the repo until
it is made; `ANDROID.md` describes the Android app, which this one copies wherever it can.

## Why GitHub Actions

An iOS app can only be built with Xcode, which runs only on macOS, which Apple licenses only on
Apple hardware. GitHub's hosted macOS runners are real Macs with Xcode installed, and they are
**free for public repositories** (functional-ai-inc/multiply.by is public). A workflow in the
repo builds the app, signs it and uploads it to App Store Connect; testing is on a real iPhone
through TestFlight. No step needs a Mac in our hands.

Other ways, not chosen: Xcode Cloud (25 hours a month with the developer membership, but set up
from Xcode on a Mac), Codemagic or Bitrise (free tiers, another account to keep), a rented Mac
(AWS EC2 Mac, Scaleway, MacinCloud: about $1 an hour, at least 24 hours per Mac on AWS and
Scaleway). A rented Mac for a day stays useful as a fallback, to look at a problem in Xcode or
the simulator by hand.

## Costs

- **Apple Developer Program:** $99 a year, as Functional AI Inc. (an organization account needs
  the D-U-N-S number, as Google Play did). Apple charges nothing per app or download for a free
  app.
- **Builds:** free (public repo). For a private repo, macOS minutes would count ten times
  against the plan's allowance.
- The app is free with no ads and no purchases, like the Android app (`ANDROID.md`, "Free, and
  no monetization needed").

## The project (`ios/`, to be made)

Everything is plain text, so nobody has to open Xcode:

- `project.yml`: the project for **XcodeGen**, which writes `MultiplyBy.xcodeproj` (generated,
  git-ignored) on the runner. Bundle ID `by.multiply.app` (the same as Android; the stores are
  separate), display name "Multiply.by", iPhone and iPad, portrait, iOS 16 or later,
  `MARKETING_VERSION` (e.g. 1.0, what users see) set here, `CURRENT_PROJECT_VERSION` (the build
  number) set by the workflow, `ITSAppUsesNonExemptEncryption` NO (no export-compliance question
  at each upload).
- `Sources/`: Swift, no frameworks or packages: the app, a view controller with one full-screen
  `WKWebView`, the file server for the bundled pages, the parental gate.
- `Assets.xcassets/AppIcon`: one 1024 x 1024 PNG rendered from the site's `icon.svg` (iOS draws
  the rounded corners; no transparency allowed).
- `site/`: the bundled pages, filled on the runner by the Android script,
  `python3 android/gather-assets.py --web ios/site` (git-ignored). Same pages, same
  `files.txt`, nothing to maintain twice.
- `.github/workflows/ios.yml`: the workflow (below).

## How the app works (as on Android)

- **Same pages, unchanged.** Never edit a generated page. The app serves `site/` itself and keeps
  the pages' addresses as close to `https://multiply.by/...` as WebKit allows:
  - WebKit does not let an app answer `https` requests (`WKURLSchemeHandler` refuses the
    built-in schemes), so the pages are served from a custom scheme,
    `multiplyby://multiply.by/...`, with `index.html` added to a path ending in `/` and the MIME
    type from the extension, like `SiteFiles.kt`.
  - Links and pictures written as `https://multiply.by/...` in `href` and `src` attributes are
    turned into the custom scheme as each HTML file is served (in memory, never on disk);
    `decidePolicyFor` does the same for any navigation that still asks for
    `https://multiply.by/...`. Text inside a page (the prompt box SOURCE opens) is not touched,
    so a copied prompt keeps its real addresses. **To check on a phone first:** localStorage
    under the custom scheme (saved progress, `multiply_last_game`), and that no picture or page
    still loads from the web.
  - Any other address: the parental gate, then Safari. A request to another host gets nothing
    (a content rule list blocks it), so no page can load outside code.
- **No ads:** the web view's user agent gets `MultiplyByApp/VERSION`
  (`applicationNameForUserAgent`), so the website's rule in every spec with ads applies unchanged
  (`CLAUDE.md`, ADS).
- **Share:** a document-start script replaces `navigator.share` with a message to the app
  (`WKScriptMessageHandler`), which asks the parental gate and opens the iOS share sheet.
- **No division:** the same hiding script as `HIDE_DIVISION_SCRIPT`, and /divide addresses go to
  /games/.
- Service worker: none (the site no longer registers one; /sw.js is not bundled). Portrait, edge to
  edge with the page padded clear of the notch and home bar, back by swipe (web view history).

## The workflow (`.github/workflows/ios.yml`)

Two jobs on `macos-latest` (pin a version, e.g. `macos-15`, once it works; pick the Xcode with
`sudo xcode-select -s` if the default is not the one App Store Connect requires):

1. **Check** (every push to `ios/`, and pull requests, forks included; no secrets): gather the
   pages, `brew install xcodegen`, `xcodegen` in `ios/`, then build for the simulator with
   signing off (`xcodebuild build -scheme MultiplyBy -destination 'generic/platform=iOS
   Simulator' CODE_SIGNING_ALLOWED=NO`). Proves the app compiles; anyone can see it pass.
2. **Release** (started by hand, `workflow_dispatch`, on `main` only):
   - gather the pages and generate the project, as above;
   - write the App Store Connect API key from the secret to a file in `$RUNNER_TEMP`
     (`AuthKey_<id>.p8`), never in the repo or the log;
   - `xcodebuild archive` for `generic/platform=iOS` with `CURRENT_PROJECT_VERSION` set to
     `${{ github.run_number }}` (every upload needs a higher build number), automatic signing and
     `-allowProvisioningUpdates` with `-authenticationKeyPath`, `-authenticationKeyID` and
     `-authenticationKeyIssuerID`: Xcode then makes and uses the certificate and profile itself
     in Apple's cloud, so no certificate file is kept anywhere;
   - `xcodebuild -exportArchive` with an `ExportOptions.plist` (`method` app-store-connect,
     `destination` upload, the team ID): signs and uploads the build to App Store Connect;
   - keep the `.xcarchive` as a workflow artifact for a few days.

About 10 minutes a run. The build appears in App Store Connect, then TestFlight, after Apple's
processing (minutes to an hour).

**Secrets** (repo Settings, Secrets and variables, Actions; never in git): `ASC_KEY_ID`,
`ASC_ISSUER_ID`, `ASC_KEY_P8` (the key file's text). Variable (not secret): `APPLE_TEAM_ID`. The
key is made in App Store Connect, Users and Access, Integrations, with the **Admin** role (cloud
signing needs it); Apple lets you download it once, so keep a copy where the Android upload key's
backup is. GitHub never gives secrets to a workflow run from a fork's pull request, so a fork
can't use our key.

## Testing

- **On a phone:** install TestFlight from the App Store and accept the invitation. Internal
  testers (people in our App Store Connect team, up to 100) get each build at once; external
  testers (up to 10,000, by email or a public link) after a short beta review of the first build.
- Play a game through to "You Won!" with wrong answers, check share, SOURCE and its copy button,
  the sounds after the first tap, rotation and the parental gate, as for Android.
- The pages themselves can be tested in WebKit on Linux before any app build: Playwright's
  `webkit` browser (`play-test.py`'s checks, in Safari's engine instead of Chromium).

## App Store requirements

- **Kids category** (ages 6-8 and 9-11): no third-party ads or analytics (none), a parental
  gate before any link that leaves the app or any purchase (links and share; the gate already
  exists on Android), no data sent anywhere.
- **Privacy:** privacy policy URL https://multiply.by/privacy/ (`PRIVACY.md` names the Android
  app; it needs a line for the iOS app before submitting), App Privacy answers "Data Not
  Collected", age rating questionnaire (no objectionable content).
- **Guideline 4.2, minimum functionality:** Apple rejects apps that are a website in a frame.
  The case for this one: the games are bundled and work with no network, the app has no browser
  chrome, and it does not show the website. Say so in the review notes.
- **Store listing:** name "Multiply.by – Times Tables" (30 characters), subtitle, description,
  keywords, support URL, 1024 x 1024 icon (from the app), screenshots for the 6.9" iPhone
  (1320 x 2868) and, with iPad support, the 13" iPad (2064 x 2752). `android/store-assets.py`
  can make them with new sizes added, or the simulator on the runner
  (`xcrun simctl io booted screenshot`). The answers to App Store Connect's forms go in a file
  like `android/assets/play-console.txt`.

## Building your own

From a fork, the check job works with no account. To put your own version on an iPhone you need
your own Apple developer account ($99 a year; a free Apple ID works only from Xcode on a Mac and
the app stops after 7 days): change the bundle ID and app name in `project.yml`, add your own
key and team ID as your fork's secrets and variable, and run the release workflow. Keep the MIT
license's copyright notice.

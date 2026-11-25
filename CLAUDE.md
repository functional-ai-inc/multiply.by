# multiply.by

A times-tables game site, served live by nginx straight from this folder (https://multiply.by).
Every page is ONE self-contained HTML file built by an AI model from a plain-text spec. Never edit a
generated file (index.html, prompt.txt, pwa.js, sw.js, ...) by hand: change the spec and
rebuild. GitHub: functional-ai-inc/multiply.by (public).

## How a page is built
- Site map: `/` is the front page: a game (now Dots) with a strip of the other games under the
  answers (prompt `prompt.txt`); `/games/` is the picture chooser (spec `games/page.txt`, the strip's
  "More games" tile); `/base/` is the base game alone (spec
  `game.txt`); each gamified game is in its own folder (`/trains/`, ...);
  `/build-it/` ("Build it yourself", menu BUILD IT) shows each game's prompt, model and build time;
  `/about/`. Every page's SOURCE opens its prompt page, `prompt/` beside it (the front page's
  is `/prompt/`, the base game's `/base/prompt/`): the folder's prompt.txt word for word in a
  box with a copy button, under the site's title band, made by `make` with `txt-html.py`
  (generated, git-ignored; `make prompt-pages` makes only these). Pages built before this
  change still link to prompt.txt until they are rebuilt.
- `layout.txt` is the frame shared by every page: title band with the "x" logo (both link to
  https://multiply.by/), share icon and desktop share menu, THE ONE MENU of every page, footer. The
  menu: always visible MUTE (games), the GAMES icon (four squares), BUILD IT and SOURCE (outlined
  buttons); on phones a menu button (three lines) opens a panel with HOME, GAME BOARD (icon and words),
  ABOUT and, on games, RULES and RESET; on tablets and computers all in one row. Pages only name
  their current item and SOURCE address.
- `footer.txt`: the three-column site info block (Get the app: the official Google Play
  badge; Feedback and the privacy policy link; Functional AI Inc.) above the copyright line, on /games/,
  About and Build It, put in by an optional
  `#include footer.txt` line.
- Each page has its own spec with one `#include layout.txt` line; `assemble-spec PAGE.txt`
  expands it into that page's `prompt.txt` (generated, git-ignored, served: every page's SOURCE
  button opens it as the prompt page, and it must stay one self-contained file a person can
  upload to any chatbot).
  - `prompt.txt` (tracked, at the root like every page's prompt.txt): the front page's whole
    prompt (/), three "Use" lines: the played game's prompt page (now
    https://multiply.by/dots/prompt/), https://multiply.by/gamify and
    https://multiply.by/selector/prompt/. To put another game on the front page, change the first
    line (for the base game, use https://multiply.by/base/prompt/ and
    https://multiply.by/grid/prompt/ instead of the first two) and the dependencies of
    build/home/index.html in the Makefile. `selector.md` (tracked; rendered by md-html.py to
    /selector/prompt/) describes the games strip (the grid's list minus the played game, pictures
    `thumbnails/GAME-thumbnail.png`, 200 x 160, last game played first, then the rest in the
    order of orders.txt, then More games) and the page's changes to the game (address
    https://multiply.by/, SOURCE /prompt/, HOME current). Same storage keys as the game's own page,
    so progress is shared.
  - `grid.md` (tracked; rendered by md-html.py to /grid/prompt/): the games grid and THE SITE'S
    ONE LIST OF GAMES (short name, key, address, thumbnail, screenshot): add a new game there.
    Used by the games page (all twelve, screenshots), the front page's strip (the list only) and,
    through gamify.md, the end of every gamified game's "You Won!" panel (all twelve,
    this game marked "Play again", thumbnails, 3 x 4; /gamify/ includes grid.md after gamify.md). Games get it when rebuilt.
  - `orders.txt` (tracked, served at /orders.txt, edited by the user): the one order of the game
    tiles on the games page, the front page strip and the "You Won!" grid; never shuffled. grid.md and selector.md point to it; /gamify/ includes it after grid.md; the
    games page and front page builds fetch it.
  - `games/page.txt`: the chooser (/games/; GAMES is the current menu item); its grid is a
    "Use https://multiply.by/grid/prompt/" line. Both pages save the tapped game in localStorage
    `multiply_last_game`. Build with `make` in `games/` (`../run-model --fetch`, model in
    `games/model`: opus).
  - `game.txt`: the base game (/base/). The site menu plus MUTE, RULES (popup) and RESET.
    Every gamified game keeps exactly this menu (gamify.md).
  - `about/about.txt`: About (ABOUT is the current menu item).
  - `build-it/page.txt`: Build it yourself (/build-it/, was /gallery/). `make` there retakes the
    screenshots (`shots.py`; also used by /games/) and builds the page (Claude). The front page's
    strip uses `thumbnails/GAME-thumbnail.png` instead (screenshots are illegible that small):
    `thumbs.py` crops each game's main picture (the robot: a finished one drawn by the game's own
    buildMiniRobotSvg); made only when missing, so a hand-made replacement is kept. Tracked in git.
  - `FAQ/faq.txt`: the FAQ, still in progress by the user, not built yet. The URL is /faq
    (currently 404); the folder needs renaming to `faq` and a Makefile like about's.
- `make` in this folder builds the base game and the front page. Base game: game.txt ->
  `base/prompt.txt` -> the model named in `model` (e.g. kimi; `run-model`, which reuses mk-gamify's
  model calls; build/build.txt notes tokens, cost, time) -> `build/index.html` -> PWA tags from
  `PWA-build.txt` inserted -> `check-scripts.py` (node --check) -> `base/index.html`. Front page:
  `prompt.txt` -> the model in `home-model` (`run-model --fetch`: the prompt
  plus the full text of each page on a "Use https://multiply.by/..." line, as a chat's fetch gives
  it: dots/prompt.txt, the /gamify text, selector.md) ->
  `build/home/index.html` (its own folder, so its build.txt does not overwrite the base game's
  `build/build.txt`, which Build It reads) -> PWA tags -> `index.html`. Also extracts the PWA files and renders icons and og-image.png. The installed app
  opens the front page; sw.js keeps every page opened online, so played games work offline.
- About: `make` in `about/` (Claude via `about/run-claude.py`, key read from
  `$HOME/.anthropic_key`).
- Custom games: `../mk-custom` from the game's folder; it combines game.txt + layout.txt + the
  folder's `custom.txt` (put at the top), sets GAME to the folder name and SOURCE to the folder.
  Served at /<folder>/ (no redirects).
  - The division game (`divide/`, Divide.by) was removed on 2026-11-23 (Evolution covers missing
    factors). /divide/ and https://divide.by redirect to https://multiply.by/games/ (nginx:
    sites-enabled/multiply.by and sites-enabled/divide.by). Its custom.txt is in git history.
  - `monster/`: Multiply Monster, a gamified version for 2nd and 3rd graders (Munch, path,
    stickers, stars; `?easy` = 2, 5 and 10). Now built with `../mk-gamify` (see below) from
    `monster/prompt.txt` (a short prompt), model `fable`. Its `custom.txt` is the hand-made design
    of the first build (by mk-custom, kept in `monster/fable/`): gamify.md no longer links to it
    or to its build-instructions.txt, but don't delete or regenerate either. mk-gamify no longer
    attaches it (a chat user doesn't get it, and builds copied it).
- Gamified games from a short prompt (e.g. `trains/`): `../mk-gamify` from the game's folder. The
  folder's prompt.txt is a few lines of prompt (not a CUSTOMIZATION section); the game's SOURCE opens
  it (as `prompt/`, which mk-gamify also makes). The folder's `model` file names the model (carbon, fable, opus, gpt, kimi or a full id; no
  default). Gemini runs on Vertex; an id with a `/` (gpt = openai/gpt-6.1-terra, kimi =
  moonshotai/kimi-k3.1-pro) goes through OpenRouter, key in ~/.openrouter-key. mk-gamify
  (`MK_EFFORT`, `MK_FORCE=1`) does EXACTLY what a chat does, so an API pass proves the prompt and
  /gamify/ work as published: it sends prompt.txt word for word plus the full text of each
  multiply.by file it links to (as if fetched; /gamify/ is remade by make first and sent as the
  plain text a fetch gives), nothing else:
  no added instructions, no preset SOURCE or GAME. The page in the answer becomes index.html (the
  text before it, customization.txt), checked but never changed: scripts must parse and SOURCE
  must open the folder's `prompt/` (relative `prompt/` or its full address), or nothing is published; a GAME shared with another game is
  reported. It also keeps a copy of each build (index.html,
  customization.txt, build.txt with model, tokens, cost, time) in a subfolder per model
  (`trains/carbon/`, `trains/fable/`, served for comparison). A failed build keeps the raw answer in
  /tmp/mk-gamify-<folder>-answer.txt. Gemini 4 Carbon stops each answer at 65,536 tokens; mk-gamify
  asks it to continue.
- `gamify.md`: a guide for an AI model writing the custom.txt of a GAMIFIED version (mascot,
  rewards, progress pictures, new screen layout; it uses Monster as its example). Served
  publicly; no build tooling in it. Simple customizations (branding, division, speech) are a
  hand edit of the base build instructions, not its subject. Its old name, multiply.md, is gone.
- `gamify/index.html` (https://multiply.by/gamify, generated by `make gamify/index.html`,
  served, git-ignored): ONE file for building a gamified game in any chatbot, the address every
  game's prompt ends with: gamify.md, grid.md, orders.txt, then the base prompt.txt (unchanged), all rendered as HTML
  by python3-markdown-it (`gamify-html.py`; the base file's HTML shows as text), title "gamify".
  A web page, not .txt: Gemini's web app refuses a .txt upload. Plain `make` rebuilds it whenever
  gamify.md or the base spec changes (no hand copying). It replaced gamify.txt (gone).
- `sitemap.xml` (generated, served) lists the public pages and /gamify/ with the dates
  their files changed; `make` remakes it every time. Add a new game to the list in
  `make-sitemap.py`. `robots.txt` (tracked) points to it.
- nginx (`/etc/nginx/sites-enabled/multiply.by`, not in git; reapply on a new server): the main
  server block has `charset utf-8;` and a `location ~ \.md$` block with
  `default_type "text/plain; charset=utf-8";` and `try_files $uri =404;`. Without it nginx sends
  .md files as application/octet-stream, which fetch tools (e.g. claude.ai) refuse to read.
  It also has a `location ~ ^/gamify(/.*)?$` block (before the .md one) with
  `add_header Cache-Control "no-cache" always;` and `try_files $uri $uri/ =404;`, so caches,
  chatbots' fetch tools included, check back for the latest /gamify/ (it matches the /gamify
  redirect too, not /gamify.md).
  A `location ~ ^/(build-it/[^/]+\.png|thumbnails/.+)$` block does the same (no-cache) for the
  game screenshots and strip pictures, which are retaken under the same names after a rebuild.
- Android app (Google Play, `by.multiply.app`): notes in `ANDROID.md`, which `make` renders to
  /android/ (`md-html.py`; generated, git-ignored), the one way to build the app: on the local
  machine with the Gradle wrapper, as /android/ describes (the release build signs with the
  upload key in ~/.multiply-play/, never in git). The Kotlin project, `gather-assets.py` and
  `store-assets.py` (the Play listing's pictures and video,
  into `android/assets/`) are in `android/`. The app's privacy policy, `PRIVACY.md`, is rendered the
  same way to /privacy/; the website's, `PRIVACY-WEBSITE.md` (ads on non-game pages, server log),
  to /privacy/website/, linked from footer.txt.
- `match/` (an older matching game) was deleted on 2026-11-23; `git checkout -- match` restores it.
- Builds take a few minutes and go live as soon as they pass; run them in the background.
- ChatGPT games (trains, planes, space, building, evolution) are never built here: the owner's
  desktop Claude Code with Claude in Chrome follows `chat-gpt-local.md` (tracked; `make` renders
  it to https://multiply.by/chat-gpt-local.html, git-ignored), ending with `make` in build-it/.
- BUILD ORDER: games (and the base game and front page) first, then Build It and /games/. Both show
  screenshots of the live games (`build-it/*.png`, taken by `shots.py` from the live page), so
  after a game rebuild run `make` in `build-it/`: it retakes the shot of every game whose
  index.html is newer. Never build Build It or /games/ in parallel with the games they show.

## Rules
- Never print, echo or commit API keys. Don't change or commit anything in /var/www/openlang.ai
  (e.g. run-vertex.py model changes): it is not part of this repo.
- ADS (website only, never in the Android app or in the games): when ads are added to any page's
  spec (`layout.txt`, `build-it/page.txt`, `about/about.txt`, ...), the spec must also say: "If
  `navigator.userAgent` contains `MultiplyByApp`, create no ad slots and load no ad script." The
  app adds `MultiplyByApp/VERSION` to its user agent (ANDROID.md, "No ads anywhere in the app");
  after the rebuild, check the page with that user agent: no ad boxes, no ad requests.
- Specs: wrap prose at about 100 columns; only code fragments and exact HTML may run longer.
- After a rebuild, test the live page with Playwright (python, chromium) at 360x640, 640x360
  (landscape), 768x1024 (tablet) and 1280x800: no console errors, nothing cut off, no page scroll
  on the game, share menu, menu bar, animations, wrong-answer distractors (position and parity).
  Then play every rebuilt game page through to "You Won!" with `./play-test.py URL ...` (a quarter
  of the answers wrong; fails on any console error or a question that stops advancing): a fresh
  build can break on its second question, which a layout check misses (a kimi front page did).
  Headless Chromium uses DejaVu Sans, about 15% wider than phone fonts.
- Commit or push only when the user asks.

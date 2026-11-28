# multiply.by

Free times-tables games for children, at **https://multiply.by**, and on
[Google Play](https://play.google.com/store/apps/details?id=multiply.by.app) as an app with no ads.

Every page of the site is **one self-contained HTML file written by an AI model from a plain-text
prompt**. This repository holds the prompts and the build tools, not the code that runs in the browser: the
pages are generated and never edited by hand. To change a game, change its prompt and build it again.

## Build a game yourself

You don't need this repository to make your own game. Paste a few lines into any chatbot that can
read web pages (Claude, ChatGPT, Gemini, ...), for example:

```
Dinosaurs version: Pterodactyl, Velociraptor, Stegosaurus, T Rex, Brontosaurus.
Show lifelike images and simple animation for how they walked or flew.

Your deliverable is a complete, playable, standalone index.html file
that I can download and open in my browser.

Use https://multiply.by/gamify
```

[/gamify](https://multiply.by/gamify) is a single page with everything the model needs: a guide to
gamifying the base game (mascot, rewards, progress pictures), the list of games, and the full
prompt of the base game. Save the answer as `index.html` and open it in a browser.

Every game on the site has a **SOURCE** button that shows the exact prompt it was built from, and
[Build it yourself](https://multiply.by/build-it/) lists each game's prompt, model and build time.

## The games

| Game | Prompt | Built with |
|------|--------|------------|
| [Robot](https://multiply.by/robot/) | [robot/prompt.txt](robot/prompt.txt) | Gemini |
| [Dinosaurs](https://multiply.by/dino/) | [dino/prompt.txt](dino/prompt.txt) | Claude Opus |
| [Monster](https://multiply.by/monster/) | [monster/prompt.txt](monster/prompt.txt) | Claude Opus |
| [Trains](https://multiply.by/trains/) | [trains/prompt.txt](trains/prompt.txt) | ChatGPT |
| [Planes](https://multiply.by/planes/) | [planes/prompt.txt](planes/prompt.txt) | ChatGPT |
| [Buildings](https://multiply.by/building/) | [building/prompt.txt](building/prompt.txt) | ChatGPT |
| [Space](https://multiply.by/space/) | [space/prompt.txt](space/prompt.txt) | ChatGPT |
| [Evolution](https://multiply.by/evolution/) | [evolution/prompt.txt](evolution/prompt.txt) | ChatGPT |
| [Block Craft](https://multiply.by/blocks/) | [blocks/prompt.txt](blocks/prompt.txt) | Gemini |
| [Chinese](https://multiply.by/chinese/) | [chinese/prompt.txt](chinese/prompt.txt) | Gemini |
| [Dot Array](https://multiply.by/dots/) | [dots/prompt.txt](dots/prompt.txt) | Claude Fable |
| [Base Game](https://multiply.by/base/) | [game.txt](game.txt) | Kimi |

Each game folder has its `prompt.txt`, a `model` file naming the model, and `build.txt` with the
model, tokens, cost and time of the build that is live.

All games share one base game ([game.txt](game.txt)): 120 multiplication facts (the 2 to 9 times
tables, 11 x 11 and the 12 times table, then the 11 and 13 to 20 times tables), spaced repetition,
and progress saved in the browser. No sign-up, nothing sent to a server.

## How the site is put together

- **Specs, not code.** Each page has a plain-text spec. `layout.txt` is the frame shared by every
  page (title band, menu, footer) and `footer.txt` the site info; a spec pulls them in with
  `#include` lines, and `assemble-spec` expands them into the page's `prompt.txt`, one file a
  person can paste into any chatbot.
- **Shared lists.** [grid.md](grid.md) is the site's one list of games, and
  [orders.txt](orders.txt) the order of their tiles everywhere. [gamify.md](gamify.md) is the guide
  for building a gamified game; [selector.md](selector.md) describes the games strip on the front
  page.
- **Pages.** `/` is the front page ([prompt.txt](prompt.txt)): the base game with a strip of the
  other games. `/games/` ([games/page.txt](games/page.txt)) is the picture chooser,
  `/build-it/` ([build-it/page.txt](build-it/page.txt)) shows how each game was built, and
  `/about/` ([about/about.txt](about/about.txt)) is About.
- **Android app.** A thin Kotlin app in [android/](android/) that ships the site's files; see
  [ANDROID.md](ANDROID.md). Privacy policies: [PRIVACY.md](PRIVACY.md) (app) and
  [PRIVACY-WEBSITE.md](PRIVACY-WEBSITE.md) (website).

## Building

The site is served as static files straight from the repository folder. `make` builds what is out
of date:

```sh
make                 # base game, front page, /gamify/, prompt pages, icons, sitemap
cd dino && ../mk-gamify   # one gamified game from its prompt.txt and model file
cd build-it && make  # retake the screenshots of rebuilt games, then the Build It page
```

`mk-gamify` sends a game's prompt exactly as a chatbot user would (the prompt word for word plus
the text of each multiply.by page it links to, nothing else), so a passing build shows the
published prompt works. It keeps a copy of each build per model (`dino/opus/`, ...) for comparison.
The ChatGPT games are built in the ChatGPT web app ([chat-gpt-local.md](chat-gpt-local.md)).

Model calls need API keys (Anthropic, Google Vertex AI or OpenRouter, depending on the model) in
files in your home directory; keys are never stored in the repository. Builds take a few minutes.

After a build, `play-test.py URL` plays a game through to "You Won!" in headless Chromium
(Playwright), with a quarter of the answers wrong, and fails on any console error or a question
that stops advancing.

## Contributing

Issues and suggestions are welcome. Because the pages are generated, a fix is a change to a spec
or a prompt, not to an `index.html`.

---

© Functional AI Inc.

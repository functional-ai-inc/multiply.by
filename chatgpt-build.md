---
description: Rebuild a multiply.by game in a ChatGPT chat and publish it (usage: /chatgpt-build GAME)
argument-hint: GAME (the game's folder, e.g. trains, planes, space, evolution)
---

# Rebuild a multiply.by game in ChatGPT

Instructions for Claude Code on the site owner's desktop, with Claude in Chrome. Some games on
https://multiply.by are built in a ChatGPT chat (GPT-6.1 Terra, included in the ChatGPT
subscription) instead of through the API: Trains, Planes, Space and Evolution. This rebuilds one of
them, exactly as a person would in the chat, and puts the new page on the web server.

To use it as a slash command, save this file as `~/.claude/commands/chatgpt-build.md` on the
desktop, then run `/chatgpt-build trains` (or planes, space, evolution, ...).

GAME is `$ARGUMENTS`: the game's folder name, as in https://multiply.by/GAME/. If it is empty, ask
which game. It must be a folder name only (letters, digits, `-`); stop if it is anything else.

## Rules

- The prompt goes to ChatGPT WORD FOR WORD: no added instructions, no edits, no "please". The site
  publishes these prompts; the point is that the prompt alone builds the game. The one exception
  is the `?v=` time stamp on the /gamify link (step 3).
- Never edit the downloaded index.html by hand, not even to fix a bug: a page that doesn't work
  is rebuilt, not patched (a rule of the whole site).
- Use a NEW ChatGPT chat for every build, never an old one.
- One game per run. Commit nothing; the server is not a git checkout you should touch beyond
  copying the two files below.
- Stop and ask the owner whenever something here doesn't match what you see (no Thinking effort
  setting, a login page, a usage-limit message, a captcha).

## 1. Get the prompt

```
mkdir -p ~/multiply-builds/GAME
curl -fsS https://multiply.by/GAME/prompt.txt -o ~/multiply-builds/GAME/prompt.txt
cat ~/multiply-builds/GAME/prompt.txt
```

If the download fails (404), stop: there is no such game. The prompt is a few lines and ends with
a link to https://multiply.by/gamify (the guide and the base game's build instructions); ChatGPT
reads that page itself.

## 2. Open ChatGPT

- ChatGPT memory must be OFF: in ChatGPT, Settings → Personalization, **Enable memory** and
  **Reference my writing style** both off. With memory on, ChatGPT follows what it remembers
  from earlier builds instead of the current /gamify page (on 2026-11-20 it kept adding a zoom
  feature that had been removed from the guide). If either is on, stop and ask the owner to turn
  it off; it is the owner's account setting, so don't change it yourself. Use a normal chat, not
  a Temporary Chat: an Unpersonalized temporary chat didn't read /gamify and made no photos.
- In Chrome (Claude in Chrome), open a new tab at https://chatgpt.com/ and start a NEW chat
  ("New chat" at the top of the left sidebar), in the **Chat** tab at the top (not Work).
- There is no model menu: the chat uses the subscription's model (GPT-6.1 Terra). The only
  setting is **Thinking effort**, the button inside the message box, left of the microphone:
  click it and drag the slider all the way to the right, until the label reads **High**. Check
  it says High before sending.

## 3. Send the prompt

- Paste the full text of `~/multiply-builds/GAME/prompt.txt` into the message box, exactly as it
  is (line breaks included), and send it. ChatGPT builds only: add `?v=` and the current clock
  time (HH:MM:SS, made at the moment you paste, e.g. `date +%H:%M:%S`) to the /gamify link, so
  `https://multiply.by/gamify` becomes `https://multiply.by/gamify?v=23:01:45`. Without a new URL
  ChatGPT often reuses its cached copy of the guide (for 25+ minutes) instead of reading the
  current one. Change nothing else in the prompt.
- Send it with the **Send** button (the arrow at the right of the message box), not the Return
  key: on 2026-11-21 Return left the prompt unsent in the box. Then check that it was sent: the
  address changes to https://chatgpt.com/c/... and the prompt shows as a message, not in the box.
- Note the time it was sent (for build.txt).
- If ChatGPT asks a question instead of building, answer only: "Use your best judgment and follow
  https://multiply.by/gamify. Please build the complete index.html now." Mention this in the
  report.

## 4. Wait, then download index.html

- A build takes about 10 to 25 minutes. Check about once a minute; don't type in the chat while it
  works. If a "Continue generating" button appears, click it.
- When it is finished, download the index.html it offers (a file link or download button) into
  `~/multiply-builds/GAME/index.html`. If it only shows the code in the chat, ask: "Please give me
  the complete index.html as a file to download." Never copy part of the code by hand.
- Note the time it finished.
- Check the file before going on; if any check fails, stop and report (do not upload):
  ```
  cd ~/multiply-builds/GAME
  head -c 15 index.html            # starts with <!DOCTYPE html> (any case)
  tail -c 20 index.html            # ends with </html> (perhaps a newline after it)
  wc -c index.html                 # more than 50,000 and at most 614,400 bytes (600 KB)
  grep -c 'href="prompt.txt"' index.html   # at least 1: SOURCE opens the game's own prompt
  grep -c 'id="main-picture"' index.html   # at least 1 (the site makes its thumbnails from it)
  ```
  Also look for signs of a cut-off answer: "...", "rest of the code", "remains the same",
  "TODO" inside the script.
  A page over 600 KB almost always has oversized or duplicated photos (gamify.md asks for each
  photo at most 960px and 80 KB, all together at most 450 KB, each embedded once). Don't
  upload it: tell the owner the size, and ask ChatGPT in the same chat: "The page is N KB. Follow
  PHOTO SIZE in https://multiply.by/gamify: each photo at most 960px across and 80 KB (WebP),
  each embedded once, the whole page at most 600 KB. Send the complete index.html again." Then
  check the new file the same way.

## 5. Write build.txt

`~/multiply-builds/GAME/build.txt`, exactly these lines (the site's Build It page reads the Model
and Time lines; Time is the minutes from sending the prompt to the finished answer, one decimal):

```
Model: openai/gpt-6.1-terra (built in a ChatGPT chat, thinking effort high, from prompt.txt)
Built: YYYY-MM-DD HH:MM +03
Tokens and cost: not recorded (ChatGPT subscription)
index.html: N bytes
Time: M.M minutes
```

Built is the finishing time in Minsk time (+03); N is the byte count with thousands separators
(e.g. 341,414).

## 6. Put it on the server

The server is the Google Cloud VM `openlang-staging` (project functional-ai, zone us-east1-b),
user `jlr`. SSH and scp need `--tunnel-through-iap`. Keep the old page as `index.prev.html`
first, so it can be put back:

```
gcloud compute ssh jlr@openlang-staging --zone=us-east1-b --tunnel-through-iap \
  --command "cd /var/www/multiply.by/GAME && cp -p index.html index.prev.html"
gcloud compute scp --zone=us-east1-b --tunnel-through-iap \
  ~/multiply-builds/GAME/index.html ~/multiply-builds/GAME/build.txt \
  jlr@openlang-staging:/var/www/multiply.by/GAME/
```

The page is live at https://multiply.by/GAME/ as soon as the copy finishes.

## 7. Test it on the server

`play-test.py` plays the game to "You Won!" with a quarter of the answers wrong and fails on any
console error, a question that stops advancing, text under 9px, or a menu-panel tap that answers:

```
gcloud compute ssh jlr@openlang-staging --zone=us-east1-b --tunnel-through-iap --command \
  "cd /var/www/multiply.by && for s in 360x640 640x360 768x1024 1280x800; do ./play-test.py --size \$s https://multiply.by/GAME/; done"
```

Also open https://multiply.by/GAME/ in Chrome and look at it on a narrow and a wide window: the
whole picture visible (not cropped), nothing cut off, the menu working.

If a test FAILS: report the failure line(s) to the owner and ask whether to put the old page
back. To put it back:

```
gcloud compute ssh jlr@openlang-staging --zone=us-east1-b --tunnel-through-iap \
  --command "cd /var/www/multiply.by/GAME && mv index.prev.html index.html"
```

## 8. Report

Tell the owner: the game, the build time, the file size, any question ChatGPT asked, and the
play-test result at each size. Remind them that the Build It screenshot and the front page's
thumbnail of this game are retaken on the server (Claude Code there: `make -C build-it`, after
deleting `thumbnails/GAME-thumbnail.png` if the game's look changed).

#!/usr/bin/env python3
"""Make the Google Play store-listing pictures and video from the live site, into assets/.

Usage: python3 store-assets.py [--site https://multiply.by] [--only icon,feature,phone,tablet,video]

Run it from anywhere; it writes next to itself, in android/assets/ (served as
https://multiply.by/android/assets/). Needs Python 3 with Playwright (`pip install playwright`,
then `playwright install chromium`), Pillow, and ffmpeg for the video. It reads the pages from the
live site, the same pages gather-assets.py puts in the app, so run it after the games you show
were rebuilt. Each part takes a few seconds, the video about two minutes.

  icon-512.png          the store icon: icon.svg at 512 x 512 (Play adds the rounded corners)
  feature-graphic.png   1024 x 500, no transparency (Play's rule): logo, name, line, game pictures
  phone/NN-PAGE.png     1080 x 1920 (9:16) phone screenshots, at most 8 (Play's limit), in store
                        order. Games are shown mid-game: a few questions answered right first.
  tablet-7/, tablet-10/  portrait tablet screenshots, 1200 x 1920 and 1600 x 2560 (TABLETS)
  robot.mp4             the Robot game played from the start to "You Won!" on a phone,
                        1080 x 1920, H.264: the first 10 moves (7 right, 3 wrong) at 1.4x
                        with the game's sounds and a mouse pointer, the rest at 12x, silent. Play takes a video only as a YouTube
                        link: upload it to YouTube (unlisted is fine), then paste the link.

listing.txt (the store texts) and play-console.txt (the answers to the Play Console's forms) are
written by hand and kept in git; the rest is generated.
"""
import argparse, os, random, re, shutil, subprocess, sys, tempfile, time, urllib.request
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")

ap = argparse.ArgumentParser()
ap.add_argument("--site", default="https://multiply.by")
ap.add_argument("--only", default="icon,feature,phone,tablet,video")
args = ap.parse_args()
SITE = args.site.rstrip("/")
ONLY = set(args.only.split(","))

# Phone screenshots, in store order: (file name, page, right answers before the picture).
# Build It and About are on the website only: in the app they open in the browser, after the
# parental gate. Play wants screenshots of the app itself, so keep them last (or drop them).
PHONE = [
    ("01-monster", "/monster/", 6),
    ("02-robot", "/robot/", 10),
    ("03-trains", "/trains/", 5),
    ("04-dino", "/dino/", 5),
    ("05-blocks", "/blocks/", 6),
    ("06-games", "/games/", 0),
    ("07-build-it", "/build-it/", 0),
    ("08-about", "/about/", 0),
]
# Tablet screenshots (optional on Play, needed to be featured on tablets): the app is held
# upright, so these are portrait too. (folder, CSS width x height, pixel ratio): 7-inch 1200 x
# 1920, 10-inch 1600 x 2560.
TABLETS = [("tablet-7", 600, 960, 2), ("tablet-10", 800, 1280, 2)]
TABLET_PAGES = [("01-monster", "/monster/", 6), ("02-trains", "/trains/", 5),
                ("03-robot", "/robot/", 10), ("04-games", "/games/", 0)]
VIDEO_PAGE = "/robot/"
VIDEO_SLOW = [False, False, True, False, False, True, False, False, True, False]  # True: wrong
VIDEO_FIRST = 1.4   # the speed of those first moves (with the game's sounds)
VIDEO_FAST = 12     # the rest of the game, this many times faster, silent
VIDEO_END = 3.0     # seconds on "You Won!" at the end

# The question and the answer buttons, as play-test.py reads them.
STATE = """() => {
  const q = document.querySelector('#question, #question-text');
  const b = [...document.querySelectorAll('#answers button')];
  const ans = x => x.innerText.trim().split(String.fromCharCode(10)).pop().trim();
  return {q: q ? q.innerText.trim() : '', a: b.map(ans),
          won: /you won|play again/i.test(document.body.innerText)};
}"""
CHANGED = """old => { const q = document.querySelector('#question, #question-text');
  const a = [...document.querySelectorAll('#answers button')]
    .map(x => x.innerText.trim().split(String.fromCharCode(10)).pop().trim()).join('|');
  return (q ? q.innerText.trim() : '') !== old.q || a !== old.a.join('|')
         || /you won|play again/i.test(document.body.innerText); }"""


def answer(pg, rnd, wrong_share, wrong=None, tap=None):
    """Answer the current question: right, or wrong with the given chance (or as `wrong` says).
    `tap(button)` does the tap (default: a plain click). False when the game is already won."""
    s = pg.evaluate(STATE)
    if s["won"]:
        return False
    m = re.search(r"(\d+)\s*([x×÷])\s*(\d+)", s["q"])
    if not m:
        raise SystemExit(f"no question on the page: {s['q']!r}")
    a, op, c = int(m[1]), m[2], int(m[3])
    right = str(a // c if op == "÷" else a * c)
    if wrong is None:
        wrong = rnd.random() < wrong_share
    k = next(i for i, t in enumerate(s["a"]) if t != right) if wrong else s["a"].index(right)
    (tap or (lambda b: b.click()))(pg.locator("#answers button").nth(k))
    try:
        pg.wait_for_function(CHANGED, arg=s, timeout=10000)
    except Exception:   # the same question can come again by chance: answer it right
        t = pg.evaluate(STATE)
        if right in t["a"]:
            pg.locator("#answers button").nth(t["a"].index(right)).click()
            pg.wait_for_timeout(1500)
    return True


def flat(path):
    """Play wants no transparency in the feature graphic and screenshots: save as plain RGB."""
    Image.open(path).convert("RGB").save(path, optimize=True)


def icon():
    path = os.path.join(OUT, "icon-512.png")
    with urllib.request.urlopen(f"{SITE}/icon-512.png") as r, open(path, "wb") as f:
        f.write(r.read())
    im = Image.open(path)
    assert im.size == (512, 512), im.size
    print("icon-512.png", im.size)


FEATURE = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; width: 1024px; height: 500px; overflow: hidden; }
body { background: #fafaf9; font-family: system-ui, "Segoe UI", Roboto, Arial, sans-serif;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 34px; }
.top { display: flex; align-items: center; gap: 22px; }
.top svg { width: 210px; height: 113px; flex: none; }
h1 { margin: 0; font-size: 76px; line-height: 1; color: #1e40af; letter-spacing: -1px; }
p { margin: 8px 0 0; font-size: 30px; color: #374151; }
.row { display: flex; gap: 12px; }
.row img { width: 146px; height: 117px; object-fit: cover; border-radius: 14px;
  border: 1px solid #e5e7eb; box-shadow: 0 2px 6px rgba(0,0,0,0.12); background: #fff; }
</style></head><body>
<div class="top">
  <svg viewBox="80 160 352 190"><g fill="none" stroke="#991b1b" stroke-width="30" stroke-linecap="round" stroke-linejoin="round">
  <path d="M 102 222 C 102 182 182 182 182 222 C 182 252 102 282 102 322 L 186 322"/>
  <path d="M 226 252 L 286 322 M 286 252 L 226 322"/>
  <path d="M 330 222 C 330 182 410 182 410 222 C 410 252 330 282 330 322 L 414 322"/></g></svg>
  <div><h1>Multiply.by</h1><p>Learn the times tables with games</p></div>
</div>
<div class="row">IMAGES</div>
</body></html>"""
FEATURE_GAMES = ["monster", "robot", "trains", "dino", "space", "blocks"]


def feature(browser):
    imgs = "".join(f'<img src="{SITE}/thumbnails/{g}-thumbnail.png" alt="">' for g in FEATURE_GAMES)
    pg = browser.new_page(viewport={"width": 1024, "height": 500})
    pg.set_content(FEATURE.replace("IMAGES", imgs), wait_until="networkidle")
    path = os.path.join(OUT, "feature-graphic.png")
    pg.screenshot(path=path)
    pg.close()
    flat(path)
    print("feature-graphic.png", Image.open(path).size)


def shots(browser, folder, pages, w, h, ratio):
    folder = os.path.join(OUT, folder)
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
    for name, page, moves in pages:
        ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=ratio,
                                  has_touch=True, is_mobile=True)
        pg = ctx.new_page()
        pg.goto(SITE + page, wait_until="networkidle")
        pg.wait_for_timeout(1000)
        rnd = random.Random(1)
        for _ in range(moves):
            if not answer(pg, rnd, 0):
                break
            pg.wait_for_timeout(700)
        pg.wait_for_timeout(1500 if moves else 300)   # let the reward animation settle
        path = os.path.join(folder, name + ".png")
        pg.screenshot(path=path)
        ctx.close()
        flat(path)
        print(f"{os.path.basename(folder)}/{name}.png", Image.open(path).size)


def phone(browser):
    shots(browser, "phone", PHONE, 360, 640, 3)


def tablet(browser):
    for folder, w, h, ratio in TABLETS:
        shots(browser, folder, TABLET_PAGES, w, h, ratio)


# Headless Chrome plays sound to nowhere, so the video takes it from inside the page: every Web
# Audio node connected to the speakers is also connected to a recorder.
AUDIO_TAP = """(() => {
  if (!window.AudioNode || !window.MediaRecorder) return;
  const rec = window.__storeAudio = { chunks: [], start: null, recorders: [] };
  const connect = AudioNode.prototype.connect, taps = new WeakMap();
  AudioNode.prototype.connect = function (dest, ...more) {
    const out = connect.call(this, dest, ...more);
    if (dest instanceof AudioDestinationNode) {
      let tap = taps.get(dest.context);
      if (!tap) {
        tap = dest.context.createMediaStreamDestination();
        taps.set(dest.context, tap);
        if (!rec.recorders.length) {   // the games use one AudioContext
          const r = new MediaRecorder(tap.stream, { mimeType: 'audio/webm;codecs=opus' });
          r.ondataavailable = e => { if (e.data.size) rec.chunks.push(e.data); };
          r.start(500);
          rec.start = Date.now() / 1000;
          rec.recorders.push(r);
        }
      }
      connect.call(this, tap);
    }
    return out;
  };
})();"""
AUDIO_STOP = """async () => {
  const rec = window.__storeAudio;
  if (!rec || !rec.recorders.length) return null;
  const r = rec.recorders[0];
  await new Promise(done => { r.onstop = done; r.stop(); });
  const blob = new Blob(rec.chunks, { type: 'audio/webm' });
  const url = await new Promise(done => {
    const f = new FileReader(); f.onload = () => done(f.result); f.readAsDataURL(blob); });
  return { start: rec.start, data: url.split(',')[1] };
}"""


# Headless Chrome draws no mouse pointer: the video gets an arrow that follows the mouse, with a
# ripple on each click.
POINTER = """(() => {
  const add = () => {
    const p = document.createElement('div');
    p.id = '__pointer';
    p.innerHTML = '<svg width="22" height="30" viewBox="0 0 22 30"><path d="M2 2 L2 24 L8 18.5 ' +
      'L12.5 28 L16.5 26 L12 16.8 L20 16.8 Z" fill="#111827" stroke="#fff" stroke-width="2" ' +
      'stroke-linejoin="round"/></svg>';
    p.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;' +
      'transform:translate(270px,560px);filter:drop-shadow(0 1px 2px rgba(0,0,0,.35))';
    document.documentElement.appendChild(p);
    const move = e => { p.style.transform = `translate(${e.clientX - 2}px,${e.clientY - 2}px)`; };
    addEventListener('mousemove', move, true);
    addEventListener('mousedown', e => {
      move(e);
      const r = document.createElement('div');
      r.style.cssText = `position:fixed;left:${e.clientX - 18}px;top:${e.clientY - 18}px;` +
        'width:36px;height:36px;border-radius:50%;background:rgba(37,99,235,.35);' +
        'z-index:2147483646;pointer-events:none;transition:transform .35s,opacity .35s';
      document.documentElement.appendChild(r);
      requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
      setTimeout(() => r.remove(), 450);
    }, true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add();
})();"""


def glide(pg, at, to, ms=550):
    """Move the mouse from `at` to `to` like a hand: eased, and timed by the clock (not by
    steps), so a busy machine makes it jerkier, never slower."""
    t0, total = time.time(), ms / 1000
    while True:
        f = min(1.0, (time.time() - t0) / total)
        e = f * f * (3 - 2 * f)
        pg.mouse.move(at[0] + (to[0] - at[0]) * e, at[1] + (to[1] - at[1]) * e)
        if f >= 1:
            break
        pg.wait_for_timeout(16)


def video(browser):
    """The Robot game on a phone, start to "You Won!": the first moves (VIDEO_SLOW) at
    VIDEO_FIRST speed with the game's sounds and a mouse pointer, then the rest VIDEO_FAST times
    faster, silent.

    Frames come from Chrome's own screencast, at the phone's full resolution (Playwright's video
    recorder draws a 3x page at 1x, in a corner). Each frame arrives with its time when the screen
    changes; ffmpeg shows it until the next one. Headless Chrome plays sound to nowhere, so the
    sound is recorded inside the page (AUDIO_TAP), sped up as much as the picture (ffmpeg's
    atempo keeps the pitch) and laid under the first part. The recording leaves out the silent
    stretches (gaps in its timestamps): aresample=async=1 puts them back first, or atempo would
    pack all the sounds together."""
    import base64
    if not shutil.which("ffmpeg"):
        raise SystemExit("the video needs ffmpeg")
    tmp = tempfile.mkdtemp()
    ctx = browser.new_context(viewport={"width": 360, "height": 640}, device_scale_factor=3,
                              has_touch=True, is_mobile=True)
    ctx.add_init_script(AUDIO_TAP)
    ctx.add_init_script(POINTER)
    pg = ctx.new_page()
    pg.goto(SITE + VIDEO_PAGE, wait_until="networkidle")
    pg.wait_for_timeout(1000)
    cdp = ctx.new_cdp_session(pg)
    frames = []   # (time in s, file)

    def frame(ev):
        f = os.path.join(tmp, f"{len(frames):05d}.jpg")
        with open(f, "wb") as out:
            out.write(base64.b64decode(ev["data"]))
        frames.append((ev["metadata"]["timestamp"], f))
        cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})

    cdp.on("Page.screencastFrame", frame)
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                      "maxWidth": 1080, "maxHeight": 1920})
    rnd = random.Random(2)
    pos = [270.0, 560.0]
    pg.mouse.move(*pos)
    pg.wait_for_timeout(1200)

    def tap(button):   # look, move there, click
        box = button.bounding_box()
        to = (box["x"] + box["width"] * rnd.uniform(0.35, 0.65),
              box["y"] + box["height"] * rnd.uniform(0.4, 0.65))
        glide(pg, pos, to, rnd.randint(450, 700))
        pos[:] = to
        pg.wait_for_timeout(rnd.randint(120, 260))
        pg.mouse.down()
        pg.wait_for_timeout(90)
        pg.mouse.up()

    moves = 0
    for wrong in VIDEO_SLOW:   # the first part: a moment to think, then the pointer goes
        pg.wait_for_timeout(rnd.randint(500, 900))
        if not answer(pg, rnd, 0, wrong=wrong, tap=tap):
            break
        moves += 1
    pg.wait_for_timeout(900)
    fast_from = time.time()
    rec = pg.evaluate(AUDIO_STOP)
    pg.evaluate("document.getElementById('__pointer').style.display = 'none'")
    while moves < 300 and answer(pg, rnd, 0.1):
        moves += 1
        pg.wait_for_timeout(900)
    pg.wait_for_timeout(1500)
    cdp.send("Page.stopScreencast")
    ctx.close()
    if len(frames) < 2:
        raise SystemExit("the screencast sent no frames")

    # Each frame lasts until the next: VIDEO_FIRST times shorter before fast_from, VIDEO_FAST
    # times shorter after.
    def span(a, b):
        return (max(0.0, min(b, fast_from) - a) / VIDEO_FIRST
                + max(0.0, b - max(a, fast_from)) / VIDEO_FAST)
    with open(os.path.join(tmp, "list.txt"), "w") as lst:
        lst.write("ffconcat version 1.0\n")
        for i, (t, f) in enumerate(frames):
            d = span(t, frames[i + 1][0]) if i + 1 < len(frames) else VIDEO_END
            lst.write(f"file '{f}'\nduration {max(d, 0.001):.4f}\n")
        lst.write(f"file '{frames[-1][1]}'\n")
    mp4 = os.path.join(OUT, "robot.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
           "-i", os.path.join(tmp, "list.txt")]
    if rec:   # the sound of the first part, at its own time
        audio = os.path.join(tmp, "sound.webm")
        with open(audio, "wb") as f:
            f.write(base64.b64decode(rec["data"]))
        delay = max(0, round((rec["start"] - frames[0][0]) / VIDEO_FIRST * 1000))
        cmd += ["-i", audio, "-filter_complex",
                f"[1:a]aresample=async=1:first_pts=0,atempo={VIDEO_FIRST},adelay={delay}|{delay},apad[a]", "-map", "0:v", "-map", "[a]",
                "-c:a", "aac", "-b:a", "160k", "-shortest"]
    else:
        print("  (the page made no sound: the video is silent)")
    cmd += ["-vf", "scale=1080:1920:flags=lanczos,fps=30", "-c:v", "libx264", "-crf", "20",
            "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    secs = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                           "default=nw=1:nk=1", mp4], capture_output=True, text=True).stdout.strip()
    print(f"robot.mp4: {moves} moves ({len(VIDEO_SLOW)} at {VIDEO_FIRST}x), {len(frames)} frames, "
          f"{float(secs):.0f} s, {os.path.getsize(mp4) / 1e6:.1f} MB")


os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    # Full Chromium: the headless shell crashes on some machines (SIGSEGV at launch)
    browser = p.chromium.launch(channel="chromium")
    if "icon" in ONLY:
        icon()
    if "feature" in ONLY:
        feature(browser)
    if "phone" in ONLY:
        phone(browser)
    if "tablet" in ONLY:
        tablet(browser)
    if "video" in ONLY:
        video(browser)
    browser.close()

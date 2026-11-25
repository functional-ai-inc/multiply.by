#!/usr/bin/env python3
"""Screenshot a game for the Build it page and the front page: open it on a 412 x 732 phone screen,
answer sixteen questions right (MOVES), let the animations settle, and keep only the game's own
scene: from just below the menu bar to just above the answer buttons (the title band, menu, answers
and footer look the same in every game). The scene is fitted onto one fixed shape, 412 x 330 (saved
at twice that, 824 x 660, for sharp phone screens): a shorter scene sits at the top and the rest is
filled with the game's background colour; a taller one is scaled down to fit, centred.
Usage: shots.py GAME OUT.png   (GAME is the folder, e.g. trains: https://multiply.by/trains/,
or base for the base game at https://multiply.by/base/)"""
import io, re, sys
from PIL import Image
from playwright.sync_api import sync_playwright

game, out = sys.argv[1], sys.argv[2]
url = "https://multiply.by/base/" if game == "base" else f"https://multiply.by/{game}/"

MOVES = 16  # right answers before the picture: far enough to show the game's progress

def question(pg):
    return pg.locator("#question, #question-text").first.inner_text().strip()

with sync_playwright() as p:
    browser = p.chromium.launch()
    # A fresh context each time: no saved progress, so every game starts from the beginning.
    ctx = browser.new_context(viewport={"width": 412, "height": 732}, device_scale_factor=2,
                              has_touch=True)
    pg = ctx.new_page()
    pg.goto(url, wait_until="networkidle")
    pg.wait_for_timeout(500)
    for move in range(MOVES):
        q = question(pg)
        m = re.search(r"(\d+)\s*[x×]\s*(\d+)", q)
        # A missing factor ("3 x __ = 18", "__ x 3 = 18" or "3 x ? = 18", Evolution): the answer is
        # the factor.
        f = re.search(r"(\d+)\s*[x×]\s*(?:_+|\?)\s*=\s*(\d+)|(?:_+|\?)\s*[x×]\s*(\d+)\s*=\s*(\d+)", q)
        if f:
            a, c = (f[1], f[2]) if f[1] else (f[3], f[4])
            answer = str(int(c) // int(a))
        elif m:
            answer = str(int(m[1]) * int(m[2]))
        else:
            sys.exit(f"{game}: move {move + 1}: no question found in {q!r}")
        buttons = pg.locator("#answers button")
        # Each button's text in the largest font: a build may add a small key number (1-4)
        # above or below the answer.
        texts = buttons.evaluate_all("bs => bs.map((x => { let best = '', size = 0; const w = document.createTreeWalker(x, NodeFilter.SHOW_TEXT); for (let n; (n = w.nextNode());) { const t = n.data.trim(); if (!t) continue; const px = parseFloat(getComputedStyle(n.parentElement).fontSize); if (px > size) { size = px; best = t; } } return best; }))")
        if answer not in texts:
            sys.exit(f"{game}: answer {answer} not among {texts}")
        buttons.nth(texts.index(answer)).click()
        try:  # the same question can come twice in a row: then just answer it again
            pg.wait_for_function("q => (document.getElementById('question') || document.getElementById('question-text')).innerText.trim() !== q",
                                 arg=q, timeout=5000)
        except Exception:
            pass
        pg.wait_for_timeout(700)
    pg.wait_for_timeout(1500)
    top, bottom = pg.evaluate("""() => [(document.getElementById('menu-bar')
                                         || document.getElementById('menu-toggle')?.closest('nav, header')
                                         || document.querySelector('nav')).getBoundingClientRect().bottom,
                                        document.getElementById('answers').getBoundingClientRect().top]""")
    shot = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
    browser.close()

W, H, SCALE = 412, 330, 2
scene = shot.crop((0, round(top * SCALE), W * SCALE, round(bottom * SCALE) - 2 * SCALE))
if scene.height < 50 * SCALE:
    sys.exit(f"{game}: the scene between the menu and the answers is only {scene.height} pixels")
# The background: the colour just below the scene's bottom-left corner, in the game's own page.
fill = shot.getpixel((4 * SCALE, round(bottom * SCALE) - 3 * SCALE))
canvas = Image.new("RGB", (W * SCALE, H * SCALE), fill)
if scene.height > H * SCALE:
    scene = scene.resize((round(scene.width * H * SCALE / scene.height), H * SCALE), Image.LANCZOS)
canvas.paste(scene, ((W * SCALE - scene.width) // 2, 0))
canvas.save(out, "PNG", optimize=True)
print(f"{game}: {out}")

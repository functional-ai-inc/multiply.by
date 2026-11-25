#!/usr/bin/env python3
"""Play a live game page from start to "You Won!" and fail on anything that goes wrong.

Usage: play-test.py URL [URL ...]      (e.g. play-test.py https://multiply.by/ https://multiply.by/blocks/)
Options: --size WxH (default 360x640), --wrong 0.25 (share of wrong answers), --seed 1,
         --max 200 (moves before giving up on reaching the end),
         --min-font 9 (smallest text allowed, in px; 0 turns the check off),
         --max-page 600 (largest page allowed, in KB; 0 turns the size checks off)

Each question is read from #question or #question-text ("7 x 8", or "56 ÷ 8" in the division game), the answer from
the #answers buttons. About a quarter of the answers are wrong on purpose (mistakes take other code
paths: corrections, retries, "Almost!" pictures). TINY TEXT: once the page has loaded and again
on its end screen, every visible piece of text must be at least --min-font px (gamify.md: NO TINY
TEXT); the page fails with the smallest offenders listed. SIZE (gamify.md: PHOTO SIZE): the page
file at most --max-page KB, each embedded image at most 80 KB, all of them together at most
450 KB, and no image embedded twice (the same data URI in two places). MENU PANEL: on a page with the site's
menu button (#menu-toggle, shown on phones), the test first opens the panel and taps an answer:
that tap must ONLY close the panel (the question and the answers stay as they were). The open panel
must be a dropdown under the bar, and the bar's GAMES, BUILD IT, SOURCE and menu button stay on screen. After every tap the page must move on (the
question or the answers change) within 10 s. The page passes when it reaches its end screen (the
page shows "You Won!" or "Play Again") with no console errors and no uncaught exceptions during the
WHOLE game. A layout check after a rebuild is not enough: each build is a fresh page written by the
model, and a game can break on its second question (a kimi front page did). Exit status 1 if any
page fails. Prints the move, question and answers where it stopped; a screenshot is saved as
/tmp/play-test-<n>.png.
"""
import argparse, random, re, sys
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("urls", nargs="+")
ap.add_argument("--size", default="360x640")
ap.add_argument("--wrong", type=float, default=0.25)
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--max", type=int, default=200)
ap.add_argument("--min-font", type=float, default=9)
ap.add_argument("--max-page", type=float, default=600)
args = ap.parse_args()
W, H = map(int, args.size.split("x"))

STATE = """() => {
  const q = document.querySelector('#question, #question-text');
  const b = [...document.querySelectorAll('#answers button')];
  // The answer is the button's last line, leaving out its key number (1-4), which a build may
  // show above or below the answer.
  const ans = (x, i) => {
    let l = x.innerText.trim().split(String.fromCharCode(10)).map(t => t.trim()).filter(Boolean);
    if (l.length > 1) {
      const k = l.lastIndexOf(String(i + 1));  // remove ONE key line: the answer may equal it
      if (k >= 0) l.splice(k, 1);
    }
    return (l.pop() || '').trim();
  };
  return {q: q ? q.innerText.trim() : '', a: b.map(ans),
          enabled: b.filter(x => !x.disabled).length,
          won: /you won|play again/i.test(document.body.innerText)};
}"""


# Visible text smaller than MIN px: elements with text of their own, shown (not display: none,
# visibility: hidden or fully transparent), with a box on the page. Returns [size, text] samples.
TINY = """min => {
  const out = [], seen = new Set();
  for (const el of document.body.querySelectorAll('*')) {
    if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TITLE'].includes(el.tagName)) continue;
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.data).join('').trim();
    if (!own) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    let shown = true;
    for (let e = el; e && e !== document.documentElement; e = e.parentElement) {
      const c = getComputedStyle(e);
      if (c.display === 'none' || c.visibility === 'hidden' || +c.opacity === 0) { shown = false; break; }
    }
    if (!shown) continue;
    const px = parseFloat(getComputedStyle(el).fontSize);
    const key = px + '|' + own.slice(0, 40);
    if (px < min - 0.01 && !seen.has(key)) { seen.add(key); out.push([px, own.slice(0, 40)]); }
  }
  return out.sort((a, b) => a[0] - b[0]);
}"""


def tiny(pg, where):
    if not args.min_font:
        return None
    t = pg.evaluate(TINY, args.min_font)
    if not t:
        return None
    shown = ", ".join(f"{px:g}px {txt!r}" for px, txt in t[:5])
    return f"{len(t)} text(s) under {args.min_font:g}px {where}: {shown}"


def size_check(html):
    """gamify.md's PHOTO SIZE: page, each embedded image, all images, no image twice."""
    if not args.max_page:
        return None
    import base64, collections
    out = []
    kb = len(html) / 1024
    if kb > args.max_page:
        out.append(f"page {kb:.0f} KB (limit {args.max_page:g})")
    uris = re.findall(rb"data:image/[a-z+]+;base64,[A-Za-z0-9+/=]{200,}", html)
    sizes = [len(base64.b64decode(u.split(b",", 1)[1] + b"==")) / 1024 for u in set(uris)]
    big = sorted(round(x) for x in sizes if x > 80)
    if big:
        out.append(f"{len(big)} image(s) over 80 KB: {big} KB")
    if sum(sizes) > 450:
        out.append(f"images {sum(sizes):.0f} KB together (limit 450)")
    twice = sum(n - 1 for n in collections.Counter(uris).values() if n > 1)
    if twice:
        out.append(f"{twice} image(s) embedded more than once")
    return "; ".join(out) or None


def right_answer(q):
    """The right answer to question text q ("3 x 7", "3 x ? = 21", "21 ÷ 3"), or None."""
    mf = (re.search(r"(\d+)\s*[x×]\s*(?:_+|\?)\s*=\s*(\d+)", q)
          or re.search(r"(?:_+|\?)\s*[x×]\s*(\d+)\s*=\s*(\d+)", q))
    if mf:
        return str(int(mf[2]) // int(mf[1]))
    m = re.search(r"(\d+)\s*([x×÷])\s*(\d+)", q)
    if not m:
        return None
    a, op, c = int(m[1]), m[2], int(m[3])
    return str(a // c if op == "÷" else a * c)


def menu_check(pg):
    """Open the menu panel, tap an answer: the tap must only close the panel."""
    toggle = pg.locator("#menu-toggle")
    if not toggle.count() or not toggle.first.is_visible():
        return None
    before = pg.evaluate(STATE)
    toggle.first.click()
    pg.wait_for_timeout(300)
    if not pg.locator("#menu-panel").first.is_visible():
        return "the menu button did not open #menu-panel"
    # The open panel is a dropdown UNDER the bar; the bar keeps its buttons on screen.
    where = pg.evaluate("""() => {
      // #menu-bar is the layout's id; a page without it: the bar that holds the menu button
      const bar = (document.getElementById('menu-bar')
        || document.getElementById('menu-toggle').closest('nav, header')
        || document.querySelector('nav')).getBoundingClientRect();
      const panel = document.getElementById('menu-panel').getBoundingClientRect();
      const off = ['#games-link', '#build-it-link', '#source-link', '#menu-toggle']
        .map(sel => document.querySelector(sel)).filter(e => e && e.getClientRects().length)
        .filter(e => e.getBoundingClientRect().right > innerWidth + 0.5).map(e => e.id);
      return {below: panel.top >= bar.bottom - 1, off};
    }""")
    if not where["below"]:
        return "the open menu panel is inside the menu bar, not a dropdown under it"
    if where["off"]:
        return f"with the menu panel open, {', '.join(where['off'])} went off the screen"
    # Tap the RIGHT answer: if the tap gets through, the question surely moves on (a wrong
    # answer can leave the same question showing, and the bug would pass unseen).
    # The open panel may cover part of the answers: tap a point of the button that is really on
    # top there (as a child would), and the right one if any of it shows, else the first that does.
    right = right_answer(before["q"])
    k = before["a"].index(right) if right in before["a"] else 0
    pt = pg.evaluate("""k => {
      const bs = [...document.querySelectorAll('#answers button')];
      const spot = b => { const r = b.getBoundingClientRect();
        for (const [fx, fy] of [[.5,.5],[.15,.5],[.85,.5],[.5,.15],[.5,.85],[.15,.15],[.15,.85]]) {
          const x = r.left + r.width * fx, y = r.top + r.height * fy;
          const e = document.elementFromPoint(x, y);
          if (e && b.contains(e)) return [x, y];
        } return null; };
      return spot(bs[k]) || bs.map(spot).find(Boolean) || null;
    }""", k)
    if not pt:
        return "with the menu panel open, every answer button is covered"
    pg.mouse.click(pt[0], pt[1])
    pg.wait_for_timeout(600)
    after = pg.evaluate(STATE)
    if pg.locator("#menu-panel").first.is_visible():
        return "a tap outside the open menu panel did not close it"
    if (after["q"], after["a"]) != (before["q"], before["a"]):
        return "a tap that closed the menu panel also answered the question"
    return None


def s_won_check(pg):
    return pg.evaluate("() => /you won|play again/i.test(document.body.innerText)")


def play(browser, url, n):
    rnd = random.Random(args.seed)
    ctx = browser.new_context(viewport={"width": W, "height": H}, has_touch=True)
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(f"exception: {e}"))
    pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    resp = pg.goto(url, wait_until="networkidle")
    pg.wait_for_timeout(500)
    sized = size_check(resp.body()) if resp else None
    wrongs = 0
    problem = None
    small = [tiny(pg, "at start")]
    problem = menu_check(pg)
    move = 0
    for move in range(1, (0 if problem else args.max) + 1):
        s = pg.evaluate(STATE)
        if s["won"]:
            break
        # A missing-factor question ("3 x ? = 21", "? x 7 = 21", or with "__") asks for the blank.
        mf = (re.search(r"(\d+)\s*[x×]\s*(?:_+|\?)\s*=\s*(\d+)", s["q"])
              or re.search(r"(?:_+|\?)\s*[x×]\s*(\d+)\s*=\s*(\d+)", s["q"]))
        m = re.search(r"(\d+)\s*([x×÷])\s*(\d+)", s["q"])
        if mf:
            right = str(int(mf[2]) // int(mf[1]))
        elif not m:
            problem = f"no question in #question / #question-text: {s['q']!r}"
            break
        else:
            a, op, c = int(m[1]), m[2], int(m[3])
            right = str(a // c if op == "÷" else a * c)
        if right not in s["a"]:
            problem = f"the answer {right} is not among the buttons {s['a']}"
            break
        wrong = rnd.random() < args.wrong
        k = next(i for i, t in enumerate(s["a"]) if t != right) if wrong else s["a"].index(right)
        try:
            pg.locator("#answers button").nth(k).click(timeout=5000)
            pg.wait_for_function(
                """old => { const q = document.querySelector('#question, #question-text');
                  const a = [...document.querySelectorAll('#answers button')].map(x => x.innerText.trim().split(String.fromCharCode(10)).pop().trim()).join('|');
                  return (q ? q.innerText.trim() : '') !== old.q || a !== old.a.join('|')
                         || /you won|play again/i.test(document.body.innerText); }""",
                arg=s, timeout=10000)
        except Exception as e:
            if move == 1:
                # A first tap that changes nothing is a bug (a child's first answer is lost),
                # not a repeated question: no question has been answered yet.
                problem = f"the FIRST tap was ignored: {s['q']!r} {s['a']} (the page did not react)"
                break
            # The same question with the answers in the same order can come again by chance:
            # answer it right once more before calling it a freeze.
            try:
                t = pg.evaluate(STATE)
                pg.locator("#answers button").nth(t["a"].index(right)).click(timeout=5000)
                pg.wait_for_function("old => document.querySelector('#question, #question-text').innerText.trim() !== old.q"
                                     " || /you won|play again/i.test(document.body.innerText)",
                                     arg=s, timeout=10000)
            except Exception:
                problem = (f"FROZE at move {move}: {s['q']!r} {s['a']} after a "
                           f"{'wrong' if wrong else 'right'} answer ({str(e).splitlines()[0]})")
                break
        wrongs += wrong
        pg.wait_for_timeout(250)
    else:
        if not problem:
            problem = f"no end screen after {args.max} moves"
    if s_won_check(pg):
        pg.wait_for_timeout(1200)  # let the end screen finish appearing
        small.append(tiny(pg, "on the end screen"))
    small = [x for x in small if x] + ([sized] if sized else [])
    if small:
        problem = (problem + "; " if problem else "") + "; ".join(small)
    if errors:
        problem = (problem + "; " if problem else "") + f"{len(errors)} error(s), first: {errors[0]}"
    if problem:
        pg.screenshot(path=f"/tmp/play-test-{n}.png")
    ctx.close()
    print(f"{'FAIL' if problem else 'OK  '} {url}: {move} moves, {wrongs} wrong"
          + (f" -- {problem} (screenshot /tmp/play-test-{n}.png)" if problem else ", reached the end"))
    return not problem


with sync_playwright() as p:
    browser = p.chromium.launch()
    results = [play(browser, url, n) for n, url in enumerate(args.urls, 1)]
    browser.close()
sys.exit(0 if all(results) else 1)

#!/usr/bin/env python3
"""Show a prompt.txt as a web page: the site's title band, then the text, exactly as written, in a
box with a copy button (the look of the prompts on Build It).

Usage: txt-html.py FOLDER/prompt.txt > FOLDER/prompt/index.html

Makes https://multiply.by/FOLDER/prompt/ for every page's prompt.txt (the root's prompt.txt gives
/prompt/). The text is HTML-escaped, so any HTML in the prompt is shown as text, never used as
markup; only https:// addresses become links. The copy button copies the text exactly as in
prompt.txt (line breaks kept). Long lines wrap to the screen (no sideways scroll on a phone). The
title names the folder, for example "train/prompt.txt"; the prompt.txt file itself stays as it is.
No AI model: this page is made by this script alone.
"""
import html
import os
import re
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()
folder = os.path.basename(os.path.dirname(os.path.abspath(path)))
at_root = os.path.dirname(path) in ("", ".")
title = "prompt.txt" if at_root else f"{folder}/prompt.txt"
crumb = "multiply.by" if at_root else folder

URL = re.compile(r"https://[^\s<>\"']+")


def linked(s):
    """HTML-escape s; make each https:// address a link (trailing punctuation stays text)."""
    out, last = [], 0
    for m in URL.finditer(s):
        url = re.sub(r"[.,;:)\]]+$", "", m.group(0))
        if url == "https://":
            continue
        out.append(html.escape(s[last:m.start()]))
        out.append(f'<a href="{html.escape(url)}" target="_blank" rel="noopener">'
                   f"{html.escape(url)}</a>")
        last = m.start() + len(url)
    out.append(html.escape(s[last:]))
    return "".join(out)


STYLE = """
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { background: #f3f4f6; color: #111827;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif; }
#page { width: 100%; margin: 0 auto; min-height: 100vh; min-height: 100dvh; }
@media (min-width: 768px) { #page { width: min(720px, max(400px, 75vh)); } }
@media (min-width: 1024px) { #page { width: min(960px, 94vw); } }
#title-band { width: 100%; background: #fff; color: #2563eb; border-bottom: 1px solid #e5e7eb;
  padding: 0.35rem 0.5rem; display: flex; align-items: center; gap: 6px; }
#logo { flex: none; display: flex; align-items: center; justify-content: center;
  width: 40px; height: 40px; text-decoration: none; }
#logo svg { width: 38px; height: 38px; }
#title-band h1 { flex: 1; min-width: 0; margin: 0; font-weight: normal; line-height: 1.2;
  white-space: nowrap; overflow: hidden; text-align: center; font-size: 18px; }
#tagline { display: inline-block; color: inherit; text-decoration: none; }
#tagline:hover { color: #1e40af; }
#share-site { border: none; background: none; color: #2563eb; display: flex; align-items: center;
  justify-content: center; flex: none; padding: 4px; margin: 0; cursor: pointer;
  min-width: 30px; min-height: 30px; }
#share-site svg { width: 22px; height: 22px; }
#share-site:hover { color: #1e40af; }
main { padding: 12px; }
.bar { display: flex; align-items: center; gap: 8px; margin: 0 0 6px; }
.crumb { flex: 1; min-width: 0; margin: 0; font-size: 0.75rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em; color: #6b7280; overflow-wrap: anywhere; }
.crumb a { color: #1e40af; text-decoration: none; }
.crumb a:hover { text-decoration: underline; }
.box { position: relative; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; }
pre { margin: 0; padding: 10px 44px 10px 12px; white-space: pre-wrap; overflow-wrap: anywhere;
  font: 0.8125rem/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  color: #111827; }
pre a { color: #1e40af; font-weight: 700; text-decoration: none; }
pre a:hover { text-decoration: underline; }
.copy-btn { position: absolute; top: 4px; right: 4px; width: 32px; height: 32px; padding: 0;
  display: flex; align-items: center; justify-content: center; border: none;
  background: transparent; color: #6b7280; border-radius: 6px; cursor: pointer; }
.copy-btn svg { width: 16px; height: 16px; }
.copy-btn:hover, .copy-btn:focus-visible { background: #e5e7eb; color: #111827; outline: none; }
.copy-btn .ic-check { display: none; color: #15803d; }
.copy-btn.copied .ic-copy { display: none; }
.copy-btn.copied .ic-check { display: block; }
#toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); z-index: 50;
  background: #111827; color: #fff; font-size: 14px; padding: 8px 14px; border-radius: 8px;
  opacity: 0; pointer-events: none; transition: opacity 200ms; }
#toast.show { opacity: 1; }
"""

LOGO = ('<svg viewBox="0 0 24 24" width="38" height="38" aria-hidden="true"><path d="M3.5 3.5 '
        'L20.5 20.5 M20.5 3.5 L3.5 20.5" fill="none" stroke="#991b1b" stroke-width="3.4" '
        'stroke-linecap="round"/></svg>')
SHARE = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
         'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" '
         'r="3"/><path d="M8.6 13.5 L15.4 17.5 M15.4 6.5 L8.6 10.5"/></svg>')
COPY = ('<svg class="ic-copy" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<rect x="9" y="9" width="12" height="12" rx="2"/><rect x="3" y="3" width="12" '
        'height="12" rx="2"/></svg>')
CHECK = ('<svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M5 12.5 L10 17.5 L19 7"/></svg>')

# The site's share (layout.txt, SHARE THE SITE): the phone's share sheet, else copy the link.
SCRIPT = r"""
(function () {
  var SITE_LINK = 'https://multiply.by/build-it/';
  var MESSAGE = [
    'Multiply.by: times-table games, each built by AI from a few lines of text.',
    'Free and open source, no sign-up. See every game and its prompt, and build your own.',
    SITE_LINK
  ].join('\n');
  function fitTagline() {   // as on every page: the tagline fills the band, 10 to 28px
    var h1 = document.querySelector('#title-band h1'), t = document.getElementById('tagline');
    t.style.fontSize = '100px';
    var width = t.getBoundingClientRect().width;
    var cap = matchMedia('(max-height: 500px)').matches ? 18 : 28;
    if (!width) return;
    var size = Math.max(10, Math.min(cap, Math.floor(100 * h1.clientWidth / width * 10) / 10)) + 'px';
    t.style.fontSize = size;
    h1.style.fontSize = size;
  }
  fitTagline();
  window.addEventListener('resize', fitTagline);
  try { document.fonts.ready.then(fitTagline); } catch (e) {}
  var toast = document.getElementById('toast'), toastTimer = null;
  function say(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 1800);
  }
  function fallbackCopy(t) {
    var ta = document.createElement('textarea');
    ta.value = t;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:-1000px;left:-1000px;opacity:0';
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }
  async function copyText(t) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(t);
        return true;
      }
    } catch (e) {}
    return fallbackCopy(t);
  }
  document.getElementById('share-site').addEventListener('click', async function () {
    if (navigator.share) {
      try { await navigator.share({ title: 'multiply.by', text: MESSAGE }); return; }
      catch (e) { if (e && e.name === 'AbortError') return; }
    }
    if (await copyText(SITE_LINK)) say('Link copied: ' + SITE_LINK);
  });
  var btn = document.getElementById('copy'), text = document.getElementById('text').textContent;
  var timer = null;
  btn.addEventListener('click', async function () {
    if (!(await copyText(text))) return;
    btn.classList.add('copied');
    btn.title = 'Copied';
    btn.setAttribute('aria-label', 'Copied');
    say('Prompt copied');
    clearTimeout(timer);
    timer = setTimeout(function () {
      btn.classList.remove('copied');
      btn.title = 'Copy prompt';
      btn.setAttribute('aria-label', 'Copy prompt');
    }, 1500);
  });
})();
"""

sys.stdout.write(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="/icon.svg">
<title>{html.escape(title)} – Multiply.by</title>
<style>{STYLE}</style>
</head>
<body>
<div id="page">
<header id="title-band">
<a id="logo" href="https://multiply.by/" aria-label="multiply.by home" title="multiply.by home">{LOGO}</a>
<h1><a id="tagline" href="https://multiply.by/"><strong>Multiply.by:</strong> learn the multiplication table</a></h1>
<button type="button" id="share-site" aria-label="Share multiply.by" title="Share multiply.by">{SHARE}</button>
</header>
<main>
<div class="bar"><p class="crumb"><a href="../">{html.escape(crumb)}</a> / prompt.txt</p></div>
<div class="box">
<button type="button" class="copy-btn" id="copy" aria-label="Copy prompt" title="Copy prompt">{COPY}{CHECK}</button>
<pre id="text">{linked(text)}</pre>
</div>
</main>
</div>
<div id="toast" role="status" aria-live="polite"></div>
<script>{SCRIPT}</script>
</body>
</html>
""")

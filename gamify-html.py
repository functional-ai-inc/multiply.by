#!/usr/bin/env python3
"""Make gamify/index.html (https://multiply.by/gamify/): ONE self-contained file for building a
gamified game in any chatbot.

Usage: gamify-html.py gamify.md grid.md orders.txt base/prompt.txt > gamify/index.html
       gamify-html.py --text gamify.md grid.md orders.txt base/prompt.txt   (as plain text)

The files before the last are gamify.md, then grid.md (the games grid that gamify.md's "You Won!"
rule refers to) and orders.txt (the order of its tiles, plain text, shown as written), so the page
needs nothing else from the web; each is rendered in turn.
The page is gamify.md rendered as HTML by markdown-it (the Debian package python3-markdown-it),
then the base build instructions, copied unchanged. The base file is plain text, NOT Markdown
(Markdown rules would turn its indented lists into code blocks): each title line underlined with
----- or ===== becomes an <h2>, and the text between is shown exactly as written, line breaks and
indents kept, in the page's font. Any HTML written in either file is shown as text, never used as
markup. A person uploads it (or a chat fetches it) with a line or two
saying what game they want, and needs nothing else from the web. It is a web page, not .txt, because Gemini's web app refuses
a .txt upload but takes an .html one. The browser-tab title is "Gamifying Multiply.by Base Game".

--text prints the same content with gamify.md as Markdown source: what mk-gamify sends a model
as the fetched page (a fetch tool turns a page into text).
"""
import html
import re
import sys

from markdown_it import MarkdownIt

args = sys.argv[1:]
as_text = args[:1] == ["--text"]
if as_text:
    args = args[1:]
texts = [open(p, encoding="utf-8").read() for p in args]
# A .txt file among the guide files (orders.txt) is plain text, not Markdown: in Markdown it is put
# in a fence, so its lines stay lines; on the page it is shown as written.
guide_parts = [("```text\n" + t.strip() + "\n```") if p.endswith(".txt") else t.strip()
               for p, t in zip(args[:-1], texts[:-1])]
guide, base = "\n\n".join(guide_parts) + "\n", texts[-1]
BASE_HEADING = "The base build instructions"
BASE_INTRO = ("The complete base build instructions (https://multiply.by/base/prompt.txt), "
              "copied unchanged. Everything from here to the end of this file is that one file.")

if as_text:
    sys.stdout.write(f"{guide.strip()}\n\n\n# {BASE_HEADING}\n\n{BASE_INTRO}\n\n{base}")
    sys.exit()

STYLE = """
body { margin: 0 auto; max-width: 52rem; padding: 1rem 16px 3rem; background: #fff; color: #1a1a1a;
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; overflow-wrap: anywhere; }
h1, h2, h3 { line-height: 1.25; margin: 1.6em 0 0.5em; }
a { color: #1e40af; }
code { font: 0.9em ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; background: #f3f3f3;
  padding: 0.1em 0.3em; border-radius: 3px; }
pre { background: #f6f6f6; border: 1px solid #e3e3e3; border-radius: 6px; padding: 0.8em 1em;
  white-space: pre-wrap; font: 0.88em/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
pre code { background: none; padding: 0; font: inherit; }
.plain { white-space: pre-wrap; font-size: 0.94rem; }
@media (prefers-color-scheme: dark) {
  body { background: #161616; color: #e6e6e6; }
  a { color: #93c5fd; }
  code, pre { background: #222; border-color: #333; }
}
"""
# No page footer: the base spec at the end already ends with the copyright notice.
# No HTML passes through: a tag written in the text ("an <img>, <svg> or <div>") is shown as text.
body = MarkdownIt("commonmark", {"html": False}).enable("table").render(guide)
# The base file: an <h2> for each underlined title, the text between as written.
parts = re.split(r"^(\S[^\n]*)\n(?:-{3,}|={3,})\n", base, flags=re.M)
spec = "" if not parts[0].strip() else f'<div class="plain">{html.escape(parts[0].strip(chr(10)))}</div>\n'
for title, text in zip(parts[1::2], parts[2::2]):
    spec += f"<h2>{html.escape(title)}</h2>\n"
    if text.strip():
        spec += f'<div class="plain">{html.escape(text.strip(chr(10)))}</div>\n'

sys.stdout.write(
    '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    f"<title>Gamifying Multiply.by Base Game</title>\n<style>{STYLE}</style>\n"
    f"{body}\n<h1>{BASE_HEADING}</h1>\n<p>{html.escape(BASE_INTRO)}</p>\n"
    f"{spec}\n</html>\n")

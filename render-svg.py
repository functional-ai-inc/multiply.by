#!/usr/bin/env python3
"""Render an SVG to a square PNG with Chromium (keeps gradients, shadows and text, which
ImageMagick's own renderer drops). Used for the web app's icons (head.txt).

Usage: render-svg.py IN.svg OUT.png SIZE
"""
import sys

from playwright.sync_api import sync_playwright

src, out, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
svg = open(src, encoding="utf-8").read()
html = ("<!doctype html><html><head><style>html,body{margin:0;background:transparent}"
        f"svg{{display:block;width:{size}px;height:{size}px}}</style></head><body>{svg}</body></html>")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": size, "height": size})
    pg.set_content(html)
    pg.screenshot(path=out, omit_background=True)
    b.close()

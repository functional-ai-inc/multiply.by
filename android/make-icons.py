#!/usr/bin/env python3
"""Makes the app's icon files from one design: an orange-to-crimson "x" with a soft shadow on a
peach background (the drafts' "3e", chosen on 2026-11-27).

Usage: python3 make-icons.py   (needs Playwright with Chromium, for the shadow and gradients)

Writes (all tracked in git; run it again after changing the design below):
  icon.svg                                  the whole icon, 512 x 512: the design's source,
                                            and the store icon (store-assets.py renders it)
  app/src/main/res/drawable/ic_launcher_background.xml   the peach gradient (a vector)
  app/src/main/res/mipmap-*/ic_launcher_foreground.png   the x with its shadow, on nothing:
                                            Android 8+ puts it over the background and crops both
                                            to the launcher's shape (108 dp canvas, 72 dp shown)
  app/src/main/res/drawable/ic_launcher_monochrome.xml   the x alone, one color, for Android 13's
                                            themed icons
  app/src/main/res/mipmap-*/ic_launcher.png  the whole icon, square, for Android 7 and older
"""
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "app", "src", "main", "res")

# The design, in a 512 x 512 square.
BACK_TOP, BACK_BOTTOM = "#ffedd5", "#fed7aa"      # peach, top to bottom
X_START, X_END = "#f97316", "#be123c"             # the x: orange (top left) to crimson
X_FROM, X_TO, X_WIDTH = 170, 342, 56              # its strokes' ends and width
SHADOW = 0.3                                      # the shadow's opacity (10 below, blur 10)

DEFS = (f'<linearGradient id="x" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{X_START}"/>'
        f'<stop offset="1" stop-color="{X_END}"/></linearGradient>'
        f'<filter id="s" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy="10" '
        f'stdDeviation="10" flood-opacity="{SHADOW}"/></filter>')
X = (f'<path d="M{X_FROM} {X_FROM} L{X_TO} {X_TO} M{X_TO} {X_FROM} L{X_FROM} {X_TO}" fill="none" '
     f'stroke="url(#x)" stroke-width="{X_WIDTH}" stroke-linecap="round" filter="url(#s)"/>')
BACK = (f'<linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BACK_TOP}"/>'
        f'<stop offset="1" stop-color="{BACK_BOTTOM}"/></linearGradient>')

ICON = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><defs>{BACK}{DEFS}</defs>'
        f'<rect width="512" height="512" fill="url(#b)"/>{X}</svg>\n')
# The adaptive icon's foreground: a 108 dp canvas of which the launcher shows the middle 72 dp, so
# the 512 square is the middle two thirds of a 768 canvas (as in the drafts, the x then fills
# the same share of the icon).
FOREGROUND = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-128 -128 768 768"><defs>{DEFS}</defs>'
              f'{X}</svg>')

DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


def dp(u):
    """A point of the 512 square, in the adaptive icon's 108 dp canvas (72 dp shown, from 18)."""
    return round(18 + u * 72 / 512, 2)


BACKGROUND_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<!-- Made by make-icons.py: the icon's peach background, top to bottom over the shown 72 dp. -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:pathData="M0,0h108v108h-108z">
        <aapt:attr name="android:fillColor">
            <gradient
                android:type="linear"
                android:startX="54"
                android:startY="18"
                android:endX="54"
                android:endY="90"
                android:startColor="#FF{BACK_TOP[1:].upper()}"
                android:endColor="#FF{BACK_BOTTOM[1:].upper()}" />
        </aapt:attr>
    </path>
</vector>
"""

a, b = dp(X_FROM), dp(X_TO)
MONOCHROME_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<!-- Made by make-icons.py: the x alone, for Android 13's themed icons (the launcher colors it). -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:pathData="M{a},{a} L{b},{b} M{b},{a} L{a},{b}"
        android:strokeColor="#FF000000"
        android:strokeWidth="{round(X_WIDTH * 72 / 512, 2)}"
        android:strokeLineCap="round" />
</vector>
"""


def render(page, svg, size, path, transparent):
    page.set_viewport_size({"width": size, "height": size})
    page.set_content('<html><body style="margin:0;background:transparent">'
                     f'<div style="width:{size}px;height:{size}px">'
                     + svg.replace("<svg ", '<svg width="100%" height="100%" ', 1) + "</div></body></html>")
    page.screenshot(path=path, omit_background=transparent)
    print(os.path.relpath(path, HERE))


def main():
    os.makedirs(os.path.join(RES, "drawable"), exist_ok=True)
    with open(os.path.join(HERE, "icon.svg"), "w") as f:
        f.write(ICON)
    with open(os.path.join(RES, "drawable", "ic_launcher_background.xml"), "w") as f:
        f.write(BACKGROUND_XML)
    with open(os.path.join(RES, "drawable", "ic_launcher_monochrome.xml"), "w") as f:
        f.write(MONOCHROME_XML)
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        for name, scale in DENSITIES.items():
            folder = os.path.join(RES, f"mipmap-{name}")
            os.makedirs(folder, exist_ok=True)
            render(page, FOREGROUND, round(108 * scale),
                   os.path.join(folder, "ic_launcher_foreground.png"), True)
            render(page, ICON, round(48 * scale), os.path.join(folder, "ic_launcher.png"), False)


if __name__ == "__main__":
    main()

SPEC  = base/prompt.txt
PWA   = PWA-build.txt
FILES = manifest.webmanifest sw.js pwa.js icon.svg og-image.svg
ICONS = icon-192.png icon-512.png

# Every page's prompt as a web page too: FOLDER/prompt.txt -> FOLDER/prompt/index.html
# (https://multiply.by/FOLDER/prompt/), and the front page's prompt.txt -> prompt/index.html.
PROMPT_PAGES = $(sort prompt/index.html base/prompt/index.html \
  $(patsubst %/prompt.txt,%/prompt/index.html,$(wildcard */prompt.txt)))

all: gamify/index.html android/index.html chat-gpt-local.html privacy/index.html privacy/website/index.html selector/prompt/index.html grid/prompt/index.html base/index.html index.html $(FILES) $(ICONS) og-image.png sitemap.xml \
  $(PROMPT_PAGES)

prompt-pages: $(PROMPT_PAGES)
.PHONY: all prompt-pages

# THE BASE GAME (https://multiply.by/base/)
# Its complete prompt (base/prompt.txt, the file its SOURCE links to): game.txt with the
# site's shared layout.txt put in at its "#include layout.txt" line.
$(SPEC): game.txt layout.txt assemble-spec
	mkdir -p base
	./assemble-spec game.txt > $(SPEC).tmp
	mv $(SPEC).tmp $(SPEC)

# https://multiply.by/gamify/: ONE file for building a GAMIFIED game in any chatbot: gamify.md,
# grid.md (the games grid on "You Won!") and orders.txt (its order), then the base game's complete
# prompt, HTML-escaped in a <pre> (Gemini's web app refuses a .txt upload but takes an .html one).
# No AI model involved.
gamify/index.html: gamify.md grid.md orders.txt $(SPEC) gamify-html.py
	mkdir -p gamify
	python3 gamify-html.py gamify.md grid.md orders.txt $(SPEC) > gamify/index.html.tmp
	mv gamify/index.html.tmp gamify/index.html

# The prompt pages: the prompt.txt text, exactly, in a box with a copy button (txt-html.py). No AI model.
prompt/index.html: prompt.txt txt-html.py
	mkdir -p prompt
	python3 txt-html.py prompt.txt > prompt/index.html.tmp
	mv prompt/index.html.tmp prompt/index.html

$(filter-out prompt/index.html,$(PROMPT_PAGES)): %/prompt/index.html: %/prompt.txt txt-html.py
	mkdir -p $(@D)
	python3 txt-html.py $< > $@.tmp
	mv $@.tmp $@

# https://multiply.by/android/: the Android app notes, ANDROID.md rendered as a page. No AI model.
android/index.html: ANDROID.md md-html.py
	mkdir -p android
	python3 md-html.py ANDROID.md > android/index.html.tmp
	mv android/index.html.tmp android/index.html

# https://multiply.by/chat-gpt-local.html: how Claude Code on the owner's desktop (with Claude in
# Chrome) builds the ChatGPT games (trains, planes, space, building, evolution), chat-gpt-local.md
# rendered as a page. No AI model.
chat-gpt-local.html: chat-gpt-local.md md-html.py
	python3 md-html.py chat-gpt-local.md > chat-gpt-local.html.tmp
	mv chat-gpt-local.html.tmp chat-gpt-local.html

# https://multiply.by/privacy/: the privacy policy (the app's Play listing links to it), PRIVACY.md
# rendered as a page. No AI model.
privacy/index.html: PRIVACY.md md-html.py
	mkdir -p privacy
	python3 md-html.py PRIVACY.md > privacy/index.html.tmp
	mv privacy/index.html.tmp privacy/index.html

# https://multiply.by/privacy/website/: the website's own privacy policy (footer link), PRIVACY-WEBSITE.md
privacy/website/index.html: PRIVACY-WEBSITE.md md-html.py
	mkdir -p privacy/website
	python3 md-html.py PRIVACY-WEBSITE.md > privacy/website/index.html.tmp
	mv privacy/website/index.html.tmp privacy/website/index.html

# The plain game page, built from base/prompt.txt (no PWA) by the model named in the
# file "model" (carbon, fable, ...; see run-model).
build/index.html: $(SPEC) model run-model
	mkdir -p build
	./run-model $(SPEC) build/index.html

# THE FRONT PAGE (https://multiply.by/): one of the games (now Dots) with a strip of the other games.
# prompt.txt, at the site's root (tracked; SOURCE opens it as /prompt/), is its whole prompt:
# "Use" lines for the game's prompt page (https://multiply.by/dots/prompt/), /gamify (gamify.md,
# grid.md and the base prompt) and selector.md (https://multiply.by/selector/prompt/: the strip
# and the few changes it makes). run-model --fetch sends it with the full text of each, as a
# chat's fetch would (mk-gamify's linked_files/message), to the model named in home-model.
# (The games chooser is /games/, built in games/.)
# https://multiply.by/selector/prompt/: selector.md rendered as a page (md-html.py). No AI model.
selector/prompt/index.html: selector.md md-html.py
	mkdir -p selector/prompt
	python3 md-html.py selector.md > selector/prompt/index.html.tmp
	mv selector/prompt/index.html.tmp selector/prompt/index.html

# https://multiply.by/grid/prompt/: grid.md (the games grid: "You Won!" screens and the games page)
# rendered as a page (md-html.py). No AI model.
grid/prompt/index.html: grid.md md-html.py
	mkdir -p grid/prompt
	python3 md-html.py grid.md > grid/prompt/index.html.tmp
	mv grid/prompt/index.html.tmp grid/prompt/index.html

# build/home/ so that its build.txt does not overwrite the base game's build/build.txt.
build/home/index.html: prompt.txt dots/prompt.txt dots/prompt/index.html gamify/index.html \
  selector.md selector/prompt/index.html orders.txt home-model run-model
	mkdir -p build/home
	./run-model --fetch prompt.txt build/home/index.html home-model

# PWA files, copied verbatim from PWA-build.txt.
$(FILES) &: $(PWA) extract-files.py
	python3 extract-files.py $(PWA) . $(FILES)

build/pwa-head.html: $(PWA) extract-files.py
	python3 extract-files.py $(PWA) build pwa-head.html

# Every served file is written under a temporary name and renamed into place,
# so a visitor never gets a half-written page.

# The served pages: the plain page with the PWA tags inserted before </head>.
base/index.html: build/index.html build/pwa-head.html check-scripts.py
	test "$$(grep -c "</head>" build/index.html)" = 1
	sed "/<\/head>/e cat build/pwa-head.html" build/index.html > base/index.html.tmp
	python3 check-scripts.py base/index.html.tmp
	mv base/index.html.tmp base/index.html

index.html: build/home/index.html build/pwa-head.html check-scripts.py
	test "$$(grep -c "</head>" build/home/index.html)" = 1
	sed "/<\/head>/e cat build/pwa-head.html" build/home/index.html > index.html.tmp
	python3 check-scripts.py index.html.tmp
	mv index.html.tmp index.html

# App icons, rendered from icon.svg.
icon-%.png: icon.svg
	convert -background none -density 300 icon.svg -resize $*x$* -depth 8 -strip $@.tmp.png
	mv $@.tmp.png $@

# Link preview picture (Open Graph), rendered from og-image.svg.
og-image.png: og-image.svg
	convert -background none -density 96 og-image.svg -depth 8 -strip og-image.tmp.png
	mv og-image.tmp.png og-image.png

# sitemap.xml for search engines (robots.txt points to it): the public pages, each dated by its
# index.html. Remade on every make (it takes a moment); it never depends on a page, so making it
# never starts a page build. Pages are listed in make-sitemap.py.
sitemap.xml:
	python3 make-sitemap.py > sitemap.xml.tmp
	mv sitemap.xml.tmp sitemap.xml

.PHONY: all sitemap.xml

# The Games page (https://multiply.by/games/), built from page.txt by the model named in "model"
# (opus) with ../run-model --fetch: the page's prompt plus grid.md (its "Use
# https://multiply.by/grid/prompt/" line), as a chat's fetch would give it.
# The page is written under a temporary name and renamed into place,
# so a visitor never gets a half-written page.

index.html: prompt.txt ../grid.md ../grid/prompt/index.html ../orders.txt model ../check-scripts.py
	../run-model --fetch prompt.txt build/index.html
	python3 ../check-scripts.py build/index.html
	cp build/index.html index.html.tmp
	mv index.html.tmp index.html

# The page's complete build instructions (the file SOURCE links to): page.txt with the
# site's shared layout.txt put in at its "#include layout.txt" line.
prompt.txt: page.txt ../layout.txt ../footer.txt ../assemble-spec
	../assemble-spec page.txt > prompt.txt.tmp
	mv prompt.txt.tmp prompt.txt

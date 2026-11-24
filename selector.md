# selector: the games strip of the front page

The front page of Multiply.by (https://multiply.by/) plays ONE of the site's games: THE GAME, the
one whose prompt the front page's prompt names (now Dots: https://multiply.by/dots/prompt/, played
on its own page at https://multiply.by/dots/). Build THE GAME exactly as its prompt says, with ONE
addition: a strip of the site's other games under the answers, so a child starts playing at once
and still sees the other games. This file describes the strip and the few changes it makes. Same
CONFIG and same storage keys as THE GAME's own page, so the progress is shared. Where this file
and THE GAME's prompt disagree, this file wins.

## Changes to the game

- **Address**: this page is played at https://multiply.by/. Every address of THE GAME's own page
  (https://multiply.by/dots/, and https://multiply.by/base/ in the base game's prompt) is
  https://multiply.by/ on this page: the share link, `?both`, `?12` and `?20`, and the rest.
- **SOURCE** on this page: `<a href="https://multiply.by/prompt/">` (the front page's own prompt,
  not THE GAME's).
- **Menu**: as in THE GAME's prompt, with HOME as the current page (`aria-current="page"`). The
  games strip and its More games tile are also a way to the other games.
- **The games grid on "You Won!"** (if THE GAME has one): THE GAME's tile is the one marked "Play
  again", although this page's address is https://multiply.by/.
- **The front page always opens ready to play**: it is HOME, so the logo, the title band and HOME
  (which all open https://multiply.by/) must lead to a game, never back to "You Won!". At
  start-up, if the saved progress is a game already WON (every fact learned, on this page or on
  THE GAME's own page, which share it), do NOT show "You Won!": start a new game exactly as Play
  Again does (the best score kept). An unfinished game is restored as usual.
- **Loading from the server**: the strip's small pictures (the `<img>` elements below) and the
  grid's thumbnails are the ONLY things this page loads from the server. Nothing else changes: no
  fetch, no other file. The game works without them (offline, or if a picture fails): a picture
  that fails to load is hidden (`onerror` sets its `visibility: hidden`), the tile and its name
  stay.
- **No page scroll, fits one screen**: everything THE GAME's prompt says about the whole UI
  fitting on one screen with no scroll (360x640, landscape, tablets, desktop) now includes the
  strip: title band, menu bar, game area, strip and footer all fit, and the page itself still
  never scrolls. The game area is what gives up the room: it keeps `flex: 1; min-height: 0`; its
  pictures (the scene, the mascot, the dot array) shrink and the answer buttons become shorter,
  but every indicator stays whole and nothing overlaps the answers.

## The games strip

- A `<nav id="games-strip" aria-label="More games">` in the app container, directly AFTER
  `#game-area` and BEFORE the footer: `flex-shrink: 0`, outside `#game-area` (a tap on it never
  answers, never starts the timer), background #f9fafb, a 1px #e5e7eb top border,
  `padding: 6px 8px`.
- One row of TILES, never wrapping: `display: flex; gap: 8px; overflow-x: auto; overflow-y: hidden;
  overscroll-behavior-x: contain; touch-action: pan-x; scrollbar-width: none;` (and
  `#games-strip::-webkit-scrollbar { display: none; }`). It scrolls sideways INSIDE ITSELF when
  the tiles do not fit (a phone shows about three and a half, the half tile saying there is more);
  the page never scrolls.
- **With a mouse** (inside `@media (hover: hover)`): the strip shows a thin scrollbar
  (`scrollbar-width: thin`, and for WebKit `#games-strip::-webkit-scrollbar { display: block;
  height: 6px; }` with a #d1d5db rounded thumb), and the mouse wheel scrolls it sideways: a
  `wheel` listener on the strip (`{ passive: false }`) that, when the wheel moves up or down
  (`Math.abs(e.deltaY) > Math.abs(e.deltaX)`) and the strip can scroll, adds `e.deltaY` to its
  `scrollLeft` and calls `e.preventDefault()`.
- **Tile**: `<a class="strip-tile" href="GAME ADDRESS">`, the whole tile one link, no underline:
  `flex: 0 0 88px`, a flex column with `gap: 3px`, white, a 1px #e5e7eb border, 10px rounded
  corners, `padding: 4px`, a soft shadow (`0 1px 2px rgba(0,0,0,0.08)`), a clear focus outline for
  the keyboard; on hover (inside `@media (hover: hover)`) the border turns #3b82f6. Inside, from
  top to bottom:
  1. NAME: the game's SHORT NAME from the strip games below (the grid's list), exactly as
     written, 12px, bold, #111827, centered, `line-height: 1.2`, one line (`white-space: nowrap;
     overflow: hidden; text-overflow: ellipsis`).
  2. PICTURE: `<img src="PICTURE" alt="" width="80" height="64">`, `display: block; width: 100%;
     height: auto; aspect-ratio: 5 / 4; object-fit: cover; border-radius: 6px;` (`alt=""` because
     the name is already the tile's text). The pictures are thumbnails, 200 x 160 (5:4): one
     simple picture of the game (a locomotive, the monster, a dinosaur), not a screenshot.
- The LAST TILE is always MORE GAMES: the same tile, name "More games", linking to
  https://multiply.by/games/, with an inline SVG in place of the picture (same 5:4 box, background
  #eff6ff, 6px rounded corners): four rounded squares in a 2 x 2 grid, #3b82f6, centered, about
  half the box's height.
- **Wider screens** (`@media (min-width: 768px) and (min-height: 600px)`, as the menu bar): tiles
  `flex: 0 0 108px`, names 14px.
- **Short screens** (`@media (max-height: 500px)`, e.g. a phone on its side): no pictures (the
  `<img>` and the SVG are `display: none`); each tile is a name-only chip: `flex: 0 0 auto;
  height: 28px; padding: 0 10px; justify-content: center;`, name 12px. The strip's padding is
  `4px 8px`.

## The order of the strip

Set once when the page opens, never changed while it is open: tiles never move under a child's
finger.

1. The LAST GAME the child opened first: the key saved in localStorage under
   `multiply_last_game` (read with the page's safe storage; if it is missing, or is not the key of
   a game in the strip games, skip this step).
2. Then the other games in the order of ORDERS (https://multiply.by/orders.txt), each only if
   not already placed (and never THE GAME) and never shuffled, so each game keeps its place.
3. MORE GAMES last.

- A tap on a game tile (a `click` listener; the link opens the game as usual) saves that game's
  key under `multiply_last_game` (with the safe storage: if storage fails, the link still works).
  The games page does the same, so a game picked there comes first here too.
- The tiles are made by the script from one list (the strip games below), names set with
  `textContent`.

## Strip games

The strip's games are THE GAMES of the games grid (https://multiply.by/grid/prompt/): every game
of its list except THE GAME, eleven in all (Base Game included), each with its short name, key,
game address and THUMBNAIL (the strip's PICTURE). The strip uses only that list from the grid
file: its tiles and layout are the ones described here, its order the one above.

## Checks (in addition to THE GAME's)

- At 360x640, 640x360, 768x1024 and 1280x800: the title band, menu bar, question, four answers,
  strip and footer are all on screen, nothing cut off, and the page does not scroll by a pixel.
  Every indicator is whole and ends above the answers.
- On a computer, the mouse wheel over the strip scrolls it sideways to More games.
- The strip shows the eleven games and then More games; on a phone it scrolls sideways inside
  itself; in landscape it shows name-only chips.
- On a first visit (nothing saved under `multiply_last_game`), the strip is in the order of
  ORDERS; reloading the page never changes it.
- After tapping Train in the strip and coming back, Train is the first tile.
- A tap on a strip tile opens that game; it never counts as an answer or starts the timer.
- The menu bar shows MUTE, the GAMES icon, BUILD IT, SOURCE and the menu button on one line at
  360px, nothing cut off; BUILD IT opens https://multiply.by/build-it/; SOURCE opens
  https://multiply.by/prompt/; the menu panel holds HOME (current), GAMES, ABOUT, RULES and RESET.
- The page's addresses (share link, `?both`, `?12`, `?20`) are https://multiply.by/, never THE
  GAME's own address.
- Progress is shared with THE GAME's own page: facts learned here count there too.
- After winning (here or on THE GAME's own page), tapping the logo, the title band or HOME opens
  a new game with its first question, not "You Won!"; the best score is kept.

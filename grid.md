# grid: the games grid of Multiply.by

A grid of the site's games, one tile per game, for a child to pick the next game to play. It is
used in two places, described at the end:

- the **"You Won!" screen** of every game (under the stage pictures): the other games, with
  small pictures;
- the **games page** (https://multiply.by/games/): every game, with big screenshots.

Build the grid exactly as this file describes. The page that uses it says which of the two it is.

## The tile

- The whole tile is ONE link to the game: `<a class="game-tile" href="GAME ADDRESS">`, no
  underline, no other links or buttons inside it.
- White, a 1px #e5e7eb border, 12px rounded corners, a soft shadow (`0 1px 3px
  rgba(0,0,0,0.1)`), `padding: 6px`, a flex column with `gap: 6px`. On hover and focus it lifts
  slightly (`transform: translateY(-2px)`, a stronger shadow, 0.15s; none when the user prefers
  reduced motion), and it has a clear focus outline for the keyboard.
- Inside, from top to bottom:
  1. NAME: the game's SHORT NAME from the games list below, exactly as written (on "You Won!",
     this game's tile says "Play again" instead), centered, bold, #111827, `line-height: 1.25`,
     one line (`white-space: nowrap; overflow: hidden; text-overflow: ellipsis`).
  2. PICTURE: an `<img>` with `alt=""` (the name is already the tile's text), `display: block;
     width: 100%; height: auto; aspect-ratio: 5 / 4; object-fit: cover;`, 8px rounded corners.
     Which picture (thumbnail or screenshot) depends on where the grid is used, see below. Both
     are 5:4. The image keeps its 5:4 space while it loads; if it fails to load (offline, for
     example) it is hidden (`onerror` sets its `visibility: hidden`), and the tile and its name
     stay. Its `src` is the FULL address from the list below (https://multiply.by/...), so it
     loads also in a page opened from a downloaded file. Every tile has its picture: NEVER put
     emoji, icons, drawings or text-only links in place of the pictures.
- The names are written into the page from the games list below (with `textContent` when the
  script makes the tiles): the page reads nothing from the games (no fetch). The pictures are the
  only files the grid loads.
- LAST GAME: a tap on a tile (a `click` listener on each tile; the link opens the game as usual)
  saves the game's KEY in localStorage under `multiply_last_game` (in try/catch: if storage fails,
  the link still opens the game). The front page puts that game first in its strip.

## The games

| Short name  | Key       | Storage name         | Game address                   | Thumbnail (200 x 160)                                  | Screenshot (412 x 330)                     |
|-------------|-----------|----------------------|--------------------------------|--------------------------------------------------------|--------------------------------------------|
| Monster     | monster   | monster              | https://multiply.by/monster/   | https://multiply.by/thumbnails/monster-thumbnail.png   | https://multiply.by/build-it/monster.png   |
| Trains      | trains    | multiply-express     | https://multiply.by/trains/    | https://multiply.by/thumbnails/trains-thumbnail.png    | https://multiply.by/build-it/trains.png    |
| Dinosaurs   | dino      | dino                 | https://multiply.by/dino/      | https://multiply.by/thumbnails/dino-thumbnail.png      | https://multiply.by/build-it/dino.png      |
| Robot       | robot     | robot                | https://multiply.by/robot/     | https://multiply.by/thumbnails/robot-thumbnail.png     | https://multiply.by/build-it/robot.png     |
| Planes      | planes    | flight               | https://multiply.by/planes/    | https://multiply.by/thumbnails/planes-thumbnail.png    | https://multiply.by/build-it/planes.png    |
| Space       | space     | starhop              | https://multiply.by/space/     | https://multiply.by/thumbnails/space-thumbnail.png     | https://multiply.by/build-it/space.png     |
| Chinese     | chinese   | wall                 | https://multiply.by/chinese/   | https://multiply.by/thumbnails/chinese-thumbnail.png   | https://multiply.by/build-it/chinese.png   |
| Block Craft | blocks    | blockcraft           | https://multiply.by/blocks/    | https://multiply.by/thumbnails/blocks-thumbnail.png    | https://multiply.by/build-it/blocks.png    |
| Evolution   | evolution | evolution            | https://multiply.by/evolution/ | https://multiply.by/thumbnails/evolution-thumbnail.png | https://multiply.by/build-it/evolution.png |
| Buildings   | building  | buildingsthroughtime | https://multiply.by/building/  | https://multiply.by/thumbnails/building-thumbnail.png  | https://multiply.by/build-it/building.png  |
| Dot Array   | dots      | dots                 | https://multiply.by/dots/      | https://multiply.by/thumbnails/dots-thumbnail.png      | https://multiply.by/build-it/dots.png      |
| Base Game   | base      | Multiply             | https://multiply.by/base/      | https://multiply.by/thumbnails/base-thumbnail.png      | https://multiply.by/build-it/base.png      |

Twelve games. Base Game is the plain game all the others are built from. The STORAGE NAME is the
game's `CONFIG.GAME`: it saves its best score (in the 2 to 9 mode) in localStorage under
`'openlang_Math_' + STORAGE NAME + '_best_score'`, for example `openlang_Math_dots_best_score`.

## On the "You Won!" screen of a game

- At the END of the "You Won!" panel, after everything already on it (the stage pictures, the
  score, the buttons such as Play Again, and the lines under them), so Play Again is seen first: a
  heading "Play another game" (bold, about 1.1rem, #111827), then the grid, and nothing after it:
  NO "More games" link (the grid already shows every game). The same after "Practice done!".
- TILES: ALL TWELVE games of the list, THIS game included. This game's tile (the one whose
  address is this page's address, compared by `location.pathname`) has a small green check badge
  (#16a34a, white check, 20px circle) on the top right corner of its PICTURE, never over the name,
  and the name "Play again"; a tap on it starts this game over, like Play Again (no page load).
  On a page that is none of them, such as a game built elsewhere, all twelve with no badge.
- ORDER: the order of ORDERS (https://multiply.by/orders.txt), never shuffled; this game's
  tile stays where the order puts it.
- PICTURES: the thumbnails, `<img src="THUMBNAIL" alt="" width="200" height="160"
  loading="lazy">`. Names 13px.
- COLUMNS: three on phones (`display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;`),
  so twelve tiles are four full rows. Wider screens (`@media (min-width: 768px) and (min-height:
  600px)`): four columns, three full rows, the grid at most 560px wide and centered, names 14px.
- SHORT SCREENS (`@media (max-height: 500px)`, e.g. a phone on its side): ONE row that scrolls
  sideways inside itself (`display: flex; overflow-x: auto; overflow-y: hidden;
  overscroll-behavior-x: contain;`), tiles `flex: 0 0 96px`.
- The "You Won!" panel is OPAQUE (a solid background, e.g. white): nothing of the game shows
  through it, at any size.
- The "You Won!" panel may now be taller than the screen: it scrolls inside itself
  (`overflow-y: auto; max-height: 100%`, `overscroll-behavior: contain`), the page behind it
  still never scrolls. The panel opens scrolled to its top ("You Won!" and the stage pictures).
- The thumbnails are the only files the game loads from the server, and only when "You Won!"
  opens (`loading="lazy"`); the game itself still needs nothing from the server.

## On the games page

- TILES: all twelve games, in the order of ORDERS (https://multiply.by/orders.txt).
- SCORE LINE: under the picture, ONE line with the game's best score and the current game's
  mistakes, centered, `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`, 0.7rem on
  phones (narrower than 640px), 0.8rem on tablets (640px to 1023px), 0.9rem on laptops and wider:
  "Best: 990 · Mistakes: 3". It is two spans with " · "
  between them (#9ca3af), each set with `textContent`, read when the page opens with the page's
  safe storage, in try/catch:
  - BEST: "Best: 990" (bold, #15803d), from the game's best score key (see STORAGE NAME above).
    A game with no best score yet (no game finished: the key is missing or not a number) shows,
    in its place, "Correct: N" (#6b7280, normal weight; never "Best: –"): N is the number of
    questions answered right in the saved progress, the length of its `learnedIds` array (0 if
    it is not an array).
  - MISTAKES: "Mistakes: 3" (#6b7280), the `mistakes` field of the game's saved progress,
    `'openlang_Math_' + STORAGE NAME + '_progress'` (JSON, `JSON.parse` in try/catch): the game
    being played, or the last one finished (Play Again clears it). No saved progress, or
    `mistakes` not a number: "Mistakes: 0".
  NOT PLAYED: a game with neither a best score nor saved progress (both keys missing or not
  usable) shows only "No results" (#9ca3af, normal weight) on the line, in place of both spans.
  Every tile has the line, so the tiles stay the same height.
- PICTURES: the screenshots, `<img src="SCREENSHOT" alt="" width="412" height="330"
  loading="lazy">` (a picture of the game's own scene: the question, the mascot or scene and the
  progress picture, without the menu and the answers). Names 1.05rem (1.2rem on laptops).
- COLUMNS: CSS grid with 12px gaps and 12px of space at the sides: two columns on phones
  (narrower than 640px), three on tablets (640px to 1023px), four on laptops and wider
  (`@media (min-width: 1024px)`).

## Checks

- "You Won!" at 360x640: the stage pictures, score and Play Again as before, then the heading,
  twelve tiles in four rows of three (this game's with the check badge and "Play again"),
  reachable by scrolling the panel, and no "More games" link after them; the page itself does not
  scroll. At 640x360: one sideways-scrolling row. At 768x1024 and 1280x800: three columns, at most 420px wide.
- Games page: twelve tiles, two columns at 360px, three at 768px, four at 1280px, no sideways
  scroll at any width, nothing cut off.
- A tap anywhere on a tile opens its game and saves its key under `multiply_last_game`.
- Games page: with Dot Array won with 990 points and its saved progress at 3 mistakes, its tile says
  "Best: 990 · Mistakes: 3" on one line; a game with no best score and no saved progress says
  "No results"; one with saved progress (8 questions right, 2 mistakes) and no best score says
  "Correct: 8 · Mistakes: 2", never "Best: –". At 360px
  and 640px "Best: 1260 · Mistakes: 10" fits on the line, not cut off.
- With the pictures missing, each tile keeps its 5:4 space and its name.
- On "You Won!" at 360px, "Play again" shows in full, its check badge on the picture; nothing of
  the game shows through the panel.

# The AlmLab portfolio book

A hardback on a dark desk that opens into a page-turning book of every project.
It runs live in the browser with three.js, like the reference: click the book to
open it, scroll, swipe or use the arrows to turn pages, hover a page to watch the
site scroll, click a page to visit it.

```
index.html              the whole page: scene, book, turns, hover, links
three.module.min.js     three.js r160
vendor/three-addons/    bloom post-processing from three.js r160
gsap.min.js             GSAP 3.15 for camera moves, turns and the intro
img/pages/*.webp        every printed page (cover, contents, 18 projects, end) and the two business cards
img/logo-shape.json     the logo's outlines (letters, arrow, flask liquid, black backing) traced from img/logo.png for the 3D sign
img/*.jpg|png           full-page screenshots that play on hover
img/video/*.mp4         6.5-second looping videos of the sites with moving heroes
render/                 page-face scripts (and the old Blender desk scripts)
pages.html              draws the printed pages; render/faces.mjs captures them
```

## Easy changes (edit index.html and push)

- **Projects, names, links, hover screenshots**: the `WORKS` list at the top of the script.
- **Feel**: the `CONFIG` block — turn speed, camera speed, glow, lamp, wood darkness, page brightness, hover scroll speed.
- **Things on the desk**: the `PROPS` block — where the pencil, the business cards and the AlmLab light-up sign sit.
  For the sign: `width`, `turn`, `lean` (how far it tips back), `glow` (the soft white light on the wood) and
  `startOn` (lit when the page loads). The sign and cards have their own spots on phones.
  Click the sign to switch it on and off, the top card to flip it over and back, the pencil to roll it forward and back.
- **Framing**: the `FRAMING` block — where the book sits on screen (centre, width, tilt) closed and open,
  for laptops and phones. The camera works out its own position from these on every screen size.
  `focus` is the zoomed-in single page on phones. `LENS` sets how long the lens is: lower means flatter, less looming.

## On phones

Tap the book to open it. Both pages of the open spread play their site on their own.
Tap a project on the Contents page to jump straight to it.
Drag up or down on a page to scroll down its site yourself (on a laptop, use the mouse wheel over the page).
Tap a page to zoom in on it. Tap it again to visit.
Swipe or use the arrows to move one page at a time while zoomed in.

## A new project or a new screenshot

1. Take a screenshot of the site 1440px wide at 2x, full page, and put it in `img/`.
2. Add it to `WORKS` in `index.html` and `pages.html`.
3. Run `python3 render/work_faces.py 19` from this folder, with the project's number. It rebuilds the printed pages
   (`img/pages/workNN.webp`) and enlarges small screenshots for the hover playback.

The cover, contents and end pages come from `pages.html`: serve the folder
(`python3 -m http.server 8765`), run `node render/faces.mjs`, then convert the PNGs to `img/pages/*.webp`.

## Moving heroes

A project with `hero: 'img/video/<name>.mp4'` in `WORKS` shows that video on its page whenever the page is open,
and rests on it for `CONFIG.heroHold` seconds before scrolling down the site. The loops are recorded frame by frame
from the live sites (1440x810, 24 fps) and their ends crossfade into their starts, so they loop without a jump.
To record a new one, add the site to `render/hero/rec.mjs`, run it, then `render/hero/enc.sh <name>`.

## The desk

The desk is a scanned black oak veneer from Poly Haven (CC0, free to use), in `img/wood/`:
`oak-3k.webp` for laptops, `oak-2k.webp` for phones, and `oak-normal.webp` for the surface detail.
`CONFIG.desk` sets how dark it is, and `WOOD_TILE` sets how fine the grain looks.
To try another wood, download its Diffuse and Normal (GL) maps from polyhaven.com and replace those files.

## Colours of the pages

`CONFIG.pageBrightness` sets how bright the printed sites are; 1 shows exactly the site's colours.
`CONFIG.pageGloss` sets how glossy the paper is (0 matte, 1 very shiny).
`REST` sets how much open pages curve up out of the spine.
Pages darken slightly as they lift during a turn, and a turning page shades the one beneath it.

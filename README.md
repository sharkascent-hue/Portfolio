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
img/desk.jpg            the desk, lamp pool and pencil, baked in Blender
img/pages/*.webp        every printed page (cover, contents, 18 projects, end)
img/*.jpg|png           full-page screenshots that play on hover
render/                 Blender scripts: desk bake, page faces, camera fit
pages.html              draws the printed pages; render/faces.mjs captures them
```

## Easy changes (edit index.html and push)

- **Projects, names, links, hover screenshots**: the `WORKS` list at the top of the script.
- **Feel**: the `CONFIG` block — turn speed, camera speed, glow, lamp, desk brightness, hover scroll speed.
- **Framing**: the `RIGS` block — where the camera sits closed and open, for laptops and phones.

## A new project or a new screenshot

1. Put the full-page screenshot in `img/` and add it to `WORKS` in `index.html` and `pages.html`.
2. Regenerate the printed pages: serve the folder (`python3 -m http.server 8765`),
   run `node render/faces.mjs`, then convert `render/faces/*.png` to `img/pages/*.webp`.

## The desk

`render/bake_desk.py` renders the wood, the lamp pool and the pencil top-down in Blender
(`pip install bpy`), about 8 minutes on 4 cores. Move the pencil in `render/book_scene.py`
(`add_props`), re-bake, save as `img/desk.jpg`.

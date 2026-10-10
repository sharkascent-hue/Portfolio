# The AlmLab portfolio book

This repo deploys as-is: `index.html` is the page.

A hardback on a desk that opens into a page-flipping book of every project.
The book is a **film rendered offline in Blender**; the page plays that film
with scroll and click and tilts it a few degrees with the mouse. That is the
same technique as the reference video, and it is why it looks like a photo
on any device.

```
./
  index.html        the page people see: film player + headline + links
  live.html         the earlier real-time 3D version, kept as a fallback
  pages.html        draws every page face (cover, contents, 18 works, end) as a 16:9 image
  frames/1920/      the film, one WebP per frame, desktop size
  frames/960/       the same film, phone size
  img/              logo, project screenshots, desk and cloth textures
  render/           everything needed to re-render the film
```

## Changing things without re-rendering

These only need an edit and a push.

- **Feel of the motion** — `index.html`, the `CONFIG` block near the top:
  tilt angle, scroll speed, how quickly the frame chases the scroll, click speed.
- **Project names and links** in the bar under the book — the `WORKS` list in
  `index.html`. Order is the order in the book.
- **Headline, subtitle, button text** — the HTML at the top of `index.html`.
- **Vignette and grain** — the `.grade` rules in the CSS of `index.html`.

## Changing what is printed on the pages (needs a re-render)

The pages are baked into the film, so a new screenshot or a new project means
re-rendering the frames that show it. The whole film is 279 frames; one page
flip is 24 frames, so a single project change is a few minutes, not hours.

1. Put the new screenshot in `img/` (any size, 16:9 is best; wider images are
   centre-cropped, taller ones keep their top).
2. Edit the `WORKS` list in **both** `index.html` (name and link) and
   `pages.html` (name and image).
3. Regenerate the page faces. Serve the `book/` folder and run the capture:

   ```
   python3 -m http.server 8000 &
   npx playwright install chromium   # first time only
   node render/faces.mjs            # writes render/faces/*.png
   ```

4. Render. Blender is installed as a Python package, so no Blender UI is needed:

   ```
   cd render
   python3.11 -m venv venv && . venv/bin/activate && pip install bpy pillow numpy
   python book_scene.py --out frames --width 1920 --samples 24          # everything, ~2 h on 4 CPU cores
   python book_scene.py --out frames --width 1920 --samples 24 --start 57 --end 80   # only one flip
   python encode.py frames out                                           # WebP at 1920 and 960
   ```

   Which frames show which project: frame 0 is the closed book, frames 1–32
   open the cover, then each flip is 24 frames. Leaf *k* (projects 2k−1 and 2k)
   flips in frames `33 + (k−1)·24` to `32 + k·24`, and project 2k is visible on
   the left page from then until leaf k+1 flips.

5. Copy `out/1920` and `out/960` over `frames/` and push.

## Changing the look of the scene (needs a full re-render)

Open `render/book_scene.py`. The things worth touching are all near the top or
in `build()`:

- **Book size and thickness** — `PAGE_W`, `PAGE_D`, `LEAF_T`, `BOARD_T`.
- **Timing** — `F_OPEN`, `F_FLIP`, `F_CLOSE` (frames per move). If you change
  these, mirror them in the `F_OPEN / F_FLIP / F_CLOSE` line of `index.html`.
- **Lamp** — in `build()`: `lamp.data.energy` (brightness), `spot_size`
  (pool width), `spot_blend` (soft edge), `shadow_soft_size` (shadow softness),
  `fill.data.energy` (the cool fill from the left).
- **Desk** — the `wood` material: `tint` darkens it, `roughness` controls the
  sheen, `tex_scale` the grain size. Swap `render/tex/wood.png` for another wood.
- **Camera** — `RIG_CLOSED` and `RIG_OPEN`: target point, elevation in degrees,
  distance. `cam.data.lens` is the focal length, `aperture_fstop` the depth of field.
- **Paper** — in `paper()`: `rough` for gloss, `emit` for how much the pages glow.

Render a single frame to check before committing hours:

```
python book_scene.py --out test --frame 36 --width 1024 --samples 32   # the first open spread
python book_scene.py --out test --frame 0  --width 1024 --samples 32   # the closed book
```

## Running locally

The player needs a web server, not `file://`:

```
python3 -m http.server 8000
# open http://localhost:8000/
```

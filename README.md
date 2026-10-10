# AlmLab Portfolio — a book you can explore

A dark desk, one lamp, and a hardback that opens into a page-flipping book of
everything AlmLab has built. Click the cover to open it, click pages to turn
them, hover to lift them, click a project name to visit the live site.

Live: enable GitHub Pages on this repo (Settings → Pages → Deploy from branch
`main`, folder `/ (root)`) and it serves at the root — no build step.

## Files

- `index.html` — the whole experience: scene, book, interactions, UI.
- `three.module.min.js` — three.js r160, `gsap.min.js` — GSAP 3.15 for camera and UI motion.
- `img/` also holds the photographic desk props (succulent, coffee, pencil), the wood and book-cloth textures and their normal maps.
- `img/` — the AlmLab logo and one screenshot per project.
- `vendor/gsap/` — GSAP 3.15 minified builds (core + every plugin).
- `vendor/lenis/` — Lenis 1.3 smooth scroll build and stylesheet.

## Adding a project

Add an entry to the `WORKS` array at the top of the script in `index.html`
and drop its screenshot in `img/`. Pages are 3:2; 16:9 shots are centre-cropped,
tall shots keep their top. Two projects fill one leaf.

## Running locally

Textures are drawn onto canvases, so it needs a web server, not `file://`:

    python3 -m http.server 8000
    # open http://localhost:8000/

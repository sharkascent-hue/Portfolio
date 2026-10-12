# Abricot: orange skincare landing page

A scroll-driven product site in the style of the reference reel: a jar in a peony that you
scroll through (the flower, the jar rising, the lid lifting, back into the flower), then the
product line, then a footer. Orange theme. Works on laptops and phones.

```
index.html          the whole site (styles, copy, scroll film)
img/*.webp          the four film shots (and -m versions for phones) and four product photos
vendor/             GSAP + ScrollTrigger (scroll), Lenis (smooth scrolling)
```

## Easy changes
- **Colours**: the `:root` block at the top of `index.html`. `--accent` is the orange.
- **Brand name and copy**: search for `ABRICOT` and edit the text in the chapters and cards.
- **Prices**: the `Add to bag · $128` buttons and the `.price` in each card.
- **The film**: the `SHOTS` list. Each shot says which image, which part of the scroll it covers,
  where the jar is in the photo (`s`) and how far to zoom (`z`) and where on screen the jar sits (`p`),
  for laptops (`a` → `b`) and phones (`ma` → `mb`). `CHAPTERS` sets when each text panel shows.

## Swapping in real motion
The shots are AI-generated keyframes (GPT Image 2.5 via Higgsfield). Once Higgsfield video
generation is available again, generate start→end clips between consecutive shots, export
them as frames and replace the crossfades with a frame-sequence player.

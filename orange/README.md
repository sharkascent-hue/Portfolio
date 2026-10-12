# Abricot (orange scroll site)

One scroll-scrubbed film: `film/film.mp4` (laptop, 1280x720) and `film/film-m.mp4` (phone, centre crop 540x720), with `.webm` fallbacks.
Scrolling plays the clip forwards (bud opens, jar rises, lid lifts, jar settles back into the flower); scrolling up plays it back.

- To swap the film: re-encode with a keyframe every 2 frames (`-g 2`) so seeking is instant, e.g.
  `ffmpeg -i clip.mp4 -an -vf scale=1280:720 -c:v libx264 -crf 24 -g 2 -keyint_min 2 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart film/film.mp4`
- `CHAPTERS` in index.html: when each text panel shows (0..1 of the film).
- `SB`: the film's background colour over time (the page around the video follows it).
- Theme colours are the `:root` tokens at the top of index.html.

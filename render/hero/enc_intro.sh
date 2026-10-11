#!/bin/bash
# intro/<key>/*.jpg (24 fps from the site's first frame) -> img/video/<key>-intro.mp4: the opening animation,
# cut where it settles, its last 0.4 s blending into what the page shows next (the hero loop's first frame, or the print).
set -e
B=/home/user/almlab/book; OUT=$B/img/video; mkdir -p $OUT
while read k cut next; do
  [ -z "$k" ] && continue
  n=$(python3 -c "print(round($cut*24))")
  if [ "$next" = "loop" ]; then ffmpeg -nostdin -v error -y -ss 0 -i $OUT/$k.mp4 -frames:v 1 /tmp/next-$k.png; else cp "$next" /tmp/next-$k.png; fi
  ffmpeg -nostdin -v error -y -framerate 24 -i intro/$k/%04d.jpg -loop 1 -framerate 24 -t 0.5 -i /tmp/next-$k.png -filter_complex \
    "[0]trim=end_frame=$n,setpts=PTS-STARTPTS,scale=1280:720:flags=lanczos,format=yuv420p[a];[1]scale=1280:720:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS[b];[a][b]xfade=transition=fade:duration=0.4:offset=$(python3 -c "print($cut-0.4)")[v]" \
    -map "[v]" -c:v libx264 -preset slow -crf 25 -profile:v main -level 4.0 -g 24 -keyint_min 24 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart -an $OUT/$k-intro.mp4
  echo "$k $(du -k $OUT/$k-intro.mp4 | cut -f1)KB $(ffprobe -v error -show_entries format=duration -of csv=p=0 $OUT/$k-intro.mp4)s"
done

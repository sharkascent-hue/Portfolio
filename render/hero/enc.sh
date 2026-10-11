#!/bin/bash
# frames/<key>/*.jpg (24 fps) -> /home/user/almlab/book/img/video/<key>.mp4, a seamless loop (its end crossfades into its start)
set -e
OUT=/home/user/almlab/book/img/video; mkdir -p $OUT
for k in "$@"; do
  n=$(ls frames/$k | wc -l); T=$(python3 -c "print($n/24)"); M=$(python3 -c "print($n/24-1)"); O=$(python3 -c "print($n/24-2)")
  ffmpeg -nostdin -v error -y -framerate 24 -i frames/$k/%04d.jpg -filter_complex \
    "[0]scale=1280:720:flags=lanczos,format=yuv420p,split[a][b];[a]trim=start=1,setpts=PTS-STARTPTS[main];[b]trim=end=1,setpts=PTS-STARTPTS[head];[main][head]xfade=transition=fade:duration=1:offset=$O[v]" \
    -map "[v]" -c:v libx264 -preset slow -crf 25 -profile:v main -level 4.0 -g 24 -keyint_min 24 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart -an $OUT/$k.mp4
  echo "$k $(du -k $OUT/$k.mp4 | cut -f1)KB $(ffprobe -v error -show_entries format=duration -of csv=p=0 $OUT/$k.mp4)s"
done

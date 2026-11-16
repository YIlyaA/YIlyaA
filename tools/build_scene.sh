#!/usr/bin/env bash
# Build assets/fox-scene.webp (looping) and assets/fox-scene-still.webp from three generated clips.
#
# Usage: tools/build_scene.sh clip1.mp4 clip2.mp4 clip3.mp4
#   clip1: K0 -> K1 (a robot falls), clip2: K1 -> K2 (the fox fixes it), clip3: K2 -> K0 (all walk on).
# Each clip ends on the frame the next one starts with, so the first frame of clips 2 and 3 is dropped.
# The loop seam (end of clip 3 -> start of clip 1) gets a 0.25 s fade. The 16:9 frame is cropped to 21:9.
# Needs ffmpeg and img2webp (brew install ffmpeg webp).
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

ffmpeg -loglevel error -y -i "$1" -vf "select=eq(n\,0),scale=1916:1080" -frames:v 1 -update 1 "$work/first.png"
mkdir "$work/frames"
ffmpeg -loglevel error -y -i "$1" -i "$2" -i "$3" -loop 1 -t 0.3 -i "$work/first.png" \
  -filter_complex "\
[0:v]scale=1916:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p[a];\
[1:v]scale=1916:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p,trim=start_frame=1,setpts=PTS-STARTPTS[b];\
[2:v]scale=1916:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p,trim=start_frame=1,setpts=PTS-STARTPTS[c];\
[3:v]scale=1916:1080,setsar=1,fps=24,format=yuv420p[d];\
[c][d]xfade=transition=fade:duration=0.25:offset=4.71,trim=end=4.96,setpts=PTS-STARTPTS[cx];\
[a][b][cx]concat=n=3:v=1:a=0,crop=1916:821:0:220,fps=15,scale=1260:540:flags=lanczos[s]" \
  -map "[s]" "$work/frames/f%04d.png"

img2webp -loop 0 -lossy -q 65 -m 6 -d 67 "$work"/frames/f*.png -o "$repo/assets/fox-scene.webp"
ffmpeg -loglevel error -y -i "$work/first.png" -vf "crop=1916:821:0:220,scale=1260:540:flags=lanczos" \
  -frames:v 1 -update 1 "$work/still.png"
cwebp -quiet -q 85 "$work/still.png" -o "$repo/assets/fox-scene-still.webp"
ls -la "$repo/assets/fox-scene.webp" "$repo/assets/fox-scene-still.webp"

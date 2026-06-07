#!/usr/bin/env bash
# pocket-director: end-to-end pipeline.
#
# Usage: ./run_all.sh my-narration.md
#
# Assumes PRoot Ubuntu with python3, ffmpeg, node, modal, playwright
# already installed (see docs/SETUP.md).

set -euo pipefail

NARRATION="${1:?usage: $0 narration.md}"
BASENAME="$(basename "${NARRATION%.md}")"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/build/$BASENAME"

echo "============================================================"
echo "  pocket-director pipeline"
echo "  narration: $NARRATION"
echo "  workdir:   $WORK"
echo "============================================================"

mkdir -p "$WORK"/{audio,slides,recordings,output}
cd "$WORK"

# Stage 1 — TTS
echo ""
echo "▶ Stage 1/6: TTS generation"
python3 "$ROOT/pipeline/01_generate_tts.py" "$NARRATION" --out audio

# Stage 2 — Build HTML
echo ""
echo "▶ Stage 2/6: Build HTML slide deck"
python3 "$ROOT/pipeline/02_build_slides.py" audio/manifest.json "$NARRATION" --out slides/slide_deck.html

# Stage 3 — Record (real-time, ~10 min for 10-min video)
echo ""
echo "▶ Stage 3/6: Playwright recording (this takes real-time, ~your video length)"
node "$ROOT/pipeline/03_render.js" "$(pwd)/slides/slide_deck.html" "$(pwd)/recordings" audio/manifest.json

WEBM=$(ls -t recordings/*.webm | head -1)

# Stage 4 — Audio mix
echo ""
echo "▶ Stage 4/6: Audio mix"
BGM="${BGM:-/root/pocket-director/music/bgm_clean.mp3}"
if [ ! -f "$BGM" ]; then
    echo "  (no BGM at $BGM, downloading default lo-fi loop...)"
    BGM="audio/_bgm.mp3"
    # Default: download a Creative Commons lo-fi loop
    yt-dlp -x --audio-format mp3 -o "audio/_bgm.%(ext)s" "https://youtu.be/PYne2exHHYU" \
        && ffmpeg -y -i audio/_bgm.mp3 -af "silenceremove=stop_periods=-1:stop_duration=0.3,volume=0.6" "$BGM"
fi
python3 "$ROOT/pipeline/04_mix_audio.py" audio/manifest.json "$BGM" --out audio/mixed.mp3

# Stage 5 — Cloud encode (Modal)
echo ""
echo "▶ Stage 5/6: Cloud encode (Modal)"
python3 "$ROOT/pipeline/05_modal_encode.py" "$WEBM" --out "output/recording_h264.mp4"

# Stage 6 — Mux + deploy
echo ""
echo "▶ Stage 6/6: Mux + deploy"
python3 "$ROOT/pipeline/06_mux.py" "output/recording_h264.mp4" "audio/mixed.mp3" \
    --out "output/${BASENAME}_final.mp4" --deploy-to-movies

echo ""
echo "============================================================"
echo "  ✓ Done!"
echo "  Final: $WORK/output/${BASENAME}_final.mp4"
ls -lh "$WORK/output/${BASENAME}_final.mp4"
echo "============================================================"

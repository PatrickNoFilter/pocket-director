#!/usr/bin/env python3
"""
Stage 4: Mix TTS narration with looping background music.

Reads audio/manifest.json, concatenates TTS mp3s, loops BGM to match
duration, applies sidechain compression (duck music under voice),
loudnorms to -14 LUFS, writes one mixed MP3.

Usage:
    python 04_mix_audio.py audio/manifest.json path/to/bgm.mp3
"""
import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd[:6])}...")
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("bgm", type=Path, help="Background music MP3 (cleaned of silence)")
    ap.add_argument("--out", type=Path, default=Path("audio/mixed.mp3"))
    ap.add_argument("--voice-vol", type=float, default=1.0)
    ap.add_argument("--bgm-vol", type=float, default=0.25)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    total_dur = sum(m["dur"] for m in manifest)
    print(f"Total narration: {total_dur:.1f}s")

    # 1. Concat TTS mp3s
    tts_concat = args.out.parent / "_tts_concat.mp3"
    concat_list = args.out.parent / "_concat_list.txt"
    concat_list.write_text("\n".join(f"file '{m['file']}'" for m in manifest))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(tts_concat)],
        check=True)

    # 2. Loop BGM to match narration duration
    bgm_looped = args.out.parent / "_bgm_looped.mp3"
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(args.bgm),
         "-t", str(total_dur), "-c", "copy", str(bgm_looped)],
        check=True)

    # 3. Mix: voice (vol 1.0) + bgm (vol 0.25), sidechain compress
    mix1 = args.out.parent / "_mix1.mp3"
    run([
        "ffmpeg", "-y",
        "-i", str(tts_concat), "-i", str(bgm_looped),
        "-filter_complex",
        f"[0:a]volume={args.voice_vol}[v];"
        f"[1:a]volume={args.bgm_vol},sidechaincompress=threshold=0.05:ratio=8:attack=5:release=800[bg];"
        f"[v][bg]amix=inputs=2:duration=first:dropout_transition=0[m]",
        "-map", "[m]", "-c:a", "libmp3lame", "-q:a", "4", str(mix1)
    ], check=True)

    # 4. Loudnorm to -14 LUFS (TikTok / YouTube safe)
    run([
        "ffmpeg", "-y", "-i", str(mix1),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "libmp3lame", "-q:a", "4", str(args.out)
    ], check=True)

    # Cleanup
    for f in [tts_concat, bgm_looped, mix1, concat_list]:
        f.unlink(missing_ok=True)

    size_mb = args.out.stat().st_size / 1024 / 1024
    print(f"✓ {args.out} written ({size_mb:.1f} MB, {total_dur:.1f}s)")


if __name__ == "__main__":
    main()

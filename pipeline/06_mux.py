#!/usr/bin/env python3
"""
Stage 6: Mux video + audio, deploy to /storage/emulated/0/Movies/.

Usage:
    python 06_mux.py video.mp4 audio.mp3 [output.mp4]
"""
import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("audio", type=Path)
    ap.add_argument("--out", type=Path, default=Path("output/final.mp4"))
    ap.add_argument("--deploy-to-movies", action="store_true",
                    help="Copy to /storage/emulated/0/Movies/ when done")
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Muxing {args.video} + {args.audio} → {args.out}")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(args.video), "-i", str(args.audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(args.out)
    ]
    subprocess.run(cmd, check=True)
    size = args.out.stat().st_size / 1024 / 1024
    print(f"✓ {args.out} ({size:.1f} MB)")

    if args.deploy_to_movies:
        movies = Path("/storage/emulated/0/Movies")
        if movies.exists():
            dst = movies / args.out.name
            shutil.copy(args.out, dst)
            print(f"✓ Deployed to {dst}")
        else:
            print(f"⚠ {movies} not found (not on Android?) — skipped deploy")


if __name__ == "__main__":
    main()

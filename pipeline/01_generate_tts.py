#!/usr/bin/env python3
"""
Stage 1: Generate TTS audio for each slide in narration.md.

Parses markdown for `### SLIDE N` sections, calls edge-tts for each,
writes one MP3 per slide + a manifest.json with durations.

Usage:
    python 01_generate_tts.py narration.md --voice id-ID-GadisNeural
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

import edge_tts


def parse_narration(path: Path) -> list[dict]:
    """Parse markdown into list of {num, title, text}."""
    text = path.read_text(encoding="utf-8")
    slides = []
    pattern = re.compile(r"###\s+SLIDE\s+(\d+)\s*[—\-–]\s*([^\n]+)\n(.*?)(?=\n###\s+SLIDE|\Z)", re.DOTALL)
    for m in pattern.finditer(text):
        num = int(m.group(1))
        title = m.group(2).strip()
        body = m.group(3).strip()
        # Title slide gets title as text (often no body); others get body
        full_text = f"{title}. {body}" if body and title not in body else (body or title)
        slides.append({"num": num, "title": title, "text": full_text})
    if not slides:
        sys.exit(f"No ### SLIDE N sections found in {path}")
    return slides


async def gen_one(slide: dict, voice: str, rate: str, out_dir: Path) -> dict:
    """Generate one MP3 via edge-tts, return entry with duration."""
    out_path = out_dir / f"slide_{slide['num']:02d}.mp3"
    communicate = edge_tts.Communicate(slide["text"], voice, rate=rate)
    await communicate.save(str(out_path))
    # Get duration via ffprobe
    import subprocess
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(out_path)],
        capture_output=True, text=True
    )
    dur = float(probe.stdout.strip())
    return {**slide, "file": str(out_path), "dur": dur}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("narration", type=Path)
    ap.add_argument("--voice", default="id-ID-GadisNeural",
                    help="edge-tts voice (default: Indonesian girl)")
    ap.add_argument("--rate", default="+0%",
                    help="TTS rate adjustment (e.g. +5%% for slightly faster)")
    ap.add_argument("--out", type=Path, default=Path("audio"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    slides = parse_narration(args.narration)
    print(f"Parsed {len(slides)} slides from {args.narration}")

    print(f"Generating TTS (voice={args.voice}, rate={args.rate})...")
    manifest = []
    for slide in slides:
        m = await gen_one(slide, args.voice, args.rate, args.out)
        print(f"  [{m['num']:02d}] {m['dur']:5.1f}s  {m['title'][:60]}")
        manifest.append(m)

    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    total = sum(m["dur"] for m in manifest)
    print(f"\n✓ {len(manifest)} MP3s + manifest.json written")
    print(f"  Total: {total:.1f}s ({total/60:.1f} min)")


if __name__ == "__main__":
    asyncio.run(main())

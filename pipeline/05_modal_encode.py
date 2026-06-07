#!/usr/bin/env python3
"""
Stage 5: Cloud-encode webm → H.264 MP4 via Modal.

Uploads the local webm to a Modal Volume, runs libx264 medium CRF 20
in a Debian container (8 vCPUs), downloads the result.

Setup (one-time, see docs/SETUP.md):
    pip install 'modal>=1.0,<1.4' toml
    modal setup   # OR: create ~/.modal.toml with token_id/secret

Usage:
    python 05_modal_encode.py path/to/recording.webm
"""
import argparse
import os
import sys
import time
from pathlib import Path


def load_modal_auth():
    """Read token from ~/.modal.toml if not already in env."""
    if os.environ.get("MODAL_TOKEN_ID") and os.environ.get("MODAL_TOKEN_SECRET"):
        return
    import toml
    cfg_path = Path.home() / ".modal.toml"
    if not cfg_path.exists():
        sys.exit("Need MODAL_TOKEN_ID+SECRET env vars or ~/.modal.toml — see docs/SETUP.md")
    cfg = toml.load(cfg_path)
    os.environ["MODAL_TOKEN_ID"] = cfg["default"]["token_id"]
    os.environ["MODAL_TOKEN_SECRET"] = cfg["default"]["token_secret"]


# --- Modal app definition (cloud-side) ---
def build_modal_app():
    """Build the Modal app, image, volume, and functions. Imported lazily."""
    import modal
    app = modal.App("pocket-director-encode")
    image = modal.Image.debian_slim(python_version="3.11").apt_install("ffmpeg")
    volume = modal.Volume.from_name("pocket-director-videos", create_if_missing=True)

    @app.function(image=image, volumes={"/data": volume}, timeout=1800, cpu=8)
    def encode(input_name: str, output_name: str, crf: int = 20, preset: str = "medium"):
        import subprocess
        cmd = ["ffmpeg", "-y", "-i", f"/data/{input_name}",
               "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", "-threads", "0",
               f"/data/{output_name}"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {p.stderr[-500:]}")
        volume.commit()
        return {"output": output_name, "size": os.path.getsize(f"/data/{output_name}")}

    @app.function(volumes={"/data": volume}, timeout=300)
    def upload(filename: str, data: bytes):
        with open(f"/data/{filename}", "wb") as f:
            f.write(data)
        volume.commit()
        return {"uploaded": filename, "size": len(data)}

    @app.function(volumes={"/data": volume}, timeout=600)
    def download(filename: str) -> bytes:
        with open(f"/data/{filename}", "rb") as f:
            return f.read()

    return app, upload, encode, download


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("webm", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--crf", type=int, default=20, help="libx264 CRF (lower = better, 18-23 typical)")
    ap.add_argument("--preset", default="medium", help="libx264 preset (ultrafast…veryslow)")
    args = ap.parse_args()
    if not args.out:
        args.out = args.webm.with_suffix(".mp4")

    load_modal_auth()
    app, upload_fn, encode_fn, download_fn = build_modal_app()

    in_name = "in_" + args.webm.name
    out_name = "out_" + args.out.name

    def run_pipeline():
        print(f"[1/4] Reading {args.webm} ({args.webm.stat().st_size/1024/1024:.1f} MB)")
        webm_bytes = args.webm.read_bytes()

        print(f"[2/4] Uploading to Modal volume...")
        t = time.time()
        upload_fn.remote(in_name, webm_bytes)
        print(f"      uploaded in {time.time()-t:.1f}s")

        print(f"[3/4] Cloud-encoding (libx264 {args.preset}, crf {args.crf})...")
        t = time.time()
        result = encode_fn.remote(in_name, out_name, crf=args.crf, preset=args.preset)
        print(f"      encoded in {time.time()-t:.1f}s → {result}")

        print(f"[4/4] Downloading to {args.out}...")
        t = time.time()
        mp4 = download_fn.remote(out_name)
        args.out.write_bytes(mp4)
        print(f"      saved in {time.time()-t:.1f}s ({args.out.stat().st_size/1024/1024:.1f} MB)")
        print(f"\n✓ {args.out}")

    import modal
    with modal.enable_output():
        with app.run():
            run_pipeline()


if __name__ == "__main__":
    main()

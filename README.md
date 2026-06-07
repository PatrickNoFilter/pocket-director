# pocket-director

> **Pro animated infographic videos — from your phone, in the cloud, for free.**

A complete pipeline for producing 10-minute documentary-style
animated infographic videos (think *Vox*, *Polymatter*, *Kurzgesagt* — but finance
and Indonesia) — **entirely from a Samsung Galaxy A33 running Termux +
PRoot Ubuntu**, with all heavy lifting offloaded to **Modal** cloud
ffmpeg.

Includes a pre-pipeline **research stage** (Stage 0) that integrates
with [last30days](https://github.com/mvanhorn/last30days-skill) to
gather facts before you write a single line of narration.

```
    Phone (Termux + PRoot Ubuntu)                 Modal Cloud
    ┌──────────────────────────┐                ┌──────────────┐
    │  1. narration.md (text)  │                │              │
    │         ↓                │                │  4. ffmpeg   │
    │  2. edge-tts → mp3s      │                │  webm → MP4  │
    │         ↓                │      upload    │  (libx264)   │
    │  3. HTML + Playwright    │ ─────────────▶ │              │
    │     → webm (1080p)       │   47 MB / 18s  │  ~70s encode │
    │         ↓                │                │              │
    │  5. mix audio (TTS+BGM)  │ ◀───────────── │  download    │
    │         ↓                │   26 MB / 9s   │   26 MB      │
    │  6. mux video+audio      │                └──────────────┘
    │         ↓                │
    │  7. /storage/.../Movies  │
    └──────────────────────────┘
```

## Why this exists

Local ffmpeg on a phone's ARM64 CPU does ~0.4× realtime for H.264
encode — an 11-minute 1080p video would take **8+ hours**. The cloud
encode via Modal does the same job in **70 seconds**. This pipeline is
designed to keep your phone cool and your time free, while still
producing broadcast-quality output.

## Quick start (assuming PRoot Ubuntu + Modal already set up)

```bash
git clone https://github.com/PatrickNoFilter/pocket-director.git
cd pocket-director
pip install -r requirements.txt
# Optional: install Playwright Chromium once
playwright install chromium

# 1. Research your topic (Stage 0 — optional, see docs/RESEARCH.md)
last30days "your topic" --output notes.md

# 2. Write your narration (markdown, one ### SLIDE N per section)
cp examples/ihsg-danantara/narration.md my-video.md
nano my-video.md

# 3. Run the full pipeline (~14 min wall-clock for a 10-min video)
./pipeline/run_all.sh my-video.md

# 4. Your video lands in /storage/emulated/0/Movies/
```

## Setup (one-time)

See [`docs/SETUP.md`](docs/SETUP.md) for the full walkthrough.
TL;DR for PRoot Ubuntu on Termux:

```bash
# In Termux
pkg install proot-distro
proot-distro install ubuntu
proot-distro login ubuntu

# Inside Ubuntu
apt update && apt install -y git ffmpeg python3 python3-pip nodejs npm
pip install -r requirements.txt
playwright install chromium

# Modal account
pip install modal
modal setup   # follow browser flow, OR export MODAL_TOKEN_ID=... / SECRET=...
```

## The pipeline in detail

### Stage 0 — Research (`last30days`, optional)

Thin shim. Skips if `notes.md` already exists. See [`docs/RESEARCH.md`](docs/RESEARCH.md).

### Stage 1 — TTS (edge-tts, `id-ID-GadisNeural` or `en-US-AriaNeural`)

Parses `narration.md` for `### SLIDE N` sections, generates one MP3 per
slide. Indonesian girl voice by default; configurable per-script.

### Stage 2 — HTML slide deck build

Renders a single 1920×1080 HTML file with one `<section>` per slide.
Animations are pure CSS + small JS:

- Bar charts grow from zero (`height` keyframe)
- Number counters tick up via `requestAnimationFrame`
- Text elements reveal in stagger via `animation-delay`
- Quote blocks slide in from left
- Timeline dots scale up sequentially
- Ken Burns pan on background images

The HTML template is in `templates/slide_deck.html` — edit colors,
fonts, layout once, reuse for all videos.

### Stage 3 — Playwright recording

Records the HTML at 1920×1080 to a webm via Chromium's built-in
screen-capture API. Auto-advances slides by the TTS duration for each
section. Runs headless, no GPU required.

### Stage 4 — Audio mix (local, ffmpeg)

Concatenates the TTS MP3s, loops the BGM, sidechain-compresses the
music under voice, loudnorm to -14 LUFS (TikTok-recommended).

### Stage 5 — Cloud encode (Modal)

Uploads the 47 MB webm to a Modal Volume, runs libx264 medium CRF 20
in a Debian container (8 vCPUs), downloads the 26 MB H.264 MP4.

### Stage 6 — Mux + deploy

Muxes video + audio locally (instant, just stream copy), copies the
final file to `/storage/emulated/0/Movies/` so it shows up in Gallery.

## Customization

| What | Where | Notes |
|------|-------|-------|
| Watermark | `templates/slide_deck.html` | Bottom-right "● YOURBRAND" |
| Voice | `pipeline/01_generate_tts.py` | `voice="id-ID-GadisNeural"` (F) or `id-ID-ArdiNeural` (M) |
| BGM | `pipeline/04_mix_audio.py` | Point to any URL or local mp3 |
| Colors | `templates/slide_deck.html` | CSS variables at top |
| Slide count | `narration.md` | One `### SLIDE N` per section |
| Resolution | `pipeline/03_record.py` | `viewport: { width: 1920, height: 1080 }` |

## Examples

- **examples/ihsg-danantara/** — 16-slide documentary on the
  Indonesian stock market crash + Danantara controversy. 10:07, 31 MB.
  This is the video the pipeline was first built to produce.

## Performance

For a 16-slide 10-minute video:

| Stage | Where | Time |
|-------|-------|------|
| 0: Research | local/CLI | 2-5 min |
| 1: TTS generation | local | 2 min |
| 2: Slide HTML build | local | 5 sec |
| 3: Playwright recording | local | 11 min (real-time) |
| 4: Audio mix | local | 10 sec |
| 5: Modal encode | cloud | 72 sec |
| 5: Modal upload/download | cloud | 27 sec |
| 6: Mux + deploy | local | 2 sec |
| **Total wall-clock** | — | **~14 min** |

## Known limitations

- **Linear narrative only** — no branching, no interactivity. This is
  documentary style, not interactive explainers.
- **Webm → MP4 is a transcode** — VP8 in, H.264 out. Visual quality
  identical (CSS animations are vector), but VP9 source would save
  some bits.
- **Modal free tier is enough** for personal use. Heavy production
  will hit Modal's $30/mo free credit.
- **English + Indonesian** are the best-tested voices. 40+ other
  edge-tts voices work but quality varies.

## Credits

Built on the shoulders of:

- [edge-tts](https://github.com/rany2/edge-tts) — Microsoft neural TTS
- [Modal](https://modal.com) — serverless Python containers with ffmpeg
- [Playwright](https://playwright.dev) — Chromium automation
- [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) — YouTube bot bypass
- [ffmpeg](https://ffmpeg.org) — Swiss army knife of media

## License

MIT — see [`LICENSE`](LICENSE).

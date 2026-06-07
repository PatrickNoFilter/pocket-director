# Setup — pocket-director

This guide gets you from a stock Samsung Galaxy A33 (or any modern
Android phone) to producing your first video with pocket-director.
Total time: ~30 minutes, mostly waiting for installs.

## 1. Termux + PRoot Ubuntu

In Termux (install from F-Droid):

```bash
pkg update && pkg install proot-distro
proot-distro install ubuntu
proot-distro login ubuntu
```

All subsequent commands run inside PRoot Ubuntu.

## 2. System dependencies

```bash
apt update && apt -y upgrade
apt install -y git ffmpeg python3 python3-pip python3-venv nodejs npm
```

Verify:

```bash
ffmpeg -version | head -1
python3 --version
node --version
```

## 3. Python deps

```bash
cd ~
git clone https://github.com/PatrickNoFilter/pocket-director.git
cd pocket-director
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

# Playwright Chromium
playwright install chromium
playwright install-deps chromium  # usually not needed in PRoot, but try if launch fails
```

### Finding Chromium

```bash
# Find the path
find ~/.cache/ms-playwright -name "chrome" -type f 2>/dev/null
# Typically: /root/.cache/ms-playwright/chromium-XXXX/chrome-linux/chrome
```

If Playwright's default `headless_shell` (no full Chrome) complains,
set `CHROME_PATH` to the full Chromium binary:

```bash
export CHROME_PATH=/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome
```

Add to your `~/.bashrc` for persistence.

## 4. Modal account (cloud encode)

Sign up at https://modal.com (free $30/month credit). Two auth options:

### Option A: Browser setup (desktop / Termux with browser)

```bash
pip install 'modal>=1.0,<1.4'
modal setup
# Follow the browser prompt
```

### Option B: Token from file (Termux without browser)

Create `~/.modal.toml` (mode 600):

```toml
[default]
token_id = "ak-xxxxxxxxxxxx"
token_secret = "as-xxxxxxxxxxxx"
```

Get the values from https://modal.com → Settings → API Tokens.

### Verify

```bash
python -c "import modal; from modal import App; print('OK')"
```

## 5. Termux-specific: storage access

So the final MP4 lands in `/storage/emulated/0/Movies/`:

```bash
# In Termux (NOT inside PRoot)
termux-setup-storage
# Grant the permission prompt
```

Inside PRoot, `/storage/emulated/0/` is usually already mounted at
`/mnt/sdcard` or accessible via `/storage/emulated/0/`. Test:

```bash
ls /storage/emulated/0/Movies/ 2>/dev/null \
  || ls /mnt/sdcard/Movies/ 2>/dev/null \
  || echo "Storage not accessible — run termux-setup-storage in Termux"
```

If neither path works, comment out the `--deploy-to-movies` flag in
`run_all.sh` and copy the file manually afterwards.

## 6. First run

```bash
cd ~/pocket-director
./pipeline/run_all.sh examples/ihsg-danantara/narration.md
```

The first Modal run takes ~30s extra for ffmpeg install in the
container. Subsequent runs use the cached image.

If everything works, your final video will be at:

- `~/pocket-director/build/ihsg-danantara/output/ihsg-danantara_final.mp4`
- `/storage/emulated/0/Movies/ihsg-danantara_final.mp4` (if storage mounted)

## Performance expectations

For the 16-slide IHSG/Danantara example (10:07 video):

| Stage | Time |
|-------|------|
| TTS generation | 2 min |
| HTML build | 5 sec |
| Playwright record | 11 min (real-time) |
| Audio mix | 10 sec |
| Modal encode | 72 sec |
| Upload/download | 27 sec |
| Mux + deploy | 2 sec |
| **Total wall-clock** | **~14 min** |

## Optional: BGM (background music)

The pipeline needs a background music file. Easiest path:

```bash
# Use yt-dlp to grab a Creative Commons lo-fi loop
yt-dlp -x --audio-format mp3 -o "music/bgm.%(ext)s" "https://youtu.be/PYne2exHHYU"
ffmpeg -y -i music/bgm.mp3 -af "silenceremove=stop_periods=-1:stop_duration=0.3,volume=0.6,loudnorm=I=-14" music/bgm_clean.mp3
```

Or use any local mp3 and point the pipeline at it via `--bgm`.

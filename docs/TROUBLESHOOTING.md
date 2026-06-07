# Troubleshooting

Common issues and fixes. If something here doesn't cover your case,
open an issue.

## Modal

### `ImportError: cannot import name 'App' from 'modal' (unknown location)`

The Modal 1.4.3 wheel is missing `__init__.py` on Termux ARM64
(manylinux build issue). Pin to an older version:

```bash
pip install --python-platform linux 'modal>=1.0,<1.4'
```

If still failing, see `devops/modal-cloud-encode-termux` skill in
Hermes Agent for the `__init__.py` shim.

### `ModuleNotFoundError: No module named 'toml'` in Modal container

You have a `toml` (or `requests`, `httpx`, etc.) import at the top of
your modal script. The cloud container doesn't have those packages.
Move the import inside a function called only from `local_entrypoint`:

```python
# BAD
import toml
cfg = toml.load(...)

# GOOD
def _load_auth():
    import toml
    return toml.load(...)

def main():
    cfg = _load_auth()
```

### Modal `watchfiles` import error on Termux

The Modal CLI is broken on Termux. Use the Python API directly
(this is what `pipeline/05_modal_encode.py` does).

## Playwright

### `Executable doesn't exist at .../chrome-linux/headless_shell`

Playwright is looking for the slim `headless_shell` binary but the
full Chromium was installed. Set `CHROME_PATH` to the full Chrome
binary:

```bash
export CHROME_PATH=$(find ~/.cache/ms-playwright -name "chrome" -path "*/chrome-linux/*" | head -1)
```

### Recording is black / blank

Chromium needs `--disable-gpu` and `--no-sandbox` (already in
`03_render.js`). If still black, your `headless_shell` build may not
support recording. Use the full Chromium:

```bash
playwright install chromium
# (not `playwright install chromium-headless-shell`)
```

## ffmpeg

### `aac @ 0x...] Too many bits ... clamping to max`

The TTS audio has 24kHz mono and asks for too many AAC bits at 192k.
This is just a warning — the audio is fine, just clamped. To silence:

```bash
# Lower AAC bitrate, or use -b:a 128k
ffmpeg -i ... -c:a aac -b:a 128k ...
```

### Mux output is shorter than expected

`-shortest` flag truncates to the shorter of video/audio. Check
durations:

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1 video.mp4
ffprobe -v error -show_entries format=duration -of default=nw=1 audio.mp3
```

## Termux / PRoot

### `/storage/emulated/0/` not accessible inside PRoot

PRoot mounts the sdcard at `/mnt/sdcard` or doesn't mount it at all.
Workarounds:

1. **Copy from Termux side**: exit PRoot, copy the file from `~/pocket-director/...` to `/storage/emulated/0/Movies/`.
2. **Bind mount in PRoot**: launch with `proot-distro login ubuntu --bind /storage/emulated/0:/mnt/sdcard`.
3. **Use the Termux Files app** to move the file.

### `dpkg` lock errors during `apt install`

Previous interrupted install. Run:

```bash
dpkg --configure -a
apt install -f
```

### Python venv `setuptools` build fails on ARM64

Add to `~/.bashrc`:

```bash
export UV_LINK_MODE=copy
export UV_NO_BUILD_ISOLATION=1
```

## Edge-tts

### Slow first request / network errors

edge-tts hits Microsoft's endpoint, no auth needed. If you get 403/timeout,
your IP may be rate-limited. Wait a few minutes, or use a different
edge-tts voice (some voices have more capacity).

### Voice doesn't sound right

List available voices:

```bash
edge-tts --list-voices | grep -E "id-ID|en-US"
```

Indonesian girl: `id-ID-GadisNeural`
Indonesian guy: `id-ID-ArdiNeural`
English woman: `en-US-AriaNeural`, `en-US-JennyNeural`
English man: `en-US-GuyNeural`, `en-US-DavisNeural`

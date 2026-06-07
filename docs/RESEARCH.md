# Research — pre-pipeline

The pocket-director pipeline starts at `narration.md`. But to write a
good narration, you need **facts**. That's what `00_research.sh`
exists for: a thin shim that ensures you've done your research
*before* you start producing.

The recommended tool is **[last30days](https://github.com/mvanhorn/last30days-skill)**,
a research aggregator that scrapes the last 30 days of discussion
across Reddit, YouTube, Hacker News, X, and a dozen other sources
for any topic. It returns a synthesis with consensus claims, source
diversity, and explicit gap analysis.

## Why this matters

For the IHSG/Danantara example, the narration script cited 8+ specific
data points (IHSG drop %, DSI fiscal impact, DPR's 3-month evaluation
demand, etc.) and triangulated 4+ Indonesian sources (Kompas, Detik
Finance, CNBC Indonesia, Kontan). Without structured research, you end
up with hand-wavy claims that fall apart in a documentary context.

## Install last30days CLI

```bash
pip install last30days
# Or from the skill repo:
git clone https://github.com/mvanhorn/last30days-skill
# Follow the skill's setup instructions
```

## Three ways to satisfy Stage 0

### A) CLI (fastest, scripted)

```bash
# After writing your narration topic into a build dir
last30days "Indonesian stock market crash Danantara" --output notes.md
./pipeline/run_all.sh my-narration.md
```

### B) Claude Code skill (interactive)

In a Claude Code session with the last30days skill installed:

```
/last30days Indonesian stock market crash Danantara
# Claude writes a research summary; save it as notes.md
```

Then run the pipeline from outside Claude Code.

### C) Manual

Just write `notes.md` by hand. Minimum useful content:

```markdown
# Research notes: <topic>

## Key facts
- IHSG dropped 5.5% on <date>, biggest single-day fall since 2020
- DSI (Danantara Sentul Investment) is a new sovereign wealth vehicle
- DPR is demanding a 3-month evaluation period

## Sources
- Kompas: <url>
- Detik Finance: <url>
- CNBC Indonesia: <url>
```

Anything with ≥5 lines and at least 3 sources is enough. The pipeline
doesn't parse `notes.md`; it's just a check that you've done the
research before recording.

## Bypassing Stage 0

If you already have your facts in your head and don't want the
research step, just create an empty `notes.md` in the build directory
**before** running `run_all.sh`:

```bash
mkdir -p build/my-video
touch build/my-video/notes.md
./pipeline/run_all.sh my-narration.md
```

`00_research.sh` will see the file exists and skip.

## Sources beyond last30days

For Indonesia-specific finance topics, last30days may not reach
Kompas / Detik / Kontan. Supplement with:

- **Google News** with `site:kompas.com` etc.
- **Twitter / X advanced search** with language=id
- **YouTube search** with date filter (last 30 days)
- **Web archive** for time-stamped claims: https://archive.org/wayback/

The pipeline is research-agnostic — `notes.md` is just a check, not
a parse target.

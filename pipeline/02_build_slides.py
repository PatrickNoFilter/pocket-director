#!/usr/bin/env python3
"""
Stage 2: Build the animated HTML slide deck.

Reads audio/manifest.json and narration.md, generates a single HTML
file with one <section> per slide. The HTML template handles all
animations via CSS keyframes and a small JS runtime.

Usage:
    python 02_build_slides.py audio/manifest.json narration.md
"""
import argparse
import json
import re
import sys
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>__TITLE__</title>
<style>__CSS__</style>
</head>
<body>
__SLIDES__
<div class="watermark">__WATERMARK__</div>
<script>__JS__</script>
</body>
</html>
"""


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0f; font-family: 'Inter', sans-serif; color: #e8e8ed;
       overflow: hidden; height: 100vh; }

.slide { width: 100vw; height: 100vh; display: none;
         flex-direction: column; justify-content: center;
         padding: 60px 80px; position: relative; }
.slide.active { display: flex; animation: fadeIn 0.4s ease; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes growUp { from { height: 0; } }
@keyframes scaleIn { from { transform: scale(0); } to { transform: scale(1); } }
@keyframes slideRight { from { transform: translateX(-40px); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; } }
@keyframes countUp { from { opacity: 0; transform: translateY(20px); }
                     to { opacity: 1; transform: translateY(0); } }

.slide-number { position: absolute; top: 28px; left: 40px;
                font-size: 13px; color: rgba(255,255,255,0.25);
                font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; }
.slide-section { position: absolute; top: 28px; right: 40px;
                 font-size: 13px; color: rgba(255,255,255,0.2); }
.slide-title { font-size: 56px; font-weight: 800; line-height: 1.1;
               letter-spacing: -1.5px; margin-bottom: 24px; max-width: 90%; }
.slide-title.active { animation: slideRight 0.6s ease; }
.slide-body { font-size: 22px; line-height: 1.65; font-weight: 300;
              color: rgba(255,255,255,0.78); max-width: 88%;
              margin-top: 16px; }
.slide-body strong { color: #fff; font-weight: 600; }
.slide-body.active { animation: countUp 0.5s ease 0.3s both; }

.data-row { display: flex; gap: 24px; margin-top: 36px; flex-wrap: wrap; }
.data-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
             border-radius: 16px; padding: 24px 30px; min-width: 200px; }
.data-card.active { animation: countUp 0.5s ease both; }
.data-card .label { font-size: 12px; color: rgba(255,255,255,0.4);
                    text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 8px; }
.data-card .value { font-size: 32px; font-weight: 700; color: #fff; }
.data-card .value.red { color: #ef4444; } .data-card .value.green { color: #22c55e; }
.data-card .value.yellow { color: #eab308; } .data-card .value.blue { color: #3b82f6; }
.data-card .source { font-size: 11px; color: rgba(255,255,255,0.25); margin-top: 8px; }

.chart-bars { display: flex; align-items: flex-end; gap: 20px;
              margin-top: 36px; height: 240px; padding: 0 12px; }
.bar-group { display: flex; flex-direction: column; align-items: center;
             gap: 10px; flex: 1; }
.bar { width: 60px; border-radius: 8px 8px 0 0;
       background: linear-gradient(180deg, #ef4444, #dc2626);
       min-height: 4px; position: relative; }
.bar.active { animation: growUp 0.8s cubic-bezier(0.34, 1.56, 0.64, 1); }
.bar .val { position: absolute; top: -28px; left: 50%; transform: translateX(-50%);
            font-size: 14px; font-weight: 600; white-space: nowrap; }
.bar.red { background: linear-gradient(180deg, #ef4444, #dc2626); }
.bar.green { background: linear-gradient(180deg, #22c55e, #16a34a); }
.bar.yellow { background: linear-gradient(180deg, #eab308, #ca8a04); }
.bar.blue { background: linear-gradient(180deg, #3b82f6, #2563eb); }
.bar.gray { background: linear-gradient(180deg, #6b7280, #4b5563); }
.bar-label { font-size: 13px; color: rgba(255,255,255,0.45); }

.timeline { display: flex; align-items: flex-start; gap: 0; margin-top: 40px;
            width: 100%; max-width: 92%; }
.tl-node { flex: 1; text-align: center; position: relative; }
.tl-node::before { content: ''; position: absolute; top: 20px; left: 50%;
                   width: 100%; height: 2px; background: rgba(255,255,255,0.1); }
.tl-node:last-child::before { display: none; }
.tl-dot { width: 14px; height: 14px; border-radius: 50%; background: #ef4444;
          margin: 0 auto 14px; position: relative; z-index: 2; }
.tl-dot.active { animation: scaleIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.tl-dot.blue { background: #3b82f6; } .tl-dot.green { background: #22c55e; }
.tl-dot.yellow { background: #eab308; }
.tl-date { font-size: 12px; color: rgba(255,255,255,0.4); margin-bottom: 6px; }
.tl-event { font-size: 14px; color: #fff; font-weight: 500; }
.tl-detail { font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 4px; }

.quote-block { border-left: 4px solid #ef4444; padding-left: 28px; margin: 32px 0;
               font-size: 26px; font-weight: 400; line-height: 1.55;
               color: rgba(255,255,255,0.9); font-style: italic; max-width: 84%; }
.quote-block.active { animation: slideRight 0.6s ease; }
.quote-source { font-size: 14px; color: rgba(255,255,255,0.45);
                margin-top: 14px; font-style: normal; }

.bullet-list { margin-top: 24px; max-width: 85%; }
.bullet-list li { font-size: 22px; line-height: 1.7; font-weight: 300;
                  color: rgba(255,255,255,0.82); list-style: none;
                  padding: 12px 0 12px 36px; position: relative; }
.bullet-list li::before { content: '▸'; position: absolute; left: 0;
                          color: #ef4444; font-weight: 700; }
.bullet-list li.active { animation: slideRight 0.5s ease both; }

.watermark { position: fixed; bottom: 24px; right: 32px;
             font-size: 13px; color: rgba(255,255,255,0.5);
             letter-spacing: 1.5px; font-weight: 600;
             padding: 8px 14px; border: 1px solid rgba(255,255,255,0.15);
             border-radius: 6px; background: rgba(0,0,0,0.3);
             backdrop-filter: blur(4px); z-index: 9999; }
.watermark::before { content: '●'; color: #ef4444; margin-right: 8px; }
"""


JS = """
const MANIFEST = __MANIFEST__;
let currentSlide = 1;

function activate(n) {
  document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
  const el = document.getElementById('slide-' + n);
  if (!el) return;
  el.classList.add('active');
  // Stagger animation for child elements
  const children = el.querySelectorAll('.slide-title, .slide-body, .data-card, .bar, .tl-dot, .quote-block, .bullet-list li');
  children.forEach((c, i) => {
    c.classList.remove('active');
    setTimeout(() => c.classList.add('active'), 50 + i * 80);
  });
  // Number counter animation
  el.querySelectorAll('[data-counter]').forEach(el => {
    const target = parseFloat(el.dataset.counter);
    const dur = 1200;
    const start = performance.now();
    const step = (now) => {
      const t = Math.min(1, (now - start) / dur);
      const v = target * (1 - Math.pow(1 - t, 3));
      const formatted = target >= 1000 ? Math.round(v).toLocaleString() : v.toFixed(0);
      el.textContent = formatted + (el.dataset.suffix || '');
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
  currentSlide = n;
}

// Expose for Playwright
window.__activate = activate;

// Auto-activate first slide
window.addEventListener('load', () => setTimeout(() => activate(1), 200));
"""


def render_slide_html(slide: dict) -> str:
    """Convert one manifest entry into an HTML section."""
    n = slide["num"]
    title = slide.get("title", "")
    body = slide.get("body", "")
    layout = slide.get("layout", "default")

    parts = [f'<section class="slide" id="slide-{n}">']
    parts.append(f'<div class="slide-number">{n:02d} / 16</div>')
    parts.append(f'<div class="slide-section">SLIDE {n}</div>')

    if layout == "title":
        parts.append(f'<h1 class="slide-title">{title}</h1>')
        if body:
            parts.append(f'<p class="slide-body">{body}</p>')
    elif layout == "chart":
        parts.append(f'<h2 class="slide-title">{title}</h2>')
        bars = slide.get("bars", [])
        if bars:
            parts.append('<div class="chart-bars">')
            max_v = max(abs(b["v"]) for b in bars) or 1
            for b in bars:
                height = int(220 * abs(b["v"]) / max_v) + 4
                color = b.get("color", "gray")
                sign = "-" if b["v"] < 0 else ""
                parts.append(f'''<div class="bar-group">
                    <div class="bar {color}" style="height: 0;" data-target-h="{height}">
                        <div class="val">{sign}{b["v"]}%</div>
                    </div>
                    <div class="bar-label">{b["label"]}</div>
                </div>''')
            parts.append('</div>')
    elif layout == "data":
        parts.append(f'<h2 class="slide-title">{title}</h2>')
        if body:
            parts.append(f'<p class="slide-body">{body}</p>')
        cards = slide.get("cards", [])
        if cards:
            parts.append('<div class="data-row">')
            for c in cards:
                color = c.get("color", "")
                parts.append(f'''<div class="data-card">
                    <div class="label">{c["label"]}</div>
                    <div class="value {color}" data-counter="{c.get("counter", 0)}" data-suffix="{c.get("suffix", "")}">{c.get("display", c["label"])}</div>
                    {f'<div class="source">{c["source"]}</div>' if c.get("source") else ''}
                </div>''')
            parts.append('</div>')
    elif layout == "timeline":
        parts.append(f'<h2 class="slide-title">{title}</h2>')
        events = slide.get("events", [])
        if events:
            parts.append('<div class="timeline">')
            for e in events:
                color = e.get("color", "red")
                parts.append(f'''<div class="tl-node">
                    <div class="tl-dot {color}"></div>
                    <div class="tl-date">{e["date"]}</div>
                    <div class="tl-event">{e["event"]}</div>
                    {f'<div class="tl-detail">{e["detail"]}</div>' if e.get("detail") else ''}
                </div>''')
            parts.append('</div>')
    elif layout == "quote":
        parts.append(f'<h2 class="slide-title">{title}</h2>')
        parts.append(f'<div class="quote-block">"{slide.get("quote", body)}"</div>')
        if slide.get("source"):
            parts.append(f'<div class="quote-source">— {slide["source"]}</div>')
    elif layout == "list":
        parts.append(f'<h2 class="slide-title">{title}</h2>')
        items = slide.get("items", [body])
        parts.append('<ul class="bullet-list">')
        for item in items:
            parts.append(f'<li>{item}</li>')
        parts.append('</ul>')
    else:
        parts.append(f'<h2 class="slide-title">{title}</h2>')
        if body:
            parts.append(f'<p class="slide-body">{body}</p>')

    parts.append('</section>')
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path, help="Path to audio/manifest.json")
    ap.add_argument("narration", type=Path, help="Original narration.md for title")
    ap.add_argument("--out", type=Path, default=Path("slides/slide_deck.html"))
    ap.add_argument("--title", default=None)
    ap.add_argument("--watermark", default="● PatrickNoFilter")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    title = args.title or args.narration.stem.replace("-", " ").title()

    slides_html = "\n".join(render_slide_html(s) for s in manifest)

    # Inject bar grow heights via inline style fallback (already in template)
    html = HTML_TEMPLATE \
        .replace("__TITLE__", title) \
        .replace("__CSS__", CSS) \
        .replace("__SLIDES__", slides_html) \
        .replace("__WATERMARK__", args.watermark) \
        .replace("__MANIFEST__", json.dumps([{"num": s["num"], "dur": s["dur"]} for s in manifest]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"✓ {args.out} written ({args.out.stat().st_size/1024:.1f} KB, {len(manifest)} slides)")


if __name__ == "__main__":
    main()

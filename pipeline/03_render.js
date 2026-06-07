#!/usr/bin/env node
/**
 * Stage 3: Record the HTML slide deck to webm via Playwright Chromium.
 *
 * Usage:
 *   node 03_render.js <html_path> <out_webm> <manifest.json>
 *
 * Reads manifest.json (array of {num, dur}), auto-advances slides by
 * their TTS duration. Outputs a 1920x1080 webm at 25fps.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const HTML_PATH = process.argv[2];
const RECORD_DIR = process.argv[3];
const MANIFEST = JSON.parse(fs.readFileSync(process.argv[4], 'utf-8'));

(async () => {
  // Clean record dir
  if (fs.existsSync(RECORD_DIR)) {
    fs.readdirSync(RECORD_DIR).forEach(f => fs.unlinkSync(path.join(RECORD_DIR, f)));
  } else {
    fs.mkdirSync(RECORD_DIR, { recursive: true });
  }

  console.log('Launching Chromium...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_PATH || undefined,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
  });

  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: { dir: RECORD_DIR, size: { width: 1920, height: 1080 } }
  });
  const page = await ctx.newPage();

  console.log('Loading HTML...');
  await page.goto('file://' + HTML_PATH, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(800);

  const t0 = Date.now();
  for (let i = 0; i < MANIFEST.length; i++) {
    const slide = MANIFEST[i];
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    console.log(`[${(i+1).toString().padStart(2)}/${MANIFEST.length}] t=${elapsed}s  Slide ${slide.num} (${slide.dur.toFixed(1)}s)`);

    if (i > 0) {
      await page.evaluate((n) => window.__activate(n), slide.num);
      await page.waitForTimeout(300);
    }

    const waitMs = (i === 0 ? slide.dur * 1000 : (slide.dur * 1000) - 300);
    await page.waitForTimeout(waitMs);
  }

  const totalElapsed = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`\nTotal: ${totalElapsed}s`);

  await ctx.close();
  await browser.close();

  const webmFiles = fs.readdirSync(RECORD_DIR).filter(f => f.endsWith('.webm'));
  if (!webmFiles.length) throw new Error('No webm recorded');
  const webmPath = path.join(RECORD_DIR, webmFiles[webmFiles.length - 1]);
  const size = (fs.statSync(webmPath).size / 1024 / 1024).toFixed(1);
  const dur = execSync(`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${webmPath}"`).toString().trim();
  console.log(`✓ ${webmPath} (${size} MB, ${dur}s)`);
})().catch(e => { console.error('❌', e); process.exit(1); });

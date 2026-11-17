// Local, read-only comparison against the archived advisor runtime.
import { chromium } from '../.tools/audit/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] });
const results = { normalization: '1440x1000, fa-IR, Asia/Tehran, first office image, empty mobile step, local font, reduced motion; dialog crop excludes the S04 background', human_approved: false, comparisons: [] };
try {
  for (const [name, origin, button, selector] of [
    ['reference', 'http://127.0.0.1:3107', /^ورود$/, '[data-slot="dialog-content"]'],
    ['invest', 'http://127.0.0.1:3109', /^ورود به حساب$/, '.login-dialog'],
  ]) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'fa-IR', timezoneId: 'Asia/Tehran', reducedMotion: 'reduce' });
    await context.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort());
    const page = await context.newPage();
    await page.goto(origin, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.getByRole('button', { name: button }).first().click();
    const dialog = page.locator(selector);
    await dialog.waitFor();
    await dialog.locator('img').first().evaluate(img => img.decode());
    await page.waitForTimeout(300);
    await dialog.screenshot({ path: `docs/stage3/evidence/dialog-${name}-1440.png`, animations: 'disabled' });
    const measured = await dialog.evaluate(el => {
      const props = element => {
        const css = getComputedStyle(element); const box = element.getBoundingClientRect();
        return { width: box.width, height: box.height, font: css.fontFamily, fontSize: css.fontSize, lineHeight: css.lineHeight, fontWeight: css.fontWeight, color: css.color, background: css.backgroundColor, borderRadius: css.borderRadius, padding: css.padding };
      };
      return { dialog: props(el), title: props(el.querySelector('h2')), input: props(el.querySelector('input')), button: props(el.querySelector('button[type="submit"]')) };
    });
    const image = await dialog.locator('img').first().evaluate(async img => {
      // naturalWidth on a srcset image is density-corrected. Decode the raw URL to compare actual source pixels.
      const raw = new window.Image(); raw.src = img.currentSrc; await raw.decode();
      return { intrinsicWidth: raw.naturalWidth, intrinsicHeight: raw.naturalHeight, displayedWidth: img.width, displayedHeight: img.height, originalBytesServed: !img.currentSrc.includes('/_next/image') };
    });
    results.comparisons.push({ name, measured, image });
    await context.close();
  }
  results.metric_differences = [];
  const [reference, invest] = results.comparisons.map(item => item.measured);
  for (const element of Object.keys(reference)) for (const property of Object.keys(reference[element])) {
    if (reference[element][property] !== invest[element][property]) results.metric_differences.push({ element, property, reference: reference[element][property], invest: invest[element][property] });
  }
  results.image_dimensions_match = JSON.stringify(results.comparisons[0].image) === JSON.stringify(results.comparisons[1].image);
  results.metrics_match = results.metric_differences.length === 0;
  results.browser = browser.version();
  await fs.writeFile('docs/stage3/evidence/visual-metrics.json', JSON.stringify(results, null, 2) + '\n');
} finally { await browser.close(); }

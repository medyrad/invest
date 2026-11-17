import { chromium, expect } from '../frontend/node_modules/@playwright/test/index.mjs';
import fs from 'node:fs/promises';
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ?? '/usr/bin/google-chrome' });
const result = { origin: 'http://127.0.0.1:3108', viewports: [], errors: [] };
try {
  for (const width of [360, 390, 768, 1440]) {
    const page = await browser.newPage({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
    page.on('pageerror', e => result.errors.push(e.message));
    await page.goto(result.origin);
    await expect(page.locator('[data-section="featured"] article')).toHaveCount(6);
    await expect(page.getByLabel('دسته‌بندی', { exact: true }).locator('option')).toHaveCount(12);
    await page.getByRole('button', { name: 'ورود به حساب', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toContainText('شماره شما برای ورود استفاده می‌شود؛ اشتراک آن برای پیگیری فرصت فقط با رضایت شما و برای گیرندهٔ مشخص انجام می‌شود.');
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeFocused();
    result.viewports.push({ width, passed: true, catalog_groups: 11, preview_cards: 6, real_login_dialog: true });
    await page.close();
  }
  expect(result.errors).toEqual([]);
  await fs.writeFile('docs/stage4/evidence/image-browser.json', JSON.stringify(result, null, 2) + '\n');
  process.stdout.write('Actual delivery image: four viewports, API catalog, S03 dialog, Escape and focus passed\n');
} finally { await browser.close(); }

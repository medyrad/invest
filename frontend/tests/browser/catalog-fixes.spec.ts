import { expect, test } from '@playwright/test';
import path from 'node:path';

const out = path.resolve(__dirname, '../../../docs/stage4/fix-evidence');
const unavailable = 'فهرست شهرهای این شهرستان فعلاً در دسترس نیست؛ انتخاب شهرستان شما حفظ شده است.';
test.use({ trace: 'off', reducedMotion: 'reduce' });

test('S04-IT-001: customer city copy preserves county, real cities and parent clearing', async ({ page }, info) => {
  await page.goto('/');
  const province = page.getByLabel('استان', { exact: true });
  const county = page.getByLabel('شهرستان', { exact: true });
  const city = page.getByLabel('شهر', { exact: true });
  await province.selectOption({ label: 'آذربایجان شرقی' });
  await county.selectOption({ label: 'هوراند' });
  const selected = await county.inputValue(); expect(selected).not.toBe('');
  await expect(city).toBeDisabled(); await expect(city.locator('option')).toHaveCount(1);
  const message = page.getByText(unavailable, { exact: true });
  await expect(message).toBeVisible(); await expect(county).toHaveValue(selected);
  const panel = page.locator('[data-section="selectors"]');
  await panel.scrollIntoViewIfNeeded(); await page.evaluate(() => document.fonts.ready);
  expect(await message.evaluate(el => { const r = el.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth && el.scrollWidth <= el.clientWidth + 1; })).toBe(true);
  await panel.screenshot({ path: path.join(out, `city-empty-${info.project.name}.png`), animations: 'disabled' });
  await page.getByRole('button', { name: 'درباره انتخاب‌ها', exact: true }).click();
  const help = page.getByRole('dialog'); await expect(help).toContainText('انتخاب شهرستان شما حفظ می‌شود');
  await expect(help).not.toContainText(/S06|کاتالوگ|پیوند|منبع/);
  if (info.project.name === 'mobile-360') await help.screenshot({ path: path.join(out, 'city-help-mobile.png') });
  await page.keyboard.press('Escape');
  await province.selectOption({ label: 'تهران' });
  await expect(county).toHaveValue(''); await expect(city).toHaveValue('');
  await county.selectOption({ label: 'تهران' }); await expect(city).toBeEnabled();
  await expect(message).toHaveCount(0); await city.selectOption({ label: 'تهران' });
  expect(await city.inputValue()).not.toBe('');
  if (info.project.name === 'desktop-1440') await panel.screenshot({ path: path.join(out, 'city-available-desktop.png'), animations: 'disabled' });
  await province.selectOption({ label: 'آذربایجان شرقی' });
  await expect(county).toHaveValue(''); await expect(city).toHaveValue('');
  await county.selectOption({ label: 'هوراند' }); await expect(county).toHaveValue(selected); await expect(city).toBeDisabled();
});

test('S04-IT-002: real ICO metadata, fresh browser decode and short home navigation smoke', async ({ page, request }, info) => {
  const badResources: string[] = [];
  page.on('response', r => { if (r.status() >= 400) badResources.push(r.url()); });
  page.on('pageerror', e => badResources.push(e.message));
  const icon = await request.get('/favicon.ico');
  expect(icon.status()).toBe(200); expect(icon.headers()['content-type']).toMatch(/^image\/(x-icon|vnd\.microsoft\.icon)/);
  const bytes = await icon.body(); expect([...bytes.subarray(0, 4)]).toEqual([0, 0, 1, 0]);
  expect(bytes.readUInt16LE(4)).toBe(4); expect(bytes.subarray(0, 100).toString()).not.toMatch(/<!doctype|<html/i);
  await page.goto('/'); await expect(page.locator('[data-section="featured"] article')).toHaveCount(6);
  for (const section of ['hero', 'main-categories', 'categories', 'featured', 'how', 'help']) await expect(page.locator(`[data-section="${section}"]`)).toHaveCount(1);
  const link = page.locator('link[rel="icon"]'); await expect(link).toHaveAttribute('href', '/favicon.ico');
  await expect(link).toHaveAttribute('type', 'image/x-icon');
  const decoded = await page.evaluate(async () => {
    const image = new Image(); image.src = document.querySelector<HTMLLinkElement>('link[rel="icon"]')!.href;
    await image.decode(); return { width: image.naturalWidth, height: image.naturalHeight };
  });
  expect(decoded.width).toBeGreaterThan(0); expect(decoded.height).toBe(decoded.width);
  if (info.project.use.viewport!.width < 1024) {
    const menu = page.getByRole('button', { name: 'منوی اصلی', exact: true }); await menu.click();
    await expect(page.getByRole('menuitem', { name: 'دستیار', exact: true })).toBeVisible();
    await page.keyboard.press('Escape'); await expect(menu).toBeFocused();
  } else {
    await page.locator('header').getByRole('link', { name: 'دستیار', exact: true }).click();
    await expect(page.getByText('این مقصد در نسخه آزمایشی فعلی فعال نیست', { exact: false })).toBeVisible();
    await page.getByRole('link', { name: 'بازگشت به خانه', exact: true }).click();
  }
  expect(badResources).toEqual([]);
});

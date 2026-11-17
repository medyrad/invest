import { expect, test } from '@playwright/test';
import path from 'node:path';

test.use({ trace: 'off', reducedMotion: 'reduce' });

test('home includes all active sections, real catalog and a truthful sample label', async ({ page }, info) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('[data-section="categories"]')).toBeVisible();
  for (const section of ['hero','main-categories','categories','featured','how','help']) await expect(page.locator(`[data-section="${section}"]`)).toHaveCount(1);
  await expect(page.getByRole('note')).toContainText('داده نمونه');
  await expect(page.locator('[data-section="featured"] article')).toHaveCount(6);
  await expect(page.locator('text=/\\d+٪ تطابق/')).toHaveCount(0);
  const groups = await page.getByLabel('دسته‌بندی', { exact: true }).locator('option').count();
  expect(groups).toBe(12);
  expect(await page.getByLabel('استان', { exact: true }).locator('option').count()).toBe(32);
  for (const section of ['hero','main-categories','categories','featured','how','help']) {
    const target = page.locator(`[data-section="${section}"]`); await target.scrollIntoViewIfNeeded();
    // The reference focus-blur pseudo-element deliberately extends 56px; inspect visible content instead.
    await expect.poll(() => target.locator('h1,h2,h3,p,button,a,input,select,article').evaluateAll(elements => elements.filter(el => {
      const css = getComputedStyle(el), rect = el.getBoundingClientRect();
      return css.visibility !== 'hidden' && rect.width > 2 && rect.height > 2 && !el.closest('[aria-hidden="true"], [inert]');
    }).every(el => { const r = el.getBoundingClientRect(); return r.left >= -1 && r.right <= innerWidth + 1; })), { message: `${section}: visible content stays inside viewport` }).toBe(true);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  // Reveal every card, including sections taller than the mobile viewport, before freezing the image.
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (let y = 0; y < await page.evaluate(() => document.documentElement.scrollHeight); y += 600) {
    await page.evaluate(v => window.scrollTo(0, v), y); await page.waitForTimeout(350);
  }
  await page.evaluate(() => document.fonts.ready);
  if (page.viewportSize()!.width <= 500) {
    const cards = await page.locator('[data-map-feed] > a').evaluateAll(es => es.map(el => { const r = el.getBoundingClientRect(); return { y: r.y, bottom: r.bottom }; }));
    expect(cards.length).toBe(2);
    expect(cards.every((r, i) => !i || r.y >= cards[i - 1].bottom)).toBe(true);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const out = process.env.INVEST_S04_EVIDENCE ?? path.resolve('../docs/stage4/evidence');
  await page.screenshot({ path: path.join(out, `home-${info.project.name}.png`), fullPage: true, clip: { x: 0, y: 0, width: page.viewportSize()!.width, height: await page.evaluate(() => document.documentElement.scrollHeight) }, animations: 'disabled' });
});

test('catalog parent changes clear invalid children and remove/clear controls work', async ({ page }) => {
  await page.goto('/');
  const group = page.getByLabel('دسته‌بندی', { exact: true }), sub = page.getByLabel('زیردسته', { exact: true });
  await expect(group).toBeVisible(); await group.selectOption('building'); await sub.selectOption('residential');
  await group.selectOption('energy'); await expect(sub).toHaveValue('');
  const province = page.getByLabel('استان', { exact: true }), county = page.getByLabel('شهرستان', { exact: true });
  await province.selectOption('province-07'); await county.selectOption({ label: 'تهران' });
  await page.getByLabel('شهر').selectOption({ label: 'تهران' });
  await province.selectOption('province-03'); await expect(county).toHaveValue('');
  await expect(page.getByLabel('شهر')).toHaveValue('');
  await page.getByRole('button', { name: 'حذف استان', exact: true }).click(); await expect(province).toHaveValue('');
  await page.getByRole('button', { name: 'پاک‌کردن انتخاب‌ها', exact: true }).click(); await expect(group).toHaveValue('');
  await page.getByRole('button', { name: 'درباره انتخاب‌ها', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('فقط بر امتیاز'); await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'درباره انتخاب‌ها', exact: true })).toBeFocused();
});

test('catalog failure, retry, empty response and recovery never fabricate fresh data', async ({ page }) => {
  await page.route('**/api/v1/catalog/**', route => route.fulfill({ status: 503, contentType: 'application/json', body: '{}' }));
  await page.goto('/'); await expect(page.getByRole('region', { name: 'وضعیت کاتالوگ' })).toContainText('دریافت کاتالوگ انجام نشد');
  await expect(page.locator('[data-section="featured"] article')).toHaveCount(0);
  await page.unroute('**/api/v1/catalog/**');
  await page.route('**/api/v1/catalog/taxonomy', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ version: 'test-empty', groups: [] }) }));
  await page.getByRole('button', { name: 'تلاش دوباره', exact: true }).click();
  await expect(page.getByRole('region', { name: 'وضعیت کاتالوگ' })).toContainText('کاتالوگ هنوز داده‌ای ندارد');
  await page.unroute('**/api/v1/catalog/taxonomy'); await page.getByRole('button', { name: 'تلاش دوباره', exact: true }).click();
  await expect(page.getByLabel('دسته‌بندی', { exact: true })).toBeVisible();
});

test('navigation, mobile menu and help disclose future destinations', async ({ page }, info) => {
  await page.goto('/'); await expect(page.locator('[data-section="help"]')).toBeVisible();
  if (info.project.use.viewport!.width < 1024) {
    await page.getByRole('button', { name: 'منوی اصلی', exact: true }).click();
    await page.getByRole('menuitem', { name: 'دستیار', exact: true }).click();
  } else await page.locator('header').getByRole('link', { name: 'دستیار', exact: true }).click();
  await expect(page.getByText('این مقصد در نسخه آزمایشی فعلی فعال نیست', { exact: false })).toBeVisible();
  await page.getByRole('link', { name: 'بازگشت به خانه', exact: true }).click();
  const help = page.locator('[data-section="help"] button[aria-expanded]').nth(1); await help.click();
  await expect(help).toHaveAttribute('aria-expanded','true'); await help.press('Enter'); await expect(help).toHaveAttribute('aria-expanded','false');
});

test('public preview-disabled response renders no synthetic cards or calculated score', async ({ page }) => {
  await page.route('**/api/v1/catalog/preview', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ version: 'public', enabled: false, synthetic: true, listings: [] }) }));
  await page.goto('/'); await expect(page.locator('[data-section="featured"]')).toBeVisible();
  await expect(page.locator('[data-section="featured"] article')).toHaveCount(0);
  await expect(page.getByText('فرصت نمایشی در حالت عمومی فعال نیست.', { exact: true })).toBeVisible();
});

test('motion and reduced-motion remain distinct without hydration errors @desktop', async ({ browser }) => {
  for (const mode of ['no-preference', 'reduce'] as const) {
    const context = await browser.newContext({ baseURL: 'http://127.0.0.1:3109', viewport: { width: 1440, height: 1000 }, reducedMotion: mode });
    const page = await context.newPage(), errors: string[] = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.clock.install(); await page.goto('/');
    await expect(page.locator('[data-section="featured"] article')).toHaveCount(6);
    const ring = page.locator('[data-section="hero"] svg').filter({ has: page.locator('line') });
    await page.clock.runFor(1000);
    const before = await ring.evaluate(el => getComputedStyle(el).transform);
    await page.clock.runFor(2000);
    const after = await ring.evaluate(el => getComputedStyle(el).transform);
    if (mode === 'reduce') {
      expect(after).toBe(before);
      await expect(page.locator('[data-section="hero"] a.surface')).toHaveCount(2);
    } else expect(after).not.toBe(before);
    expect(errors).toEqual([]); await context.close();
  }
});

test('touch menu and keyboard catalog controls retain focus and clear descendants @desktop', async ({ browser }) => {
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:3109', viewport: { width: 360, height: 800 }, hasTouch: true, isMobile: true, reducedMotion: 'reduce' });
  const page = await context.newPage(); await page.goto('/');
  await page.getByRole('button', { name: 'منوی اصلی', exact: true }).tap();
  await expect(page.getByRole('menuitem', { name: 'دستیار', exact: true })).toBeVisible();
  await page.keyboard.press('Escape'); await expect(page.getByRole('button', { name: 'منوی اصلی', exact: true })).toBeFocused();
  const group = page.getByLabel('دسته‌بندی', { exact: true }), subtype = page.getByLabel('زیردسته', { exact: true });
  await group.focus(); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter'); await expect(group).toHaveValue('building');
  await subtype.focus(); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter'); await expect(subtype).toHaveValue('residential');
  await group.focus(); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter'); await expect(subtype).toHaveValue('');
  await page.getByRole('button', { name: 'پاک‌کردن انتخاب‌ها', exact: true }).tap(); await expect(group).toHaveValue('');
  await context.close();
});

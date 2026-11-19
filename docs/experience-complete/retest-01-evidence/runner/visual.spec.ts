import {expect, test} from '@playwright/test';
import fs from 'node:fs';

const reference = 'http://expit-reference:3107';

for (const width of [360, 390, 768, 1440]) test(`fresh same-state profile and land reference ${width}`, async ({browser}) => {
  test.setTimeout(180000);
  const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
  const product = await context.newPage();
  const source = await context.newPage();

  await source.goto(`${reference}/tools/ma-profile`);
  await expect(source.getByText('اطلاعات پایه', {exact: true})).toBeVisible({timeout: 60000});
  await source.evaluate(() => document.fonts.ready);
  await source.screenshot({path: `/retest/reference-profile-${width}.png`, fullPage: true});
  await product.goto('/tools/ma-profile');
  await expect(product.locator('.professional-form')).toBeVisible({timeout: 30000});
  await product.evaluate(() => document.fonts.ready);
  await product.screenshot({path: `/retest/product-profile-${width}.png`, fullPage: true});

  await source.goto(`${reference}/tools/land-preparation`);
  await expect(source.getByText('انتخاب خدمات و محل', {exact: true})).toBeVisible({timeout: 60000});
  await source.evaluate(() => document.fonts.ready);
  await source.screenshot({path: `/retest/reference-land-${width}.png`, fullPage: true});
  await product.goto('/tools/land-preparation');
  await expect(product.getByText('انتخاب خدمات و محل', {exact: true})).toBeVisible({timeout: 30000});
  await product.evaluate(() => document.fonts.ready);
  await product.screenshot({path: `/retest/product-land-${width}.png`, fullPage: true});

  await context.close();
});

test('fresh guide preview and downloaded HTML are visibly readable', async ({page}) => {
  await page.goto('/local-roles');
  await page.getByRole('button', {name: / · user$/}).click();
  await page.waitForURL(url => !url.pathname.includes('local-roles'));
  await page.goto('/opportunities');
  await expect(page.locator('article').first()).toBeVisible({timeout: 30000});
  const href = await page.locator('article').first().getByRole('link').first().getAttribute('href');
  await page.goto(`/guide/${href!.split('/').pop()}`);
  const frame = page.frameLocator('iframe[title="راهنمای اقدام"]');
  await expect(frame.getByRole('heading', {name: /گام‌های اقدام/})).toBeVisible({timeout: 30000});
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({path: '/retest/report-preview-visible.png', fullPage: true});
  const wait = page.waitForEvent('download');
  await page.getByRole('button', {name: 'دانلود فایل راهنما', exact: true}).click();
  const download = await wait;
  const path = await download.path();
  // فایل دانلودی بدون پسوند در temp مرورگر text/plain باز می‌شود؛ همان bytes را
  // برای مشاهده واقعی HTML در document مستقل render می‌کنیم.
  await page.setContent(fs.readFileSync(path!, 'utf8'), {waitUntil: 'load'});
  await expect(page.getByRole('heading', {name: /گام‌های اقدام/})).toBeVisible();
  await page.screenshot({path: '/retest/report-download-visible.png', fullPage: true});
});

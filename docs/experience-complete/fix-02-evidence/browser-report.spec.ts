import {expect, test} from '@playwright/test';
import fs from 'node:fs';

test('preview, first download and redownload use the same Persian route label', async ({page}) => {
  await page.goto('/local-roles');
  await page.getByRole('button', {name: / · user$/}).click();
  await page.waitForURL(url => !url.pathname.includes('local-roles'));
  await page.goto('/opportunities');
  await expect(page.locator('article').first()).toBeVisible({timeout: 30_000});
  const href = await page.locator('article').first().getByRole('link').first().getAttribute('href');
  await page.goto(`/guide/${href!.split('/').pop()}`);

  const frame = page.frameLocator('iframe[title="راهنمای اقدام"]');
  await expect(frame.getByText('مسیر: سرمایه‌گذار', {exact: true})).toBeVisible({timeout: 30_000});
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({path: '/evidence/browser-preview.png', fullPage: true});

  const downloadButton = page.getByRole('button', {name: 'دانلود فایل راهنما', exact: true});
  await expect(downloadButton).toBeEnabled();
  const [receipt, firstDownload] = await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/api/v1/core/personal') && response.request().method() === 'POST'),
    page.waitForEvent('download'),
    downloadButton.click(),
  ]);
  expect(receipt.status()).toBe(200);
  const firstPath = await firstDownload.path();
  const first = fs.readFileSync(firstPath!, 'utf8');
  expect(first).toContain('مسیر: سرمایه‌گذار');
  expect(first).not.toContain('مسیر: investor');

  await page.goto('/profile');
  const saved = page.getByRole('heading', {name: 'گزارش‌های ذخیره‌شده'}).locator('..').getByRole('link').first();
  await expect(saved).toBeVisible({timeout: 30_000});
  const secondEvent = page.waitForEvent('download');
  await saved.click();
  const secondPath = await (await secondEvent).path();
  const second = fs.readFileSync(secondPath!, 'utf8');
  expect(second).toBe(first);

  await page.setContent(second, {waitUntil: 'load'});
  await expect(page.getByText('مسیر: سرمایه‌گذار', {exact: true})).toBeVisible();
  await page.screenshot({path: '/evidence/browser-redownload.png', fullPage: true});
  fs.writeFileSync('/evidence/fresh-report.html', second);
});

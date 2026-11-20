import {expect, test} from '@playwright/test';
import fs from 'node:fs';

test('investor preview and frozen downloads show the Persian route label', async ({page}) => {
  await page.goto('/local-roles');
  await page.getByRole('button', {name: / · user$/}).click();
  await page.waitForURL(url => !url.pathname.includes('local-roles'));
  await page.goto('/opportunities');
  await expect(page.locator('article').first()).toBeVisible({timeout: 30_000});
  const href = await page.locator('article').first().getByRole('link').first().getAttribute('href');
  await page.goto(`/guide/${href!.split('/').pop()}`);

  const frame = page.frameLocator('iframe[title="راهنمای اقدام"]');
  await expect(frame.getByText('مسیر: سرمایه‌گذار', {exact: true})).toBeVisible({timeout: 30_000});
  await expect(frame.getByText('مسیر: investor', {exact: true})).toHaveCount(0);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({path: '/evidence/browser-preview.png', fullPage: true});

  const button = page.getByRole('button', {name: 'دانلود فایل راهنما', exact: true});
  const [mutation, download] = await Promise.all([
    page.waitForResponse(r => r.url().endsWith('/api/v1/core/personal') && r.request().method() === 'POST'),
    page.waitForEvent('download'),
    button.click(),
  ]);
  expect(mutation.status()).toBe(200);
  const first = fs.readFileSync((await download.path())!, 'utf8');
  expect(first).toContain('مسیر: سرمایه‌گذار');
  expect(first).not.toContain('مسیر: investor');

  await page.goto('/profile');
  const saved = page.getByRole('heading', {name: 'گزارش‌های ذخیره‌شده'}).locator('..').getByRole('link').first();
  await expect(saved).toBeVisible({timeout: 30_000});
  const redownload = page.waitForEvent('download');
  await saved.click();
  const second = fs.readFileSync((await (await redownload).path())!, 'utf8');
  expect(second).toBe(first);
  await page.setContent(second, {waitUntil: 'load'});
  await expect(page.getByText('مسیر: سرمایه‌گذار', {exact: true})).toBeVisible();
  await expect(page.getByText('مسیر: investor', {exact: true})).toHaveCount(0);
  await page.screenshot({path: '/evidence/browser-redownload.png', fullPage: true});
  fs.writeFileSync('/evidence/fresh-report.html', second);
});

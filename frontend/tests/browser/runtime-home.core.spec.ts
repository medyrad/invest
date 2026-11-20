import { randomInt } from 'node:crypto';
import { expect, test, type Browser } from '@playwright/test';

const port = new URL(process.env.CORE_URL || 'http://127.0.0.1:3108').port || '3108';

async function login(browser: Browser, host: 'localhost' | '127.0.0.1') {
  const context = await browser.newContext({ baseURL: `http://${host}:${port}`, viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  await page.goto('/');
  await page.getByRole('button', { name: 'ورود به حساب', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('textbox', { name: 'شماره موبایل', exact: true }).fill(`0912${randomInt(1000000, 9999999)}`);
  await page.getByRole('button', { name: 'دریافت کد', exact: true }).click();
  const code = await page.getByTestId('trial-code').textContent();
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill(code!);
  await page.getByRole('button', { name: 'ورود', exact: true }).click();
  await expect(page.getByRole('button', { name: /^حساب کاربری/ })).toBeVisible();
  expect((await context.cookies()).find(cookie => cookie.name === 'invest_session')?.httpOnly).toBe(true);
  await context.close();
}

test('primary runtime login succeeds on both exact development aliases', async ({ browser }) => {
  await login(browser, 'localhost');
  await login(browser, '127.0.0.1');
});

test('published multi-city map remains useful with motion and reduced motion', async ({ browser }) => {
  for (const width of [390, 1440]) for (const reducedMotion of ['reduce', 'no-preference'] as const) {
    const context = await browser.newContext({ baseURL: `http://127.0.0.1:${port}`, viewport: { width, height: width === 390 ? 844 : 1000 }, reducedMotion });
    const page = await context.newPage();
    await page.goto('/');
    const points = page.locator('[data-map-scene] svg g[aria-label*="پروژه"]');
    await expect(points).toHaveCount(4, { timeout: 15_000 });
    const links = page.locator('[data-map-feed] a[href^="/opportunities/"]');
    await expect(links.first()).toBeVisible({ timeout: reducedMotion === 'reduce' ? 5_000 : 8_000 });
    if (reducedMotion === 'reduce') await expect(links).toHaveCount(2);
    const target = await links.first().getAttribute('href');
    await links.first().click();
    await expect(page).toHaveURL(new RegExp(`${target!.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`));
    await expect(page.locator('main')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await context.close();
  }
});

test('delayed home bootstrap shows skeleton then content, and failure retries without stale success', async ({ browser }) => {
  for (const width of [390, 1440]) {
    const context = await browser.newContext({ baseURL: `http://127.0.0.1:${port}`, viewport: { width, height: width === 390 ? 844 : 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    let release!: () => void;
    const delayed = new Promise<void>(resolve => { release = resolve; });
    await page.route('**/api/v1/core/opportunities', async route => {
      const response = await route.fetch();
      await delayed;
      await route.fulfill({ response });
    });
    await page.goto('/');
    await expect(page.locator('[data-loading="home-map"]')).toBeVisible();
    await expect(page.locator('[data-loading="home-catalog"]')).toBeVisible();
    await expect(page.locator('[data-section="featured"] article')).toHaveCount(0);
    expect(await page.locator('.loading-skeleton').first().evaluate(element => getComputedStyle(element).animationName)).toBe('none');
    release();
    await expect(page.locator('[data-map-scene]')).toBeVisible();
    await page.unroute('**/api/v1/core/opportunities');
    let fail = true;
    await page.route('**/api/v1/catalog/taxonomy', route => fail ? route.fulfill({ status: 503, contentType: 'application/json', body: '{}' }) : route.continue());
    await page.reload();
    await expect(page.locator('[data-loading-error]')).toBeVisible();
    await expect(page.locator('[data-section="featured"] article')).toHaveCount(0);
    fail = false;
    await page.getByRole('button', { name: 'تلاش دوباره', exact: true }).click();
    await expect(page.locator('[data-map-scene]')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await context.close();
  }
});

test('report wait uses the lazy local animation and resolves to the server preview', async ({ browser }) => {
  const context = await browser.newContext({ baseURL: `http://127.0.0.1:${port}`, viewport: { width: 1440, height: 1000 }, reducedMotion: 'no-preference' });
  const page = await context.newPage();
  const external: string[] = [];
  const animationRequests: string[] = [];
  const wasmRequests: string[] = [];
  page.on('request', request => {
    const url = new URL(request.url());
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) external.push(request.url());
    if (url.pathname === '/animations/invest-analysis.json') animationRequests.push(request.url());
    if (url.pathname === '/animations/dotlottie-player.wasm') wasmRequests.push(request.url());
  });
  await page.goto('/');
  const opportunity = await page.locator('[data-map-feed] a[href^="/opportunities/"]').first().getAttribute('href');
  await page.goto(opportunity!);
  let release!: () => void;
  const delayed = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/core/guide/*', async route => {
    const response = await route.fetch();
    await delayed;
    await route.fulfill({ response });
  });
  await page.getByRole('link', { name: /دیدن راهنمای اقدام/ }).first().click();
  await expect(page.locator('[data-loading="report"]')).toBeVisible({ timeout: 20_000 });
  await expect(page.locator('[data-meaningful-loader]')).toBeVisible({ timeout: 20_000 });
  await expect.poll(() => animationRequests.length).toBeGreaterThan(0);
  await expect.poll(() => wasmRequests.length).toBeGreaterThan(0);
  release();
  await expect(page.getByTitle('راهنمای اقدام')).toBeVisible({ timeout: 15_000 });
  await page.unroute('**/api/v1/core/guide/*');
  expect(external).toEqual([]);
  await context.close();
});

import { expect, test } from '@playwright/test';

test('Persian shell loads the local reference font at both widths', async ({ page }, testInfo) => {
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'fa');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  await expect(page.getByRole('heading', { name: /سرمایه‌تان را/ })).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('32px Vazirmatn'))).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(failures).toEqual([]);
  await page.screenshot({ path: `../docs/stage3/evidence/foundation-${testInfo.project.name}.png` });
});

test('same-origin preserves JSON, query, cookies and CSRF rejection', async ({ page, context }) => {
  await page.goto('/');
  const result = await page.evaluate(async () => {
    const bootstrap = await fetch('/api/v1/auth/csrf');
    const { csrfToken } = await bootstrap.json();
    document.cookie = 'probe=browser; SameSite=Lax; Path=/';
    const denied = await fetch('/api/v1/_test/probe', { method: 'POST' });
    const accepted = await fetch('/api/v1/_test/probe?q=' + encodeURIComponent('تهران'), {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ message: 'سرمایه‌گزین', amount: '1500000000' }),
    });
    const method = await fetch('/api/v1/health/live', { method: 'POST', headers: { 'X-CSRFToken': csrfToken } });
    return {
      denied: denied.status, accepted: accepted.status, body: await accepted.json(),
      method: method.status, requestId: accepted.headers.get('X-Request-ID'),
      exposedCookie: document.cookie.includes('csrftoken'),
    };
  });
  expect(result.denied).toBe(403);
  expect(result.accepted).toBe(200);
  expect(result.method).toBe(405);
  expect(result.body).toEqual({ method: 'POST', body: { message: 'سرمایه‌گزین', amount: '1500000000' }, query: 'تهران', cookie: 'browser' });
  expect(result.requestId).toMatch(/^[\da-f-]{36}$/);
  expect(result.exposedCookie).toBe(false);
  const cookies = await context.cookies();
  expect(cookies.find(cookie => cookie.name === 'csrftoken')?.httpOnly).toBe(true);
  expect(cookies.find(cookie => cookie.name === 'probe_reply')?.value).toBe('received');
  const forbidden = await context.request.post('/api/v1/_test/probe', {
    headers: { Origin: 'https://evil.example', 'X-CSRFToken': 'invalid' },
  });
  expect(forbidden.status()).toBe(403);
});

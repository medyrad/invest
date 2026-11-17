import { randomInt } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

test.use({ trace: 'off' });
const root = path.resolve(__dirname, '../../..');
const phone = () => '0913' + String(randomInt(1000000, 9999999));
const privacy = 'شماره شما برای ورود استفاده می‌شود؛ اشتراک آن برای پیگیری فرصت فقط با رضایت شما و برای گیرندهٔ مشخص انجام می‌شود.';
const channelName = 'invest-auth-events-v1';

async function open(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'ورود به حساب', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
}
async function issue(page: Page, mobile = phone()) {
  await page.getByRole('textbox', { name: 'شماره موبایل', exact: true }).fill(mobile);
  const response = page.waitForResponse(r => r.url().endsWith('/auth/issue'));
  await page.getByRole('button', { name: 'دریافت کد', exact: true }).click();
  const receipt = await (await response).json();
  await expect(page.getByTestId('trial-code')).toBeVisible();
  return receipt as { challenge_id: string; expires_at: string; notification: { code: string } };
}
async function login(page: Page, mobile = phone()) {
  await open(page);
  const receipt = await issue(page, mobile);
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill(receipt.notification.code);
  await page.getByRole('button', { name: 'ورود', exact: true }).click();
  await expect(page.getByRole('region', { name: 'وضعیت ورود' })).toBeVisible();
  return receipt;
}
function inspect(challenge: string): { issues: number; activity: string[] } {
  if (!/^[a-f0-9-]{36}$/.test(challenge)) throw new Error('Synthetic challenge UUID required');
  const script = `import json; from django.conf import settings; from apps.identity.models import OTPChallenge,IssueEvent,AuthSession; assert settings.INVEST_ENV=='test' and settings.DATABASES['default']['NAME']=='invest_browser'; u=OTPChallenge.objects.get(pk='${challenge}').user_id; print(json.dumps({'issues':IssueEvent.objects.filter(user_id=u).count(),'activity':list(AuthSession.objects.filter(user_id=u).order_by('id').values_list('last_activity',flat=True))},default=str))`;
  const output = execFileSync('docker', ['compose', '--env-file', '.env', '-f', 'deploy/compose.yaml', 'exec', '-T', 'browser-api', '/app/.venv/bin/python', 'manage.py', 'shell', '-c', script], { cwd: root, encoding: 'utf8' });
  return JSON.parse(output.trim().split('\n').at(-1)!);
}

test('@desktop S03-IT-001: lost accepted resend recovers its key, challenge, TTL and quota', async ({ page }) => {
  test.setTimeout(100_000);
  await open(page);
  const first = await issue(page);
  await page.getByRole('button', { name: 'دریافت کد تازه', exact: true }).waitFor({ state: 'visible', timeout: 65_000 });
  const requests: { key: string; mobile: string }[] = [];
  let accepted: typeof first | undefined;
  let failResponse = true;
  await page.route('**/api/v1/auth/issue', async route => {
    requests.push(route.request().postDataJSON());
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    const receipt = await response.json();
    if (failResponse) {
      accepted = receipt;
      failResponse = false;
      await route.abort('failed');
    } else {
      expect(receipt.challenge_id === accepted!.challenge_id).toBe(true);
      expect(receipt.expires_at === accepted!.expires_at).toBe(true);
      await route.fulfill({ response });
    }
  });
  await page.getByRole('button', { name: 'دریافت کد تازه', exact: true }).click();
  await expect(page.locator('.auth-error')).toBeVisible();
  await expect(page.getByTestId('trial-code')).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'ورود', exact: true })).toBeDisabled();
  expect(inspect(first.challenge_id).issues).toBe(2);
  await page.getByRole('button', { name: 'تلاش دوباره برای دریافت نتیجه', exact: true }).click();
  await expect(page.getByTestId('trial-code')).toBeVisible();
  expect(requests.length).toBe(2);
  expect(requests[0].key === requests[1].key).toBe(true);
  expect(requests[0].mobile === requests[1].mobile).toBe(true);
  expect(accepted!.challenge_id !== first.challenge_id).toBe(true);
  expect(inspect(first.challenge_id).issues).toBe(2);
  const recovered = (await page.getByTestId('trial-code').textContent())!;
  expect(recovered === accepted!.notification.code).toBe(true);
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill(recovered);
  await page.getByRole('button', { name: 'ورود', exact: true }).click();
  await expect(page.getByRole('region', { name: 'وضعیت ورود' })).toBeVisible();
});

test('@desktop S03-IT-002: logout clears the other tab without affecting an independent device', async ({ page, context, browser }) => {
  const messages: unknown[] = [];
  await context.exposeBinding('__observeAuthSignal', (_source, value) => { messages.push(value); });
  await context.addInitScript(() => {
    const original = window.BroadcastChannel.prototype.postMessage;
    window.BroadcastChannel.prototype.postMessage = function (value: unknown) {
      void (window as unknown as { __observeAuthSignal: (data: unknown) => Promise<void> }).__observeAuthSignal(value);
      return original.call(this, value);
    };
  });
  const mobile = phone();
  const receipt = await login(page, mobile);
  const tab = await context.newPage();
  await tab.goto('/');
  await expect(tab.getByRole('region', { name: 'وضعیت ورود' })).toBeVisible();
  const device = await browser.newContext({ baseURL: new URL(page.url()).origin });
  try {
    const other = await device.newPage();
    await login(other, mobile);
    const activity = inspect(receipt.challenge_id).activity;
    await page.getByRole('button', { name: 'حساب کاربری', exact: true }).click();
  await page.getByRole('menuitem', { name: 'خروج', exact: true }).click();
    await expect(page.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeVisible();
    await expect(tab.getByRole('region', { name: 'وضعیت ورود' })).not.toBeVisible();
    expect(await tab.locator('.account-status-header [dir="ltr"]').count()).toBe(0);
    expect((await (await tab.request.get('/api/v1/auth/me')).json()).authenticated).toBe(false);
    expect((await (await other.request.get('http://127.0.0.1:3109/api/v1/auth/me')).json()).authenticated).toBe(true);
    await expect(other.getByRole('region', { name: 'وضعیت ورود' })).toBeVisible();
    expect(inspect(receipt.challenge_id).activity).toEqual(activity);
    await expect.poll(() => messages.length).toBeGreaterThan(0);
    expect(messages.every(value => JSON.stringify(value) === JSON.stringify({ type: 'session-invalidated' }))).toBe(true);
  } finally { await device.close(); }
});

test('@desktop S03-IT-002: a delayed old me response cannot restore identity after logout', async ({ page, context }) => {
  await login(page);
  const tab = await context.newPage();
  await tab.goto('/');
  await expect(tab.getByRole('region', { name: 'وضعیت ورود' })).toBeVisible();
  let release!: () => void;
  let captured!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  const capturedResponse = new Promise<void>(resolve => { captured = resolve; });
  let first = true;
  await tab.route('**/api/v1/auth/me', async route => {
    const response = await route.fetch();
    if (first) {
      first = false;
      expect((await response.json()).authenticated).toBe(true);
      captured();
      await held;
    }
    await route.fulfill({ response });
  });
  await tab.evaluate(() => window.dispatchEvent(new Event('focus')));
  await capturedResponse;
  await page.getByRole('button', { name: 'حساب کاربری', exact: true }).click();
  await page.getByRole('menuitem', { name: 'خروج', exact: true }).click();
  await expect(page.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeVisible();
  await expect(tab.getByRole('region', { name: 'وضعیت ورود' })).not.toBeVisible();
  const delivered = tab.waitForResponse(async r => r.url().endsWith('/auth/me') && (await r.json()).authenticated === true);
  release();
  await delivered;
  await tab.evaluate(() => new Promise<void>(resolve => window.requestAnimationFrame(() => resolve())));
  await expect(tab.getByRole('region', { name: 'وضعیت ورود' })).not.toBeVisible();
  await expect(tab.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeVisible();
  // A later fresh server read must also stay logged out.
  const fresh = tab.waitForResponse(r => r.url().endsWith('/auth/me'));
  await tab.evaluate(() => window.dispatchEvent(new Event('pageshow')));
  expect((await (await fresh).json()).authenticated).toBe(false);
  await expect(tab.getByRole('region', { name: 'وضعیت ورود' })).not.toBeVisible();
});

test('@desktop S03-IT-002: focus, visibility and page return recheck me without extending idle', async ({ page, context }) => {
  const receipt = await login(page);
  const activity = inspect(receipt.challenge_id).activity;
  const paths: string[] = [];
  page.on('request', r => { if (r.url().includes('/api/v1/auth/')) paths.push(new URL(r.url()).pathname); });
  for (const event of ['focus', 'visibilitychange', 'pageshow']) {
    const response = page.waitForResponse(r => r.url().endsWith('/auth/me'));
    await page.evaluate(type => (type === 'visibilitychange' ? document : window).dispatchEvent(new Event(type)), event);
    expect((await (await response).json()).authenticated).toBe(true);
  }
  expect(inspect(receipt.challenge_id).activity).toEqual(activity);
  expect(paths.every(value => value === '/api/v1/auth/me')).toBe(true);
  await page.goto('/?return=1');
  await expect(page.getByRole('region', { name: 'وضعیت ورود' })).toBeVisible();
  const csrf = (await (await context.request.get('/api/v1/auth/csrf')).json()).csrfToken;
  await context.request.post('/api/v1/auth/logout', { headers: { 'X-CSRFToken': csrf }, data: {} });
  await page.goBack();
  await expect(page.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeVisible();
  expect(inspect(receipt.challenge_id).activity).toEqual(activity);
});

test('@desktop S03-IT-002: cross-tab signals cannot grant identity without server evidence', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeEnabled();
  const response = page.waitForResponse(r => r.url().endsWith('/auth/me'));
  await page.evaluate(name => {
    const channel = new window.BroadcastChannel(name);
    channel.postMessage({ type: 'session-invalidated', authenticated: true, user: { role: 'admin' } });
    channel.close();
  }, channelName);
  expect((await (await response).json()).authenticated).toBe(false);
  await expect(page.getByRole('region', { name: 'وضعیت ورود' })).not.toBeVisible();
});

test('S03-IT-003: approved D26 copy wraps readably without changing reference typography', async ({ page }, info) => {
  await open(page);
  await page.evaluate(() => document.fonts.ready);
  const note = page.locator('.privacy-note');
  await expect(note).toHaveText(privacy);
  await note.scrollIntoViewIfNeeded();
  const metrics = await note.evaluate(el => {
    const css = getComputedStyle(el);
    return { width: el.clientWidth, scroll: el.scrollWidth, height: el.getBoundingClientRect().height, fontSize: css.fontSize, fontWeight: css.fontWeight, lineHeight: css.lineHeight };
  });
  expect(metrics.scroll).toBeLessThanOrEqual(metrics.width);
  expect(metrics.fontSize).toBe('12px');
  expect(metrics.fontWeight).toBe('600');
  expect(metrics.height).toBeLessThanOrEqual(6 * parseFloat(metrics.lineHeight));
  const evidence = process.env.INVEST_FIX_EVIDENCE ?? path.join(root, 'docs/stage3/fix-evidence');
  await page.screenshot({ path: path.join(evidence, `privacy-copy-${info.project.name}.png`), animations: 'disabled' });
  await note.screenshot({ path: path.join(evidence, `privacy-note-${info.project.name}.png`), animations: 'disabled' });
});

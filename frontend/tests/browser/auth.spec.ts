import { randomInt } from 'node:crypto';
import { expect, test, type Page, type TestInfo } from '@playwright/test';

test.use({ trace: 'off' });

const phone = () => '0912' + String(randomInt(1000000, 9999999));
async function open(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'ورود به حساب', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
}
async function issue(page: Page, mobile = phone()) {
  await page.getByRole('textbox', { name: 'شماره موبایل', exact: true }).fill(mobile);
  await page.getByRole('button', { name: 'دریافت کد', exact: true }).click();
  await expect(page.getByTestId('trial-code')).toBeVisible();
  return (await page.getByTestId('trial-code').textContent())!;
}
async function capture(page: Page, info: TestInfo, name: string) {
  const input = page.getByRole('textbox', { name: 'کد تایید', exact: true });
  const filled = await input.count() ? await input.inputValue() : '';
  const options = { maskColor: '#e1e7ef', animations: 'disabled' as const, mask: [page.getByTestId('trial-code'), ...(filled ? [page.locator('.code-cells')] : [])] };
  await page.screenshot({ ...options, path: `../docs/stage3/evidence/${name}-${info.project.name}.png` });
  const dialog = page.getByRole('dialog');
  if (await dialog.count() && await dialog.isVisible()) {
    const dimensions = await dialog.evaluate(el => ({ height: el.clientHeight, scroll: el.scrollHeight, top: el.scrollTop }));
    expect(await dialog.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
    if (dimensions.scroll > dimensions.height) {
      await dialog.evaluate(el => { el.scrollTop = el.scrollHeight; });
      await page.screenshot({ ...options, path: `../docs/stage3/evidence/${name}-bottom-${info.project.name}.png` });
      await dialog.evaluate((el, top) => { el.scrollTop = top; }, dimensions.top);
    }
  }
}

test('real login, wrong code, reload, logout and HttpOnly session', async ({ page, context }, info) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await open(page);
  await expect(page.getByRole('textbox', { name: 'شماره موبایل', exact: true })).toBeFocused();
  await capture(page, info, 'login-mobile-step');
  const code = await issue(page);
  await expect(page.getByRole('textbox', { name: 'کد تایید', exact: true })).toBeFocused();
  await capture(page, info, 'login-code-step');
  const wrong = code === '111111' ? '222222' : '111111';
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill(wrong);
  await page.getByRole('button', { name: 'ورود', exact: true }).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('کد صحیح نیست');
  await capture(page, info, 'login-wrong-code');
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill(code.replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[Number(d)]));
  await page.getByRole('button', { name: 'ورود', exact: true }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('region', { name: 'وضعیت ورود' })).toContainText('وارد شده‌اید');
  const cookie = (await context.cookies()).find(c => c.name === 'invest_session');
  expect(cookie?.httpOnly).toBe(true);
  expect(await page.evaluate(() => document.cookie.includes('invest_session'))).toBe(false);
  expect(await page.evaluate(() => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) }))).toEqual({ local: [], session: [] });
  await page.reload();
  await expect(page.getByRole('button', { name: 'حساب کاربری', exact: true })).toBeVisible();
  await capture(page, info, 'login-success');
  await page.getByRole('button', { name: 'حساب کاربری', exact: true }).click();
  await page.getByRole('menuitem', { name: 'خروج', exact: true }).click();
  await expect(page.getByText('از حساب خارج شدید.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeVisible();
  await context.addCookies([{ name: 'invest_session', value: cookie!.value, url: 'http://127.0.0.1:3109' }]);
  expect((await (await page.request.get('/api/v1/auth/me')).json()).authenticated).toBe(false);
  expect(errors).toEqual([]);
});

test('invalid mobile is never truncated and focus stays in modal', async ({ page }, info) => {
  await open(page);
  const field = page.getByRole('textbox', { name: 'شماره موبایل', exact: true });
  const invalid = '091234567890000000000000000000000000000000000000000000000000000000000000';
  await field.fill(invalid);
  await page.getByRole('button', { name: 'دریافت کد', exact: true }).click();
  await expect(field).toHaveValue(invalid);
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('شماره موبایل ایران');
  await capture(page, info, 'login-invalid-mobile');
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => !!document.activeElement?.closest('dialog'))).toBe(true);
  }
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'ورود به حساب', exact: true })).toBeFocused();
});

test('edit invalidates the previous challenge and enforces server spacing', async ({ page }, info) => {
  await open(page);
  await issue(page);
  await expect(page.getByRole('button', { name: /ارسال مجدد در/ })).toBeDisabled();
  await page.getByRole('button', { name: 'ویرایش شماره', exact: true }).click();
  await page.getByRole('button', { name: 'دریافت کد', exact: true }).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('کمی صبر کنید');
  await expect(page.getByRole('button', { name: 'دریافت کد', exact: true })).toBeDisabled();
  await capture(page, info, 'login-rate-limit');
});

test('six code cells support paste and expiry UI; server expiry is separately tested', async ({ page, context }, info) => {
  await open(page);
  const code = await issue(page);
  await expect(page.locator('.code-cells span')).toHaveCount(6);
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.evaluate(value => navigator.clipboard.writeText(value), code);
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).focus();
  await page.keyboard.press('Control+V');
  await expect(page.getByRole('textbox', { name: 'کد تایید', exact: true })).toHaveValue(code);
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill('');
  await page.evaluate(() => navigator.clipboard.writeText(''));
  await page.clock.install();
  await page.clock.fastForward(121000);
  await expect(page.getByText('اعتبار کد تمام شده است.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'ورود', exact: true })).toBeDisabled();
  await expect(page.getByTestId('trial-code')).not.toBeVisible();
  await capture(page, info, 'login-expired-ui');
});

test('lost verify body recovers only from the received session cookie', async ({ page }) => {
  await open(page);
  const code = await issue(page);
  await page.route('**/api/v1/auth/verify', async route => {
    const response = await route.fetch();
    await route.fulfill({ response, status: 502, body: JSON.stringify({ error: { message: 'پاسخ آزمایشی گم شد.' } }) });
  });
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill(code);
  await page.getByRole('button', { name: 'ورود', exact: true }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.getByRole('region', { name: 'وضعیت ورود' })).toContainText('وارد شده‌اید');
});

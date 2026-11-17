import { randomInt } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

const root = path.resolve(__dirname, '../../..');
const evidence = path.join(root, process.env.A1_EVIDENCE || '.tools/s05-a1/browser-iteration');
const apiContainer = process.env.A1_API_CONTAINER || 'invest-a1-browser-api';
const python = process.env.A1_PYTHON || '/src/.venv/bin/python';
const backendDir = process.env.A1_BACKEND_DIR || '/src';
function command(script: string) { return execFileSync('docker', ['exec', '-w', backendDir, apiContainer, python, 'manage.py', 'shell', '-c', script], { encoding: 'utf8', cwd: root }); }
async function login(page: Page, phone: string) {
  await page.goto('/drafts');
  await page.getByRole('button', { name: 'ورود به حساب', exact: true }).click();
  await page.getByRole('textbox', { name: 'شماره موبایل', exact: true }).fill(phone);
  await page.getByRole('button', { name: 'دریافت کد', exact: true }).click();
  const code = page.getByTestId('trial-code'); await expect(code).toBeVisible();
  await page.getByRole('textbox', { name: 'کد تایید', exact: true }).fill((await code.textContent())!);
  await page.getByRole('button', { name: 'ورود', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'پروژه تازه', exact: true })).toBeVisible();
}
async function save(page: Page) {
  const response = page.waitForResponse(r => /\/workspace\/drafts\/[a-f0-9-]+$/.test(r.url()) && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'ذخیره پیش‌نویس', exact: true }).click();
  const r = await response; expect(r.status()).toBe(200); await expect(page.getByRole('status').filter({ hasText: 'ذخیره شد' })).toBeVisible(); return r.json();
}
async function draft(page: Page) {
  const response = page.waitForResponse(r => r.url().endsWith('/workspace/drafts') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'ایجاد پیش‌نویس پروژه', exact: true }).click();
  expect((await response).status()).toBe(200); await expect(page.getByLabel('عنوان پروژه', { exact: true })).toBeVisible();
}
async function capture(page: Page, name: string) {
  await page.screenshot({ path: path.join(evidence, name), fullPage: true, mask: [page.locator('.account-status-header')] });
}
const phone = () => '0914' + randomInt(1000000, 9999999);
test.use({ trace: 'off' });

test('A1 journey: lost create, exact conditional form, file, resume on second device, trash', async ({ page, browser }) => {
  test.setTimeout(100000); page.on('dialog', d => void d.accept()); const mobile = phone(); await login(page, mobile);
  let lost = true; const keys: string[] = [];
  await page.route('**/api/v1/workspace/drafts', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    keys.push(route.request().postDataJSON().key); const response = await route.fetch();
    if (lost) { lost = false; await route.abort('failed'); } else await route.fulfill({ response });
  });
  await page.getByRole('button', { name: 'ایجاد پیش‌نویس پروژه', exact: true }).click();
  await expect(page.getByRole('button', { name: 'دریافت نتیجه همان عملیات', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'دریافت نتیجه همان عملیات', exact: true }).click();
  await expect(page.getByLabel('عنوان پروژه', { exact: true })).toBeVisible(); expect(keys.length).toBe(2); expect(keys[0]).toBe(keys[1]);
  await page.getByLabel('عنوان پروژه', { exact: true }).fill('پروژه مصنوعی آزمون مستقل A1');
  await page.getByLabel('نیاز مالی کل — وضعیت', { exact: true }).selectOption('known'); await page.getByRole('textbox', { name: 'نیاز مالی کل', exact: true }).fill('۱٫۵');
  await page.getByRole('group', { name: 'مسیرهای پروژه', exact: true }).getByRole('checkbox', { name: 'اجاره', exact: true }).check();
  await page.getByLabel('ودیعه — وضعیت', { exact: true }).selectOption('unknown');
  await page.getByLabel('اجاره ماهانه — وضعیت', { exact: true }).selectOption('known'); await page.getByRole('textbox', { name: 'اجاره ماهانه', exact: true }).fill('0');
  const receipt = await save(page); expect(receipt.effective.budget.value).toBe('1500000000'); expect(receipt.effective.deposit.status).toBe('unknown'); expect(receipt.effective.monthly_rent.value).toBe('0');
  await page.getByRole('group', { name: 'مسیرهای پروژه', exact: true }).getByRole('checkbox', { name: 'اجاره', exact: true }).uncheck(); await save(page); await expect(page.getByLabel('ودیعه — وضعیت', { exact: true })).not.toBeVisible();
  await page.getByRole('group', { name: 'مسیرهای پروژه', exact: true }).getByRole('checkbox', { name: 'اجاره', exact: true }).check(); await expect(page.getByLabel('ودیعه — وضعیت', { exact: true })).toHaveValue('unknown'); await save(page);
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgZGIGAAAOAAfXb+R4AAAAAElFTkSuQmCC', 'base64');
  await page.getByLabel('نوع فایل', { exact: true }).selectOption('image');
  await page.getByLabel('انتخاب فایل', { exact: true }).setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: png });
  await expect(page.getByText('synthetic.png', { exact: true })).toBeVisible();
  command('from apps.workspace.files import check_one; [check_one() for _ in range(10)]');
  await expect(page.getByRole('link', { name: 'دریافت خصوصی', exact: true })).toBeVisible({ timeout: 15000 });
  const download = await page.request.get(await page.getByRole('link', { name: 'دریافت خصوصی', exact: true }).getAttribute('href') || '');
  expect(download.status()).toBe(200); expect(download.headers()['content-type']).toBe('image/jpeg'); expect(download.headers()['cache-control']).toContain('no-store');
  await capture(page, 'journey-editor.png');
  await page.getByRole('button', { name: 'حذف فایل', exact: true }).click(); await expect(page.getByRole('button', { name: 'بازیابی فایل', exact: true })).toBeVisible(); await page.getByRole('button', { name: 'بازیابی فایل', exact: true }).click();
  const second = await browser.newContext({ baseURL: new URL(page.url()).origin });
  try { const other = await second.newPage(); await login(other, mobile); await other.getByRole('button', { name: 'ادامه ویرایش', exact: true }).click(); await expect(other.getByLabel('عنوان پروژه', { exact: true })).toHaveValue('پروژه مصنوعی آزمون مستقل A1'); }
  finally { await second.close(); }
  await page.getByRole('button', { name: 'حذف پیش‌نویس', exact: true }).click(); await page.getByRole('button', { name: 'سطل حذف', exact: true }).click(); await page.getByRole('button', { name: 'بازیابی پیش‌نویس', exact: true }).click(); await expect(page.getByLabel('عنوان پروژه', { exact: true })).toHaveValue('پروژه مصنوعی آزمون مستقل A1');
});

test('A1 layout, keyboard, organization and heritage conditions at four widths', async ({ page }) => {
  test.setTimeout(90000); page.on('dialog', d => void d.accept()); await login(page, phone());
  await page.getByRole('button', { name: 'درخواست نمایندگی سازمان', exact: true }).click();
  for (const label of ['نام رسمی', 'کشور', 'نوع سازمان', 'شناسه ثبت', 'اختیار امضای جاری', 'نام نماینده', 'حدود اختیار']) await page.getByLabel(label, { exact: true }).fill(label === 'شناسه ثبت' ? `SYNTH-${randomInt(10000,99999)}` : 'مصنوعی آزمون');
  await page.getByLabel('شروع اعتبار (میلادی)', { exact: true }).fill('2026-11-17'); await page.getByRole('button', { name: 'ذخیره درخواست', exact: true }).click(); await expect(page.getByRole('status').filter({ hasText: 'درخواست با رسید' })).toBeVisible();
  await page.getByLabel('مالک', { exact: true }).selectOption({ index: 1 }); await draft(page);
  await page.getByRole('checkbox', { name: 'میراث', exact: true }).check(); await page.getByRole('checkbox', { name: 'ترتیبات اختصاصی مرمت و بهره‌برداری دارد', exact: true }).check();
  await page.getByLabel('دریافت مبلغ قرارداد مرمت و تحویل بنا به مالک / دولت', { exact: true }).check(); await expect(page.getByLabel('مدت بهره‌برداری میراث — وضعیت', { exact: true })).not.toBeVisible();
  await page.getByLabel('دریافت مبلغ قرارداد مرمت و تحویل بنا به مالک / دولت', { exact: true }).uncheck(); await page.getByLabel('مرمت و اجاره مدت‌دار بنا برای بهره‌برداری', { exact: true }).check(); await expect(page.getByLabel('مدت بهره‌برداری میراث — وضعیت', { exact: true })).toBeVisible();
  await save(page);
  for (const width of [360,390,768,1440]) {
    await page.setViewportSize({ width, height: 900 }); await page.getByRole('heading', { name: 'مشخصات عمومی و موقعیت', exact: true }).scrollIntoViewIfNeeded();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const unnamed = await page.locator('.workspace-container input:not([type=hidden]), .workspace-container textarea, .workspace-container select').evaluateAll(nodes => nodes.filter(n => { const e = n as HTMLInputElement; return !e.labels?.length && !e.getAttribute('aria-label') && !e.closest('fieldset')?.querySelector('legend'); }).length);
    expect(unnamed).toBe(0); await page.getByLabel('عنوان پروژه', { exact: true }).focus(); await page.keyboard.press('Tab'); expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe('BODY'); await capture(page, `editor-${width}.png`);
  }
});

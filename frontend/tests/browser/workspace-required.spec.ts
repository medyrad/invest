import { execFileSync } from 'node:child_process';
import { randomInt, randomUUID } from 'node:crypto';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

const root = path.resolve(__dirname, '../../..');
const evidence = process.env.A1_REQUIRED_EVIDENCE || path.join(root, '.tools/a1-fix-02/browser');
const apiContainer = process.env.A1_API_CONTAINER || 'invest-a1-browser-api';
const baseURL = process.env.A1_BASE_URL || 'http://127.0.0.1:3109';
test.use({ trace: 'off' });
test.beforeEach(async ({ context }) => {
  // Sensitive fixture exists only inside the synthetic browser DB; no OTP/public role endpoint.
  const phone = '+1202' + randomInt(1000000, 9999999);
  const script = `from django.conf import settings; from django.utils import timezone; from apps.identity.models import User; from apps.identity.sessions import mint_session; import json; assert settings.INVEST_ENV=='test' and settings.DATABASES['default']['NAME'].endswith('_browser'); user=User.objects.create_user(mobile='${phone}'); _,token=mint_session(user,timezone.now()); print(json.dumps({'token':token}))`;
  const output = execFileSync('docker', ['exec', apiContainer, '/app/.venv/bin/python', 'manage.py', 'shell', '-c', script], { cwd: root, encoding: 'utf8' });
  const { token } = JSON.parse(output.trim().split('\n').at(-1)!);
  await context.addCookies([{ name: 'invest_session', value: token, url: baseURL, httpOnly: true, sameSite: 'Lax' }]);
});
const modelLabel = 'شناسه مدل قرارداد';
const durationLabel = 'مدت کل طرح / اجاره';
const modelRow = (page: Page) => page.locator('.workspace-field').filter({ has: page.getByRole('textbox', { name: modelLabel, exact: true }) });
const durationRow = (page: Page) => page.locator('.workspace-field').filter({ has: page.getByLabel(`${durationLabel} — وضعیت`, { exact: true }) });
const route = (page: Page, name: string) => page.getByRole('group', { name: 'مسیرهای پروژه', exact: true }).getByRole('checkbox', { name, exact: true });
const missing = (page: Page) => page.locator('section').filter({ has: page.getByRole('heading', { name: 'نقص‌های اطلاعات ذخیره‌شده', exact: true }) });
async function create(page: Page) {
  page.on('dialog', d => void d.accept()); await page.goto('/drafts');
  const pending = page.waitForResponse(r => r.url().endsWith('/workspace/drafts') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'ایجاد پیش‌نویس پروژه', exact: true }).click();
  const response = await pending; expect(response.status()).toBe(200); return response.json();
}
async function save(page: Page, status = 200) {
  const pending = page.waitForResponse(r => /\/workspace\/drafts\/[a-f0-9-]+$/.test(r.url()) && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'ذخیره پیش‌نویس', exact: true }).click();
  const response = await pending; expect(response.status()).toBe(status);
  if (status === 200) await expect(page.locator('.workspace-notice')).toContainText('ذخیره شد');
  return response.json();
}

test('FIX-02 model_id: incomplete, explicit statuses, valid text and invalid input match server missing', async ({ page }) => {
  const initial = await create(page); expect(initial.missing).toContain('model_id');
  await expect(modelRow(page).locator('small')).toContainText('برای تکمیل اطلاعات');
  await expect(page.getByRole('textbox', { name: modelLabel, exact: true })).not.toHaveAttribute('required');
  let dto = await save(page); expect(dto.missing).toContain('model_id'); await expect(missing(page)).toContainText(modelLabel);
  await modelRow(page).screenshot({ path: path.join(evidence, 'model-id-missing.png') });
  for (const [button, state] of [['نامعلوم', 'unknown'], ['نامربوط', 'not_applicable']]) {
    await modelRow(page).getByRole('button', { name: button, exact: true }).click(); dto = await save(page);
    expect(dto.raw.model_id).toBe(state); expect(dto.missing).not.toContain('model_id'); await expect(missing(page)).not.toContainText(modelLabel);
    await modelRow(page).screenshot({ path: path.join(evidence, `model-id-${state}.png`) });
  }
  await page.getByRole('textbox', { name: modelLabel, exact: true }).fill('مدل قراردادی مصنوعی'); dto = await save(page); expect(dto.missing).not.toContain('model_id');
  await page.getByRole('textbox', { name: modelLabel, exact: true }).fill('   '); const invalid = await save(page, 400); expect(invalid.error.fields.model_id).toBeTruthy(); await expect(page.getByRole('textbox', { name: modelLabel, exact: true })).toHaveValue('   ');
  await modelRow(page).getByRole('button', { name: 'پاک‌کردن مقدار', exact: true }).click(); dto = await save(page); expect(dto.missing).toContain('model_id');
});

test('FIX-02 duration: optional visibility, lessee requirement, mixed routes, inactive return and fee independence', async ({ page }) => {
  test.setTimeout(45000); await create(page);
  await route(page, 'مشارکت').check(); await expect(durationRow(page)).toBeVisible(); await expect(durationRow(page).locator('small')).toHaveCount(0);
  let dto = await save(page); expect(dto.missing).not.toContain('duration_years'); await expect(missing(page)).not.toContainText(durationLabel);
  await route(page, 'اجاره').check(); await expect(durationRow(page).locator('small')).toContainText('برای تکمیل اطلاعات');
  dto = await save(page); expect(dto.missing).toContain('duration_years'); await expect(missing(page)).toContainText(durationLabel);
  await durationRow(page).screenshot({ path: path.join(evidence, 'duration-required-lessee.png') });
  for (const state of ['unknown', 'not_applicable']) {
    await page.getByLabel(`${durationLabel} — وضعیت`, { exact: true }).selectOption(state);
    await page.getByLabel(`${durationLabel} — مبنای شروع`, { exact: true }).fill('unspecified');
    dto = await save(page); expect(dto.missing).not.toContain('duration_years'); expect(dto.effective.duration_years.status).toBe(state);
  }
  await page.getByLabel(`${durationLabel} — وضعیت`, { exact: true }).selectOption('known');
  await page.getByRole('textbox', { name: durationLabel, exact: true }).fill('0'); dto = await save(page); expect(dto.effective.duration_years.value).toBe('0');
  await route(page, 'اجاره').uncheck(); await expect(durationRow(page)).toBeVisible(); await expect(durationRow(page).locator('small')).toHaveCount(0); dto = await save(page); expect(dto.effective.duration_years.value).toBe('0');
  await durationRow(page).screenshot({ path: path.join(evidence, 'duration-optional-investor.png') });
  await route(page, 'مشارکت').uncheck(); dto = await save(page); expect(dto.inactive).toContain('duration_years'); await expect(durationRow(page)).toHaveCount(0);
  const csrf = (await (await page.request.get('/api/v1/auth/csrf')).json()).csrfToken;
  const injected = { field: { namespace: 'invest.opportunity.project', key: 'duration_years', version: 1 }, unit: { code: 'YEAR', version: 1 }, status: 'known', source_value: '999', basis: { start_basis: 'unspecified' } };
  const response = await page.request.post(`/api/v1/workspace/drafts/${dto.id}`, { headers: { 'X-CSRFToken': csrf }, data: { key: randomUUID(), version: dto.version, routes: [], heritage_enabled: false, values: { duration_years: injected } } });
  expect(response.status()).toBe(200); dto = await response.json(); expect(dto.raw.duration_years.source_value).toBe('0'); expect(dto.effective.duration_years).toBeUndefined();
  await page.reload(); await page.getByRole('button', { name: 'ادامه ویرایش', exact: true }).click(); await route(page, 'اجاره').check(); await expect(page.getByRole('textbox', { name: durationLabel, exact: true })).toHaveValue('0');
  await route(page, 'میراث').check(); dto = await save(page); expect(dto.missing).not.toContain('duration_years'); await expect(durationRow(page).locator('small')).toHaveCount(1);
  await route(page, 'اجاره').uncheck(); await expect(durationRow(page)).toBeVisible(); await expect(durationRow(page).locator('small')).toHaveCount(0);
  await page.getByRole('checkbox', { name: 'ترتیبات اختصاصی مرمت و بهره‌برداری دارد', exact: true }).check();
  await page.getByLabel('دریافت مبلغ قرارداد مرمت و تحویل بنا به مالک / دولت', { exact: true }).check(); await expect(page.getByLabel('مدت بهره‌برداری میراث — وضعیت', { exact: true })).not.toBeVisible();
  dto = await save(page); expect(dto.missing).not.toContain('heritage_years'); expect(dto.missing).not.toContain('duration_years');
  await page.getByLabel('دریافت مبلغ قرارداد مرمت و تحویل بنا به مالک / دولت', { exact: true }).uncheck(); await page.getByLabel('مرمت و اجاره مدت‌دار بنا برای بهره‌برداری', { exact: true }).check();
  dto = await save(page); expect(dto.missing).toContain('heritage_years'); expect(dto.missing).not.toContain('duration_years');
});

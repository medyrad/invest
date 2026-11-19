import {test, expect, type Page} from '@playwright/test';
import fs from 'node:fs';

async function login(page: Page) {
  await page.goto('/local-roles');
  await page.getByRole('button', {name: / · user$/}).click();
  await page.waitForURL(url => !url.pathname.includes('local-roles'));
}

const section = (page: Page) => page.getByRole('heading', {name: 'اطلاعات حرفه‌ای برای اعمال اختیاری در جست‌وجو'}).locator('..');

// Harness تاریخی checkboxهای همیشه‌نمایان را هدف می‌گرفت. در نسخه نهایی همان
// انتخاب‌های لازم از کنترل قابل‌مشاهده MultiDrop و با کلیک واقعی انجام می‌شوند.
async function ensureProfessionalRequired(page: Page, form: any, roles: string[]) {
  const entity = form.getByLabel(/نوع فعالیت/);
  if (await entity.inputValue() === '') await entity.selectOption('individual');
  const trigger = form.locator('[role=combobox]').first();
  await trigger.click();
  for (const role of roles) {
    const checkbox = page.getByRole('checkbox', {name: role, exact: true});
    if (!await checkbox.isChecked()) await checkbox.click();
  }
  await page.keyboard.press('Escape');
}

for (const mode of ['400', '401', '500', 'offline', 'lost']) test(`profile failure ${mode}`, async ({page}) => {
  await login(page); await page.goto('/profile'); const form = section(page);
  await expect(form.getByLabel('نام', {exact: true})).toBeVisible();
  await ensureProfessionalRequired(page, form, ['سرمایه‌گذار']);
  await form.getByLabel('نام', {exact: true}).fill(`نسخه قبلی ${mode}`);
  await form.getByRole('button', {name: 'ذخیره اطلاعات حرفه‌ای اختیاری', exact: true}).click();
  await expect(form.getByRole('status')).toContainText('با رسید سرور', {timeout: 30000});
  await form.getByLabel('نام', {exact: true}).fill(`ورودی جدید ${mode}`);
  let sent = false;
  await page.route('**/api/v1/core/personal', async route => {
    if (route.request().method() !== 'POST') return route.continue(); sent = true;
    if (mode === 'lost') { await route.fetch(); return route.abort('connectionfailed'); }
    if (mode === 'offline') return route.abort('internetdisconnected');
    return route.fulfill({status: Number(mode), contentType: 'application/json', body: JSON.stringify({error: {message: 'خطای مصنوعی مستقل'}})});
  });
  await form.getByRole('button', {name: 'ذخیره اطلاعات حرفه‌ای اختیاری', exact: true}).click();
  await expect(form.getByRole('alert')).toBeVisible({timeout: 30000});
  expect(sent).toBe(true); await expect(form.getByLabel('نام', {exact: true})).toHaveValue(`ورودی جدید ${mode}`);
  await expect(form.getByRole('status')).toHaveCount(0);
  const actual = await (await page.request.get('/api/v1/core/personal')).json();
  expect(JSON.parse(actual.profile.professional).name).toBe(`${mode === 'lost' ? 'ورودی جدید ' : 'نسخه قبلی '}${mode}`);
});

test('professional save then basic save preserves both roles', async ({page}) => {
  await login(page); await page.goto('/profile'); const form = section(page);
  await page.waitForLoadState('networkidle');
  await expect(form.getByLabel('نام', {exact: true})).not.toHaveValue('');
  await ensureProfessionalRequired(page, form, ['سرمایه‌گذار', 'پیمانکار']);
  const professionalName = `ویرایش مستقل ${Date.now()}`;
  await form.getByLabel('نام', {exact: true}).fill(professionalName);
  await form.getByRole('button', {name: 'ذخیره اطلاعات حرفه‌ای اختیاری', exact: true}).click();
  await expect(form.getByRole('status')).toContainText('با رسید سرور', {timeout: 30000});
  await page.getByRole('textbox', {name: 'نام نمایشی', exact: true}).fill('نام مستقل');
  await page.getByRole('button', {name: 'ذخیره پروفایل اختیاری', exact: true}).click();
  await expect(page.getByText('پروفایل اختیاری در حساب ذخیره شد.', {exact: true})).toBeVisible();
  const result = await (await page.request.get('/api/v1/core/personal')).json();
  expect(JSON.parse(result.profile.professional || '{}').roles).toEqual(expect.arrayContaining(['investor', 'contractor']));
  expect(JSON.parse(result.profile.professional || '{}').name).toBe(professionalName);
});

test('guide preview content survives first download', async ({page}) => {
  await login(page); await page.goto('/opportunities'); await expect(page.locator('article').first()).toBeVisible({timeout: 30000});
  const href = await page.locator('article').first().getByRole('link').first().getAttribute('href'); await page.goto(`/guide/${href!.split('/').pop()}`);
  await expect(page.getByRole('button', {name: 'دانلود فایل راهنما', exact: true})).toBeEnabled({timeout: 30000});
  const frame = page.frameLocator('iframe[title="راهنمای اقدام"]');
  const before = await frame.locator('body').innerText(); fs.writeFileSync('/evidence/preview.txt', before);
  const checks = frame.locator('input[data-k]'); if (await checks.count()) await checks.first().locator('..').click();
  const wait = page.waitForEvent('download'); await page.getByRole('button', {name: 'دانلود فایل راهنما', exact: true}).click(); const download = await wait;
  const html = fs.readFileSync((await download.path())!, 'utf8'); fs.writeFileSync('/evidence/first-download.html', html);
  const headings = await frame.locator('h2').allTextContents(); fs.writeFileSync('/evidence/preview-headings.json', JSON.stringify(headings, null, 2));
  expect(html).toContain('گام‌های اقدام');
  expect(html).not.toMatch(/<li>(pre|step)-?\d+<\/li>/);
});

for (const width of [360, 390, 768, 1440]) test(`local geometry focus ${width}`, async ({browser}) => {
  const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'}); const page = await context.newPage();
  await page.goto('/tools/land-preparation'); await expect(page.getByText('عملیات و مطالعات آماده‌سازی', {exact: true})).toBeVisible({timeout: 30000}); await page.evaluate(() => document.fonts.ready);
  const data: any = await page.evaluate(() => ({width: innerWidth, doc: document.documentElement.scrollWidth, body: document.body.getBoundingClientRect().toJSON(), font: getComputedStyle(document.body).fontFamily, overflow: [...document.querySelectorAll('h1,h2,p,button,label,input,select')].filter(element => { const rect = element.getBoundingClientRect(); return rect.width && rect.height && (rect.left < -1 || rect.right > innerWidth + 1); }).map(element => ({tag: element.tagName, text: element.textContent?.slice(0, 100), rect: element.getBoundingClientRect().toJSON()}))}));
  await page.screenshot({path: `/evidence/land-viewport-${width}.png`, animations: 'disabled'}); await page.screenshot({path: `/evidence/land-full-${width}.png`, fullPage: true, animations: 'disabled'});
  const focus = []; for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); focus.push(await page.evaluate(() => ({tag: document.activeElement?.tagName, text: document.activeElement?.textContent?.slice(0, 80), rect: document.activeElement?.getBoundingClientRect().toJSON()}))); }
  fs.writeFileSync(`/evidence/geometry-${width}.json`, JSON.stringify({...data, focus}, null, 2));
  expect(data.overflow.filter((row: any) => row.tag === 'BUTTON')).toEqual([]); await context.close();
});

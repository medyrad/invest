import {expect, test, type Page} from '@playwright/test';
import fs from 'node:fs';

async function login(page: Page) {
  await page.goto('/local-roles');
  await page.getByRole('button', {name: / · user$/}).click();
  await page.waitForURL(url => !url.pathname.includes('local-roles'));
}

async function ensureProfessionalRequired(page: Page, form: any, roles = ['سرمایه‌گذار']) {
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

test.afterEach(async ({page}) => page.unrouteAll({behavior: 'wait'}));

for (const mode of ['400', '401', '500', 'offline', 'lost']) test(`independent edit preserves record and stable retry ${mode}`, async ({page}) => {
  await login(page);
  await page.goto('/saved');
  await page.getByRole('tab', {name: /فیلترهای ذخیره/}).click();
  await page.getByRole('button', {name: 'افزودن فیلتر تازه', exact: true}).first().click();
  const original = `مبنای مستقل ${mode} ${Date.now()}`;
  await page.getByLabel('نام', {exact: true}).fill(original);
  const created = page.waitForResponse(r => r.url().endsWith('/core/personal') && r.request().method() === 'POST');
  await page.getByRole('button', {name: 'ذخیره جست‌وجو', exact: true}).click();
  expect((await created).status()).toBe(200);
  await page.getByRole('button').filter({hasText: original}).first().click();
  await page.getByRole('button', {name: 'ویرایش شرایط', exact: true}).click();
  await page.getByLabel('نام', {exact: true}).fill(`${original} ویرایش`);
  let body: any;
  let intercepted = false;
  await page.route('**/api/v1/core/personal', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    body = route.request().postDataJSON();
    if (mode === 'lost') {
      await route.fetch();
      intercepted = true;
      return route.abort('connectionfailed');
    }
    if (mode === 'offline') {
      intercepted = true;
      return route.abort('internetdisconnected');
    }
    intercepted = true;
    return route.fulfill({status: Number(mode), contentType: 'application/json', body: JSON.stringify({error: {message: 'شکست مستقل'}})});
  });
  await page.getByRole('button', {name: 'ذخیره جست‌وجو', exact: true}).click();
  await expect.poll(() => intercepted).toBe(true);
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByLabel('نام', {exact: true})).toHaveValue(`${original} ویرایش`);
  const state = await (await page.request.get('/api/v1/core/personal')).json();
  expect(state.searches.find((row: any) => row.id === body.id)?.name).toBe(mode === 'lost' ? `${original} ویرایش` : original);
  await page.unrouteAll({behavior: 'wait'});
  const retry = page.waitForRequest(r => r.url().endsWith('/core/personal') && r.method() === 'POST');
  await page.getByRole('button', {name: 'ذخیره جست‌وجو', exact: true}).click();
  expect((await retry).postDataJSON().key).toBe(body.key);
});

for (const mode of ['400', '401', '500', 'offline', 'lost']) test(`independent results-page save preserves input and stable retry ${mode}`, async ({page}) => {
  await login(page);
  await page.goto('/opportunities');
  await page.getByRole('textbox', {name: 'جست‌وجو در نتایج', exact: true}).fill(`عبارت مستقل ${mode}`);
  await page.waitForLoadState('networkidle');
  await page.getByRole('button', {name: 'فیلترهای ذخیره‌شده', exact: true}).click();
  await page.getByRole('menuitem', {name: 'ذخیره جست‌وجوی فعلی', exact: true}).click();
  const name = `ذخیره صفحه نتیجه ${mode}`;
  await page.getByLabel('یک نام برایش بگذارید').fill(name);
  let body: any;
  let intercepted = false;
  await page.route('**/api/v1/core/personal', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    body = route.request().postDataJSON();
    if (mode === 'lost') {
      await route.fetch(); intercepted = true; return route.abort('connectionfailed');
    }
    if (mode === 'offline') {
      intercepted = true; return route.abort('internetdisconnected');
    }
    intercepted = true;
    return route.fulfill({status: Number(mode), contentType: 'application/json', body: JSON.stringify({error: {message: 'شکست مستقل'}})});
  });
  const save = page.getByRole('dialog').getByRole('button', {name: 'ذخیره', exact: true});
  await save.click();
  await expect.poll(() => intercepted).toBe(true);
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByLabel('یک نام برایش بگذارید')).toHaveValue(name);
  await page.unrouteAll({behavior: 'wait'});
  const retry = page.waitForRequest(r => r.url().endsWith('/core/personal') && r.method() === 'POST');
  await save.click();
  expect((await retry).postDataJSON().key).toBe(body.key);
});

test('independent same-field profile conflict preserves losing tab input', async ({page, context}) => {
  await login(page);
  await page.goto('/profile');
  const other = await context.newPage();
  await other.goto('/profile');
  const first = page.locator('.professional-form');
  const second = other.locator('.professional-form');
  await expect(first.getByLabel('نام', {exact: true})).toBeEnabled();
  await expect(second.getByLabel('نام', {exact: true})).toBeEnabled();
  await ensureProfessionalRequired(page, first);
  await ensureProfessionalRequired(other, second);
  const a = `تب نخست ${Date.now()}`;
  const b = `تب دوم ${Date.now()}`;
  await first.getByLabel('نام', {exact: true}).fill(a);
  await second.getByLabel('نام', {exact: true}).fill(b);
  await first.getByRole('button', {name: 'ذخیره اطلاعات حرفه‌ای اختیاری', exact: true}).click();
  await expect(first.getByRole('status')).toContainText('رسید سرور');
  const response = other.waitForResponse(r => r.url().endsWith('/core/personal') && r.request().method() === 'POST');
  await second.getByRole('button', {name: 'ذخیره اطلاعات حرفه‌ای اختیاری', exact: true}).click();
  expect((await response).status()).toBe(409);
  await expect(second.getByRole('alert')).toBeVisible();
  await expect(second.getByLabel('نام', {exact: true})).toHaveValue(b);
  const state = await (await page.request.get('/api/v1/core/personal')).json();
  expect(JSON.parse(state.profile.professional).name).toBe(a);
});

for (const mode of ['500', 'lost']) test(`independent quick profile retry ${mode}`, async ({page}) => {
  await login(page);
  await page.goto('/opportunities');
  await page.getByRole('button', {name: /درباره شما/}).click();
  await page.getByRole('button', {name: /ساخت سریع پروفایل|ویرایش/}).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByText('سازنده', {exact: true}).click();
  const capital = dialog.getByPlaceholder('مثلاً ۵۰');
  if (await capital.isVisible()) await capital.fill('81');
  let body: any;
  let done = false;
  await page.route('**/api/v1/core/personal', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    body = route.request().postDataJSON();
    if (mode === 'lost') {
      await route.fetch();
      done = true;
      return route.abort('connectionfailed');
    }
    done = true;
    return route.fulfill({status: 500, contentType: 'application/json', body: JSON.stringify({error: {message: 'شکست مستقل'}})});
  });
  await dialog.getByRole('button', {name: 'ذخیره و اعمال روی فیلترها', exact: true}).click();
  await expect.poll(() => done).toBe(true);
  await expect(dialog.getByRole('alert')).toContainText('ورودی شما حفظ شده است');
  if (await capital.isVisible()) await expect(capital).toHaveValue('81');
  await page.unrouteAll({behavior: 'wait'});
  const retry = page.waitForRequest(r => r.url().endsWith('/core/personal') && r.method() === 'POST');
  await dialog.getByRole('button', {name: 'ذخیره و اعمال روی فیلترها', exact: true}).click();
  expect((await retry).postDataJSON().key).toBe(body.key);
});

test('independent real pointer opens save menu while results refresh', async ({page}) => {
  await login(page);
  await page.goto('/opportunities');
  let slow = false;
  await page.route('**/api/v1/core/opportunities?*', async route => {
    if (slow) await new Promise(resolve => setTimeout(resolve, 900));
    await route.continue();
  });
  slow = true;
  await page.getByLabel('مبلغ', {exact: true}).check();
  const trigger = page.getByRole('button', {name: 'فیلترهای ذخیره‌شده', exact: true});
  await trigger.click();
  const item = page.getByRole('menuitem', {name: 'ذخیره جست‌وجوی فعلی', exact: true});
  await expect(item).toBeVisible();
  await item.scrollIntoViewIfNeeded();
  const hit = await item.evaluate(el => {
    const r = el.getBoundingClientRect();
    const target = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return target === el || el.contains(target);
  });
  expect(hit).toBe(true);
  await item.click();
  await expect(page.getByRole('dialog', {name: 'ذخیره این جست‌وجو'})).toBeVisible();
});

for (const width of [360, 390, 768, 1440]) test(`independent land three-stage back and pointer geometry ${width}`, async ({browser}) => {
  const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
  const page = await context.newPage();
  await page.goto('/tools/land-preparation');
  await page.evaluate(() => document.fonts.ready);
  const editor = page.locator('.service-editor');
  await expect(editor.getByText('انتخاب خدمات و محل', {exact: true})).toBeVisible();
  await editor.getByLabel('چگونه مایل به ورود هستید؟', {exact: true}).selectOption('investor');
  const groups = editor.locator('.service-option-group [role=combobox]');
  await expect(groups).toHaveCount(2);
  for (let i = 0; i < 2; i++) {
    await groups.nth(i).click();
    await page.getByRole('dialog').getByRole('checkbox').first().click();
    await page.keyboard.press('Escape');
  }
  const selected = await editor.locator('.service-selected-order li').allTextContents();
  expect(selected).toHaveLength(2);
  await editor.getByRole('button', {name: 'ادامه، شرایط بسته خدمات', exact: true}).click();
  await expect(editor.locator('.service-steps [aria-current=step]')).toContainText('شرایط بسته خدمات');
  for (let cycle = 0; cycle < 40; cycle++) {
    const next = editor.getByRole('button', {name: /پرسش بعدی بی‌پاسخ/});
    if (!await next.isVisible().catch(() => false)) break;
    await next.click();
    const active = page.locator(':focus');
    const tag = await active.evaluate(el => el.tagName);
    if (tag === 'SELECT') await active.selectOption({index: 1});
    else if (tag === 'INPUT' || tag === 'TEXTAREA') await active.fill('1');
  }
  // پاسخ parent می‌تواند پرسش شرطی تازه بسازد؛ چند دور تا پایدارشدن فرم لازم است.
  for (let pass = 0; pass < 10; pass++) {
    let changed = false;
    for (const select of await editor.locator('[data-service-field] select').all()) {
      if (await select.isEnabled() && await select.locator('option').count() > 1 && await select.inputValue() === '') {
        await select.selectOption({index: 1});
        changed = true;
      }
    }
    // React پرسش وابسته را پس از commit پاسخ parent وارد DOM می‌کند.
    await page.waitForTimeout(100);
    const remaining = await editor.locator('[data-service-field] select').evaluateAll(nodes => nodes.filter(node => !(node as HTMLSelectElement).disabled && (node as HTMLSelectElement).value === '' && (node as HTMLSelectElement).options.length > 1).length);
    if (!changed && remaining === 0) break;
  }
  for (const input of await editor.locator('[data-service-field] input:not([type=checkbox]):not([type=radio])').all()) {
    if (await input.isEnabled() && !await input.inputValue()) await input.fill('1');
  }
  const radios = editor.locator('[data-service-field] input[type=radio]');
  const names = await radios.evaluateAll(nodes => [...new Set(nodes.map(node => (node as HTMLInputElement).name))]);
  for (const name of names) await editor.locator(`[data-service-field] input[type=radio][name="${name}"]`).first().check();
  await editor.getByRole('button', {name: 'نمایش جمع‌بندی بسته خدمات', exact: true}).click();
  await expect(editor.getByRole('heading', {name: /جمع‌بندی آماده‌سازی/})).toBeVisible();
  await expect(editor.locator('.service-steps [aria-current=step]')).toContainText('جمع‌بندی بسته');
  await editor.getByRole('button', {name: 'ویرایش شرایط بسته', exact: true}).click();
  await editor.getByRole('button', {name: 'ویرایش خدمات و محل', exact: true}).click();
  expect(await editor.locator('.service-selected-order li').allTextContents()).toEqual(selected);
  const controls = await editor.locator('button,input,select,textarea,[role=combobox]').evaluateAll((nodes, w) => nodes.filter(node => {
    const r = node.getBoundingClientRect(); return r.width > 0 && r.height > 0;
  }).map(node => {
    const r = node.getBoundingClientRect();
    const x = Math.max(0, Math.min(innerWidth - 1, r.left + r.width / 2));
    const y = Math.max(0, Math.min(innerHeight - 1, r.top + r.height / 2));
    const target = document.elementFromPoint(x, y);
    return {left: r.left, right: r.right, hit: target === node || node.contains(target)};
  }), width);
  expect(controls.filter((row: any) => row.left < 0 || row.right > width + 1)).toEqual([]);
  fs.writeFileSync(`/retest/land-geometry-${width}.json`, JSON.stringify({width, selected, controls}, null, 2));
  await page.screenshot({path: `/retest/land-${width}.png`, fullPage: true});
  await context.close();
});

for (const width of [360, 390, 768, 1440]) test(`independent professional consumers visible and focusable ${width}`, async ({browser}) => {
  const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
  const page = await context.newPage();
  await login(page);
  const observations: any[] = [];
  for (const route of ['/tools/ma-profile', '/profile', '/saved']) {
    await page.goto(route);
    if (route === '/saved') await page.getByRole('tab', {name: /پروفایل حرفه/}).click();
    const form = page.locator('.professional-form');
    await expect(form).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    await expect(form.getByText('معرفی و نقش حرفه‌ای', {exact: true})).toBeVisible();
    await expect(form.getByText('حوزه و توان اجرایی', {exact: true})).toBeVisible();
    const trigger = form.locator('[role=combobox]').first();
    await trigger.focus();
    await expect(trigger).toBeFocused();
    const rect = await trigger.evaluate(el => el.getBoundingClientRect().toJSON());
    observations.push({route, rect});
  }
  fs.writeFileSync(`/retest/profile-consumers-${width}.json`, JSON.stringify(observations, null, 2));
  await page.screenshot({path: `/retest/profile-saved-${width}.png`, fullPage: true});
  await context.close();
});

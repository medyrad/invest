import {test, expect, type Page} from '@playwright/test';
import fs from 'node:fs';

test('delayed profile refresh must not erase a newer edit', async ({page}) => {
  await page.goto('/local-roles');
  await page.getByRole('button', {name: / · user$/}).click();
  await page.waitForURL(url => !url.pathname.includes('local-roles'));
  await page.goto('/profile');
  await page.waitForLoadState('networkidle');
  const form = page.getByRole('heading', {name: 'اطلاعات حرفه‌ای برای اعمال اختیاری در جست‌وجو'}).locator('..');
  await expect(form.getByLabel('نام', {exact: true})).not.toHaveValue('');

  // پیش‌شرط جدید قرارداد فرم: نوع فعالیت و حداقل یک نقش، با کنترل واقعی UI.
  const entity = form.getByLabel(/نوع فعالیت/);
  if (await entity.inputValue() === '') await entity.selectOption('individual');
  const trigger = form.locator('[role=combobox]').first();
  await trigger.click();
  const investor = page.getByRole('checkbox', {name: 'سرمایه‌گذار', exact: true});
  if (!await investor.isChecked()) await investor.click();
  await page.keyboard.press('Escape');

  let release!: () => void;
  const hold = new Promise<void>(resolve => { release = resolve; });
  let posted = false;
  let captured = false;
  await page.route('**/api/v1/core/personal', async route => {
    if (route.request().method() === 'POST') { posted = true; return route.continue(); }
    if (posted && !captured) {
      const response = await route.fetch();
      captured = true;
      await hold;
      return route.fulfill({response});
    }
    return route.continue();
  });
  await form.getByLabel('نام', {exact: true}).fill('نسخه ذخیره شده');
  await form.getByRole('button', {name: 'ذخیره اطلاعات حرفه‌ای اختیاری', exact: true}).click();
  await expect(form.getByRole('status')).toContainText('با رسید سرور', {timeout: 30000});
  await expect.poll(() => captured).toBe(true);
  await form.getByLabel('نام', {exact: true}).fill('ویرایش تازه هنوز ذخیره نشده');
  release();
  await expect(form.getByLabel('نام', {exact: true})).toHaveValue('ویرایش تازه هنوز ذخیره نشده');
  await page.waitForLoadState('networkidle');
  fs.writeFileSync('/evidence/profile-late-refresh.json', JSON.stringify({actual: await form.getByLabel('نام', {exact: true}).inputValue()}));
  await expect(form.getByLabel('نام', {exact: true})).toHaveValue('ویرایش تازه هنوز ذخیره نشده');
});

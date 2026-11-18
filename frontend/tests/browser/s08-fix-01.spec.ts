import {test,expect} from '@playwright/test';
import path from 'node:path';
const evidence=path.resolve(__dirname,'../../../docs/stage8/fix-01-evidence/after');
const kinds=['proposal','ideas','land-preparation','foreign-investment','ma-notice','ma-renewal','ma-manager','ma-exchange','charity'];

test('S08 FIX progress readable at 360/390 with working focus and keyboard',async({page})=>{
 for(const width of [360,390]){
  await page.setViewportSize({width,height:844});await page.goto('/tools/land-preparation');
  const copy=page.locator('.service-progress-description strong');await expect(copy).toBeVisible();const bounds=(await copy.boundingBox())!;expect(bounds.width).toBeGreaterThanOrEqual(100);expect(bounds.height).toBeLessThan(120);
  const next=page.getByRole('button',{name:'پرسش بعدی بی‌پاسخ'});const action=(await next.boundingBox())!;expect(action.y).toBeGreaterThanOrEqual(bounds.y+bounds.height);
  await next.click();expect(await page.evaluate(()=>document.activeElement?.getAttribute('aria-label'))).toBeTruthy();await page.keyboard.press('Tab');expect(await page.evaluate(()=>document.activeElement?.tagName)).not.toBe('BODY');
  await page.screenshot({path:evidence+`/progress-${width}.png`,fullPage:false});
 }
});

test('S08 FIX renewal source groups contain their fields in source order desktop/mobile',async({page})=>{
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto('/tools/ma-renewal');
  const sections=page.locator('.service-form-group');const rights=sections.filter({has:page.getByRole('heading',{name:'محدوده، حقوق و مشوق‌های قابل بررسی',exact:true})});const residents=sections.filter({has:page.getByRole('heading',{name:'ساکنان و اسکان موقت',exact:true})});
  await expect(rights).toBeVisible();await expect(residents).toBeVisible();
  expect(await rights.locator('[data-service-field]').evaluateAll(es=>es.map(e=>e.getAttribute('data-service-field')))).toEqual(['gis','authority','evidenceDate','parcels','incentive','incentiveRef']);
  await expect(residents.locator('[data-service-field="displacement"]')).toBeVisible();expect((await rights.boundingBox())!.y).toBeLessThan((await residents.boundingBox())!.y);
  const displacement=residents.locator('[data-service-field="displacement"] select');await displacement.selectOption('yes');await expect(residents.locator('[data-service-field="deposit"]')).toBeVisible();await expect(residents.locator('[data-service-field="rent"]')).toBeVisible();await displacement.selectOption('no');await expect(residents.locator('[data-service-field="deposit"]')).toHaveCount(0);await expect(residents.locator('[data-service-field="households"]')).toHaveCount(0);
  await page.screenshot({path:evidence+`/renewal-groups-${width}.png`,fullPage:true});
 }
});

test('S08 FIX risk filter uses source classification and preserves all development finance',async({page})=>{
 await page.goto('/tools/foreign-investment');await page.getByText('مراجع و نهادهای معرفی‌شده برای مطالعه',{exact:true}).click();const select=page.getByRole('combobox',{name:'نمایش منابع بین‌المللی',exact:true});await expect(select.locator('option[value="risk"]')).toHaveText('بیمه و پوشش ریسک');
 const cards=page.locator('.service-reference-library>article');
 await select.selectOption('risk');await expect(cards).toHaveCount(1);await expect(cards.first()).toContainText('ICIEC');await expect(cards.first()).toContainText('احراز نشده');await page.screenshot({path:evidence+'/international-risk-1440.png',fullPage:true});
 await select.selectOption('finance');expect(await cards.count()).toBeGreaterThan(0);await expect(cards.filter({hasText:'ICIEC'})).toHaveCount(0);
 await select.selectOption('development');expect(await cards.count()).toBeGreaterThan(0);await expect(cards.filter({hasText:'هبیتات'})).toHaveCount(1);await expect(cards.filter({hasText:'ICIEC'})).toHaveCount(0);
 await select.selectOption('all');await expect(cards).toHaveCount(8);
});

test('S08 FIX Persian step labels across nine services and true false remain meaningful',async({page})=>{
 for(const kind of kinds){await page.goto('/tools/'+kind);await expect(page.locator('.service-editor form')).toBeVisible();const labels=await page.locator('.service-steps,.service-compact-steps').innerText();expect(labels).not.toMatch(/renewal|notice|manager|exchange|true|false/);expect(labels).toMatch(/[آ-ی]/)}
 const box=page.locator('[data-service-field="demo"] input[type="checkbox"]');await expect(box).toBeVisible();await box.check();await expect(page.locator('[data-service-field="demo"]')).toContainText('پاسخ: بله');await box.uncheck();await expect(page.locator('[data-service-field="demo"]')).toContainText('پاسخ: خیر');
 // Complete only the current charity form, then inspect the actual summary, including false.
 for(let pass=0;pass<3;pass++){
  const radios=page.locator('.service-editor form input[type="radio"]');if(await radios.count()&&!await page.locator('.service-editor form input[type="radio"]:checked').count())await radios.first().check();
  for(const select of await page.locator('.service-editor form select').all()){if(!await select.isVisible()||await select.inputValue())continue;const value=await select.locator('option').evaluateAll(os=>os.map(o=>(o as HTMLOptionElement).value).find(Boolean));if(value)await select.selectOption(value)}
  for(const input of await page.locator('.service-editor form textarea,.service-editor form input:not([type="checkbox"]):not([type="radio"])').all()){if(!await input.isVisible()||await input.inputValue())continue;await input.fill(await input.getAttribute('inputmode')==='decimal'?'1':'داده مصنوعی اصلاح')}
 }
 await page.getByRole('button',{name:/^ادامه به /}).click();const row=page.locator('.service-summary dl>div').filter({has:page.locator('dt',{hasText:'سناریوی آموزشی محله فرضی الف'})});await expect(row.locator('dd')).toHaveText('خیر');await expect(page.locator('.service-summary')).not.toContainText('false');await page.screenshot({path:evidence+'/charity-false-summary-1440.png',fullPage:true});
});

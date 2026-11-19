import {expect,test,type Page} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const evidence=path.resolve(__dirname,'../../../docs/experience-complete/evidence');
const ready=expect.configure({timeout:30_000});
test.setTimeout(120_000);

async function localRole(page:Page,name='مشتری مصنوعی'){
  await page.goto('/local-roles');
  await page.getByRole('button',{name:new RegExp('^'+name+' ·')}).click();
  await page.waitForURL(url=>!url.pathname.includes('local-roles'));
}

async function trialLogin(page:Page,mobile:string){
  await page.getByLabel('شماره موبایل',{exact:true}).fill(mobile);
  await page.getByRole('button',{name:'دریافت کد',exact:true}).click();
  await ready(page.getByTestId('trial-code')).toBeVisible();
  await page.getByLabel('کد تایید',{exact:true}).fill((await page.getByTestId('trial-code').textContent())!);
  await page.getByRole('button',{name:'ورود',exact:true}).click();
  await ready(page.getByRole('dialog')).not.toBeVisible();
}

test('@desktop PC-A01 keeps the exact save intent and applies it once after a lost response',async({page})=>{
  const suffix=String(Date.now()).slice(-7),mobile='0912'+suffix;
  await page.goto('/opportunities');
  const card=page.locator('article').filter({has:page.getByRole('button',{name:'ذخیره پروژه',exact:true})}).first();
  await ready(card).toBeVisible();
  const href=await card.getByRole('link').first().getAttribute('href');
  const id=href!.split('/').pop()!;
  await card.getByRole('button',{name:'ذخیره پروژه',exact:true}).click();
  let consumeCalls=0,lose=true;
  await page.route('**/api/v1/auth/intent/consume',async route=>{
    consumeCalls++;
    const response=await route.fetch();
    if(lose){lose=false;await route.abort('connectionfailed')}else await route.fulfill({response});
  });
  await trialLogin(page,mobile);
  const personalResponse=await page.request.get('/api/v1/core/personal');
  expect(personalResponse.ok()).toBe(true);
  const personal=await personalResponse.json();
  expect(personal.saved.filter((x:{id:string})=>x.id===id)).toHaveLength(1);
  expect(consumeCalls).toBe(2);
  await page.getByRole('button',{name:'حساب کاربری',exact:true}).click();
  await page.getByRole('menuitem',{name:'خروج',exact:true}).click();
  await ready(page.getByRole('button',{name:'ورود به حساب',exact:true})).toBeVisible();
});

test('@desktop PC-A01 cancellation does not carry a save into a later account',async({page})=>{
  await page.goto('/opportunities');
  const card=page.locator('article').filter({has:page.getByRole('button',{name:'ذخیره پروژه',exact:true})}).nth(1);
  await ready(card).toBeVisible();
  const id=(await card.getByRole('link').first().getAttribute('href'))!.split('/').pop()!;
  await card.getByRole('button',{name:'ذخیره پروژه',exact:true}).click();
  await page.getByRole('button',{name:'بستن پنجره ورود',exact:true}).click();
  await localRole(page);
  const personal=await (await page.request.get('/api/v1/core/personal')).json();
  expect(personal.saved.some((x:{id:string})=>x.id===id)).toBe(false);
});

test('@desktop PC-A02/03 multi-role profile confirms server save and preserves input on failure',async({page})=>{
  await localRole(page);
  await page.goto('/profile');
  const section=page.getByRole('heading',{name:'اطلاعات حرفه‌ای برای اعمال اختیاری در جست‌وجو'}).locator('..');
  await section.getByRole('checkbox',{name:'سرمایه‌گذار',exact:true}).check();
  await section.getByRole('checkbox',{name:'مشاور',exact:true}).check();
  await section.getByLabel('نام',{exact:true}).fill('پروفایل چندنقشی مصنوعی');
  await section.locator('select').nth(0).selectOption('company');
  await section.locator('select').nth(1).selectOption({label:'تهران'});
  await page.getByLabel('سرمایه قابل تخصیص (میلیارد تومان)',{exact:true}).fill('12.5');
  await section.locator('select').nth(2).selectOption('reported');
  await section.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();
  await ready(section.getByRole('status')).toContainText('با رسید سرور');
  const saved=await (await page.request.get('/api/v1/core/personal')).json();
  expect(JSON.parse(saved.profile.professional).roles).toEqual(expect.arrayContaining(['investor','consultant']));
  let reject=true;
  await page.route('**/api/v1/core/personal',async route=>{
    if(route.request().method()==='POST'&&reject){reject=false;await route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({error:{message:'شکست مصنوعی ذخیره'}})})}else await route.continue();
  });
  await section.getByLabel('نام',{exact:true}).fill('ورودی حفظ‌شده پس از شکست');
  await section.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();
  await ready(section.getByRole('alert')).toContainText('شکست مصنوعی ذخیره');
  await ready(section.getByLabel('نام',{exact:true})).toHaveValue('ورودی حفظ‌شده پس از شکست');
  const after=await (await page.request.get('/api/v1/core/personal')).json();
  expect(JSON.parse(after.profile.professional).name).toBe('پروفایل چندنقشی مصنوعی');
  const dl=page.waitForEvent('download');
  await section.getByRole('button',{name:'دریافت خلاصه خواندنی پروفایل',exact:true}).click();
  const file=await dl;
  expect(fs.readFileSync((await file.path())!,'utf8')).toContain('خلاصه پروفایل حرفه‌ای');
});

test('@desktop PC-A04/05 guide preview and historical re-download use the same readable snapshot',async({page})=>{
  await localRole(page);
  await page.goto('/opportunities');
  const href=await page.locator('article').first().getByRole('link').first().getAttribute('href');
  const id=href!.split('/').pop()!;
  await page.goto('/guide/'+id);
  await ready(page.getByTitle('راهنمای اقدام')).toBeVisible();
  const first=page.waitForEvent('download');
  await page.getByRole('button',{name:'دانلود فایل راهنما',exact:true}).click();
  const firstFile=await first,firstBytes=fs.readFileSync((await firstFile.path())!);
  expect(firstBytes.toString()).toContain('نسخه قواعد');
  expect(firstBytes.toString()).toContain('این دریافت پرونده یا درخواست تازه‌ای ایجاد نمی‌کند');
  await page.goto('/profile');
  const report=page.getByRole('heading',{name:'گزارش‌های ذخیره‌شده',exact:true}).locator('..').getByRole('link').first();
  const second=page.waitForEvent('download');
  await report.click();
  const secondFile=await second,secondBytes=fs.readFileSync((await secondFile.path())!);
  expect(secondBytes.equals(firstBytes)).toBe(true);
  expect(secondBytes.subarray(0,1).toString()).toBe('<');
});

for(const width of [360,390,768,1440]) test(`PC-A06 grouped land and guide have no horizontal overflow at ${width}px`,async({browser})=>{
  fs.mkdirSync(evidence,{recursive:true});
  const context=await browser.newContext({viewport:{width,height:1000}}),page=await context.newPage();
  await page.goto('/tools/land-preparation');
  await ready(page.getByText('عملیات و مطالعات آماده‌سازی',{exact:true})).toBeVisible();
  await ready(page.getByText('توسعه زمین، خدمات مالکیتی و حفاظت ملک',{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>innerWidth)).toBe(width);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  const serviceGuide=await page.getByRole('button',{name:'راهنمای این خدمت',exact:true}).boundingBox();
  expect(serviceGuide).not.toBeNull();
  expect(serviceGuide!.x).toBeGreaterThanOrEqual(0);
  expect(serviceGuide!.x+serviceGuide!.width).toBeLessThanOrEqual(width);
  await page.screenshot({path:path.join(evidence,`land-${width}.png`),fullPage:true,animations:'disabled'});
  await page.goto('/opportunities');
  const href=await page.locator('article').first().getByRole('link').first().getAttribute('href');
  await page.goto('/guide/'+href!.split('/').pop()!);
  await ready(page.getByRole('button',{name:'دانلود فایل راهنما',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>innerWidth)).toBe(width);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  await page.screenshot({path:path.join(evidence,`guide-${width}.png`),fullPage:true,animations:'disabled'});
  await context.close();
});

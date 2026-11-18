import { randomInt } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { expect, test, type Page } from '../../../frontend/node_modules/@playwright/test';

const root = path.resolve(__dirname, '../../..');
const evidence = path.join(root, process.env.A1_EVIDENCE || '.tools/s05-a1/browser-iteration');
const apiContainer = process.env.A1_API_CONTAINER || 'invest-a1-browser-api';
const python = process.env.A1_PYTHON || '/app/.venv/bin/python';
const backendDir = process.env.A1_BACKEND_DIR || '/app';
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
  await page.screenshot({ path: path.join(evidence, (process.env.A1_SCREEN_PREFIX || '') + name), fullPage: true, mask: [page.locator('.account-status-header')] });
  if (name.startsWith('editor-')) { await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(evidence, 'viewport-' + name), mask: [page.locator('.account-status-header')] }); }
}
const phone = () => '0914' + randomInt(1000000, 9999999);
test.use({ trace: 'off' });

for (const kind of ['list','detail','save']) for (const switchAccount of [false,true]) {
 test(`late ${kind}: ${switchAccount ? 'switch B':'logout only'}`, async({page})=>{
  test.setTimeout(60000);page.on('dialog',d=>void d.accept());
  await login(page,phone());await draft(page);
  await page.getByLabel('عنوان پروژه',{exact:true}).fill('PRIVATE_A_LATE');
  const initial=await save(page);
  let release!:()=>void;let arrived!:()=>void;const serverArrived=new Promise<void>(r=>arrived=r);const gate=new Promise<void>(r=>release=r);let captured=false;let delivered!:()=>void;const delivery=new Promise<void>(r=>delivered=r);
  await page.route('**/api/v1/workspace/**',async route=>{
    const req=route.request();const path=new URL(req.url()).pathname;
    const match=kind==='list' ? path.endsWith('/drafts')&&req.method()==='GET' : path.endsWith('/'+initial.id)&&req.method()===(kind==='save'?'POST':'GET');
    if(!match||captured)return route.continue();captured=true;
    const response=await route.fetch();expect(response.status()).toBe(200);const actual=await response.json();
    expect(JSON.stringify(actual)).toContain('PRIVATE_A_LATE');arrived();await gate;
    try{await route.fulfill({response});}catch{/* Old request may be cancelled on account change. */}finally{delivered();}
  });
  if(kind==='list')await page.getByRole('button',{name:'ذخیره پیش‌نویس',exact:true}).click();
  if(kind==='detail'){await page.getByLabel('نوع فایل',{exact:true}).selectOption('image');await page.getByLabel('انتخاب فایل',{exact:true}).setInputFiles({name:'late.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgZGIGAAAOAAfXb+R4AAAAAElFTkSuQmCC','base64')});}
  if(kind==='save')await page.getByRole('button',{name:'ذخیره پیش‌نویس',exact:true}).click();
  await serverArrived;
  await page.getByRole('button',{name:'حساب کاربری',exact:true}).click();await page.getByRole('menuitem',{name:'خروج',exact:true}).click();
  await expect(page.getByRole('button',{name:'ورود به حساب',exact:true})).toBeVisible();
  if(switchAccount){await login(page,phone());await draft(page);await page.getByLabel('عنوان پروژه',{exact:true}).fill('PRIVATE_B_CURRENT');await save(page);}
  release();await delivery;await page.evaluate(()=>new Promise<void>(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r()))));
  const visibleText=await page.locator('body').innerText();expect(visibleText).not.toContain(initial.id);expect(visibleText).not.toContain('late.png');
  if(switchAccount){await expect(page.getByLabel('عنوان پروژه',{exact:true})).toHaveValue('PRIVATE_B_CURRENT');expect(JSON.stringify(await(await page.request.get('/api/v1/workspace/drafts')).json())).not.toContain(initial.id);}
  else await expect(page.getByLabel('عنوان پروژه',{exact:true})).not.toBeVisible();
  await expect(page.getByText('PRIVATE_A_LATE',{exact:true}).filter({visible:true})).toHaveCount(0);
  await page.reload();if(switchAccount){await page.getByRole('button',{name:'ادامه ویرایش',exact:true}).click();await expect(page.getByLabel('عنوان پروژه',{exact:true})).toHaveValue('PRIVATE_B_CURRENT');}else await expect(page.getByRole('button',{name:'ورود به حساب',exact:true})).toBeVisible();
 });
}
test('approved representative and distinct route widgets',async({page})=>{
 test.setTimeout(60000);page.on('dialog',d=>void d.accept());await login(page,phone());
 const uid=(await(await page.request.get('/api/v1/auth/me')).json()).user.id;expect(uid).toMatch(/^[a-f0-9-]{36}$/);
 const output=command(`from django.conf import settings; from django.db import connection; assert settings.INVEST_ENV=='test' and connection.settings_dict['NAME'].endswith('_browser'); from apps.workspace.models import Organization,RepresentationRequest,Representation; from apps.identity.models import User; u=User.objects.get(pk='${uid}'); o=Organization.objects.create(name='سازمان مصنوعی مستقل',country='ایران',registration='${uid}'); r=RepresentationRequest.objects.create(organization=o,applicant=u,details={'name':'سازمان مصنوعی مستقل'},status='approved'); Representation.objects.create(organization=o,user=u,status='active'); print('REQUEST='+str(r.pk))`);
 const id=output.match(/REQUEST=([a-f0-9-]{36})/)![1];await page.reload();await page.getByLabel('مالک',{exact:true}).selectOption(id);await draft(page);
 const choices=page.getByRole('group',{name:'مسیرهای پروژه',exact:true});
 for(const [route,label] of [['مشارکت','حداقل سرمایه ورود'],['پیمانکاری','نقدینگی اجرای پیمان'],['خرید','قیمت خرید'],['اجاره','ودیعه'],['میراث','حداقل سرمایه ورود']]){
  await choices.getByRole('checkbox',{name:route,exact:true}).check();await expect(page.getByLabel(label+' — وضعیت',{exact:true})).toBeVisible();
  await page.getByLabel(label+' — وضعیت',{exact:true}).selectOption('unknown');await save(page);
  await choices.getByRole('checkbox',{name:route,exact:true}).uncheck();await expect(page.getByLabel(label+' — وضعیت',{exact:true})).not.toBeVisible();
  await choices.getByRole('checkbox',{name:route,exact:true}).check();await expect(page.getByLabel(label+' — وضعیت',{exact:true})).toHaveValue('unknown');await choices.getByRole('checkbox',{name:route,exact:true}).uncheck();
 }
 await choices.getByRole('checkbox',{name:'میراث',exact:true}).check();await page.getByRole('checkbox',{name:'ترتیبات اختصاصی مرمت و بهره‌برداری دارد',exact:true}).check();
 await page.getByLabel('دریافت مبلغ قرارداد مرمت و تحویل بنا به مالک / دولت',{exact:true}).check();await expect(page.getByLabel('مدت بهره‌برداری میراث — وضعیت',{exact:true})).not.toBeVisible();
 await page.getByLabel('دریافت مبلغ قرارداد مرمت و تحویل بنا به مالک / دولت',{exact:true}).uncheck();await page.getByLabel('مرمت و اجاره مدت‌دار بنا برای بهره‌برداری',{exact:true}).check();await expect(page.getByLabel('مدت بهره‌برداری میراث — وضعیت',{exact:true})).toBeVisible();
});
test('all project widgets and unit controls exist',async({page})=>{
 test.setTimeout(60000);page.on('dialog',d=>void d.accept());await login(page,phone());await draft(page);
 const choices=page.getByRole('group',{name:'مسیرهای پروژه',exact:true});for(const route of ['مشارکت','پیمانکاری','خرید','اجاره','میراث'])await choices.getByRole('checkbox',{name:route,exact:true}).check();
 await page.getByRole('checkbox',{name:'ترتیبات اختصاصی مرمت و بهره‌برداری دارد',exact:true}).check();
 const schema=await(await page.request.get('/api/v1/workspace/schema')).json();expect(schema.fields.length).toBe(69);
 for(const f of schema.fields){if(f.unit){await expect(page.getByLabel(f.label+' — وضعیت',{exact:true})).toBeVisible();await expect(page.getByLabel(f.label+' — واحد',{exact:true})).toHaveValue(f.unit);}
 else if(f.kind==='multi')await expect(page.locator('#field-'+f.key)).toBeVisible();else await expect(page.getByLabel(f.label,{exact:true})).toBeVisible();}
});

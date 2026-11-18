import {test,expect,type Page} from '@playwright/test';
import fs from 'node:fs';
const evidence='../docs/core-delivery/fix-01-evidence';
async function role(p:Page,name:string){await p.goto('/local-roles');await p.getByRole('button',{name:new RegExp('^'+name+' ·')}).click();await p.waitForURL(u=>!u.pathname.includes('local-roles'))}
async function save(p:Page){const response=p.waitForResponse(r=>r.request().method()==='POST'&&/\/workspace\/drafts\/[^/]+$/.test(new URL(r.url()).pathname));await p.getByRole('button',{name:'ذخیره پیش‌نویس',exact:true}).click();expect((await response).status()).toBe(200);await expect(p.getByRole('status').filter({hasText:'ذخیره شد'})).toBeVisible()}
async function toggle(p:Page,name:string,checked:boolean){p.once('dialog',d=>d.accept());await p.getByRole('checkbox',{name,exact:true}).setChecked(checked)}
test('operator work period: explicit unit, resume, switch routes, publish, detail and frozen guide',async({browser})=>{
 fs.mkdirSync(evidence,{recursive:true});
 const owner=await browser.newContext(),admin=await browser.newContext();const p=await owner.newPage(),a=await admin.newPage();
 await role(p,'مالک مصنوعی');await role(a,'ادمین بررسی مستقل مصنوعی');
 await p.goto('/drafts');await p.getByLabel('نوع فرصت',{exact:true}).selectOption('project');await p.getByRole('button',{name:'ایجاد پیش‌نویس',exact:true}).click();
 await toggle(p,'بهره‌برداری',true);
 const title='دوره خدمت مصنوعی CORE-FIX-01 '+Date.now();
 const schema=await (await p.request.get('/api/v1/workspace/schema?kind=project')).json();
 for(const f of schema.fields){
  if(f.key==='operator_work_period')continue;
  const input=p.locator('#field-'+f.key),status=p.getByLabel(f.label+' — وضعیت',{exact:true});
  if(f.unit){if(await status.isVisible()){await status.selectOption('unknown');const basis=p.getByLabel(f.label+' — مبنای شروع',{exact:true});if(await basis.isVisible())await basis.fill('unspecified')}}
  else if(await input.isVisible()){
   if(f.key==='title')await input.fill(title);
   else if(f.key==='description')await input.fill('شرح خدمت مصنوعی: نگهداری تاسیسات و پایش عملکرد پس از تحویل کارگاه.');
   else if(await input.evaluate((e:Element)=>e.tagName==='SELECT'))await input.selectOption('unknown');
   else if(await input.evaluate((e:Element)=>e.tagName==='FIELDSET'))await input.locator('select').selectOption('unknown');
   else await input.locator('..').getByRole('button',{name:'نامعلوم',exact:true}).click();
  }
 }
 await save(p);await expect(p.getByText('دوره کار بهره‌برداری',{exact:true}).last()).toBeVisible();
 const period=p.getByLabel('دوره کار بهره‌برداری',{exact:true}),unit=p.getByLabel('دوره کار بهره‌برداری — واحد',{exact:true});
 await p.getByLabel('دوره کار بهره‌برداری — وضعیت',{exact:true}).selectOption('known');
 await expect(unit).toHaveValue('');await unit.selectOption('DAY');await period.fill('۱۸٫۵');await p.getByLabel('دوره کار بهره‌برداری — مبنای شروع',{exact:true}).fill('تحویل کارگاه');
 await save(p);await p.reload();await p.locator('li').filter({has:p.getByText(title,{exact:true})}).getByRole('button',{name:'ادامه ویرایش',exact:true}).click();await expect(period).toHaveValue('۱۸٫۵');await expect(unit).toHaveValue('DAY');
 await toggle(p,'پیمانکاری',true);await toggle(p,'بهره‌برداری',false);await expect(period).not.toBeVisible();await save(p);await p.reload();await p.locator('li').filter({has:p.getByText(title,{exact:true})}).getByRole('button',{name:'ادامه ویرایش',exact:true}).click();await expect(period).not.toBeVisible();
 await toggle(p,'بهره‌برداری',true);await toggle(p,'پیمانکاری',false);await expect(period).toHaveValue('۱۸٫۵');await save(p);
 await p.screenshot({path:evidence+'/operator-form-1440.png',fullPage:true,mask:[p.locator('.account-status-header')]});
 await p.getByRole('button',{name:'ارسال نسخه ذخیره‌شده برای بررسی',exact:true}).click();await expect(p.getByRole('status').filter({hasText:'نسخه ذخیره‌شده ارسال شد'})).toBeVisible();
 await a.goto('/admin');const row=a.locator('details').filter({has:a.locator('summary',{hasText:title})}).first();await row.locator('summary').click();await row.getByLabel('نتیجه',{exact:true}).selectOption('approved');await row.getByLabel('دلیل تصمیم',{exact:true}).fill('بررسی مستقل دوره خدمت مصنوعی');await row.getByRole('button',{name:'ثبت تصمیم',exact:true}).click();await expect(row.locator('summary')).toContainText('تأییدشده');
 const feed=await (await p.request.get('/api/v1/core/opportunities?criteria='+encodeURIComponent(JSON.stringify({route:'operator',q:title})))).json();expect(feed.items).toHaveLength(1);
 const item=feed.items[0];expect(item.fields.operator_work_period.unit.code).toBe('DAY');expect(item.fields.operator_work_period.basis.start_basis).toBe('تحویل کارگاه');expect(item.fields.min_capital).toBeUndefined();
 await p.goto('/opportunities/'+item.id);await p.getByText('مقادیر دقیق، واحدها و مبنای ادعاهای ثبت‌شده',{exact:true}).click();await expect(p.getByText('دوره کار بهره‌برداری',{exact:true}).first()).toBeVisible();await expect(p.getByText('۱۸.۵ روز',{exact:true}).first()).toBeVisible();
 await p.screenshot({path:evidence+'/operator-detail-1440.png',fullPage:true,animations:'disabled',mask:[p.locator('.account-status-header')]});
 await p.goto('/guide/'+item.id);const download=p.waitForEvent('download');await p.getByRole('button',{name:'دانلود فایل راهنما',exact:true}).click();const file=await download;const html=fs.readFileSync((await file.path())!,'utf8');expect(html).toContain('دوره کار بهره‌برداری');expect(html).toContain('تحویل کارگاه');expect(html).toContain('operator_work_period');
 fs.writeFileSync(evidence+'/operator-journey.json',JSON.stringify({opportunity_id:item.id,revision:item.revision,period:item.fields.operator_work_period,synthetic:true},null,2)+'\n');
 await owner.close();await admin.close();
});

for(const kind of ['project','fund','sale']){
 test('compare groups, two to four, navigation and mobile: '+kind,async({browser})=>{
  const c=await browser.newContext(),p=await c.newPage();const apiErrors:string[]=[];await p.route('**/api/v1/auth/csrf',async route=>{const response=await route.fetch();await new Promise(resolve=>setTimeout(resolve,200));await route.fulfill({response})});p.on('response',async r=>{if(r.status()>=400&&r.url().includes('/api/')){apiErrors.push(new URL(r.url()).pathname+':'+r.status());console.log('failed API',new URL(r.url()).pathname,r.status(),(await r.json()).error?.code)}});const items:{id:string}[]=[];let cursor:string|null=null;
  do {const response=await p.request.get('/api/v1/core/opportunities?'+new URLSearchParams({criteria:JSON.stringify({kind}),...(cursor?{cursor}:{})}));expect(response.status()).toBe(200);const feed:{items:{id:string}[];next:string|null}=await response.json();items.push(...feed.items);cursor=feed.next;}while(cursor&&items.length<4);
  expect(items.length).toBeGreaterThanOrEqual(4);const ids=items.slice(0,4).map(x=>x.id);
  for(const count of [2,3,4]){
   await p.goto('/compare?ids='+ids.slice(0,count).join(','));
   const groups=p.locator('[data-compare-group]');await expect(groups).toHaveCount(kind==='sale'?3:4);
   expect(await groups.evaluateAll(els=>els.map(e=>e.getAttribute('data-compare-group')))).toEqual(kind==='sale'?['money','risk','project']:['money','time','risk','project']);
   expect(await groups.locator('h2').allTextContents()).toEqual(kind==='project'?['پول','زمان','ریسک و حقوق','پروژه و محل']:kind==='fund'?['پول','زمان','ریسک و حقوق','صندوق و طرح']:['پول','ریسک و حقوق','دارایی و محل']);
   await expect(p.getByRole('navigation',{name:'پیمایش گروه‌های مقایسه'})).toBeVisible();
   await expect(p.getByRole('table').first().locator('thead th')).toHaveCount(count+1);
   const missingKeys=await p.locator('[data-compare-group] tbody tr').evaluateAll(els=>els.map(e=>e.id.slice(4)));
   const csrf=(await (await p.request.get('/api/v1/auth/csrf')).json()).csrfToken;
   const data=await (await p.request.post('/api/v1/core/compare',{headers:{'X-CSRFToken':csrf},data:{ids:ids.slice(0,count)}})).json();
   expect([...missingKeys].sort()).toEqual([...data.rows.map((r:{key:string})=>r.key),...(kind==='project'?['routes']:[])].sort());
  }
  for(const width of [1440,390]){
   await p.setViewportSize({width,height:1000});await p.goto('/compare?ids='+ids.slice(0,2).join(','));await expect(p.getByRole('table').first()).toBeVisible();
   const nav=p.getByRole('navigation',{name:'پیمایش گروه‌های مقایسه'});const last=nav.getByRole('link').last();await last.focus();await p.keyboard.press('Enter');await expect(p).toHaveURL(/#compare-project$/);
   expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
   await p.screenshot({path:evidence+'/compare-'+kind+'-'+width+'.png',fullPage:true,animations:'disabled'});
  }
  await p.getByRole('button',{name:'برداشتن انتخاب',exact:true}).first().click();await expect(p.getByText('حداقل دو مورد انتخاب کنید.',{exact:true})).toBeVisible();
  await p.locator('section input[type=checkbox]:not(:checked):not(:disabled)').first().check();
  await expect(p.getByRole('table').first().locator('thead th')).toHaveCount(3);
  for(const count of [3,4]){await p.locator('section input[type=checkbox]:not(:checked):not(:disabled)').first().check();await expect(p.getByRole('table').first().locator('thead th')).toHaveCount(count+1)}
  await expect(p.locator('section input[type=checkbox]:not(:checked)').first()).toBeDisabled();
  await p.getByRole('button',{name:'پاک کردن همه',exact:true}).click();await expect(p.getByText('حداقل دو مورد انتخاب کنید.',{exact:true})).toBeVisible();
  expect(apiErrors).toEqual([]);await c.close();
 });
}

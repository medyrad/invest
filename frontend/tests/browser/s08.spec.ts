import {test,expect,type Page} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const evidence=path.resolve(__dirname,'../../../docs/stage8/evidence');

async function role(page:Page,name:string){await page.goto('/local-roles');await page.getByRole('button',{name:new RegExp('^'+name+' ·')}).click();await page.waitForURL(u=>!u.pathname.includes('local-roles'))}
async function fillRequired(page:Page){
 const editor=page.locator('.service-editor');
 for(let pass=0;pass<3;pass++){
  const radios=editor.locator('form input[type=radio]:visible');if(await radios.count()&&!await editor.locator('form input[type=radio]:checked').count())await radios.first().check();
  const selectLabels=await editor.locator('form select:visible').evaluateAll(es=>es.map(e=>e.getAttribute('aria-label')).filter(Boolean)) as string[];
  for(const label of selectLabels){const select=editor.locator('form').getByRole('combobox',{name:label,exact:true});if(!await select.isVisible())continue;
   if(await select.inputValue())continue;
   const value=await select.locator('option').evaluateAll(os=>os.map(x=>(x as HTMLOptionElement).value).find(x=>x!==''));if(value)await select.selectOption(value);
  }
  for(const input of await editor.locator('form input:not([type=checkbox]):not([type=radio]):visible, form textarea:visible').all()){
   if(await input.inputValue())continue;const label=await input.getAttribute('aria-label')||'';const numeric=await input.getAttribute('inputmode')==='decimal';await input.fill(label.includes('مبنای شروع')?'unspecified':numeric?'10':'داده مصنوعی مرورگر');
  }
  const checks=editor.locator('form input[type=checkbox]:visible');if(await checks.count()&&!await checks.first().isChecked())await checks.first().check();
  await page.waitForTimeout(400);
 }
}
const kinds=['proposal','ideas','land-preparation','foreign-investment','ma-notice','ma-renewal','ma-manager','ma-exchange','charity'];
for(const kind of kinds)test('S08 complete browser journey '+kind,async({browser})=>{
 const customer=await browser.newContext(),admin=await browser.newContext(),expert=await browser.newContext();const p=await customer.newPage(),a=await admin.newPage(),e=await expert.newPage();
 await role(p,'مشتری مصنوعی');await p.goto('/tools/'+kind);await expect(p.locator('.service-editor form')).toBeVisible();
 // Every control is entered in the native UI; required conditional questions appear from server schema.
 for(let step=0;step<2;step++){const next=p.getByRole('button',{name:/^ادامه به /});if(!await next.count())break;await fillRequired(p);await next.click();await p.waitForTimeout(400)}
 await expect(p.getByRole('heading',{name:/^جمع‌بندی /})).toBeVisible();
 // Quantities are entered as decimal strings through explicit unit/status controls.
 const errors=p.locator('.service-summary [role=alert]');if(await errors.count())throw new Error(await errors.allTextContents()+ ' '+kind);
 await p.getByRole('button',{name:'ذخیره پیش‌نویس؛ حتی ناقص',exact:true}).click();await expect(p.locator('.service-notice')).toContainText('ذخیره');
 const drafts=await (await p.request.get('/api/v1/workspace/drafts')).json();const draft=drafts.drafts.find((d:{kind:string})=>d.kind===kind);expect(draft).toBeTruthy();expect(draft.missing).toEqual([]);
 const before=(await (await p.request.get('/api/v1/core/dashboard')).json()).cases.length;
 const dl=p.waitForEvent('download');await p.getByRole('button',{name:'دریافت بسته؛ بدون ارسال',exact:true}).click();const download=await dl;const file=await download.path();expect(fs.readFileSync(file!,'utf8')).toContain('دریافت بسته به معنی ارسال درخواست نیست');if(kind==='ideas')fs.copyFileSync(file!,evidence+'/ideas-report.html');expect((await (await p.request.get('/api/v1/core/dashboard')).json()).cases.length).toBe(before);
 await p.screenshot({path:evidence+'/'+kind+'-summary-1440.png',fullPage:true,animations:'disabled'});
 await p.getByRole('button',{name:'ارسال صریح برای بررسی کارشناس',exact:true}).click();await p.waitForURL(/\/requests\/[a-f0-9-]+$/);const id=p.url().split('/').pop()!;
 await role(a,'ادمین بررسی مستقل مصنوعی');const dashboard=await (await a.request.get('/api/v1/core/dashboard')).json();const c=dashboard.cases.find((x:{id:string})=>x.id===id);expect(c.subject.type).toBe('service');expect(c.opportunity_id).toBeNull();const selected=dashboard.experts.find((x:{name:string})=>x.name==='کارشناس مصنوعی یک');
 const card=a.locator('article').filter({has:a.locator('a[href="/requests/'+id+'"]')});await card.getByLabel('کارشناس جاری',{exact:true}).selectOption(selected.id);await card.getByLabel('علت ارجاع یا تغییر',{exact:true}).fill('ارجاع مصنوعی مرورگر');await card.getByRole('button',{name:'ارجاع پرونده',exact:true}).click();await expect(card.getByRole('link')).toContainText('ارجاع‌شده');
 await role(e,'کارشناس مصنوعی یک');await e.goto('/requests/'+id);await e.getByLabel('متن پیام',{exact:true}).fill('پاسخ نهایی مصنوعی خدمت '+kind);await e.getByLabel('نوع اقدام',{exact:true}).selectOption('answer');await e.getByLabel('موعد پیگیری بعد',{exact:true}).fill(new Date(Date.now()+2*86400000).toISOString().slice(0,16));await e.getByLabel('گام بعد',{exact:true}).fill('تکمیل مدارک مصنوعی');await e.getByRole('button',{name:'ارسال پیام',exact:true}).click();await expect(e.getByText('پاسخ نهایی مصنوعی خدمت '+kind,{exact:true})).toBeVisible();
 await p.reload();await expect(p.getByText('پاسخ نهایی مصنوعی خدمت '+kind,{exact:true})).toBeVisible();await p.getByLabel('متن پیام',{exact:true}).fill('پیگیری مشتری مصنوعی');await p.getByRole('button',{name:'ارسال پیام',exact:true}).click();await expect(p.getByText('پیگیری مشتری مصنوعی',{exact:true})).toBeVisible();
 for(const ctx of [customer,admin,expert])await ctx.close();
});

test('S08 mobile conditional housing, exact totals and hidden restore',async({browser})=>{
 const ctx=await browser.newContext({viewport:{width:390,height:844}}),p=await ctx.newPage();await role(p,'مشتری مصنوعی');await p.goto('/tools/ma-renewal');
 const definition=await (await p.request.get('/api/v1/services/schema/ma-renewal')).json();const name=(key:string)=>definition.fields.find((f:{key:string})=>f.key===key).label.replace(/[\s،,(]*اختیاری\)?/g,'').replace(/[،;،,:]+$/u,'').trim();
 await p.getByRole('combobox',{name:name('displacement'),exact:true}).selectOption('yes');
 for(const [key,value] of [['households','۱۰'],['deposit','۲۰۰'],['rent','۵'],['months','۶']]){
  const label=name(key);await p.getByRole('combobox',{name:label+' — وضعیت',exact:true}).selectOption('known');await p.getByLabel(label,{exact:true}).fill(value);if(key==='months')await p.getByLabel(label+' — مبنای شروع',{exact:true}).fill('unspecified');
 }
 await fillRequired(p); // Remaining optional text/selects; entered numeric values are preserved.
 await p.getByRole('button',{name:/^ادامه به /}).click();await expect(p.getByRole('heading',{name:/^جمع‌بندی /})).toBeVisible();await expect(p.getByText(/ودیعه قابل بازگشت کل:/)).toContainText('2000000000');await expect(p.getByText(/اجاره کل دوره:/)).toContainText('300000000');
 await p.screenshot({path:evidence+'/renewal-exact-390.png',fullPage:true,animations:'disabled'});
 await p.locator('.service-steps button').first().click();await p.getByRole('combobox',{name:name('displacement'),exact:true}).selectOption('no');await expect(p.getByLabel(name('deposit'),{exact:true})).not.toBeVisible();await p.getByRole('combobox',{name:name('displacement'),exact:true}).selectOption('yes');await expect(p.getByLabel(name('deposit'),{exact:true})).toHaveValue('۲۰۰');
 expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await ctx.close();
});

test('S08 lost save response replays same operation and no extra revision',async({browser})=>{
 const ctx=await browser.newContext(),p=await ctx.newPage();await role(p,'مشتری مصنوعی');await p.goto('/tools/ideas');await fillRequired(p);await p.getByRole('button',{name:'ذخیره پیش‌نویس؛ حتی ناقص',exact:true}).click();await expect(p.locator('.service-notice')).toContainText('ذخیره');
 const bodies:string[]=[];let lose=true;await p.route('**/api/v1/workspace/drafts/*',async route=>{if(route.request().method()!=='POST')return route.continue();bodies.push(route.request().postData()!);const response=await route.fetch();if(lose){lose=false;await route.abort('connectionfailed')}else await route.fulfill({response})});
 await p.getByRole('button',{name:'ذخیره پیش‌نویس؛ حتی ناقص',exact:true}).click();await expect(p.getByRole('button',{name:'دریافت نتیجه همان عملیات',exact:true})).toBeVisible();await p.getByRole('button',{name:'دریافت نتیجه همان عملیات',exact:true}).click();await expect(p.locator('.service-notice')).toContainText('رسید ذخیره بازیابی شد');expect(bodies).toHaveLength(2);expect(bodies[0]).toBe(bodies[1]);const body=JSON.parse(bodies[0]);const saved=await (await p.request.get('/api/v1/workspace/drafts')).json();expect(saved.drafts.find((d:{kind:string})=>d.kind==='ideas').version).toBe(body.version+1);await ctx.close();
});

test('S08 responsive catalog, nested land order and no embedded engine',async({browser})=>{
 const ctx=await browser.newContext(),p=await ctx.newPage();await p.goto('/tools');await expect(p.getByRole('heading',{name:'همه خدمات، بر اساس آنچه دارید'})).toBeVisible();
 for(const width of [360,768,1440]){await p.setViewportSize({width,height:1000});await p.goto('/tools/land-preparation');await expect(p.locator('.service-editor')).toBeVisible();await expect(p.locator('iframe')).toHaveCount(0);expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await p.screenshot({path:evidence+'/land-initial-'+width+'.png',fullPage:true,animations:'disabled'})}
 const d=await (await p.request.get('/api/v1/services/schema/land-preparation')).json();const choices=d.fields.find((f:{key:string})=>f.key==='types').options;await p.getByRole('checkbox',{name:choices['lp-legal'],exact:true}).check();await p.getByRole('checkbox',{name:choices['lp-ownership'],exact:true}).check();await p.getByRole('button',{name:'بالا بردن '+choices['lp-ownership'],exact:true}).click();const order=await p.locator('fieldset.service-full ol li').allTextContents();expect(order[0]).toContain(choices['lp-ownership']);await ctx.close();
});

async function enterRoleWithCurrentPage(page:Page,name:string){const roles=await (await page.request.get('/api/v1/core/local-roles')).json();const chosen=roles.roles.find((r:{name:string})=>r.name===name);const csrf=await (await page.request.get('/api/v1/auth/csrf')).json();const response=await page.request.post('/api/v1/core/local-roles',{data:{id:chosen.id},headers:{'X-CSRFToken':csrf.csrfToken}});expect(response.ok()).toBe(true);const me=page.waitForResponse(r=>r.url().endsWith('/auth/me'));await page.evaluate(()=>window.dispatchEvent(new Event('focus')));await me}

test('S08 guest input survives login, old private response cannot enter next account',async({browser})=>{
 const ctx=await browser.newContext(),p=await ctx.newPage();await p.goto('/tools/ideas');const input=p.locator('[data-service-field="title"] textarea,[data-service-field="title"] input').first();await input.fill('راز مصنوعی مهمان');await enterRoleWithCurrentPage(p,'مشتری مصنوعی');await expect(input).toHaveValue('راز مصنوعی مهمان');
 await p.getByRole('button',{name:'ذخیره پیش‌نویس؛ حتی ناقص',exact:true}).click();await expect(p.locator('.service-notice')).toContainText('ذخیره');
 let release!:()=>void;const held=new Promise<void>(r=>{release=r});let seen!:()=>void;const caught=new Promise<void>(r=>{seen=r});let once=true;
 await p.route('**/api/v1/workspace/drafts',async route=>{if(route.request().method()!=='GET'||!once)return route.continue();once=false;const response=await route.fetch();seen();await held;await route.fulfill({response})});
 await p.reload();await caught;await enterRoleWithCurrentPage(p,'مالک مصنوعی');release();await expect(input).toHaveValue('');await p.waitForTimeout(500);expect(await p.locator('.service-editor').textContent()).not.toContain('راز مصنوعی مهمان');await ctx.close();
});

test('S08 private service attachment uses real scanner and stays private after submission',async({browser})=>{
 test.setTimeout(60000);const ctx=await browser.newContext(),p=await ctx.newPage();await role(p,'مشتری مصنوعی');await p.goto('/tools/ideas');await fillRequired(p);await p.getByRole('button',{name:'ذخیره پیش‌نویس؛ حتی ناقص',exact:true}).click();await expect(p.locator('.service-notice')).toContainText('ذخیره');
 await p.getByLabel('انتخاب فایل',{exact:true}).setInputFiles(path.resolve(__dirname,'../../../backend/tests/fixtures/s08/synthetic.pdf'));await expect(p.getByText('synthetic.pdf',{exact:true})).toBeVisible();await expect(p.getByText('بررسی موفق',{exact:false})).toBeVisible({timeout:35000});await p.getByRole('button',{name:'حذف فایل',exact:true}).click();await expect(p.getByRole('button',{name:'بازیابی فایل',exact:true})).toBeVisible();await p.getByRole('button',{name:'بازیابی فایل',exact:true}).click();await expect(p.getByRole('link',{name:'دریافت خصوصی',exact:true})).toBeVisible();const packageDownload=p.waitForEvent('download');await p.getByRole('button',{name:'دریافت بسته؛ بدون ارسال',exact:true}).click();const bundle=await packageDownload;expect(fs.readFileSync((await bundle.path())!).subarray(0,2).toString()).toBe('PK');
 await p.getByRole('button',{name:'ارسال صریح برای بررسی کارشناس',exact:true}).click();await p.waitForURL(/\/requests\/[a-f0-9-]+$/);const link=p.getByRole('link',{name:'دریافت پیوست خصوصی ثبت‌شده خدمت',exact:true});await expect(link).toBeVisible();const href=(await link.getAttribute('href'))!;expect((await p.request.get(href)).status()).toBe(200);
 const stranger=await browser.newContext(),s=await stranger.newPage();expect((await s.request.get(new URL(href,p.url()).href)).status()).toBe(403);await stranger.close();await ctx.close();
});

test('S08 noncash charity exact capacity, unit, period and dormant values',async({browser})=>{
 const ctx=await browser.newContext({viewport:{width:360,height:800}}),p=await ctx.newPage();await role(p,'مشتری مصنوعی');await p.goto('/tools/charity');await p.getByRole('radio',{name:'سلامت و امداد را دسترس‌پذیرتر کنیم',exact:true}).check();await p.locator('[data-service-field="type"] select').selectOption('expertise');await fillRequired(p);
 await p.locator('[data-service-field="noncash_capacity"] select').first().selectOption('known');await p.locator('[data-service-field="noncash_capacity"] select').nth(1).selectOption('SESSION');await p.locator('[data-service-field="noncash_capacity"] input').fill('۱٫۵');
 await p.getByRole('button',{name:'ذخیره پیش‌نویس؛ حتی ناقص',exact:true}).click();await expect(p.locator('.service-notice')).toContainText('ذخیره');
 await p.locator('[data-service-field="type"] select').selectOption('cash');await expect(p.locator('[data-service-field="noncash_capacity"] input')).not.toBeVisible();await p.getByRole('button',{name:'ذخیره پیش‌نویس؛ حتی ناقص',exact:true}).click();await expect(p.locator('.service-notice')).toContainText('ذخیره');const ds=await (await p.request.get('/api/v1/workspace/drafts')).json();const d=ds.drafts.find((d:{kind:string})=>d.kind==='charity');expect(d.effective.noncash_capacity).toBeUndefined();expect(d.raw.noncash_capacity.source_value).toBe('۱٫۵');
 await p.locator('[data-service-field="type"] select').selectOption('expertise');await expect(p.locator('[data-service-field="noncash_capacity"] input')).toHaveValue('۱٫۵');await p.getByRole('button',{name:/^ادامه به /}).click();await expect(p.getByRole('heading',{name:'اثر اجتماعی: نیازمند برآورد کارشناس'})).toBeVisible();await p.screenshot({path:evidence+'/charity-noncash-360.png',fullPage:true,animations:'disabled'});await ctx.close();
});

test('S08 notice historical passport preserves issuer signature guarantee and source',async({browser})=>{
 const ctx=await browser.newContext(),p=await ctx.newPage();await p.goto('/tools/ma-notice');await p.locator('[data-service-field="project"] select').selectOption('REF-SIROS5');await p.getByRole('button',{name:/^ادامه به /}).click();await expect(p.getByText('ثبت‌نام و امضای الکترونیکی',{exact:true})).toBeVisible();await expect(p.getByText('تضمین شرکت و انجام تعهد',{exact:true})).toBeVisible();await expect(p.getByText('شناسه رسمی فراخوان',{exact:true})).toBeVisible();await expect(p.getByRole('link',{name:/خبر مبنای الگوی تاریخی/})).toBeVisible();await p.screenshot({path:evidence+'/notice-historical-passport-1440.png',fullPage:true,animations:'disabled'});await ctx.close();
});

import '/independent/saved.spec';
import '/independent/independent.spec';
import '/independent/race.spec';
import '/independent/clipping.spec';
import {test,expect} from '@playwright/test';

test('two profile tabs preserve genuinely different dirty edits on conflict',async({page,context})=>{
 await login(page);await page.goto('/profile');const other=await context.newPage();await other.goto('/profile');
 const a=page.locator('.professional-form'),b=other.locator('.professional-form');
 await expect(a.getByLabel('نام',{exact:true})).toBeEnabled();await expect(b.getByLabel('نام',{exact:true})).toBeEnabled();
 await a.getByRole('checkbox',{name:'سرمایه‌گذار',exact:true}).check();await b.getByRole('checkbox',{name:'سرمایه‌گذار',exact:true}).check();
 await a.getByLabel('نام',{exact:true}).fill('تغییر قطعی تب اول');await b.getByLabel('نام',{exact:true}).fill('ورودی متفاوت تب دوم');
 await a.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();await expect(a.getByRole('status')).toContainText('با رسید سرور');
 const response=other.waitForResponse(r=>r.url().endsWith('/core/personal')&&r.request().method()==='POST');
 await b.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();expect((await response).status()).toBe(409);
 await expect(b.getByRole('alert')).toBeVisible();await expect(b.getByLabel('نام',{exact:true})).toHaveValue('ورودی متفاوت تب دوم');
 const actual=await(await page.request.get('/api/v1/core/personal')).json();expect(JSON.parse(actual.profile.professional).name).toBe('تغییر قطعی تب اول');
});

for(const mode of ['400','401','500','offline','lost'])test('search-page save retains input and same-key retry '+mode,async({page})=>{
 await login(page);await page.goto('/opportunities');await page.getByRole('textbox',{name:'جست‌وجو در نتایج',exact:true}).fill('آزمون-'+mode+'-'+Date.now());await page.waitForLoadState('networkidle');
 await page.getByRole('button',{name:'فیلترهای ذخیره‌شده',exact:true}).press('Enter');
 await page.getByRole('menuitem',{name:'ذخیره جست‌وجوی فعلی',exact:true}).press('Enter');
 await page.getByLabel('یک نام برایش بگذارید').fill('تلاش مجدد جست‌وجو '+mode);
 let body;let finished=false;
 await page.route('**/api/v1/core/personal',async r=>{
  if(r.request().method()!=='POST')return r.continue();body=r.request().postDataJSON();
  if(mode==='lost'){await r.fetch();finished=true;return r.abort('connectionfailed');}
  finished=true;if(mode==='offline')return r.abort('internetdisconnected');
  return r.fulfill({status:Number(mode),contentType:'application/json',body:JSON.stringify({error:{message:'خطای آزمون'}})});
 });
 const save=page.getByRole('dialog').getByRole('button',{name:'ذخیره',exact:true});await save.click();
 await expect.poll(()=>finished).toBe(true);await expect(page.getByRole('alert')).toBeVisible();
 await expect(page.getByLabel('یک نام برایش بگذارید')).toHaveValue('تلاش مجدد جست‌وجو '+mode);
 await page.unrouteAll({behavior:'wait'});const retry=page.waitForRequest(r=>r.url().endsWith('/core/personal')&&r.method()==='POST');
 await save.click();expect((await retry).postDataJSON().key).toBe(body.key);await expect(page.getByRole('dialog')).toHaveCount(0);
});
// The historical lost-response test returns before route.fetch settles.
// Await teardown in this runner only; original assertions and evidence remain unchanged.
test.afterEach(async({page})=>{await page.unrouteAll({behavior:'wait'});});

async function login(page){await page.goto('/local-roles');await page.getByRole('button',{name:/ · user$/}).click();await page.waitForURL(u=>!u.pathname.includes('local-roles'));}
for(const mode of ['400','401','500','offline','lost'])test('edit criteria preserves old record and retry '+mode,async({page})=>{
 await login(page);await page.goto('/saved');
 await page.getByRole('tab',{name:/فیلترهای ذخیره/}).click();
 await page.getByRole('button',{name:'افزودن فیلتر تازه',exact:true}).first().click();
 const name='ویرایش-'+mode+'-'+Date.now();await page.getByLabel('نام',{exact:true}).fill(name);
 const created=page.waitForResponse(r=>r.url().endsWith('/core/personal')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'ذخیره جست‌وجو',exact:true}).click();expect((await created).status()).toBe(200);
 await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.getByRole('button').filter({hasText:name}).first().click();
 await page.getByRole('button',{name:'ویرایش شرایط',exact:true}).click();
 await page.getByLabel('نام',{exact:true}).fill(name+' جدید');
 let savedBody;let completed=false;
 await page.route('**/api/v1/core/personal',async r=>{
  if(r.request().method()!=='POST')return r.continue();savedBody=r.request().postDataJSON();
  if(mode==='lost'){await r.fetch();completed=true;return r.abort('connectionfailed');}
  completed=true;if(mode==='offline')return r.abort('internetdisconnected');
  return r.fulfill({status:Number(mode),contentType:'application/json',body:JSON.stringify({error:{message:'خطای کنترل‌شده'}})});
 });
 await page.getByRole('button',{name:'ذخیره جست‌وجو',exact:true}).click();
 await expect.poll(()=>completed).toBe(true);await expect(page.getByRole('alert')).toBeVisible();
 await expect(page.getByLabel('نام',{exact:true})).toHaveValue(name+' جدید');
 const before=await(await page.request.get('/api/v1/core/personal')).json();
 expect(before.searches.find(x=>x.id===savedBody.id).name).toBe(mode==='lost'?name+' جدید':name);
 await page.unroute('**/api/v1/core/personal');
 const retried=page.waitForRequest(r=>r.url().endsWith('/core/personal')&&r.method()==='POST');
 await page.getByRole('button',{name:'ذخیره جست‌وجو',exact:true}).click();expect((await retried).postDataJSON().key).toBe(savedBody.key);
 await expect(page.getByRole('dialog')).toHaveCount(0);
});

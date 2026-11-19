import {test,expect} from '@playwright/test';
import fs from 'node:fs';
async function login(page){await page.goto('/local-roles');await page.getByRole('button',{name:/ · user$/}).click();await page.waitForURL(u=>!u.pathname.includes('local-roles'));}
const section=page=>page.getByRole('heading',{name:'اطلاعات حرفه‌ای برای اعمال اختیاری در جست‌وجو'}).locator('..');
for(const mode of ['400','401','500','offline','lost']) test('profile failure '+mode,async({page})=>{
 await login(page);await page.goto('/profile');const s=section(page);
 await expect(s.getByLabel('نام',{exact:true})).toBeVisible();
 await s.getByRole('checkbox',{name:'سرمایه‌گذار',exact:true}).check();
 await s.getByLabel('نام',{exact:true}).fill('نسخه قبلی '+mode);
 await s.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();
 await expect(s.getByRole('status')).toContainText('با رسید سرور',{timeout:30000});
 await s.getByLabel('نام',{exact:true}).fill('ورودی جدید '+mode);
 let sent=false;
 await page.route('**/api/v1/core/personal',async route=>{
  if(route.request().method()!=='POST')return route.continue();sent=true;
  if(mode==='lost'){await route.fetch();return route.abort('connectionfailed');}
  if(mode==='offline')return route.abort('internetdisconnected');
  return route.fulfill({status:Number(mode),contentType:'application/json',body:JSON.stringify({error:{message:'خطای مصنوعی مستقل'}})});
 });
 await s.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();
 await expect(s.getByRole('alert')).toBeVisible({timeout:30000});
 expect(sent).toBe(true);await expect(s.getByLabel('نام',{exact:true})).toHaveValue('ورودی جدید '+mode);
 await expect(s.getByRole('status')).toHaveCount(0);
 const actual=await (await page.request.get('/api/v1/core/personal')).json();
 expect(JSON.parse(actual.profile.professional).name).toBe((mode==='lost'?'ورودی جدید ':'نسخه قبلی ')+mode);
});
test('professional save then basic save preserves both roles',async({page})=>{
 await login(page);await page.goto('/profile');const s=section(page);
 await page.waitForLoadState('networkidle');
 await expect(s.getByLabel('نام',{exact:true})).not.toHaveValue('');
 await s.getByRole('checkbox',{name:'سرمایه‌گذار',exact:true}).setChecked(true);
 await s.getByRole('checkbox',{name:'پیمانکار',exact:true}).setChecked(true);
 const professionalName='ویرایش مستقل '+Date.now();
 await s.getByLabel('نام',{exact:true}).fill(professionalName);
 await s.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();
 await expect(s.getByRole('status')).toContainText('با رسید سرور',{timeout:30000});
 await page.getByRole('textbox',{name:'نام نمایشی',exact:true}).fill('نام مستقل');
 await page.getByRole('button',{name:'ذخیره پروفایل اختیاری',exact:true}).click();
 await expect(page.getByText('پروفایل اختیاری در حساب ذخیره شد.',{exact:true})).toBeVisible();
 const result=await (await page.request.get('/api/v1/core/personal')).json();
 expect(JSON.parse(result.profile.professional||'{}').roles).toEqual(expect.arrayContaining(['investor','contractor']));
 expect(JSON.parse(result.profile.professional||'{}').name).toBe(professionalName);
});
test('guide preview content survives first download',async({page})=>{
 await login(page);await page.goto('/opportunities');await expect(page.locator('article').first()).toBeVisible({timeout:30000});
 const href=await page.locator('article').first().getByRole('link').first().getAttribute('href');await page.goto('/guide/'+href!.split('/').pop());
 await expect(page.getByRole('button',{name:'دانلود فایل راهنما',exact:true})).toBeEnabled({timeout:30000});
 const frame=page.frameLocator('iframe[title="راهنمای اقدام"]');
 const before=await frame.locator('body').innerText();fs.writeFileSync('/evidence/preview.txt',before);
 const checks=frame.locator('input[data-k]');if(await checks.count())await checks.first().locator('..').click();
 const wait=page.waitForEvent('download');await page.getByRole('button',{name:'دانلود فایل راهنما',exact:true}).click();const dl=await wait;
 const html=fs.readFileSync((await dl.path())!,'utf8');fs.writeFileSync('/evidence/first-download.html',html);
 const headings=await frame.locator('h2').allTextContents();
 fs.writeFileSync('/evidence/preview-headings.json',JSON.stringify(headings,null,2));
 expect(html).toContain('گام‌های اقدام');
 expect(html).not.toMatch(/<li>(pre|step)-?\d+<\/li>/);
});
for(const width of [360,390,768,1440])test('local geometry focus '+width,async({browser})=>{
 const c=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});const p=await c.newPage();await p.goto('/tools/land-preparation');await expect(p.getByText('عملیات و مطالعات آماده‌سازی',{exact:true})).toBeVisible({timeout:30000});await p.evaluate(()=>document.fonts.ready);
 const data=await p.evaluate(()=>({width:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.getBoundingClientRect().toJSON(),font:getComputedStyle(document.body).fontFamily,overflow:[...document.querySelectorAll('h1,h2,p,button,label,input,select')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&(r.left< -1||r.right>innerWidth+1)}).map(e=>({tag:e.tagName,text:e.textContent?.slice(0,100),rect:e.getBoundingClientRect().toJSON()}))}));
 await p.screenshot({path:`/evidence/land-viewport-${width}.png`,animations:'disabled'});await p.screenshot({path:`/evidence/land-full-${width}.png`,fullPage:true,animations:'disabled'});
 const focus=[];for(let i=0;i<12;i++){await p.keyboard.press('Tab');focus.push(await p.evaluate(()=>({tag:document.activeElement?.tagName,text:document.activeElement?.textContent?.slice(0,80),rect:document.activeElement?.getBoundingClientRect().toJSON()})))}
 fs.writeFileSync(`/evidence/geometry-${width}.json`,JSON.stringify({...data,focus},null,2));
 expect(data.overflow.filter(x=>x.tag==='BUTTON')).toEqual([]);await c.close();
});

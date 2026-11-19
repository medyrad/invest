import {expect,test,type Page} from '@playwright/test';
import fs from 'node:fs';

const product='http://127.0.0.1:3109';
const reference='http://expit-reference:3107';
const widths=[360,390,768,1440];

for(const width of widths)test(`same-condition reference baseline ${width}`,async({browser})=>{
 test.setTimeout(120000);
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
 const page=await context.newPage();
 await page.goto(reference+'/tools/ma-profile');
 await expect(page.getByText('اطلاعات پایه',{exact:true})).toBeVisible({timeout:30000});await fonts(page);
 await page.screenshot({path:`/evidence/reference-profile-empty-${width}.png`,fullPage:true});
 await page.goto(reference+'/tools/land-preparation');
 await expect(page.getByText('انتخاب خدمات و محل',{exact:true})).toBeVisible({timeout:30000});await fonts(page);
 await page.screenshot({path:`/evidence/reference-land-empty-${width}.png`,fullPage:true});
 await context.close();
});

async function login(page:Page){
 await page.goto(product+'/local-roles');
 await page.getByRole('button',{name:/ · user$/}).click();
 await page.waitForURL(url=>!url.pathname.includes('local-roles'));
}

async function fonts(page:Page){await page.evaluate(()=>document.fonts.ready)}

function insideViewport(rect:{left:number;right:number;top:number;bottom:number},width:number,height=1000){
 return rect.left>=0&&rect.right<=width+1&&rect.top>=0&&rect.top<height&&rect.bottom>0;
}

for(const width of widths)test(`professional form structure, focus and account badge ${width}`,async({browser})=>{
 test.setTimeout(180000);
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
 const page=await context.newPage();
 await page.goto(product+'/tools/ma-profile');
 const form=page.locator('.professional-form');
 await expect(form).toBeVisible({timeout:30000});await fonts(page);
 await expect(form.getByText('معرفی و نقش حرفه‌ای',{exact:true})).toBeVisible();
 await expect(form.getByText('حوزه و توان اجرایی',{exact:true})).toBeVisible();
 await expect(form.getByText('گواهینامه یا صلاحیت مرتبط',{exact:true})).toBeVisible();
 await expect(form.getByText('سوابق و تجربه',{exact:true})).toBeVisible();
 await expect(form.getByText(/۰ از ۲ پرسش ضروری/)).toBeVisible();
 await expect(form.getByText('برای استفاده از راهنما نیازی به کد ملی، اطلاعات حساب بانکی یا بارگذاری مدارک نیست.')).toBeVisible();
 const roleTrigger=form.locator('[role=combobox]').first();
 await expect(roleTrigger).toBeVisible();
 expect(await form.getByRole('checkbox',{name:'سرمایه‌گذار',exact:true}).count()).toBe(0);
 await roleTrigger.click();
 await expect(page.getByRole('checkbox',{name:'سرمایه‌گذار',exact:true})).toBeVisible();
 await page.keyboard.press('Escape');
 const next=form.getByRole('button',{name:/پرسش بعدی بی‌پاسخ/});
 await next.click();await expect(form.getByLabel('نوع فعالیت',{exact:true})).toBeFocused();
 await page.screenshot({path:`/evidence/product-profile-guest-${width}.png`,fullPage:true});

 await login(page);
 for(const route of ['/tools/ma-profile','/profile','/saved']){
  await page.goto(product+route);
  if(route==='/saved')await page.getByRole('tab',{name:/پروفایل حرفه/}).click();
  await expect(page.locator('.professional-form')).toBeVisible({timeout:30000});await fonts(page);
  const account=page.getByRole('button',{name:/^حساب کاربری/});
  const rect=await account.evaluate(el=>el.getBoundingClientRect().toJSON());
  expect(insideViewport(rect,width)).toBeTruthy();
  expect(await account.evaluate(el=>{const r=el.getBoundingClientRect();const hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return hit===el||el.contains(hit)})).toBeTruthy();
  await account.focus();await expect(account).toBeFocused();await account.click();
  await expect(page.getByRole('menuitem',{name:'پروفایل و اعلان‌ها'})).toBeVisible();await page.keyboard.press('Escape');
  const slug=route.replaceAll('/','-');
  await page.screenshot({path:`/evidence/product${slug}-account-${width}.png`,fullPage:true});
 }
 await context.close();
});

for(const width of widths)test(`land all stages preserve values and controls ${width}`,async({browser})=>{
 test.setTimeout(180000);
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
 const page=await context.newPage();await page.goto(product+'/tools/land-preparation');
 const editor=page.locator('.service-editor');await expect(editor).toBeVisible({timeout:30000});await fonts(page);
 for(const [title,sub] of [['انتخاب خدمات و محل','یک ملک، چند خدمت'],['شرایط بسته خدمات','اسناد، پرداخت و تحویل'],['جمع‌بندی بسته','خروجی و قدم بعد']]){
  await expect(editor.getByText(title,{exact:true})).toBeVisible();await expect(editor.getByText(sub,{exact:true})).toBeVisible();
 }
 await editor.getByLabel('چگونه مایل به ورود هستید؟',{exact:true}).selectOption('investor');
 const drops=editor.locator('.service-option-group [role=combobox]');expect(await drops.count()).toBe(2);
 for(let index=0;index<2;index++){
  await drops.nth(index).click();const option=page.getByRole('checkbox').first();await option.click();await page.keyboard.press('Escape');
 }
 const selectedBefore=await editor.locator('.service-selected-order li').allTextContents();expect(selectedBefore.length).toBe(2);
 await page.screenshot({path:`/evidence/product-land-stage1-${width}.png`,fullPage:true});
 await editor.getByRole('button',{name:'ادامه، شرایط بسته خدمات',exact:true}).click();
 await expect(editor.getByText(/بسته شما شامل ۲ خدمت است/)).toBeVisible();
 await expect(editor.locator('.service-steps [aria-current=step]')).toContainText('شرایط بسته خدمات');
 await page.screenshot({path:`/evidence/product-land-stage2-${width}.png`,fullPage:true});
 for(const select of await editor.locator('[data-service-field] select').all())if(await select.isEnabled()&&await select.locator('option').count()>1)await select.selectOption({index:1});
 for(const input of await editor.locator('[data-service-field] input:not([type=checkbox]):not([type=radio])').all())if(await input.isEnabled()&&!await input.inputValue())await input.fill('1');
 const radios=editor.locator('[data-service-field] input[type=radio]');
 const names=await radios.evaluateAll(nodes=>[...new Set(nodes.map(node=>(node as HTMLInputElement).name))]);
 for(const name of names)await editor.locator(`[data-service-field] input[type=radio][name="${name}"]`).first().check();
 for(let attempt=0;attempt<30;attempt++){
  const selects=editor.locator('[data-service-field] select');
  const index=await selects.evaluateAll(nodes=>nodes.findIndex(node=>(node as HTMLSelectElement).selectedIndex===0&&(node as HTMLSelectElement).options.length>1));
  if(index<0)break;await selects.nth(index).selectOption({index:1});
 }
 const publicBuyer=editor.getByLabel('خریدار خدمت عمومی و منبع پرداخت چقدر مشخص است؟',{exact:true});
 if(await publicBuyer.isVisible().catch(()=>false))await publicBuyer.selectOption({index:1});
 for(let attempt=0;attempt<20;attempt++){
  const next=editor.getByRole('button',{name:/پرسش بعدی بی‌پاسخ/});if(!await next.isVisible().catch(()=>false))break;
  await next.click();const active=page.locator(':focus');const tag=await active.evaluate(el=>el.tagName);
  if(tag==='SELECT')await active.selectOption({index:1});
  else if(tag==='INPUT'||tag==='TEXTAREA')await active.fill('1');
  else if(await active.getAttribute('role')==='combobox'){await active.click();await page.getByRole('checkbox').first().click();await page.keyboard.press('Escape')}
 }
 const summary=editor.getByRole('heading',{name:/جمع‌بندی آماده‌سازی/});
 for(let submit=0;submit<4&&!await summary.isVisible().catch(()=>false);submit++){
  await editor.getByRole('button',{name:'نمایش جمع‌بندی بسته خدمات',exact:true}).click();
  await page.waitForTimeout(500);
  if(await summary.isVisible().catch(()=>false))break;
  const selects=editor.locator('[data-service-field] select');
  for(let attempt=0;attempt<30;attempt++){
   const index=await selects.evaluateAll(nodes=>nodes.findIndex(node=>(node as HTMLSelectElement).selectedIndex===0&&(node as HTMLSelectElement).options.length>1));
   if(index<0)break;await selects.nth(index).selectOption({index:1});
  }
 }
 await expect(summary).toBeVisible();
 await expect(editor.getByRole('button',{name:'ویرایش شرایط بسته',exact:true})).toBeVisible();
 await page.screenshot({path:`/evidence/product-land-stage3-${width}.png`,fullPage:true});
 await editor.getByRole('button',{name:'ویرایش شرایط بسته',exact:true}).click();
 await editor.getByRole('button',{name:'ویرایش خدمات و محل',exact:true}).click();
 expect(await editor.locator('.service-selected-order li').allTextContents()).toEqual(selectedBefore);
 const geometry=await editor.evaluate((el,w)=>({documentWidth:document.documentElement.scrollWidth,controls:[...el.querySelectorAll<HTMLElement>('button,input,select,textarea,[role=combobox]')].filter(x=>{const r=x.getBoundingClientRect();return r.width>0&&r.height>0}).map(x=>({text:x.getAttribute('aria-label')||x.textContent?.trim().slice(0,50),...x.getBoundingClientRect().toJSON(),hit:(()=>{const r=x.getBoundingClientRect();const h=document.elementFromPoint(Math.max(0,Math.min(innerWidth-1,r.left+r.width/2)),Math.max(0,Math.min(innerHeight-1,r.top+r.height/2)));return h===x||x.contains(h)})()}))}),width);
 expect(geometry.controls.filter((r:any)=>r.left<0||r.right>width+1)).toEqual([]);
 fs.writeFileSync(`/evidence/land-geometry-${width}.json`,JSON.stringify(geometry,null,2));
 await context.close();
});

for(const mode of ['400','401','500','offline','lost'])test(`quick professional card preserves input and retries ${mode}`,async({page})=>{
 test.setTimeout(120000);await login(page);await page.goto(product+'/opportunities');
 await page.getByRole('button',{name:/درباره شما/}).click();
 await page.getByRole('button',{name:/ساخت سریع پروفایل|ویرایش/}).click();
 const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible();
 await dialog.getByText('سازنده',{exact:true}).click();
 const capital=dialog.getByPlaceholder('مثلاً ۵۰');if(await capital.isVisible())await capital.fill('73');
 let first:any;let finished=false;
 await page.route('**/api/v1/core/personal',async route=>{
  if(route.request().method()!=='POST')return route.continue();first=route.request().postDataJSON();
  if(mode==='lost'){await route.fetch();finished=true;return route.abort('connectionfailed')}
  finished=true;if(mode==='offline')return route.abort('internetdisconnected');
  return route.fulfill({status:Number(mode),contentType:'application/json',body:JSON.stringify({error:{message:'خطای کنترل‌شده'}})});
 });
 await dialog.getByRole('button',{name:'ذخیره و اعمال روی فیلترها',exact:true}).click();
 await expect.poll(()=>finished).toBeTruthy();await expect(dialog.getByRole('alert')).toContainText('ورودی شما حفظ شده است');
 if(await capital.isVisible())await expect(capital).toHaveValue('73');
 await page.unrouteAll({behavior:'wait'});
 const retry=page.waitForRequest(request=>request.url().endsWith('/core/personal')&&request.method()==='POST');
 await dialog.getByRole('button',{name:'ذخیره و اعمال روی فیلترها',exact:true}).click();
 expect((await retry).postDataJSON().key).toBe(first.key);await expect(dialog).toHaveCount(0);
});

test('real pointer click opens save dialog during ranking refresh',async({page})=>{
 test.setTimeout(120000);await login(page);await page.goto(product+'/opportunities');
 let delay=false;
 await page.route('**/api/v1/core/opportunities?*',async route=>{if(delay)await new Promise(resolve=>setTimeout(resolve,700));await route.continue()});
 delay=true;
 await page.getByLabel('مبلغ',{exact:true}).check();
 const trigger=page.getByRole('button',{name:'فیلترهای ذخیره‌شده',exact:true});
 await trigger.click();
 const item=page.getByRole('menuitem',{name:'ذخیره جست‌وجوی فعلی',exact:true});await expect(item).toBeVisible();
 await item.click();
 await expect(page.getByRole('dialog',{name:'ذخیره این جست‌وجو'})).toBeVisible();
});

test('actual immutable report has preview semantics and readable document design',async({browser})=>{
 test.setTimeout(180000);
 const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true,reducedMotion:'reduce'});
 const page=await context.newPage();await login(page);await page.goto(product+'/opportunities');
 const article=page.locator('article').first();await expect(article).toBeVisible({timeout:30000});
 const href=await article.getByRole('link').first().getAttribute('href');await page.goto(product+'/guide/'+href!.split('/').pop());
 const frame=page.frameLocator('iframe[title="راهنمای اقدام"]');await expect(frame.locator('body')).toContainText('پرونده کامل',{timeout:30000});
 const preview=await frame.locator('body').innerText();
 const wait=page.waitForEvent('download');await page.getByRole('button',{name:'دانلود فایل راهنما',exact:true}).click();
 const download=await wait;const html=fs.readFileSync((await download.path())!,'utf8');fs.writeFileSync('/evidence/actual-report.html',html);
 for(const text of ['پرونده کامل','گام‌های اقدام','رسید و مبنای ثابت گزارش'])expect(html).toContain(text);
 for(const text of ['پرونده کامل','گام‌های اقدام'])expect(preview).toContain(text);
 expect(html).toContain('class="doc-brand"');expect(html).toContain('class="card"');
 for(const width of widths){
  const documentPage=await context.newPage();await documentPage.setViewportSize({width,height:1200});await documentPage.setContent(html,{waitUntil:'load'});await fonts(documentPage);
  await documentPage.screenshot({path:`/evidence/actual-report-${width}.png`,fullPage:true});await documentPage.close();
 }
 await context.close();
});

test.afterEach(async({page})=>{await page.unrouteAll({behavior:'wait'})});

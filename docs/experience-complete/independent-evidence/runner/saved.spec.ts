import {test,expect} from '@playwright/test';
import fs from 'node:fs';
async function login(page){await page.goto('/local-roles');await page.getByRole('button',{name:/^مشتری مصنوعی ·/}).click();await page.waitForURL(u=>!u.pathname.includes('local-roles'));}
for(const mode of ['400','401','500','offline','lost'])test('saved criteria preserves input on '+mode,async({page})=>{
 await login(page);await page.goto('/saved');await page.getByRole('button',{name:'افزودن فیلتر تازه',exact:true}).first().click();
 await page.getByLabel('نام',{exact:true}).fill('شرایط مستقل '+mode);
 await page.route('**/api/v1/core/personal',async route=>{
   if(route.request().method()!=='POST')return route.continue();
   if(mode==='lost'){await route.fetch();return route.abort('connectionfailed');}
   if(mode==='offline')return route.abort('internetdisconnected');
   return route.fulfill({status:Number(mode),contentType:'application/json',body:JSON.stringify({error:{message:'خطای ذخیره مستقل'}})});
 });
 await page.getByRole('button',{name:'ذخیره جست‌وجو',exact:true}).click();
 await expect(page.getByRole('dialog',{name:'جست‌وجوی تازه'})).toBeVisible();
 await expect(page.getByLabel('نام',{exact:true})).toHaveValue('شرایط مستقل '+mode);
});
test('guest criteria snapshot and same-key replay across two tabs',async({page,context})=>{
 await page.goto('/opportunities');await page.getByRole('button',{name:'فیلترهای ذخیره‌شده',exact:true}).click();
 await page.getByRole('menuitem',{name:/ذخیره/}).first().click();
 await page.getByLabel('یک نام برایش بگذارید').fill('snapshot مستقل');
 let snapshot;await page.route('**/api/v1/auth/intent',async r=>{snapshot=r.request().postDataJSON();await r.continue()});
 await page.getByRole('button',{name:'ورود و ذخیره',exact:true}).click();
 await page.getByLabel('شماره موبایل',{exact:true}).fill('0919'+String(Date.now()).slice(-7));
 await page.getByRole('button',{name:'دریافت کد',exact:true}).click();await expect(page.getByTestId('trial-code')).toBeVisible({timeout:30000});
 await page.getByLabel('کد تایید',{exact:true}).fill((await page.getByTestId('trial-code').textContent())!);
 await page.getByRole('button',{name:'ورود',exact:true}).click();await expect(page.getByRole('dialog')).not.toBeVisible({timeout:30000});
 const p=await (await page.request.get('/api/v1/core/personal')).json();expect(p.searches).toHaveLength(1);expect(p.searches[0].criteria).toEqual(snapshot.snapshot.operation.criteria);
 const tab=await context.newPage();await tab.goto('/saved');
 const data={key:snapshot.snapshot.key,action:'search',id:null,value:{name:snapshot.snapshot.operation.name,criteria:snapshot.snapshot.operation.criteria}};
 const post=async p=>p.evaluate(async data=>{const csrf=await(await fetch('/api/v1/auth/csrf')).json();const r=await fetch('/api/v1/core/personal',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf.csrfToken},body:JSON.stringify(data)});return {status:r.status,data:await r.json()}},data);
 const replies=await Promise.all([post(page),post(tab)]);expect(replies.map(x=>x.status)).toEqual([200,200]);
 expect((await(await page.request.get('/api/v1/core/personal')).json()).searches).toHaveLength(1);
 fs.writeFileSync('/evidence/guest-snapshot.json',JSON.stringify({criteria:p.searches[0].criteria,replayStatuses:replies.map(x=>x.status)},null,2));
});
test('late consumed handoff cannot be adopted by account B in second tab',async({page,context})=>{
 await page.goto('/opportunities');const card=page.locator('article').filter({has:page.getByRole('button',{name:'ذخیره پروژه',exact:true})}).nth(1);await expect(card).toBeVisible({timeout:30000});
 const id=(await card.getByRole('link').first().getAttribute('href'))!.split('/').pop();
 await card.getByRole('button',{name:'ذخیره پروژه',exact:true}).click();
 let release;const hold=new Promise<void>(r=>release=r);let captured=false;
 await page.route('**/api/v1/auth/intent/consume',async r=>{const response=await r.fetch();captured=true;await hold;await r.fulfill({response})});
 await page.getByLabel('شماره موبایل',{exact:true}).fill('0918'+String(Date.now()).slice(-7));await page.getByRole('button',{name:'دریافت کد',exact:true}).click();await expect(page.getByTestId('trial-code')).toBeVisible({timeout:30000});
 await page.getByLabel('کد تایید',{exact:true}).fill((await page.getByTestId('trial-code').textContent())!);await page.getByRole('button',{name:'ورود',exact:true}).click();
 await expect.poll(()=>captured,{timeout:30000}).toBe(true);
 const tab=await context.newPage();await tab.goto('/local-roles');await tab.getByRole('button',{name:/^مالک مصنوعی ·/}).click();await tab.waitForURL(u=>!u.pathname.includes('local-roles'));
 const before=await(await tab.request.get('/api/v1/core/personal')).json();expect(before.saved.some(x=>x.id===id)).toBe(false);
 release();await expect.poll(async()=>!(await page.getByRole('dialog').isVisible())||await page.getByRole('dialog').getByRole('alert').isVisible(),{timeout:30000}).toBe(true);
 const other=await(await tab.request.get('/api/v1/core/personal')).json();
 fs.writeFileSync('/evidence/late-handoff.json',JSON.stringify({target:id,before:before.saved.map(x=>x.id),otherAccountSaved:other.saved.map(x=>x.id)},null,2));
 expect(other.saved.some(x=>x.id===id)).toBe(false);
});

import {test,expect} from '@playwright/test';
import fs from 'node:fs';
test('delayed profile refresh must not erase a newer edit',async({page})=>{
 await page.goto('/local-roles');await page.getByRole('button',{name:/ · user$/}).click();await page.waitForURL(u=>!u.pathname.includes('local-roles'));await page.goto('/profile');await page.waitForLoadState('networkidle');
 const s=page.getByRole('heading',{name:'اطلاعات حرفه‌ای برای اعمال اختیاری در جست‌وجو'}).locator('..');
 await expect(s.getByLabel('نام',{exact:true})).not.toHaveValue('');
 let release;const hold=new Promise<void>(r=>release=r);let post=false,captured=false;
 await page.route('**/api/v1/core/personal',async r=>{if(r.request().method()==='POST'){post=true;return r.continue();}if(post&&!captured){const response=await r.fetch();captured=true;await hold;return r.fulfill({response});}return r.continue();});
 await s.getByLabel('نام',{exact:true}).fill('نسخه ذخیره شده');await s.getByRole('button',{name:'ذخیره اطلاعات حرفه‌ای اختیاری',exact:true}).click();await expect(s.getByRole('status')).toContainText('با رسید سرور',{timeout:30000});await expect.poll(()=>captured).toBe(true);
 await s.getByLabel('نام',{exact:true}).fill('ویرایش تازه هنوز ذخیره نشده');release();
 await expect(s.getByLabel('نام',{exact:true})).toHaveValue('ویرایش تازه هنوز ذخیره نشده');
 await page.waitForLoadState('networkidle');
 fs.writeFileSync('/evidence/profile-late-refresh.json',JSON.stringify({actual:await s.getByLabel('نام',{exact:true}).inputValue()}));
 await expect(s.getByLabel('نام',{exact:true})).toHaveValue('ویرایش تازه هنوز ذخیره نشده');
});

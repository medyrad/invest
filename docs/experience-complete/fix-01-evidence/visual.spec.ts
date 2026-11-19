import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import '/independent/reference.spec';
for(const width of [360,390,768,1440])test('profile consumers and source pairs '+width,async({browser})=>{
 test.setTimeout(240000);
 const c=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
 const p=await c.newPage();
 for(const [name,base] of [['reference','http://expit-reference:3107'],['product','http://127.0.0.1:3109']]){
  await p.goto(base+'/tools/ma-profile');if(name==='reference')await expect(p.getByText('اطلاعات پایه',{exact:true}).first()).toBeVisible({timeout:60000});else await expect(p.locator('.professional-form')).toBeVisible({timeout:30000});await p.evaluate(()=>document.fonts.ready);
  await p.screenshot({path:`/evidence/${name}-profile-guest-${width}.png`,fullPage:true});
 }
 await p.goto('http://127.0.0.1:3109/local-roles');await p.getByRole('button',{name:/ · user$/}).click();await p.waitForURL(u=>!u.pathname.includes('local-roles'));
 for(const route of ['/tools/ma-profile','/profile','/saved']){
  await p.goto('http://127.0.0.1:3109'+route);
  if(route==='/saved')await p.getByRole('tab',{name:/پروفایل حرفه/}).click();
  const form=p.locator('.professional-form');await expect(form).toBeVisible({timeout:30000});
  if(route==='/saved'&&width<1024)expect(await p.locator('.saved-profile-layout').evaluate(e=>getComputedStyle(e).gridTemplateColumns.split(' ').length)).toBe(1);
  await p.evaluate(()=>document.fonts.ready);
  const geometry=await form.evaluate(e=>({width:innerWidth,rect:e.getBoundingClientRect().toJSON(),controls:[...e.querySelectorAll('input,select,button')].map(x=>x.getBoundingClientRect().toJSON())}));
  expect(geometry.controls.filter(r=>r.width>0&&(r.left<0||r.right>width+1))).toEqual([]);
  const slug=route.replaceAll('/','-');await p.screenshot({path:`/evidence/product${slug}-account-${width}.png`,fullPage:true});
  fs.writeFileSync(`/evidence/profile${slug}-${width}.json`,JSON.stringify(geometry));
 }
 await c.close();
});

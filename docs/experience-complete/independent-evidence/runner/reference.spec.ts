import {test,expect} from '@playwright/test';
import fs from 'node:fs';
test.setTimeout(240000);
for(const width of [1440,390,360,768])test('fresh matched land reference '+width,async({browser})=>{
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
 const rows=[];
 for(const [name,base] of [['reference','http://expit-reference:3107'],['product','http://127.0.0.1:3109']]){
  const p=await context.newPage();await p.goto(base+'/tools/land-preparation',{timeout:180000});
  await expect(p.getByRole('heading',{name:/آماده‌سازی/}).first()).toBeVisible({timeout:90000});
  await expect(p.getByText('توسعه زمین، خدمات مالکیتی و حفاظت ملک',{exact:true})).toBeVisible({timeout:30000});
  await p.waitForLoadState('networkidle');
  await p.evaluate(()=>document.fonts.ready);
  const frames=p.frames();for(const f of frames){await f.evaluate(()=>document.fonts.ready).catch(()=>{});}
  await p.screenshot({path:`/evidence/${name}-land-matched-${width}.png`,fullPage:true,animations:'disabled'});
  await p.screenshot({path:`/evidence/${name}-land-viewport-${width}.png`,animations:'disabled'});
  rows.push({name,url:p.url(),width,frameCount:frames.length,frames:await Promise.all(frames.map(f=>f.evaluate(()=>({url:location.pathname,font:getComputedStyle(document.body).fontFamily,ready:document.readyState,text:document.body.innerText.slice(0,10000)}))))});
  await p.close();
 }
 fs.writeFileSync(`/evidence/reference-comparison-${width}.json`,JSON.stringify(rows,null,2));await context.close();
});

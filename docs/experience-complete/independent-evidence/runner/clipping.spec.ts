import {test,expect} from '@playwright/test';
import fs from 'node:fs';
for(const width of [360,390,768,1440])test('hero real hit testing '+width,async({browser})=>{
 const c=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});const p=await c.newPage();await p.goto('/tools/land-preparation');await p.waitForLoadState('networkidle');
 const button=p.getByRole('button',{name:'راهنمای این خدمت',exact:true});await expect(button).toBeVisible();
 const geometry=await button.evaluate(e=>{const r=e.getBoundingClientRect(),parents=[];for(let x=e.parentElement;x;x=x.parentElement){const s=getComputedStyle(x);if(s.overflow!=='visible')parents.push({tag:x.tagName,overflow:s.overflow,rect:x.getBoundingClientRect().toJSON()})}const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {rect:r.toJSON(),hit:hit?.outerHTML.slice(0,500),hitButton:!!hit&&(e===hit||e.contains(hit)),parents,viewport:innerWidth}});
 await p.screenshot({path:`/evidence/hero-stable-${width}.png`,animations:'disabled'});
 fs.writeFileSync(`/evidence/hit-${width}.json`,JSON.stringify(geometry,null,2));
 await button.click({timeout:10000});await p.screenshot({path:`/evidence/guide-sheet-${width}.png`,animations:'disabled'});
 expect(geometry.hitButton).toBe(true);await c.close();
});

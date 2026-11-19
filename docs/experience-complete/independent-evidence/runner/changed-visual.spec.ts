import {test,expect} from '@playwright/test';
import fs from 'node:fs';
test.setTimeout(180000);
for(const route of ['/saved','/tools/ma-profile'])test('changed empty route fresh reference '+route,async({browser})=>{
 const c=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'}),rows=[];
 for(const [name,base] of [['reference','http://expit-reference:3107'],['product','http://127.0.0.1:3109']]){
 const p=await c.newPage();await p.goto(base+route,{timeout:120000});await p.waitForLoadState('networkidle');await p.evaluate(()=>document.fonts.ready);
 const slug=route.split('/').pop();await p.screenshot({path:`/evidence/${name}-${slug}-empty-1440.png`,fullPage:true,animations:'disabled'});
 rows.push({name,route,final:p.url(),text:(await p.locator('body').innerText()).slice(0,12000)});await p.close();
 }fs.writeFileSync('/evidence/changed-'+route.split('/').pop()+'.json',JSON.stringify(rows,null,2));await c.close();
});

import { chromium } from '../../../frontend/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
const out = 'docs/stage4/independent-evidence/visual';
const names = ['hero','main-categories','categories','featured','how','help','footer'];
const browser = await chromium.launch({ executablePath:'/usr/bin/google-chrome', headless:true, args:['--no-sandbox'] });
const result = { browser:browser.version(), viewport:{width:1440,height:1000}, font:'Vazirmatn33', time:'2026-11-17T12:00:00Z', reducedMotion:true, fixture:'advisor-preview-v1', human_approved:false, referenceMode:'production', targetMode:'production', sections:[], reference_errors:[], target_errors:[] };
result.fontSha256 = createHash('sha256').update(await fs.readFile('frontend/public/fonts/Vazirmatn-variable.woff2')).digest('hex');
result.archiveSha256 = JSON.parse(await fs.readFile('docs/stage4/evidence/reference-integrity.json')).archive_sha256;
try {
 for (const [mode,origin] of [['reference','http://127.0.0.1:3107'],['invest',process.env.INVEST_CAPTURE_ORIGIN ?? 'http://127.0.0.1:3108']]) {
  for (let index=0; index<names.length; index++) {
   const context=await browser.newContext({viewport:result.viewport,reducedMotion:'reduce',locale:'fa-IR',timezoneId:'Asia/Tehran'});
   await context.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
   const page=await context.newPage();
   page.on('pageerror',e=>(mode==='reference'?result.reference_errors:result.target_errors).push(e.message.slice(0,1000)));
   await page.clock.install({time:new Date(result.time)});await page.clock.pauseAt(new Date(result.time));
   await page.goto(origin,{waitUntil:'networkidle'});
   if(mode==='invest')await page.locator('[data-section="featured"]').waitFor({state:'attached'});
   await page.evaluate(()=>document.fonts.ready);
   await page.addStyleTag({content:'nextjs-portal{display:none!important}'});
   const element=names[index]==='footer'?page.locator('main > footer'):page.locator('main > section').nth(index);
   const box=await element.boundingBox();
   for(let y=Math.max(0,box.y-100);y<box.y+box.height;y+=650){await page.evaluate(v=>window.scrollTo(0,v),y);await page.clock.runFor(850);}
   await element.scrollIntoViewIfNeeded();
   if(names[index]==='how') {const step=element.getByRole('button',{name:'دلیل هر پیشنهاد کنارش نوشته شده',exact:false});if(await step.count())await step.click();}
   await page.clock.runFor(1800);
   await page.evaluate(() => document.fonts.ready);
   await page.clock.runFor(900);
   const data=await element.evaluate(el=>{const r=el.getBoundingClientRect(),css=getComputedStyle(el),title=el.querySelector('h1,h2');return {width:r.width,height:r.height,font:css.fontFamily,title:title?{text:title.textContent,fontSize:getComputedStyle(title).fontSize,lineHeight:getComputedStyle(title).lineHeight}:null};});
   await element.screenshot({path:`${out}/${names[index]}-${mode}-1440.png`,animations:'disabled'});
   result.sections.push({mode,name:names[index],...data});await context.close();
  }
 }
 await fs.writeFile(`${out}/section-comparison.json`,JSON.stringify(result,null,2)+'\n');
} finally { await browser.close(); }

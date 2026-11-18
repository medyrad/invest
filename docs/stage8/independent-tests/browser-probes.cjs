// شکاف‌های مستقل: F30 در صفحه واقعی، کنترل عملی موبایل و نمایش HTML خروجی.
const path=require('path'),fs=require('fs'),assert=require('assert/strict');
const root=path.resolve(__dirname,'../../..');const {chromium}=require(root+'/frontend/node_modules/@playwright/test');
const out=root+'/docs/stage8/independent-evidence';
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome'});const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));const result={};
try{
 const c={route:'investor',group:['transport'],preferences:{subtypes:['roads'],'adv:roads:revenue':'user','adv:roads:toll':'notallowed'}};
 await page.goto('http://127.0.0.1:3108/opportunities?criteria='+encodeURIComponent(JSON.stringify(c)));
 await page.getByRole('button',{name:/پرسش‌های تخصصی/}).click();
 const q=page.getByRole('combobox',{name:'اختیار اخذ عوارض در مسیر انتخاب‌شده چه وضعیتی دارد؟'});await q.waitFor();assert.equal(await q.inputValue(),'notallowed');
 await page.getByText('راهنمای تخصصی بر پایه پاسخ‌های فعال',{exact:true}).click();await page.getByText('مانع ارزیابی قطعی وجود دارد؛ درخواست کمک از کارشناس مجاز است.',{exact:true}).waitFor();
 const feeds=await page.evaluate(async criteria=>{const call=async c=>{const r=await fetch('/api/v1/core/opportunities?criteria='+encodeURIComponent(JSON.stringify(c)));return {status:r.status,data:await r.json()}};const a=await call(criteria);const clean=JSON.parse(JSON.stringify(criteria));delete clean.preferences['adv:roads:toll'];return [a,await call(clean)]},c);
 assert(feeds.every(x=>x.status===200));const data=feeds.map(x=>x.data);assert.deepEqual(data[0].items.map(x=>[x.id,x.matching]),data[1].items.map(x=>[x.id,x.matching]));result.f30={passed:true,items:data[0].items.length,blockedAssessmentVisible:true,unchangedRanking:true};await page.screenshot({path:out+'/roads-block-1440.png',fullPage:true});
 await page.setViewportSize({width:360,height:780});await page.goto('http://127.0.0.1:3108/tools/land-preparation');const progress=page.locator('.service-progress-description strong');await progress.waitFor();const bounds=await progress.boundingBox();result.mobileProgress={width:bounds.width,height:bounds.height,text:await progress.innerText()};
 const next=page.getByRole('button',{name:'پرسش بعدی بی‌پاسخ'});await next.click();result.mobileProgress.jumpFocused=await page.evaluate(()=>document.activeElement?.getAttribute('aria-label'));assert(result.mobileProgress.jumpFocused);await page.keyboard.press('Tab');result.mobileProgress.tabFocus=await page.evaluate(()=>document.activeElement?.tagName);await page.screenshot({path:out+'/mobile-progress-360.png',fullPage:false});
 result.mobileProgress.readabilityPassed=bounds.width>=100&&bounds.height<120;
 const report=fs.readFileSync(out+'/ideas-report.html','utf8');await page.setContent(report);result.mobileReport={overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),title:await page.title()};await page.screenshot({path:out+'/ideas-report-360.png',fullPage:true});assert(!result.mobileReport.overflow);
 result.pageErrors=errors;assert.deepEqual(errors,[]);fs.writeFileSync(out+'/browser-probes.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(!result.mobileProgress.readabilityPassed)process.exitCode=1;
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});

const fs=require('node:fs'),path=require('node:path');const root=path.resolve(__dirname,'../../..');const {chromium}=require(path.join(root,'frontend/node_modules/@playwright/test'));
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
 const results={viewport:{width:1440,height:1000},human_approved:false,scope:'Fresh same-browser dialog crops; complete S04 background excluded; empty mobile step, first office image, fonts ready, reduced motion',cases:[]};
 try{for(const [name,origin,button,selector] of [['reference','http://127.0.0.1:3107',/^ورود$/,'[data-slot="dialog-content"]'],['invest','http://127.0.0.1:3108',/^ورود به حساب$/,'dialog']]){
  const context=await browser.newContext({viewport:results.viewport,locale:'fa-IR',timezoneId:'Asia/Tehran',reducedMotion:'reduce'});await context.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
  const page=await context.newPage();await page.goto(origin,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);await page.getByRole('button',{name:button}).first().click();const dialog=page.locator(selector);await dialog.waitFor();await dialog.locator('img').first().evaluate(img=>img.decode());await page.waitForTimeout(350);
  await dialog.screenshot({path:path.join(root,'docs/stage3/independent-evidence/visual-'+name+'-1440.png'),animations:'disabled'});
  const dimensions=await dialog.evaluate(el=>{const r=el.getBoundingClientRect();return {width:r.width,height:r.height,font:getComputedStyle(el).fontFamily}});
  results.cases.push({name,dimensions});await context.close();
 }}finally{await browser.close();}
 fs.writeFileSync(path.join(root,'docs/stage3/independent-evidence/visual-comparison.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
})().catch(e=>{console.error(e.message);process.exitCode=1});
